FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy shared packages
COPY packages/ /packages/

# Copy service
COPY services/metadata-extractor/ /app/

# Install dependencies
RUN pip install --no-cache-dir -e /packages/alice-events && \
    pip install --no-cache-dir -e /packages/alice-models && \
    pip install --no-cache-dir -e /packages/alice-config && \
    pip install --no-cache-dir -e /packages/alice-utils && \
    pip install --no-cache-dir -e .

EXPOSE 8003

CMD ["uvicorn", "metadata_extractor.main:app", "--host", "0.0.0.0", "--port", "8003"]