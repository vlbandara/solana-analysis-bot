#!/bin/bash

# Evolution API Test Setup Script
# This script starts Evolution API and runs the setup process

echo "🚀 Starting Evolution API Local Test Setup"
echo "=========================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

echo "✅ Docker is running"

# Check if docker-compose exists
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose not found. Please install Docker Compose."
    exit 1
fi

echo "✅ Docker Compose found"

# Start Evolution API
echo ""
echo "📡 Starting Evolution API container..."
docker-compose -f docker-compose.evolution.yml up -d

if [ $? -eq 0 ]; then
    echo "✅ Evolution API container started"
else
    echo "❌ Failed to start Evolution API container"
    exit 1
fi

# Wait for Evolution API to be ready
echo ""
echo "⏳ Waiting for Evolution API to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8080/manager/instance/fetchInstances > /dev/null 2>&1; then
        echo "✅ Evolution API is ready!"
        break
    fi
    
    if [ $i -eq 30 ]; then
        echo "❌ Evolution API did not start within 30 seconds"
        echo "📋 Checking container logs:"
        docker-compose -f docker-compose.evolution.yml logs evolution-api
        exit 1
    fi
    
    echo "   Attempt $i/30 - waiting..."
    sleep 2
done

# Install Python dependencies
echo ""
echo "📦 Installing Python dependencies..."
if command -v uv &> /dev/null; then
    echo "Using uv package manager..."
    uv add requests qrcode[pil]
elif command -v pip &> /dev/null; then
    echo "Using pip package manager..."
    pip install requests qrcode[pil]
else
    echo "❌ No Python package manager found (uv or pip)"
    exit 1
fi

echo "✅ Python dependencies installed"

# Run the setup script
echo ""
echo "🔧 Running Evolution API setup..."
python3 setup_evolution.py

echo ""
echo "🎉 Evolution API test setup complete!"
echo ""
echo "📱 Next steps:"
echo "1. If setup was successful, your WhatsApp is now connected"
echo "2. You can test sending messages using: python3 evolution_whatsapp.py"
echo "3. To integrate with your existing workflow, update your scripts to use Evolution API"
echo ""
echo "🛑 To stop Evolution API: docker-compose -f docker-compose.evolution.yml down"
echo "📋 To view logs: docker-compose -f docker-compose.evolution.yml logs -f evolution-api"