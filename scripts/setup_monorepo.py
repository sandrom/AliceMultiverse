#!/usr/bin/env python3
"""Setup script for AliceMultiverse monorepo structure."""

import os
import sys
import shutil
from pathlib import Path
import subprocess


def create_directory_structure():
    """Create the monorepo directory structure."""
    directories = [
        "packages/alice-config/alice_config",
        "packages/alice-config/tests",
        "packages/alice-utils/alice_utils", 
        "packages/alice-utils/tests",
        "services/alice-interface/src/alice_interface",
        "services/alice-interface/tests",
        "services/asset-processor/src/asset_processor",
        "services/asset-processor/tests",
        "services/quality-analyzer/src/quality_analyzer",
        "services/quality-analyzer/tests",
        "services/metadata-extractor/src/metadata_extractor",
        "services/metadata-extractor/tests",
    ]
    
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created {dir_path}")


def create_package_files():
    """Create remaining package configuration files."""
    
    # alice-config package
    config_pyproject = """[project]
name = "alice-config"
version = "0.1.0"
description = "Configuration management for AliceMultiverse"
readme = "README.md"
requires-python = ">=3.9"
dependencies = [
    "omegaconf>=2.3.0",
    "pydantic>=2.0.0",
]

[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[tool.setuptools]
packages = ["alice_config"]
"""
    
    # alice-utils package  
    utils_pyproject = """[project]
name = "alice-utils"
version = "0.1.0"
description = "Common utilities for AliceMultiverse"
readme = "README.md"
requires-python = ">=3.9"
dependencies = [
    "pillow>=10.0.0",
    "numpy>=1.24.0",
]

[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[tool.setuptools]
packages = ["alice_utils"]
"""
    
    files = {
        "packages/alice-config/pyproject.toml": config_pyproject,
        "packages/alice-utils/pyproject.toml": utils_pyproject,
    }
    
    for file_path, content in files.items():
        with open(file_path, "w") as f:
            f.write(content.strip())
        print(f"✓ Created {file_path}")


def create_service_templates():
    """Create basic service templates."""
    
    service_pyproject_template = """[project]
name = "{service_name}"
version = "0.1.0"
description = "{description}"
readme = "README.md"
requires-python = ">=3.9"
dependencies = [
    "alice-events @ file://../../packages/alice-events",
    "alice-models @ file://../../packages/alice-models",
    "alice-config @ file://../../packages/alice-config",
    "alice-utils @ file://../../packages/alice-utils",
    "fastapi>=0.100.0",
    "uvicorn>=0.23.0",
]

[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[tool.setuptools]
packages = ["{package_name}"]
package-dir = {{"" = "src"}}
"""

    dockerfile_template = """FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copy shared packages
COPY packages/ /packages/

# Copy service
COPY services/{service_name}/ /app/

# Install dependencies
RUN pip install --no-cache-dir -e /packages/alice-events && \\
    pip install --no-cache-dir -e /packages/alice-models && \\
    pip install --no-cache-dir -e /packages/alice-config && \\
    pip install --no-cache-dir -e /packages/alice-utils && \\
    pip install --no-cache-dir -e .

EXPOSE {port}

CMD ["uvicorn", "{package_name}.main:app", "--host", "0.0.0.0", "--port", "{port}"]
"""

    claude_context_template = """# {service_name} Context

This service handles {description}.

## Responsibilities
- {responsibility1}
- {responsibility2}

## Events
### Publishes
- {event1}
- {event2}

### Subscribes
- {event3}
- {event4}

## API Endpoints
- GET /health - Health check
- GET /metrics - Prometheus metrics
{endpoints}

## Dependencies
- alice-events: Event infrastructure
- alice-models: Data models
- alice-config: Configuration
- alice-utils: Utilities
"""

    services = {
        "alice-interface": {
            "description": "Main orchestration and AI interface service",
            "package_name": "alice_interface",
            "port": 8000,
        },
        "asset-processor": {
            "description": "Media processing and organization service",
            "package_name": "asset_processor", 
            "port": 8001,
        },
        "quality-analyzer": {
            "description": "Quality assessment pipeline service",
            "package_name": "quality_analyzer",
            "port": 8002,
        },
        "metadata-extractor": {
            "description": "Metadata extraction and search service",
            "package_name": "metadata_extractor",
            "port": 8003,
        }
    }
    
    for service_name, config in services.items():
        service_dir = f"services/{service_name}"
        
        # Create pyproject.toml
        pyproject_content = service_pyproject_template.format(
            service_name=service_name,
            description=config["description"],
            package_name=config["package_name"]
        )
        with open(f"{service_dir}/pyproject.toml", "w") as f:
            f.write(pyproject_content.strip())
        
        # Create Dockerfile
        dockerfile_content = dockerfile_template.format(
            service_name=service_name,
            package_name=config["package_name"],
            port=config["port"]
        )
        with open(f"{service_dir}/Dockerfile", "w") as f:
            f.write(dockerfile_content.strip())
        
        # Create .claude-context.md
        context_content = claude_context_template.format(
            service_name=service_name.replace("-", " ").title(),
            description=config["description"],
            responsibility1="TODO: Add specific responsibility",
            responsibility2="TODO: Add specific responsibility",
            event1="TODO: Add event type",
            event2="TODO: Add event type",
            event3="TODO: Add event type", 
            event4="TODO: Add event type",
            endpoints="# TODO: Add service-specific endpoints"
        )
        with open(f"{service_dir}/.claude-context.md", "w") as f:
            f.write(context_content.strip())
        
        # Create __init__.py files
        Path(f"{service_dir}/src/{config['package_name']}/__init__.py").touch()
        Path(f"{service_dir}/tests/__init__.py").touch()
        
        print(f"✓ Created templates for {service_name}")


