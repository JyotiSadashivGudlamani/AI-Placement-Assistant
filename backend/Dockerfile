# Dockerfile for FastAPI Backend
FROM python:3.13-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install system dependencies needed for native builds and text processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY backend ./backend

# Create runtime directories for ChromaDB and uploads
RUN mkdir -p /app/backend/chroma_db /app/backend/uploads

# Default container configuration
# host.docker.internal connects the container to the Windows host running Ollama
ENV OLLAMA_BASE_URL=http://host.docker.internal:11434 \
    OLLAMA_MODEL_NAME=llama3.2:3b \
    MONGO_URI=mongodb://mongo:27017 \
    MONGO_DB_NAME=ai_placement_prep \
    CHROMA_DB_DIR=/app/backend/chroma_db \
    LOG_LEVEL=INFO

EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
