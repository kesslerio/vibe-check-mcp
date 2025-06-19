# Simple Dockerfile for Vibe Check MCP Server - Smithery deployment
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and data
COPY src/ ./src/
COPY data/ ./data/
COPY VERSION .

# Set Python path
ENV PYTHONPATH=/app/src

# Run the MCP server
CMD ["python", "-m", "vibe_check.server"]