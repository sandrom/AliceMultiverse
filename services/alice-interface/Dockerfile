FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including PostgreSQL client for migrations
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy shared packages
COPY packages/ /packages/

# Copy service
COPY services/alice-interface/ /app/

# Copy main alicemultiverse package for database models and migrations
COPY alicemultiverse/ /app/alicemultiverse/
COPY alembic/ /app/alembic/
COPY alembic.ini /app/
COPY pyproject.toml /app/

# Copy entrypoint script
COPY scripts/docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Install dependencies
RUN pip install --no-cache-dir -e /packages/alice-events && \
    pip install --no-cache-dir -e /packages/alice-models && \
    pip install --no-cache-dir -e /packages/alice-config && \
    pip install --no-cache-dir -e /packages/alice-utils && \
    pip install --no-cache-dir -e . && \
    pip install --no-cache-dir alembic psycopg2-binary

EXPOSE 8000

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["uvicorn", "alice_interface.main:app", "--host", "0.0.0.0", "--port", "8000"]