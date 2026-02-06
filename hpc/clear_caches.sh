#!/bin/bash

# Clear all Python and processing caches on HPC
# Note: PYTHONDONTWRITEBYTECODE=1 is set in activate script, so .pyc files shouldn't exist
# This script is a safety measure to clean up any stale cache that might exist
# Run this script if you want to force fresh code execution
# Usage: ./clear_caches.sh

echo "🧹 CLEARING ALL CACHES ON HPC"
echo "=============================="
echo ""
echo "📍 Code location: \$HOME/podcast/src/ (personal space)"
echo "📍 Data location: \$DATA/podcast_env/ (project space)"
echo ""

# Count caches before (only in source directory where code runs from)
PYCACHE_COUNT=$(find "$HOME/podcast/src" -type d -name "__pycache__" 2>/dev/null | wc -l)
PYC_COUNT=$(find "$HOME/podcast/src" -name "*.pyc" 2>/dev/null | wc -l)

echo "📊 Found in source directory:"
echo "   - $PYCACHE_COUNT __pycache__ directories"
echo "   - $PYC_COUNT .pyc files"

if [ "$PYCACHE_COUNT" -eq 0 ] && [ "$PYC_COUNT" -eq 0 ]; then
    echo "   ✅ No Python cache found (as expected with PYTHONDONTWRITEBYTECODE=1)"
else
    echo ""
    echo "   ⚠️  Unexpected cache found (PYTHONDONTWRITEBYTECODE should prevent this)"
fi
echo ""

# Clear Python bytecode cache from source directory
echo "🧹 Clearing Python bytecode cache from source directory..."
find "$HOME/podcast/src" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$HOME/podcast/src" -name "*.pyc" -delete 2>/dev/null || true
echo "   ✅ Source directory cache cleared"

# Clear waveform cache (optional - stored in $DATA project space with audio files)
WAVEFORM_CACHE_DIR="$DATA/podcast_env/input/.waveform_cache"
if [ -d "$WAVEFORM_CACHE_DIR" ]; then
    WAVEFORM_COUNT=$(find "$WAVEFORM_CACHE_DIR" -name "*.pkl" 2>/dev/null | wc -l)
    if [ $WAVEFORM_COUNT -gt 0 ]; then
        echo ""
        read -p "🌊 Found $WAVEFORM_COUNT waveform cache files in \$DATA. Clear them? [y/N]: " clear_waveform
        if [[ "$clear_waveform" =~ ^[Yy]$ ]]; then
            rm -rf "$WAVEFORM_CACHE_DIR"
            echo "   ✅ Waveform cache cleared (waveforms will be regenerated)"
        else
            echo "   ℹ️  Waveform cache kept (faster processing, no visual changes)"
        fi
    fi
fi

echo ""
echo "✅ All caches cleared!"
echo ""
echo "💡 Next steps:"
echo "   1. Upload your updated code:"
echo "      rsync -av ~/podcast/src/ arc:~/podcast/src/"
echo "      rsync -av ~/podcast/hpc/ arc:~/podcast/hpc/"
echo "   2. Submit new jobs:"
echo "      ssh arc -t 'cd ~/podcast && ./hpc/submit_video_conversion.sh'"
echo ""
echo "ℹ️  Note: With PYTHONDONTWRITEBYTECODE=1 set, jobs always use fresh code from \$HOME/podcast/src/"
echo ""
