# Use slim Python base
FROM python:3.11-slim

# Create app user for security
RUN groupadd -r app && useradd -r -g app app

WORKDIR /app

# Prevent Python from writing .pyc files and enable unbuffered stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system deps and create non-root user
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

# Use a modest number of workers for small instances; bind to 0.0.0.0
ENV PORT=5000
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app", "--workers", "2", "--threads", "4", "--timeout", "120"]
