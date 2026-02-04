#!/bin/bash

# ARC-compatible batch video conversion script
# Adapted for Oxford ARC HPC cluster environment
# Converts podcast audio files to MP4 videos with waveform visualisation

#SBATCH --job-name=podcast_video
#SBATCH --output=logs/video_conversion_%A_%a.out
#SBATCH --error=logs/video_conversion_%A_%a.err
#SBATCH --clusters=htc
#SBATCH --partition=short
#SBATCH --time=04:00:00
#SBATCH --mem=32G
#SBATCH --cpus-per-task=4
# Note: This workflow is CPU-based (no GPU required)

echo "🎙️  PODCAST VIDEO CONVERSION JOB"
echo "================================="
echo "Job started at: $(date)"
echo "Running on node: $SLURM_NODENAME"
echo "Job ID: $SLURM_JOB_ID"
echo "Task ID: $SLURM_ARRAY_TASK_ID"
echo "Cluster: $SLURM_CLUSTER_NAME"
echo ""

# ============================================
# STEP 1: Parse Arguments
# ============================================
echo "📋 STEP 1: Parsing arguments..."

# Default values
ENHANCE_AUDIO=false
SINGLE_FILE=""
TRANSCRIPTION=false
TRANSCRIPTION_ARGS=""

# Parse command line arguments passed from submit script
while [[ $# -gt 0 ]]; do
    case $1 in
        --enhance-audio)
            ENHANCE_AUDIO=true
            shift
            ;;
        --single-file)
            SINGLE_FILE="$2"
            shift 2
            ;;
        --transcription)
            TRANSCRIPTION=true
            shift
            ;;
        --mask-personal-names)
            TRANSCRIPTION_ARGS="$TRANSCRIPTION_ARGS --mask-personal-names"
            shift
            ;;
        --language)
            TRANSCRIPTION_ARGS="$TRANSCRIPTION_ARGS --language $2"
            shift 2
            ;;
        --fix-spurious-repetitions)
            TRANSCRIPTION_ARGS="$TRANSCRIPTION_ARGS --fix-spurious-repetitions"
            shift
            ;;
        --save-name-masking-logs)
            TRANSCRIPTION_ARGS="$TRANSCRIPTION_ARGS --save-name-masking-logs"
            shift
            ;;
        --speaker-attribution)
            TRANSCRIPTION_ARGS="$TRANSCRIPTION_ARGS --speaker-attribution"
            shift
            ;;
        --exclude-names-from-masking)
            TRANSCRIPTION_ARGS="$TRANSCRIPTION_ARGS --exclude-names-from-masking $2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

echo "   Audio enhancement: $ENHANCE_AUDIO"
echo "   Transcription: $TRANSCRIPTION"
if [ -n "$TRANSCRIPTION_ARGS" ]; then
    echo "   Transcription options:$TRANSCRIPTION_ARGS"
fi
if [ -n "$SINGLE_FILE" ]; then
    echo "   Single file mode: $(basename "$SINGLE_FILE")"
fi
echo ""

# ============================================
# STEP 2: Environment Activation
# ============================================
echo "📦 STEP 2: Activating environment..."

# Source the activation script from personal space (in hpc subdirectory)
ACTIVATION_SCRIPT="$HOME/podcast/hpc/activate_project_env_arc.sh"

if [ -f "$ACTIVATION_SCRIPT" ]; then
    source "$ACTIVATION_SCRIPT"
    echo "   ✅ Environment activated via $ACTIVATION_SCRIPT"
    echo "   🐍 Python version: $(python --version)"
else
    echo "   ❌ Error: Activation script not found at $ACTIVATION_SCRIPT"
    echo "   💡 Expected location: ~/podcast/hpc/activate_project_env_arc.sh"
    exit 1
fi

# Define paths (already set by activation script, but define for clarity)
CONDA_ENV_PATH="$DATA/podcast_env"
AUDIO_INPUT_DIR="$CONDA_ENV_PATH/input"
OUTPUT_DIR="$CONDA_ENV_PATH/output"
ASSETS_DIR="$CONDA_ENV_PATH/assets"
SRC_DIR="$HOME/podcast/src"

echo "   📁 Audio input: $AUDIO_INPUT_DIR"
echo "   📁 Output: $OUTPUT_DIR"
echo "   📁 Assets: $ASSETS_DIR"
echo ""

