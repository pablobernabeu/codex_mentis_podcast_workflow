#!/bin/bash

# setup_arc_structure.sh
# One-time setup to create proper directory structure on Oxford ARC
# 
# Architecture:
#   Personal space (~):  Scripts, code, configs (quota-limited)
#   Project space ($DATA): Large files, assets, outputs (more space)

set -e  # Exit on error

echo "==================================="
echo "Oxford ARC Directory Setup"
echo "Podcast Video Converter"
echo "==================================="
echo ""

# Check environment
if [ -z "$DATA" ]; then
    echo "❌ ERROR: \$DATA environment variable not set"
    echo "   This should be set by ARC automatically"
    echo "   Please ensure you're logged into ARC"
    exit 1
fi

echo "✓ Environment variables:"
echo "  HOME: $HOME"
echo "  DATA: $DATA"
echo ""

# Define directories
PERSONAL_DIR="$HOME/podcast"
PROJECT_DIR="$DATA/podcast_env"

echo "==================================="
echo "Creating Directory Structure"
echo "==================================="
echo ""

# Personal space structure (lightweight files - scripts, source code)
echo "1. Setting up personal space: $PERSONAL_DIR"
mkdir -p "$PERSONAL_DIR"
mkdir -p "$PERSONAL_DIR/hpc"       # HPC cluster scripts
mkdir -p "$PERSONAL_DIR/src"       # Source code
mkdir -p "$PERSONAL_DIR/logs"      # Job logs
echo "   ✅ Personal directories created"
echo ""

# Project space structure (heavy files - audio, video, assets)
echo "2. Setting up project space: $PROJECT_DIR"
mkdir -p "$PROJECT_DIR"
mkdir -p "$PROJECT_DIR/input"           # Input audio files
mkdir -p "$PROJECT_DIR/output"          # Output MP4 videos
mkdir -p "$PROJECT_DIR/transcripts"     # Transcription output (optional)
mkdir -p "$PROJECT_DIR/assets"          # Podcast logo and assets
mkdir -p "$PROJECT_DIR/older_input"     # Archived audio files
mkdir -p "$PROJECT_DIR/.waveform_cache" # Waveform analysis cache
mkdir -p "$PROJECT_DIR/venv"            # Virtual environment
mkdir -p "$PROJECT_DIR/.pip_cache"      # Pip cache
mkdir -p "$PROJECT_DIR/.python_user"    # Python user packages
mkdir -p "$PROJECT_DIR/.matplotlib"     # Matplotlib cache
mkdir -p "$PROJECT_DIR/.cache"          # General cache
mkdir -p "$PROJECT_DIR/.huggingface_cache"  # HuggingFace models (for transcription)
mkdir -p "$PROJECT_DIR/.torch_cache"    # PyTorch cache
echo "   ✅ Project directories created"
echo ""

# Check disk usage
echo "==================================="
echo "Disk Usage Check"
echo "==================================="
echo ""
echo "Personal space quota:"
quota -s 2>/dev/null || du -sh "$HOME" 2>/dev/null || echo "  (quota command not available)"
echo ""
echo "Project space usage:"
du -sh "$PROJECT_DIR" 2>/dev/null || echo "  (directory empty or not accessible)"
echo ""

# Create README files
echo "3. Creating README files..."

cat > "$PERSONAL_DIR/README.md" << 'EOF'
# Personal Space - Podcast Video Converter

This directory contains lightweight files that fit within home directory quota limits.

## Structure

- `hpc/`: HPC cluster scripts (SLURM batch scripts, job submission)
- `src/`: Python source code
- `logs/`: Job output logs

## Usage

```bash
# Activate environment
source activate_project_env_arc.sh

# Submit batch job
cd hpc
./submit_video_conversion.sh

# Submit single file
./submit_video_conversion.sh --single-file input/episode.wav
```

## Data Location

Large files are stored in project space: `$DATA/podcast_env/`
EOF

cat > "$PROJECT_DIR/README.md" << 'EOF'
# Project Space - Podcast Video Converter

This directory contains large files stored in project space with more quota.

## Structure

- `input/`: Place audio files here (WAV, MP3, M4A, FLAC, OGG, AAC, WMA)
- `output/`: Generated MP4 videos
- `assets/`: Podcast logo (podcast_logo.png or similar)
- `older_input/`: Archived audio files
- `.waveform_cache/`: Cached waveform analysis data
- `venv/`: Python virtual environment

## Uploading Files

```bash
# From local machine
scp your_audio.wav USER@arc-login.arc.ox.ac.uk:$DATA/podcast_env/input/
scp podcast_logo.png USER@arc-login.arc.ox.ac.uk:$DATA/podcast_env/assets/
```

## Required Assets

Place your podcast logo in the `assets/` directory:
- File name: `podcast_logo.*` (any image format)
- Recommended size: 500x500 pixels or larger

## Monitoring Space

```bash
du -sh $DATA/podcast_env/*
```
EOF

cat > "$PROJECT_DIR/input/README.md" << 'EOF'
# Audio Input Directory

Place your podcast audio files here for processing.

