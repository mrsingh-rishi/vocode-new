#!/bin/bash

# Docker setup validation script

echo "🐳 Docker Setup Validation"
echo "=========================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
        return 1
    fi
}

# Function to print warning
print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Check if Docker is installed
echo "Checking Docker installation..."
docker --version > /dev/null 2>&1
print_status $? "Docker is installed"

# Check if Docker is running
echo "Checking if Docker is running..."
docker info > /dev/null 2>&1
print_status $? "Docker daemon is running"

# Check if docker-compose is available
echo "Checking Docker Compose..."
if command -v docker-compose &> /dev/null; then
    docker-compose --version > /dev/null 2>&1
    print_status $? "Docker Compose is installed"
elif docker compose version &> /dev/null; then
    print_status 0 "Docker Compose (plugin) is available"
else
    print_status 1 "Docker Compose is not available"
fi

# Check if .env file exists
echo "Checking environment configuration..."
if [ -f .env ]; then
    print_status 0 ".env file exists"
    
    # Check for required environment variables
    required_vars=("TWILIO_ACCOUNT_SID" "TWILIO_AUTH_TOKEN" "TWILIO_PHONE_NUMBER" "OPENAI_API_KEY" "ELEVEN_LABS_API_KEY" "DEEPGRAM_API_KEY")
    
    for var in "${required_vars[@]}"; do
        if grep -q "^${var}=" .env && ! grep -q "^${var}=your_.*_here" .env && ! grep -q "^${var}=$" .env; then
            print_status 0 "$var is configured"
        else
            print_warning "$var is not properly configured in .env"
        fi
    done
else
    print_status 1 ".env file does not exist"
    echo "Run: cp .env.example .env and configure it"
fi

# Test Docker build
echo "Testing Docker build..."
docker build -t vocode-app-test . > /dev/null 2>&1
if print_status $? "Docker image builds successfully"; then
    # Clean up test image
    docker rmi vocode-app-test > /dev/null 2>&1
fi

# Check port availability
echo "Checking port availability..."
if ! lsof -i :8000 > /dev/null 2>&1; then
    print_status 0 "Port 8000 is available"
else
    print_warning "Port 8000 is already in use"
fi

if ! lsof -i :6379 > /dev/null 2>&1; then
    print_status 0 "Port 6379 is available"
else
    print_warning "Port 6379 is already in use (Redis might be running)"
fi

# Test docker-compose configuration
echo "Validating Docker Compose configuration..."
docker-compose config > /dev/null 2>&1
print_status $? "Docker Compose configuration is valid"

echo ""
echo "🚀 Setup Recommendations:"
echo "========================"

if [ ! -f .env ]; then
    echo "1. Run: make setup (or cp .env.example .env)"
    echo "2. Edit .env with your actual API keys"
fi

echo "3. Start the application:"
echo "   • For development: make docker-compose-up"
echo "   • For production: docker-compose -f docker-compose.prod.yml up -d"
echo ""
echo "4. Access the application at: http://localhost:8000/docs"
echo ""

# Quick start suggestion
echo "💡 Quick start command:"
if [ -f .env ]; then
    echo "   docker-compose up --build"
else
    echo "   make setup && docker-compose up --build"
fi