# ============================================
# STEP 2.5: Sync files from home to data
# ============================================
echo "📂 STEP 2.5: Syncing files from home to data directory..."

# Sync input audio files
HOME_INPUT="$HOME/podcast/input"
if [ -d "$HOME_INPUT" ] && [ "$(ls -A "$HOME_INPUT" 2>/dev/null)" ]; then
    echo "   🔄 Syncing audio files from $HOME_INPUT..."
    rsync -av --ignore-existing "$HOME_INPUT/" "$AUDIO_INPUT_DIR/"
    echo "   ✅ Audio files synced"
else
    echo "   ℹ️  No audio files in home input directory"
fi

# Sync assets (logo, images)
HOME_ASSETS="$HOME/podcast/assets"
if [ -d "$HOME_ASSETS" ] && [ "$(ls -A "$HOME_ASSETS" 2>/dev/null)" ]; then
    echo "   🔄 Syncing assets from $HOME_ASSETS..."
    rsync -av --ignore-existing "$HOME_ASSETS/" "$ASSETS_DIR/"
    echo "   ✅ Assets synced"
else
    echo "   ℹ️  No assets in home assets directory"
fi

# Sync episode_titles.json for pre-configured titles
EPISODE_TITLES_FILE="$HOME/podcast/episode_titles.json"
DATA_TITLES_FILE="$CONDA_ENV_PATH/episode_titles.json"
if [ -f "$EPISODE_TITLES_FILE" ]; then
    echo "   🔄 Syncing episode_titles.json..."
    cp "$EPISODE_TITLES_FILE" "$DATA_TITLES_FILE"
    echo "   ✅ Episode titles synced"
fi
echo ""

# ============================================
# STEP 3: Select Audio File
# ============================================
echo "🎵 STEP 3: Selecting audio file..."

# Check for pre-selected files list (from interactive submit script)
SELECTED_FILES_LIST="$CONDA_ENV_PATH/.selected_files.txt"