## Supported Formats

- WAV (recommended for best quality)
- MP3
- M4A/AAC
- FLAC
- OGG
- WMA

## Episode Images (Optional)

You can add an optional image for each episode:
- Name must match audio filename (e.g., `episode.png` for `episode.wav`)
- Formats: PNG, JPG, JPEG, WEBP, GIF, BMP
EOF

cat > "$PROJECT_DIR/output/README.md" << 'EOF'
# Video Output Directory

Generated MP4 videos will be saved here.

Each processed audio file will create:
- `{filename}.mp4` - The final video with waveform visualisation

## Downloading Results

```bash
# From local machine
scp USER@arc-login.arc.ox.ac.uk:$DATA/podcast_env/output/*.mp4 ./
```
EOF

cat > "$PROJECT_DIR/assets/README.md" << 'EOF'
# Assets Directory

Place your podcast branding assets here.

## Required: Podcast Logo

- **File name**: `podcast_logo.*` (with any image extension)
- **Recommended size**: 500x500 pixels or larger (square format works best)
- **Formats**: PNG, JPG, JPEG, GIF, BMP, WEBP, TIFF
- **Important**: Only place ONE logo file to avoid conflicts

## Uploading

```bash
scp podcast_logo.png USER@arc-login.arc.ox.ac.uk:$DATA/podcast_env/assets/
```
EOF

echo "   ✅ README files created"
echo ""

# Create symlink for convenience
echo "4. Creating convenience symlink..."
if [ ! -L "$PERSONAL_DIR/data_storage" ]; then
    ln -s "$PROJECT_DIR" "$PERSONAL_DIR/data_storage"
    echo "   ✅ Symlink created: ~/podcast/data_storage -> $DATA/podcast_env"
else
    echo "   ℹ️  Symlink already exists"
fi
echo ""

# Install fonts for video generation
echo "5. Installing TrueType fonts for video text rendering..."
FONTS_DIR="$HOME/.fonts"
mkdir -p "$FONTS_DIR"

# Check if DejaVu fonts already installed
if [ -f "$FONTS_DIR/DejaVuSerif.ttf" ]; then
    echo "   ✅ Fonts already installed"
else
    echo "   📥 Downloading DejaVu fonts..."
    cd /tmp
    FONT_URL="https://github.com/dejavu-fonts/dejavu-fonts/releases/download/version_2_37/dejavu-fonts-ttf-2.37.tar.bz2"
    
    # Try wget first, fall back to curl
    if command -v wget &> /dev/null; then
        wget -q "$FONT_URL" || { echo "   ❌ Download failed"; exit 1; }
    elif command -v curl &> /dev/null; then
        curl -L -O "$FONT_URL" || { echo "   ❌ Download failed"; exit 1; }
    else
        echo "   ❌ Neither wget nor curl available. Please install fonts manually."
        exit 1
    fi
    
    echo "   📦 Extracting fonts..."
    tar -xjf dejavu-fonts-ttf-2.37.tar.bz2
    
    echo "   📋 Installing fonts..."
    cp dejavu-fonts-ttf-2.37/ttf/*.ttf "$FONTS_DIR/"
    
    echo "   🧹 Cleaning up..."
    rm -rf dejavu-fonts-ttf-2.37*
    
    # Update font cache if fc-cache is available
    if command -v fc-cache &> /dev/null; then
        echo "   🔄 Updating font cache..."
        fc-cache -f -v "$FONTS_DIR" > /dev/null 2>&1
    fi
    
    echo "   ✅ Fonts installed: $(ls "$FONTS_DIR"/DejaVu*.ttf | wc -l) DejaVu fonts"
fi
echo ""

# Summary
echo "==================================="
echo "Setup Complete!"
echo "==================================="
echo ""
echo "Directory structure created:"
echo ""
echo "📁 Personal space (~): $PERSONAL_DIR"
echo "   ├── hpc/              (HPC cluster scripts)"
echo "   ├── src/              (Python source code)"
echo "   ├── logs/             (Job logs)"
echo "   └── data_storage/     (→ symlink to \$DATA)"
echo ""
echo "📁 Project space (\$DATA): $PROJECT_DIR"
echo "   ├── input/            (Audio input files)"
echo "   ├── output/           (MP4 output files)"
echo "   ├── assets/           (Podcast logo)"
echo "   ├── older_input/      (Archived files)"
echo "   ├── .waveform_cache/  (Analysis cache)"
echo "   └── venv/             (Virtual environment)"
echo ""
echo "Next steps:"
echo "1. Copy HPC scripts to: $PERSONAL_DIR/hpc/"
echo "2. Copy src/ files to: $PERSONAL_DIR/src/"
echo "3. Upload podcast logo to: $PROJECT_DIR/assets/"
echo "4. Upload episode images (optional) to: $PROJECT_DIR/input/"
echo "5. Run: source $PERSONAL_DIR/activate_project_env_arc.sh"
echo "6. Install packages: pip install -r requirements.txt"
echo ""
echo "✅ TrueType fonts installed - video text will render at proper size"
echo ""
