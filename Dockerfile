# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set work directory
WORKDIR /app

# Install system dependencies required for audio processing and Redis
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libasound2-dev \
    portaudio19-dev \
    redis-server \
    curl \
    wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirement.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirement.txt

# Copy application code
COPY . .

# Create a directory for audio files if needed
RUN mkdir -p /app/audio_files

# Expose the port the app runs on
EXPOSE 8000

# Create a startup script that handles Redis and the application
RUN echo '#!/bin/bash\n\
# Start Redis server in the background\n\
redis-server --daemonize yes --bind 0.0.0.0 --port 6379\n\
\n\
# Wait for Redis to start\n\
sleep 2\n\
\n\
# Start the FastAPI application\n\
exec uvicorn main:app --host 0.0.0.0 --port 8000\n\
' > /app/start.sh

# Make the startup script executable
RUN chmod +x /app/start.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/docs || exit 1

# Start the application
CMD ["/app/start.sh"]
