#!/bin/bash

# verify_arc_upload.sh
# Quick verification that all files are in place on Oxford ARC

echo "========================================"
echo "ARC Upload Verification"
echo "Podcast Video Converter"
echo "========================================"
echo ""

# Check base directory
echo "📁 Base Directory:"
echo "   Current: $(pwd)"
echo "   Expected: ~/podcast"
echo ""

# Check personal space structure
echo "📜 Personal Space ($HOME/podcast):"
echo "-----------------------------------"
PERSONAL_DIR="$HOME/podcast"

if [ -d "$PERSONAL_DIR" ]; then
    echo "✅ Personal directory exists"
    
    # Check HPC scripts
    echo ""
    echo "   HPC Scripts:"
    for script in submit_video_conversion.sh batch_video_conversion.sh setup_arc_structure.sh activate_project_env_arc.sh; do
        if [ -f "$PERSONAL_DIR/hpc/$script" ]; then
            echo "      ✅ hpc/$script"
        else
            echo "      ❌ hpc/$script (missing)"
        fi
    done
    
    # Check source files
    echo ""
    echo "   Source Files:"
    for src in main.py audio_processor.py video_generator.py waveform_visualizer.py; do
        if [ -f "$PERSONAL_DIR/src/$src" ]; then
            echo "      ✅ src/$src"
        else
            echo "      ❌ src/$src (missing)"
        fi
    done
    
    # Check requirements
    echo ""
    echo "   Config Files:"
    if [ -f "$PERSONAL_DIR/requirements.txt" ]; then
        PKGS=$(wc -l < "$PERSONAL_DIR/requirements.txt")
        echo "      ✅ requirements.txt ($PKGS packages)"
    else
        echo "      ❌ requirements.txt (missing)"
    fi
    
    if [ -f "$PERSONAL_DIR/episode_titles.json" ]; then
        echo "      ✅ episode_titles.json"
    else
        echo "      ℹ️  episode_titles.json (will be created on first run)"
    fi
else
    echo "❌ Personal directory not found: $PERSONAL_DIR"
    echo "   Run setup_arc_structure.sh first"
fi

echo ""

# Check project space structure
echo "💾 Project Space ($DATA/podcast_env):"
echo "-----------------------------------"
PROJECT_DIR="$DATA/podcast_env"

if [ -d "$PROJECT_DIR" ]; then
    echo "✅ Project directory exists"
    du -sh "$PROJECT_DIR" 2>/dev/null | awk '{print "   Total size: "$1}'
    echo ""
    
    # Check subdirectories
    for dir in input output assets older_input .waveform_cache venv; do
        if [ -d "$PROJECT_DIR/$dir" ]; then
            SIZE=$(du -sh "$PROJECT_DIR/$dir" 2>/dev/null | awk '{print $1}')
            COUNT=$(find "$PROJECT_DIR/$dir" -type f 2>/dev/null | wc -l)
            echo "   ✅ $dir/ ($SIZE, $COUNT files)"
        else
            echo "   ❌ $dir/ (missing)"
        fi
    done
    
    # Check for podcast logo
    echo ""
    echo "   Required Assets:"
    LOGO_FILES=$(find "$PROJECT_DIR/assets" -name "podcast_logo.*" -type f 2>/dev/null | wc -l)
    if [ "$LOGO_FILES" -gt 0 ]; then
        LOGO=$(find "$PROJECT_DIR/assets" -name "podcast_logo.*" -type f 2>/dev/null | head -1)
        echo "      ✅ Podcast logo: $(basename "$LOGO")"
    else
        echo "      ❌ Podcast logo not found!"
        echo "         Upload: scp podcast_logo.png USER@arc-login.arc.ox.ac.uk:\$DATA/podcast_env/assets/"
    fi
    
    # Check for audio files
    echo ""
    echo "   Audio Files:"
    AUDIO_COUNT=$(find "$PROJECT_DIR/input" \( -name "*.wav" -o -name "*.mp3" -o -name "*.m4a" -o -name "*.flac" -o -name "*.ogg" -o -name "*.aac" -o -name "*.wma" \) -type f 2>/dev/null | wc -l)
    if [ "$AUDIO_COUNT" -gt 0 ]; then
        echo "      ✅ Found $AUDIO_COUNT audio file(s):"
        find "$PROJECT_DIR/input" \( -name "*.wav" -o -name "*.mp3" -o -name "*.m4a" -o -name "*.flac" -o -name "*.ogg" -o -name "*.aac" -o -name "*.wma" \) -type f 2>/dev/null | head -5 | while read f; do
            SIZE=$(du -h "$f" | cut -f1)
            echo "         - $(basename "$f") ($SIZE)"
        done
        if [ "$AUDIO_COUNT" -gt 5 ]; then
            echo "         ... and $((AUDIO_COUNT-5)) more"
        fi
    else
        echo "      ℹ️  No audio files found (upload to $PROJECT_DIR/input/)"
    fi
    
    # Check for output videos
    echo ""
    echo "   Output Videos:"
    VIDEO_COUNT=$(find "$PROJECT_DIR/output" -name "*.mp4" -type f 2>/dev/null | wc -l)
    if [ "$VIDEO_COUNT" -gt 0 ]; then
        echo "      ✅ Found $VIDEO_COUNT video(s):"
        find "$PROJECT_DIR/output" -name "*.mp4" -type f 2>/dev/null | head -5 | while read f; do
            SIZE=$(du -h "$f" | cut -f1)
            echo "         - $(basename "$f") ($SIZE)"
        done
    else
        echo "      ℹ️  No output videos yet"
    fi
