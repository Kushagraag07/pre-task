"""
app.py
Flask REST API for Product Management
Phase 1: Application Design & Development

Features:
✅ Uses PostgreSQL (Cloud SQL) with SQLAlchemy ORM
✅ UUID as primary key (secure & globally unique)
✅ Full CRUD endpoints (GET, POST, PUT, DELETE)
✅ Ready for Google Cloud SQL (Auth Proxy or direct)
"""

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
import os

# -----------------------------------------------------------------------------
# 1️⃣ Flask Application Setup
# -----------------------------------------------------------------------------
app = Flask(__name__)

# Load environment variables (for secure DB credentials)
# Example .env file:
# DB_USER=postgres
# DB_PASS=yourpassword
# DB_NAME=products_db
# DB_HOST=127.0.0.1
# DB_PORT=5432
app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME')}"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy ORM
db = SQLAlchemy(app)


# -----------------------------------------------------------------------------
# 2️⃣ Database Model
# -----------------------------------------------------------------------------
class Product(db.Model):
    """Product table schema"""

    __tablename__ = 'product'

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
            "price": float(self.price) if self.price else None,
            "quantity": self.quantity,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# -----------------------------------------------------------------------------
# 3️⃣ API Routes
# -----------------------------------------------------------------------------
# database connection check route
@app.route('/db-check')
def db_check():
    try:
        with app.app_context():
            # Wrap raw SQL in text()
            result = db.session.execute(text("SELECT current_database(), inet_server_addr();"))
            db_name, server_ip = result.fetchone()
            return jsonify({
                "status": "Connected ✅",
                "database": db_name,
                "server_ip": str(server_ip)
            })
    except Exception as e:
        return jsonify({"status": "Connection failed ❌", "error": str(e)}), 500

# Health check route
@app.route('/')
def index():
    return jsonify({"message": "Flask API is running successfully!"}), 200


# ------------------- [GET] /products -------------------
@app.route('/products', methods=['GET'])
def get_products():
    """Retrieve all products"""
    products = Product.query.all()
    return jsonify([p.to_dict() for p in products]), 200


# ------------------- [GET] /products/<id> -------------------
@app.route('/products/<uuid:product_id>', methods=['GET'])
def get_product(product_id):
    """Retrieve a single product by ID"""
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    return jsonify(product.to_dict()), 200


# ------------------- [POST] /products -------------------
@app.route('/products', methods=['POST'])
def create_product():
    """Create a new product"""
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({"error": "Missing required field 'name'"}), 400

    new_product = Product(
        name=data['name'],
        description=data.get('description'),
        price=data.get('price'),
        quantity=data.get('quantity', 0),
    )

    db.session.add(new_product)
    db.session.commit()

    return jsonify({"message": "Product created successfully", "product": new_product.to_dict()}), 201


# ------------------- [PUT] /products/<id> -------------------
@app.route('/products/<uuid:product_id>', methods=['PUT'])
def update_product(product_id):
    """Update an existing product by ID"""
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "No update data provided"}), 400

    product.name = data.get('name', product.name)
    product.description = data.get('description', product.description)
    product.price = data.get('price', product.price)
    product.quantity = data.get('quantity', product.quantity)
    product.updated_at = datetime.utcnow()

    db.session.commit()
    return jsonify({"message": "Product updated successfully", "product": product.to_dict()}), 200


# ------------------- [DELETE] /products/<id> -------------------
@app.route('/products/<uuid:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """Delete a product by ID"""
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": "Product deleted successfully"}), 200


# -----------------------------------------------------------------------------
# 4️⃣ Initialize Database (Run once when starting for the first time)
#
# Note: Flask 3 removed the `before_first_request` decorator on the app object.
# To support Flask 3+ and explicit startup, create a helper `init_db()` and call
# it inside `if __name__ == '__main__'` using `app.app_context()` so tables are
# created when the app is started directly.
# -----------------------------------------------------------------------------
def init_db():
    """Create database tables if they don't exist."""
    db.create_all()


# -----------------------------------------------------------------------------
# 5️⃣ Main entry point
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    # Debug=True is fine for local dev. For Cloud Run / production, set to False.
    app.run(host='0.0.0.0', port=5000, debug=True)
