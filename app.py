"""
app.py
Flask REST API for Product Management
Phase 1: Application Design & Development
"""

import os
import time
import uuid
from datetime import datetime
from functools import wraps

from flask import Flask, jsonify, request, Response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import UUID
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# Configure logging BEFORE creating the app so handlers exist early
from app_logging import *

# --------------------------------------------------------------------------
# Flask Application Setup
# --------------------------------------------------------------------------
app = Flask(__name__)

# Load environment variables (for secure DB credentials)
app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME')}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize SQLAlchemy ORM
db = SQLAlchemy(app)

# Load API key from environment for authentication
API_KEY = os.getenv("API_KEY")

# --------------------------------------------------------------------------
# Authentication decorator
# --------------------------------------------------------------------------
def require_api_key(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if request.headers.get("X-API-Key") != API_KEY:
            return jsonify({"error": "Unauthorized"}), 401
        return fn(*args, **kwargs)
    return wrapper

# --------------------------------------------------------------------------
# Database Model
# --------------------------------------------------------------------------
class Product(db.Model):
    """Product table schema"""

    __tablename__ = "product"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2))
    quantity = db.Column(db.Integer)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=datetime.utcnow)

    def to_dict(self):
        """Convert model to dictionary for JSON responses"""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "price": float(self.price) if self.price is not None else None,
            "quantity": self.quantity,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

# --------------------------------------------------------------------------
# Prometheus metrics
# --------------------------------------------------------------------------
REQS = Counter("http_requests_total", "HTTP requests", ["method", "path", "status"])
LAT = Histogram("request_latency_seconds", "Request latency", buckets=[0.05, 0.1, 0.2, 0.4, 0.8, 1.6, 3.2])

@app.before_request
def _pm_start():
    request._pm_t0 = time.time()

@app.after_request
def _pm_end(resp):
    try:
        dt = time.time() - getattr(request, "_pm_t0", time.time())
        LAT.observe(dt)
        # convert status to string for label stability
        REQS.labels(request.method, request.path, str(resp.status_code)).inc()
    except Exception:
        pass
    return resp

@app.route("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

# --------------------------------------------------------------------------
# Request logging (structured) - must be defined after app creation
# --------------------------------------------------------------------------
@app.before_request
def _start_timer():
    request._t0 = time.time()

@app.after_request
def _log_request(resp):
    try:
        dt_ms = int((time.time() - getattr(request, "_t0", time.time())) * 1000)
        app.logger.info(
            "request",
            extra={
                "method": request.method,
                "path": request.path,
                "status": resp.status_code,
                "latency_ms": dt_ms,
                "remote_ip": request.headers.get("X-Forwarded-For", request.remote_addr),
                "user_agent": request.user_agent.string,
            },
        )
    except Exception:
        app.logger.exception("failed to log request")
    return resp

# --------------------------------------------------------------------------
# API Routes
# --------------------------------------------------------------------------
@app.route("/db-check")
def db_check():
    try:
        with app.app_context():
            result = db.session.execute(text("SELECT current_database(), inet_server_addr();"))
            db_name, server_ip = result.fetchone()
            return jsonify({"status": "Connected ✅", "database": db_name, "server_ip": str(server_ip)})
    except Exception as e:
        app.logger.exception("DB check failed")
        return jsonify({"status": "Connection failed ❌", "error": str(e)}), 500

@app.route("/")
def index():
    return jsonify({"message": "Flask API is running successfully!okok"}), 200

@app.route("/health", methods=["GET"])
def health():
    return "OK", 200

# Products endpoints
@app.route("/products", methods=["GET"])
def get_products():
    products = Product.query.all()
    return jsonify([p.to_dict() for p in products]), 200

@app.route("/products/<uuid:product_id>", methods=["GET"])
def get_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    return jsonify(product.to_dict()), 200

@app.route("/products", methods=["POST"])
@require_api_key
def create_product():
    data = request.get_json()
    if not data or "name" not in data:
        return jsonify({"error": "Missing required field 'name'"}), 400

    new_product = Product(
        name=data["name"],
        description=data.get("description"),
        price=data.get("price"),
        quantity=data.get("quantity", 0),
    )

    db.session.add(new_product)
    db.session.commit()

    return jsonify({"message": "Product created successfully", "product": new_product.to_dict()}), 201

@app.route("/products/<uuid:product_id>", methods=["PUT"])
@require_api_key
def update_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "No update data provided"}), 400

    product.name = data.get("name", product.name)
    product.description = data.get("description", product.description)
    product.price = data.get("price", product.price)
    product.quantity = data.get("quantity", product.quantity)
    product.updated_at = datetime.utcnow()

    db.session.commit()
    return jsonify({"message": "Product updated successfully", "product": product.to_dict()}), 200

@app.route("/products/<uuid:product_id>", methods=["DELETE"])
@require_api_key
def delete_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": "Product deleted successfully"}), 200

# --------------------------------------------------------------------------
# DB initialization helper (run once manually if needed)
# --------------------------------------------------------------------------
def init_db():
    """Create database tables if they don't exist. Run in app context."""
    with app.app_context():
        db.create_all()
        app.logger.info("Database tables ensured.")

# --------------------------------------------------------------------------
# Main entry point
# --------------------------------------------------------------------------
if __name__ == "__main__":
    init_on_start = os.getenv("INIT_DB_ON_START", "false").lower() in ("1", "true", "yes")
    if init_on_start:
        init_db()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=os.getenv("FLASK_DEBUG", "false").lower() in ("1", "true"))