else
    echo "❌ Project directory not found: $PROJECT_DIR"
    echo "   Run: ~/podcast/hpc/setup_arc_structure.sh"
fi

echo ""

# Check virtual environment
echo "🐍 Python Environment:"
echo "-----------------------------------"
VENV_PATH="$PROJECT_DIR/venv"

if [ -d "$VENV_PATH" ] && [ -f "$VENV_PATH/bin/activate" ]; then
    echo "✅ Virtual environment exists"
    
    # Temporarily activate to check packages
    source "$VENV_PATH/bin/activate" 2>/dev/null
    
    echo "   Python: $(python --version 2>&1)"
    
    # Check key packages
    echo ""
    echo "   Required Packages:"
    for pkg in moviepy librosa numpy scipy; do
        if python -c "import ${pkg//-/_}" 2>/dev/null; then
            VER=$(python -c "import ${pkg//-/_}; print(getattr(${pkg//-/_}, '__version__', 'installed'))" 2>/dev/null)
            echo "      ✅ $pkg: $VER"
        else
            echo "      ❌ $pkg (not installed)"
        fi
    done
    
    # Check Pillow (imports as PIL)
    if python -c "import PIL" 2>/dev/null; then
        VER=$(python -c "import PIL; print(PIL.__version__)" 2>/dev/null)
        echo "      ✅ Pillow: $VER"
    else
        echo "      ❌ Pillow (not installed)"
    fi
    
    # Check opencv (headless version)
    if python -c "import cv2" 2>/dev/null; then
        VER=$(python -c "import cv2; print(cv2.__version__)" 2>/dev/null)
        echo "      ✅ opencv: $VER"
    else
        echo "      ❌ opencv-python-headless (not installed)"
    fi
    
    deactivate 2>/dev/null
else
    echo "⚠️  Virtual environment not found"
    echo "   Create with: python -m venv $VENV_PATH"
    echo "   Then: pip install -r ~/podcast/requirements.txt"
fi

echo ""

# Check FFmpeg
echo "🎬 FFmpeg:"
echo "-----------------------------------"
if command -v ffmpeg &> /dev/null; then
    echo "✅ FFmpeg available"
    ffmpeg -version 2>&1 | head -1 | sed 's/^/   /'
else
    echo "⚠️  FFmpeg not in PATH"
    echo "   Try: module load FFmpeg"
fi

echo ""

# Summary
echo "========================================"
echo "Summary"
echo "========================================"

# Count issues
ISSUES=0
[ ! -d "$PERSONAL_DIR/hpc" ] && ((ISSUES++))
[ ! -d "$PERSONAL_DIR/src" ] && ((ISSUES++))
[ ! -d "$PROJECT_DIR" ] && ((ISSUES++))
[ "$LOGO_FILES" -eq 0 ] 2>/dev/null && ((ISSUES++))
[ ! -f "$VENV_PATH/bin/activate" ] && ((ISSUES++))

if [ $ISSUES -eq 0 ]; then
    echo "🎉 Setup verification PASSED!"
    echo ""
    echo "Ready to convert videos:"
    echo "  1. source ~/podcast/hpc/activate_project_env_arc.sh"
    echo "  2. cd ~/podcast/hpc"
    echo "  3. ./submit_video_conversion.sh"
else
    echo "⚠️  Found $ISSUES issue(s) - check output above"
    echo ""
    echo "To fix, run:"
    echo "  ~/podcast/hpc/setup_arc_structure.sh"
fi
echo ""
