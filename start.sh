#!/bin/bash

# Vocode Application Startup Script
# This script helps you get started with the Vocode application

set -e

echo "🎤 Vocode Application Setup"
echo "=========================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📋 Setting up environment variables..."
    cp .env.example .env
    echo "✅ Created .env file from template"
    echo "⚠️  Please edit .env with your actual API keys before continuing"
    echo ""
    echo "Required keys:"
    echo "  - TWILIO_ACCOUNT_SID"
    echo "  - TWILIO_AUTH_TOKEN"
    echo "  - TWILIO_PHONE_NUMBER"
    echo "  - OPENAI_API_KEY"
    echo "  - ELEVEN_LABS_API_KEY"
    echo "  - DEEPGRAM_API_KEY"
    echo ""
    read -p "Press Enter after you've configured your .env file..."
fi

# Check for Docker
if command -v docker &> /dev/null; then
    echo "🐳 Docker detected!"
    
    # Check if docker-compose is available
    if command -v docker-compose &> /dev/null; then
        echo "📦 Starting application with Docker Compose..."
        docker-compose up --build
    else
        echo "📦 Starting application with Docker..."
        echo "🔨 Building Docker image..."
        docker build -t vocode-app .
        
        echo "🚀 Starting Redis..."
        docker run -d --name vocode-redis -p 6379:6379 redis:7-alpine || true
        
        echo "🚀 Starting Vocode application..."
        docker run -p 8000:8000 --link vocode-redis:redis --env-file .env vocode-app
    fi
elif command -v poetry &> /dev/null; then
    echo "📝 Poetry detected!"
    echo "📦 Installing dependencies..."
    poetry install --extras "telephony"
    
    echo "🚀 Starting application with Poetry..."
    poetry run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
else
    echo "⚠️  Neither Docker nor Poetry found!"
    echo "Please install one of the following:"
    echo "  - Docker: https://docs.docker.com/get-docker/"
    echo "  - Poetry: https://python-poetry.org/docs/#installation"
    echo ""
    echo "Alternatively, you can use pip:"
    echo "  pip install -r requirement.txt"
    echo "  uvicorn main:app --host 0.0.0.0 --port 8000"
    exit 1
fi
