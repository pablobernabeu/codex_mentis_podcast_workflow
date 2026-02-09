#!/bin/bash

# activate_project_env_arc.sh
# Environment activation script for Oxford ARC HPC
# Source this script to set up the podcast video conversion environment
#
# Usage: source ~/podcast/activate_project_env_arc.sh

echo "🎙️  Activating Podcast Video Converter Environment"
echo "==================================================="

# ============================================
# Load Required Modules
# ============================================
echo ""
echo "📦 Loading modules..."

# Try to load Python module (ARC uses module system)
if command -v module &> /dev/null; then
    # Try Python 3.12 first, fall back to available versions
    module load Python/3.12 2>/dev/null || \
    module load Python/3.11 2>/dev/null || \
    module load Python/3.10 2>/dev/null || \
    module load python 2>/dev/null || \
    echo "   ⚠️  Could not load Python module, using system Python"
    
    # Load FFmpeg if available
    module load FFmpeg 2>/dev/null || \
    module load ffmpeg 2>/dev/null || \
    echo "   ⚠️  FFmpeg module not available, checking PATH..."
fi

# ============================================
# Set Directory Paths
# ============================================
echo ""
echo "📁 Setting up paths..."

# Personal space (scripts, source code)
export PODCAST_HOME="$HOME/podcast"

# Project space (data, outputs, heavy files)
export PODCAST_DATA="$DATA/podcast_env"

# Set application directories
export PODCAST_INPUT_DIR="$PODCAST_DATA/input"
export PODCAST_OUTPUT_DIR="$PODCAST_DATA/output"
export PODCAST_ASSETS_DIR="$PODCAST_DATA/assets"

# Cache directories - redirect ALL caches to project space to avoid exhausting personal quota
export PIP_CACHE_DIR="$PODCAST_DATA/.pip_cache"
export PYTHONUSERBASE="$PODCAST_DATA/.python_user"
export XDG_CACHE_HOME="$PODCAST_DATA/.cache"
export MPLCONFIGDIR="$PODCAST_DATA/.matplotlib"
export HF_HOME="$PODCAST_DATA/.huggingface_cache"
export TRANSFORMERS_CACHE="$PODCAST_DATA/.huggingface_cache"
export TORCH_HOME="$PODCAST_DATA/.torch_cache"
export NUMBA_CACHE_DIR="$PODCAST_DATA/.cache/numba"

# Disable Python bytecode cache (.pyc files) to avoid stale code issues during development
export PYTHONDONTWRITEBYTECODE=1

# Ensure pip installs to project space
export PATH="$PODCAST_DATA/.python_user/bin:$PATH"

echo "   PODCAST_HOME: $PODCAST_HOME"
echo "   PODCAST_DATA: $PODCAST_DATA"
echo "   Input: $PODCAST_INPUT_DIR"
echo "   Output: $PODCAST_OUTPUT_DIR"
echo "   Assets: $PODCAST_ASSETS_DIR"
echo "   Cache: $XDG_CACHE_HOME"

# ============================================
# Activate Virtual Environment
# ============================================
echo ""
echo "🐍 Activating virtual environment..."

VENV_PATH="$PODCAST_DATA/venv"

if [ -d "$VENV_PATH" ] && [ -f "$VENV_PATH/bin/activate" ]; then
    source "$VENV_PATH/bin/activate"
    echo "   ✅ Virtual environment activated"
    echo "   Python: $(python --version)"
    echo "   Location: $(which python)"
else
    echo "   ⚠️  Virtual environment not found at $VENV_PATH"
    echo "   Creating new virtual environment..."
    python -m venv "$VENV_PATH"
    source "$VENV_PATH/bin/activate"
    echo "   ✅ Created and activated virtual environment"
    echo ""
    echo "   💡 Install requirements with:"
    echo "      pip install -r ~/podcast/requirements.txt"
fi

# ============================================
# Set Up Convenience Aliases
# ============================================
echo ""
echo "⚡ Setting up convenience aliases..."

# Quick navigation
alias cdpodcast='cd $PODCAST_HOME'
alias cdinput='cd $PODCAST_INPUT_DIR'
alias cdoutput='cd $PODCAST_OUTPUT_DIR'
alias cdassets='cd $PODCAST_ASSETS_DIR'

# Quick commands
alias submit_video='$PODCAST_HOME/hpc/submit_video_conversion.sh'
alias check_jobs='squeue -u $USER --clusters=htc'
alias check_logs='tail -f $PODCAST_HOME/logs/video_conversion_*.out'

echo "   ✅ Aliases configured"
echo ""
echo "   Available aliases:"
echo "   - cdpodcast    : Go to podcast home"
echo "   - cdinput      : Go to input directory"
echo "   - cdoutput     : Go to output directory"
echo "   - cdassets     : Go to assets directory"
echo "   - submit_video : Submit video conversion job"
echo "   - check_jobs   : Check running jobs"
echo "   - check_logs   : View job logs"

# ============================================
# Verify FFmpeg
# ============================================
echo ""
echo "🔍 Verifying dependencies..."

if command -v ffmpeg &> /dev/null; then
    echo "   ✅ FFmpeg: $(ffmpeg -version 2>&1 | head -n1 | cut -d' ' -f3)"
else
    echo "   ❌ FFmpeg not found!"
    echo "   Video conversion requires FFmpeg."
    echo "   Try: module load FFmpeg"
fi

# Check for TrueType fonts
FONTS_DIR="$HOME/.fonts"
if [ -f "$FONTS_DIR/DejaVuSerif.ttf" ] && [ -f "$FONTS_DIR/DejaVuSans.ttf" ]; then
    echo "   ✅ TrueType fonts: $(ls "$FONTS_DIR"/DejaVu*.ttf 2>/dev/null | wc -l) fonts available"
else
    echo "   ⚠️  TrueType fonts not found!"
    echo "   Video text rendering will use tiny default fonts."
    echo "   Fix: Run ~/podcast/hpc/install_fonts.sh or re-run setup"
fi

# ============================================
# Final Status
# ============================================
echo ""
echo "==================================================="
echo "✅ Environment Ready!"
echo "==================================================="
echo ""
echo "Quick start:"
echo "  1. Upload audio: scp file.wav USER@arc-login.arc.ox.ac.uk:\$DATA/podcast_env/input/"
echo "  2. Submit job:   cd ~/podcast/hpc && ./submit_video_conversion.sh"
echo "  3. Monitor:      squeue -u \$USER --clusters=htc"
echo "  4. Results:      ls \$DATA/podcast_env/output/"
echo ""
