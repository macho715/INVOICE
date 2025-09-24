# Multi-stage build for HVDC Project Invoice Audit System
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create and set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Install the package
RUN pip install --no-cache-dir -e .

# Production stage
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.local/bin:$PATH"

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Create app directory
WORKDIR /app

# Copy Python dependencies from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --from=builder /app .

# Create necessary directories
RUN mkdir -p /app/out /app/io /app/logs && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import invoice_audit; print('OK')" || exit 1

# Expose port (if web interface is added)
EXPOSE 8000

# Default command
CMD ["python", "shpt_audit_system.py", "--help"]

# Labels for metadata
LABEL maintainer="HVDC Project Team <hvdc-project@samsung.com>"
LABEL version="1.0.0"
LABEL description="HVDC Project Invoice Audit System - Samsung C&T Logistics & ADNOC·DSV Partnership"
LABEL org.opencontainers.image.source="https://github.com/macho715/INVOICE"
LABEL org.opencontainers.image.documentation="https://github.com/macho715/INVOICE#readme"
LABEL org.opencontainers.image.licenses="MIT"
