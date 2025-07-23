FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY test_product/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY test_product/ /app/test_product/

# Create log directory
RUN mkdir -p /app/logs

# Set environment variables
ENV PYTHONPATH=/app
ENV TEST_PRODUCT_LOG_FILE=/app/logs/test_product.log
ENV TEST_PRODUCT_HOST=0.0.0.0
ENV TEST_PRODUCT_PORT=8000

# Expose the application port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["python", "-m", "test_product.main"]