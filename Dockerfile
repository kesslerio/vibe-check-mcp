# Multi-stage Dockerfile for Vibe Compass MCP Server
# Optimized for both development and production use

# Base stage with common dependencies
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash mcp

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Development stage
FROM base as development

# Install development dependencies
RUN pip install --no-cache-dir \
    pytest \
    pytest-cov \
    black \
    isort \
    mypy

# Copy source code
COPY src/ ./src/
COPY data/ ./data/
COPY tests/ ./tests/

# Change ownership to mcp user
RUN chown -R mcp:mcp /app

# Switch to non-root user
USER mcp

# Expose port for MCP server
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import sys; sys.path.insert(0, '/app/src'); \
    from vibe_compass.server import run_server; print('Health check passed')" || exit 1

# Default command for development
CMD ["python", "-m", "vibe_compass.server"]

# Production stage
FROM base as production

# Copy only necessary files for production
COPY src/ ./src/
COPY data/ ./data/

# Create config directory for mounting
RUN mkdir -p /app/config && chown -R mcp:mcp /app

# Switch to non-root user
USER mcp

# Expose port for MCP server
EXPOSE 8000

# Production health check (more robust)
HEALTHCHECK --interval=60s --timeout=15s --start-period=120s --retries=5 \
    CMD python -c "import sys; sys.path.insert(0, '/app/src'); \
    from vibe_compass.server import run_server; print('Production health check passed')" || exit 1

# Optimized production command
CMD ["python", "-O", "-m", "vibe_compass.server"]

# Default stage is development
FROM development