if [ -n "$SINGLE_FILE" ]; then
    # Single file mode - construct proper path
    if [[ "$SINGLE_FILE" = /* ]]; then
        AUDIO_FILE="$SINGLE_FILE"
    elif [ -f "$SINGLE_FILE" ]; then
        AUDIO_FILE="$(realpath "$SINGLE_FILE")"
    else
        AUDIO_FILE="$AUDIO_INPUT_DIR/$(basename "$SINGLE_FILE")"
    fi
    echo "   📁 Single file mode: $(basename "$AUDIO_FILE")"
elif [ -f "$SELECTED_FILES_LIST" ]; then
    # Use pre-selected files from interactive submit
    mapfile -t audio_files < "$SELECTED_FILES_LIST"
    
    if [ ${#audio_files[@]} -eq 0 ]; then
        echo "   ❌ Selected files list is empty"
        exit 1
    fi
    
    # Array mode - select file based on task ID (SLURM_ARRAY_TASK_ID is 1-based)
    TASK_INDEX=$((SLURM_ARRAY_TASK_ID - 1))
    if [ $TASK_INDEX -ge ${#audio_files[@]} ]; then
        echo "   ❌ Task index $TASK_INDEX exceeds selected files (${#audio_files[@]})"
        exit 1
    fi
    
    AUDIO_FILE="${audio_files[$TASK_INDEX]}"
    echo "   📁 Processing file $SLURM_ARRAY_TASK_ID/${#audio_files[@]}: $(basename "$AUDIO_FILE")"
else
    # Fallback: find all audio files
    mapfile -t audio_files < <(find "$AUDIO_INPUT_DIR" \( -name "*.wav" -o -name "*.WAV" -o -name "*.mp3" -o -name "*.MP3" -o -name "*.m4a" -o -name "*.M4A" -o -name "*.flac" -o -name "*.FLAC" -o -name "*.ogg" -o -name "*.OGG" -o -name "*.aac" -o -name "*.AAC" -o -name "*.wma" -o -name "*.WMA" \) -type f | sort)
    
    if [ ${#audio_files[@]} -eq 0 ]; then
        echo "   ❌ No audio files found in $AUDIO_INPUT_DIR"
        echo "   🎵 Supported formats: WAV, MP3, M4A, FLAC, OGG, AAC, WMA"
        echo "   💡 Please copy your audio files to: $AUDIO_INPUT_DIR"
        exit 1
    fi
    
    # Array mode - select file based on task ID
    TASK_INDEX=$((SLURM_ARRAY_TASK_ID - 1))
    if [ $TASK_INDEX -ge ${#audio_files[@]} ]; then
        echo "   ❌ Task index $TASK_INDEX exceeds available files (${#audio_files[@]})"
        exit 1
    fi
    
    AUDIO_FILE="${audio_files[$TASK_INDEX]}"
    echo "   📁 Processing file $SLURM_ARRAY_TASK_ID/${#audio_files[@]}: $(basename "$AUDIO_FILE")"
fi

# Verify file exists and is readable
if [ ! -f "$AUDIO_FILE" ]; then
    echo "   ❌ Audio file not found: $AUDIO_FILE"
    exit 1
fi

echo "   📊 File size: $(du -h "$AUDIO_FILE" | cut -f1)"
echo "   🎵 File format: ${AUDIO_FILE##*.}"
echo ""

# ============================================
# STEP 4: Verify Environment
# ============================================
echo "🔍 STEP 4: Verifying environment..."

# Quick version check
timeout 10 python --version
if [ $? -eq 0 ]; then
    echo "   ✅ Python accessible"
else
    echo "   ❌ Python not accessible"
    exit 1
fi

# Check FFmpeg
if command -v ffmpeg &> /dev/null; then
    echo "   ✅ FFmpeg available: $(ffmpeg -version 2>&1 | head -n1)"
else
    echo "   ⚠️  FFmpeg not found in PATH, attempting module load..."
    module load FFmpeg 2>/dev/null || true
fi

# Check required packages
python -c "import moviepy; print('   ✅ MoviePy:', moviepy.__version__)" 2>/dev/null || echo "   ❌ MoviePy not installed"
python -c "import librosa; print('   ✅ Librosa:', librosa.__version__)" 2>/dev/null || echo "   ❌ Librosa not installed"
python -c "import PIL; print('   ✅ Pillow available')" 2>/dev/null || echo "   ❌ Pillow not installed"
echo ""

# ============================================
# STEP 5: Run Video Conversion
# ============================================
echo "🎬 STEP 5: Running video conversion..."
echo ""

# Build command arguments
CONVERSION_ARGS=""
if [ "$ENHANCE_AUDIO" = true ]; then
    CONVERSION_ARGS="$CONVERSION_ARGS --enhance-audio"
fi

# Change to source directory
cd "$SRC_DIR" || { echo "❌ Failed to cd to $SRC_DIR"; exit 1; }

# Set environment variables for the Python script
export PODCAST_INPUT_DIR="$AUDIO_INPUT_DIR"
export PODCAST_OUTPUT_DIR="$OUTPUT_DIR"
export PODCAST_ASSETS_DIR="$ASSETS_DIR"

# Copy episode_titles.json to src directory where main.py expects it
if [ -f "$CONDA_ENV_PATH/episode_titles.json" ]; then
    cp "$CONDA_ENV_PATH/episode_titles.json" "$HOME/podcast/episode_titles.json"
fi

# Build command with batch mode
CONVERSION_CMD="python main.py --batch"
if [ "$ENHANCE_AUDIO" = true ]; then
    CONVERSION_CMD="$CONVERSION_CMD --enhance-audio"
fi

# Add specific file if in single-file mode
if [ -n "$SINGLE_FILE" ]; then
    CONVERSION_CMD="$CONVERSION_CMD --file \"$AUDIO_FILE\""
fi

# Run the conversion with timeout (3 hours max)
echo "Running: $CONVERSION_CMD"
echo "---"

eval timeout 10800 $CONVERSION_CMD

CONVERSION_EXIT_CODE=$?

echo ""
echo "---"

# ============================================
# STEP 6: Run Transcription (if enabled)
# ============================================
TRANSCRIPTION_EXIT_CODE=0

if [ "$TRANSCRIPTION" = true ]; then
    echo ""
    echo "📝 STEP 6: Running transcription..."
    echo ""
    
    # Check if speech_transcription workflow is available
    TRANSCRIPTION_SCRIPT="$HOME/speech_transcription/transcription.py"
    TRANSCRIPTION_OUTPUT_DIR="$CONDA_ENV_PATH/transcripts"
    
    # Create transcripts directory if it doesn't exist
    mkdir -p "$TRANSCRIPTION_OUTPUT_DIR"
    
    if [ -f "$TRANSCRIPTION_SCRIPT" ]; then
        echo "   ✅ Transcription script found"
        echo "   📁 Output: $TRANSCRIPTION_OUTPUT_DIR"
        echo ""
        
        # Activate speech transcription environment if available
        SPEECH_TRANSCRIPTION_ENV="$DATA/speech_transcription_env"
        if [ -f "$SPEECH_TRANSCRIPTION_ENV/venv/bin/activate" ]; then
            source "$SPEECH_TRANSCRIPTION_ENV/venv/bin/activate"
            echo "   ✅ Speech transcription environment activated"
        fi
        
        # Set output directory for transcription
        export TRANSCRIPTION_OUTPUT_BASE="$TRANSCRIPTION_OUTPUT_DIR"
        
        # Change to speech transcription directory
        cd "$HOME/speech_transcription" || { echo "❌ Failed to cd to speech_transcription"; }
        
        # Run transcription
        echo "   Running transcription on: $(basename "$AUDIO_FILE")"
        echo "   Options:$TRANSCRIPTION_ARGS"
        echo "   ---"
        
        timeout 10800 python "$TRANSCRIPTION_SCRIPT" "$AUDIO_FILE" $TRANSCRIPTION_ARGS
        TRANSCRIPTION_EXIT_CODE=$?
        
        echo "   ---"
        
        if [ $TRANSCRIPTION_EXIT_CODE -eq 0 ]; then
            echo "   ✅ Transcription completed successfully!"
            
            # Check for output files
            if [ -f "$TRANSCRIPTION_OUTPUT_DIR/${BASE_NAME}_transcription.txt" ]; then
                echo "   📄 Transcript: ${BASE_NAME}_transcription.txt"
            fi
            if [ -f "$TRANSCRIPTION_OUTPUT_DIR/${BASE_NAME}_transcription.docx" ]; then
                echo "   📄 Word doc: ${BASE_NAME}_transcription.docx"
            fi
        elif [ $TRANSCRIPTION_EXIT_CODE -eq 124 ]; then
            echo "   ❌ Transcription timed out"
        else
            echo "   ❌ Transcription failed with exit code $TRANSCRIPTION_EXIT_CODE"
        fi
        
        # Return to source directory
        cd "$SRC_DIR" || true
    else
        echo "   ⚠️  Transcription script not found: $TRANSCRIPTION_SCRIPT"
        echo "   💡 To enable transcription, install the speech_transcription workflow:"
        echo "      https://github.com/pablobernabeu/secure_local_HPC_speech_transcription"
        TRANSCRIPTION_EXIT_CODE=1
    fi
fi

# ============================================
# STEP 7: Report Results
# ============================================
echo ""
echo "📊 STEP 7: Checking results..."

BASE_NAME=$(basename "$AUDIO_FILE" | sed 's/\.[^.]*$//')

if [ $CONVERSION_EXIT_CODE -eq 0 ]; then
    echo "✅ SUCCESS: Video conversion completed!"
    
    # Check for output files
    if [ -f "$OUTPUT_DIR/${BASE_NAME}.mp4" ]; then
        echo "   📹 Video: ${BASE_NAME}.mp4 ($(du -h "$OUTPUT_DIR/${BASE_NAME}.mp4" | cut -f1))"
    fi
    
elif [ $CONVERSION_EXIT_CODE -eq 124 ]; then
    echo "❌ TIMEOUT: Conversion exceeded 3 hour limit"
else
    echo "❌ FAILURE: Conversion failed with exit code $CONVERSION_EXIT_CODE"
fi

echo ""
echo "🏁 JOB SUMMARY"
echo "=============="
echo "Job completed at: $(date)"
echo "File processed: $(basename "$AUDIO_FILE")"
echo "Video conversion exit code: $CONVERSION_EXIT_CODE"
if [ "$TRANSCRIPTION" = true ]; then
    echo "Transcription exit code: $TRANSCRIPTION_EXIT_CODE"
fi
echo "Node: $SLURM_NODENAME"
echo "Job ID: $SLURM_JOB_ID"
echo "Task ID: $SLURM_ARRAY_TASK_ID"
echo "Working directory: $CONDA_ENV_PATH"

# Exit with error if either task failed
if [ $CONVERSION_EXIT_CODE -ne 0 ]; then
    exit $CONVERSION_EXIT_CODE
elif [ $TRANSCRIPTION_EXIT_CODE -ne 0 ]; then
    exit $TRANSCRIPTION_EXIT_CODE
else
    exit 0
fi
