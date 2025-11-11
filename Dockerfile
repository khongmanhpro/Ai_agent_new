# Use Python 3.11 slim image
FROM python:3.11-slim

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
RUN pip install --upgrade pip && \
    pip install --no-cache-dir flask flask-cors flask-swagger-ui requests websockets && \
    pip install --no-cache-dir numpy pandas nltk neo4j openai tiktoken && \
    pip install --no-cache-dir faiss-cpu sentence-transformers

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
