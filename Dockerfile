# Dockerfile for Google Cloud Run (100% free tier)
FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy app files
COPY . .

# Create database on startup
RUN python init_db.py

# Use gunicorn for production (Cloud Run compatible)
CMD exec gunicorn --bind :$PORT --workers 1 --worker-class eventlet -w 1 app:app
