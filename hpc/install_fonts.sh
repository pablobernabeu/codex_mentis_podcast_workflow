#!/bin/bash
# Install DejaVu fonts for podcast video generation
# Run this on the HPC cluster if fonts weren't installed during initial setup
# or if you need to reinstall them
#
# NOTE: Fonts are automatically installed by setup_arc_structure.sh
#       This script is only needed for manual reinstallation

set -e  # Exit on error

echo "🎨 Installing DejaVu Fonts for Podcast Video Generation"
echo "========================================================"

# Create fonts directory
FONTS_DIR="$HOME/.fonts"
echo "📁 Creating font directory: $FONTS_DIR"
mkdir -p "$FONTS_DIR"

# Download DejaVu fonts
echo "📥 Downloading DejaVu fonts..."
cd /tmp
FONT_URL="https://github.com/dejavu-fonts/dejavu-fonts/releases/download/version_2_37/dejavu-fonts-ttf-2.37.tar.bz2"
wget -q "$FONT_URL" || curl -L -O "$FONT_URL"

# Extract fonts
echo "📦 Extracting fonts..."
tar -xjf dejavu-fonts-ttf-2.37.tar.bz2

# Copy to user fonts directory
echo "📋 Installing fonts..."
cp dejavu-fonts-ttf-2.37/ttf/*.ttf "$FONTS_DIR/"

# Cleanup
echo "🧹 Cleaning up..."
rm -rf dejavu-fonts-ttf-2.37*

# Update font cache
echo "🔄 Updating font cache..."
if command -v fc-cache &> /dev/null; then
    fc-cache -f -v "$FONTS_DIR"
fi

# Verify installation
echo ""
echo "✅ Font Installation Complete!"
echo ""
echo "🔍 Verifying DejaVu fonts..."
ls -lh "$FONTS_DIR"/DejaVu*.ttf

if command -v fc-list &> /dev/null; then
    echo ""
    echo "📋 Available DejaVu fonts:"
    fc-list | grep -i dejavu || echo "  (fc-list not available, but files are installed)"
fi

echo ""
echo "✨ Ready! Your next video generation will use proper TrueType fonts."
echo "   Text size will now be correct instead of tiny."
