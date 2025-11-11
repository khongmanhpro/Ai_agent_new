# Use Python 3.9 slim image (more stable for ML packages)
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    git \
    libssl-dev \
    libffi-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY core/requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Install MiniRAG framework locally
COPY MiniRAG/ ./MiniRAG/
RUN cd MiniRAG && pip install -e .

# Copy project files
COPY . .

# Create necessary directories
RUN mkdir -p logs/insurance_rag data

# Set environment variables
ENV PYTHONPATH=/app:$PYTHONPATH
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${API_PORT:-8001}/health || exit 1

# Expose port
EXPOSE ${API_PORT:-8001}

# Default command
CMD ["python", "core/insurance_api_simple.py"]
