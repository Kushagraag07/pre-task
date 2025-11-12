# Use slim Python base
FROM python:3.11-slim

# Create app user for security (avoid running as root)
RUN groupadd -r app && useradd -r -g app app

WORKDIR /app

# Prevent Python from writing .pyc files and enable unbuffered stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# App logging level (read by your app_logging.py)
ENV LOG_LEVEL=INFO
ENV PORT=5000

# Install system deps and create non-root user (--no-install-recommends to keep image size small)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
 && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app

# Change ownership and switch to non-root user
RUN chown -R app:app /app
USER app

# Start gunicorn binding to 0.0.0.0:5000
# - --access-logfile - : write access logs to stdout
# - --error-logfile  - : write error logs to stderr
# - --capture-output   : capture stdout/stderr from workers (optional but helpful)
# - --log-level        : gunicorn internal log level (info/debug)
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app", "--workers", "2", "--threads", "4", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "--capture-output", "--log-level", "info"]
