#!/bin/bash
# Setup script for Codex Mentis Podcast Video Converter

echo "🎙️  Setting up Codex Mentis Podcast Video Converter"
echo "=================================================="

# Check if Python is installed
if ! command -v python &> /dev/null; then
    echo "❌ Python is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✓ Python found: $(python --version)"

# Check if pip is installed
if ! command -v pip &> /dev/null; then
    echo "❌ pip is not installed. Please install pip."
    exit 1
fi

echo "✓ pip found: $(pip --version)"

# Install Python dependencies
echo ""
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully!"
else
    echo "❌ Failed to install dependencies. Please check the error messages above."
    exit 1
fi

# Check directory structure
echo ""
echo "📁 Checking directory structure..."

directories=("input" "output" "assets" "src")
for dir in "${directories[@]}"; do
    if [ -d "$dir" ]; then
        echo "✓ $dir/ directory exists"
    else
        echo "❌ $dir/ directory missing"
    fi
done

# Check for logo
echo ""
echo "🖼️  Checking for podcast logo..."
if [ -f "assets/podcast_logo.jpeg" ]; then
    echo "✅ Podcast logo found!"
else
    echo "⚠️  Podcast logo not found."
    echo "Please place your podcast logo at: assets/podcast_logo.jpeg"
    echo ""
    echo "Logo requirements:"
    echo "• File name: podcast_logo.jpeg"
    echo "• Recommended size: 500x500 pixels or larger"
    echo "• Format: JPG or PNG"
fi

echo ""
echo "🎯 Setup complete! Usage instructions:"
echo "1. Place your WAV files in the input/ directory"
echo "2. Ensure your podcast logo is at assets/podcast_logo.jpeg"
echo "3. Run: python src/main.py"
echo ""
echo "📚 For more information, see README.md"
