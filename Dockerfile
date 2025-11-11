# ==========================================
# WWMAA Backend - Multi-Stage Docker Build
# ==========================================
# Optimized for Railway deployment with minimal image size
# Supports development, staging, and production environments

# ==========================================
# Stage 1: Builder
# ==========================================
FROM python:3.9-slim as builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ==========================================
# Stage 2: Runtime
# ==========================================
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Copy Python dependencies from builder
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=appuser:appuser backend/ /app/backend/

# Copy Railway startup script for debugging
COPY --chown=appuser:appuser railway-start.sh /app/railway-start.sh

# Create necessary directories and make startup script executable
RUN mkdir -p /var/log/wwmaa && \
    chown -R appuser:appuser /var/log/wwmaa && \
    chmod +x /app/railway-start.sh

# Switch to non-root user
USER appuser

# Environment variables (overrideable at runtime)
ENV PYTHON_ENV=production \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

# Expose port (Railway will override with $PORT)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT}/api/health || exit 1

# Start command with Railway debug script
# This script validates environment variables and provides detailed startup logging
CMD ["/app/railway-start.sh"]
