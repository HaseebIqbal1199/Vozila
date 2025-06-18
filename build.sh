#!/bin/bash
# Build script for Render deployment

echo "Starting Vozila build process..."

# Update package list
apt-get update

# Install FFmpeg
echo "Installing FFmpeg..."
apt-get install -y ffmpeg

# Verify FFmpeg installation
if command -v ffmpeg &> /dev/null; then
    echo "FFmpeg installed successfully:"
    ffmpeg -version | head -1
else
    echo "Warning: FFmpeg installation failed"
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Build completed successfully!"
