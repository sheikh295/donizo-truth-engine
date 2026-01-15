#!/bin/bash
# Donizo Truth Engine - Quick Start Script

echo "======================================================================"
echo "  DONIZO TRUTH ENGINE - Quick Start"
echo "======================================================================"
echo ""
echo "This script will:"
echo "  1. Build the Docker image"
echo "  2. Start the interactive menu"
echo ""
echo "No dependencies needed on your machine - everything runs in Docker!"
echo ""
echo "======================================================================"
echo ""

# Create data directory if it doesn't exist
mkdir -p data

echo "Building Docker image (this may take a few minutes)..."
docker build -t donizo-engine:latest .

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Build successful!"
    echo ""
    echo "Starting interactive menu..."
    echo "======================================================================"
    echo ""

    # Run the container interactively
    docker run -it --rm \
        -v "$(pwd)/data:/data" \
        --name donizo-truth-engine \
        donizo-engine:latest
else
    echo ""
    echo "❌ Build failed! Please check the error messages above."
    exit 1
fi
