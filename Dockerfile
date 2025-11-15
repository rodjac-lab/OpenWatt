# Multi-stage Dockerfile for OpenWatt API (FastAPI)
# Production-ready with optimization and security best practices

# Stage 1: Builder - Install dependencies
FROM python:3.11-slim as builder

WORKDIR /build

# Install system dependencies for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime - Minimal production image
FROM python:3.11-slim

# Create non-root user for security
RUN useradd -m -u 1000 openwatt && \
    mkdir -p /app && \
    chown -R openwatt:openwatt /app

WORKDIR /app

# Copy Python dependencies from builder stage
COPY --from=builder --chown=openwatt:openwatt /root/.local /home/openwatt/.local

# Copy application code
COPY --chown=openwatt:openwatt api/ ./api/
COPY --chown=openwatt:openwatt db/ ./db/
COPY --chown=openwatt:openwatt parsers/ ./parsers/
COPY --chown=openwatt:openwatt ingest/ ./ingest/
COPY --chown=openwatt:openwatt scripts/ ./scripts/

# Set PATH to include user-installed packages
ENV PATH=/home/openwatt/.local/bin:$PATH

# Switch to non-root user
USER openwatt

# Expose port 8000
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5)" || exit 1

# Run the application
CMD ["uvicorn", "api.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