def create_docker_compose():
    """Create docker-compose.yml for local development."""
    
    docker_compose = """version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  alice-interface:
    build:
      context: .
      dockerfile: services/alice-interface/Dockerfile
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379
      - SERVICE_NAME=alice-interface
    depends_on:
      redis:
        condition: service_healthy
    volumes:
      - ./services/alice-interface:/app
      - ./packages:/packages

  asset-processor:
    build:
      context: .
      dockerfile: services/asset-processor/Dockerfile
    ports:
      - "8001:8001"
    environment:
      - REDIS_URL=redis://redis:6379
      - SERVICE_NAME=asset-processor
    depends_on:
      redis:
        condition: service_healthy
    volumes:
      - ./services/asset-processor:/app
      - ./packages:/packages
      - ./inbox:/inbox
      - ./organized:/organized

  quality-analyzer:
    build:
      context: .
      dockerfile: services/quality-analyzer/Dockerfile
    ports:
      - "8002:8002"
    environment:
      - REDIS_URL=redis://redis:6379
      - SERVICE_NAME=quality-analyzer
    depends_on:
      redis:
        condition: service_healthy
    volumes:
      - ./services/quality-analyzer:/app
      - ./packages:/packages

  metadata-extractor:
    build:
      context: .
      dockerfile: services/metadata-extractor/Dockerfile
    ports:
      - "8003:8003"
    environment:
      - REDIS_URL=redis://redis:6379
      - SERVICE_NAME=metadata-extractor
    depends_on:
      redis:
        condition: service_healthy
    volumes:
      - ./services/metadata-extractor:/app
      - ./packages:/packages

volumes:
  redis-data:
"""
    
    with open("docker-compose.yml", "w") as f:
        f.write(docker_compose.strip())
    print("✓ Created docker-compose.yml")


def main():
    """Run the monorepo setup."""
    print("Setting up AliceMultiverse monorepo structure...")
    
    # Create directories
    create_directory_structure()
    
    # Create package files
    create_package_files()
    
    # Create service templates
    create_service_templates()
    
    # Create docker-compose
    create_docker_compose()
    
    print("\n✅ Monorepo structure created successfully!")
    print("\nNext steps:")
    print("1. Run 'make install-dev' to install all packages")
    print("2. Run 'make test' to verify everything works")
    print("3. Start development with 'docker-compose up'")


if __name__ == "__main__":
    main()