# Multi-stage build for asset processor service
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user first
RUN useradd -m -u 1000 alice

# Copy installed packages from builder to alice user
COPY --from=builder --chown=alice:alice /root/.local /home/alice/.local
ENV PATH=/home/alice/.local/bin:$PATH

# Copy application code
COPY src/ ./src/
COPY pyproject.toml .

# Install the package
RUN pip install --no-deps -e .

# Change ownership and switch to alice user
RUN chown -R alice:alice /app
USER alice

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8001/health').raise_for_status()"

# Expose port
EXPOSE 8001

# Run the service
CMD ["python", "-m", "uvicorn", "asset_processor.simple_main:app", "--host", "0.0.0.0", "--port", "8001"]