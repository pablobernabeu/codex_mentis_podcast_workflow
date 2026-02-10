#!/bin/bash

# Auto-submit video conversion jobs to Oxford ARC HPC
# Usage: ./submit_video_conversion.sh [options...]
# 
# Batch mode (default):
#   ./submit_video_conversion.sh
#   ./submit_video_conversion.sh --enhance-audio
#
# Single file mode:
#   ./submit_video_conversion.sh --single-file input/myfile.wav
#   ./submit_video_conversion.sh --single-file input/myfile.mp3 --enhance-audio
#
# Options:
#   --single-file <path>     Specify exact file to convert
#   --enhance-audio          Enable audio enhancement (EQ, normalisation, click removal)
#   --time-limit HH:MM:SS    Maximum time per file (default: 8h)
#   --memory <size>          Memory allocation (default: 32G)

echo "🎙️  AUTO-SUBMIT VIDEO CONVERSION JOBS"
echo "======================================"

# Create logs directory if it doesn't exist
LOGS_DIR="$HOME/podcast/logs"
if [ ! -d "$LOGS_DIR" ]; then
    mkdir -p "$LOGS_DIR"
    echo "📁 Created logs directory: $LOGS_DIR"
fi

# Ensure we're in the right directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "📍 Project directory: $PROJECT_DIR"
echo ""

# ============================================
# Parse Arguments
# ============================================
SINGLE_FILE=""
ENHANCE_AUDIO=""
TIME_LIMIT=""
MEMORY=""
CONVERSION_ARGS=""

# Transcription options (enabled by default)
TRANSCRIPTION="true"
TRANSCRIPTION_ARGS=""
NO_TRANSCRIPTION=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --single-file)
            SINGLE_FILE="$2"
            shift 2
            ;;
        --enhance-audio)
            ENHANCE_AUDIO="--enhance-audio"
            CONVERSION_ARGS="$CONVERSION_ARGS --enhance-audio"
            shift
            ;;
        --time-limit)
            TIME_LIMIT="$2"
            shift 2
            ;;
        --memory)
            MEMORY="$2"
            shift 2
            ;;
        # Transcription options
        --transcription)
            TRANSCRIPTION="true"
            shift
            ;;
        --no-transcription)
            TRANSCRIPTION=""
            NO_TRANSCRIPTION="true"
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
        -h|--help)
            echo "Usage: ./submit_video_conversion.sh [options]"
            echo ""
            echo "HPC-specific options:"
            echo "  --single-file <path>       Specify exact file to convert"
            echo "  --time-limit HH:MM:SS      Maximum time per file (default: 8h)"
            echo "  --memory <size>            Memory allocation (default: 32G)"
            echo ""
            echo "Video conversion options:"
            echo "  --enhance-audio            Enable audio enhancement"
            echo ""
            echo "Transcription options (enabled by default, requires speech_transcription workflow):"
            echo "  --no-transcription         Disable audio transcription"
            echo "  --mask-personal-names      Mask personal names in transcript"
            echo "  --language <lang>          Transcription language (english, spanish, etc.)"
            echo "  --fix-spurious-repetitions Remove repetitive patterns"
            echo "  --save-name-masking-logs   Save detailed masking logs"
            echo "  --speaker-attribution      Enable speaker diarisation"
            echo "  --exclude-names-from-masking <names>  Comma-separated names to exclude"
            echo ""
            echo "Examples:"
            echo "  ./submit_video_conversion.sh"
            echo "  ./submit_video_conversion.sh --enhance-audio"
            echo "  ./submit_video_conversion.sh --no-transcription"
            echo "  ./submit_video_conversion.sh --single-file input/episode.wav"
            echo "  ./submit_video_conversion.sh --mask-personal-names --language english"
            echo "  ./submit_video_conversion.sh --time-limit 06:00:00 --memory 64G"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Add transcription flag to conversion args if enabled
if [ -n "$TRANSCRIPTION" ]; then
    CONVERSION_ARGS="$CONVERSION_ARGS --transcription"
fi

# Pass transcription args to batch script
if [ -n "$TRANSCRIPTION_ARGS" ]; then
    CONVERSION_ARGS="$CONVERSION_ARGS $TRANSCRIPTION_ARGS"
fi

# ============================================
# Sync files from home to data directory
# ============================================
echo "📂 Syncing files from home to data directory..."

AUDIO_INPUT_DIR="$DATA/podcast_env/input"
HOME_INPUT="$HOME/podcast/input"
HOME_ASSETS="$HOME/podcast/assets"
ASSETS_DIR="$DATA/podcast_env/assets"
EPISODE_TITLES_FILE="$HOME/podcast/episode_titles.json"

# Ensure target directories exist
mkdir -p "$AUDIO_INPUT_DIR" "$ASSETS_DIR"

# Sync input audio files (always update newer files)
if [ -d "$HOME_INPUT" ] && [ "$(ls -A "$HOME_INPUT" 2>/dev/null)" ]; then
    echo "   🔄 Syncing audio files from $HOME_INPUT..."
    rsync -av --update "$HOME_INPUT/" "$AUDIO_INPUT_DIR/" 2>/dev/null
    echo "   ✅ Audio files synced"
fi

# Sync assets (logo, images) - always update to ensure latest versions
if [ -d "$HOME_ASSETS" ] && [ "$(ls -A "$HOME_ASSETS" 2>/dev/null)" ]; then
    echo "   🔄 Syncing assets from $HOME_ASSETS..."
    rsync -av "$HOME_ASSETS/" "$ASSETS_DIR/" 2>/dev/null
    echo "   ✅ Assets synced (including updated logo)"
fi
echo ""

# ============================================
# Load existing episode titles
# ============================================
declare -A EPISODE_TITLES
if [ -f "$EPISODE_TITLES_FILE" ]; then
    # Parse JSON file for existing titles
    while IFS="=" read -r key value; do
        EPISODE_TITLES["$key"]="$value"
    done < <(python3 -c "
import json
with open('$EPISODE_TITLES_FILE', 'r') as f:
    titles = json.load(f)
for k, v in titles.items():
    print(f'{k}={v}')
" 2>/dev/null)
fi

# Function to get/set episode title interactively
get_episode_title() {
    local filename="$1"
    local basename="${filename%.*}"
    
    # Check if we already have a title
    if [ -n "${EPISODE_TITLES[$basename]}" ]; then
        echo "${EPISODE_TITLES[$basename]}"
        return
    fi
    
    # Generate suggested title from filename
    local suggested="$basename"
    # Replace underscores with colons for title format
    if [[ "$suggested" == *"_"* ]]; then
        suggested="${suggested//_/:}"
        # Normalize multiple spaces to single space
        suggested=$(echo "$suggested" | sed 's/  \+/ /g')
    fi
    
    echo ""
    echo "   📝 Episode: $basename"
    echo "   Suggested title: '$suggested'"
    read -p "   Enter title (or press Enter for suggested): " user_title
    
    if [ -n "$user_title" ]; then
        EPISODE_TITLES["$basename"]="$user_title"
        echo "$user_title"
    else
        EPISODE_TITLES["$basename"]="$suggested"
        echo "$suggested"
    fi
}

# Function to save episode titles
save_episode_titles() {
    # Build Python dictionary entries in bash
    local dict_entries=""
    for key in "${!EPISODE_TITLES[@]}"; do
        # Escape single quotes in values
        local escaped_value="${EPISODE_TITLES[$key]//\'/\\\'}"
        dict_entries+="    '$key': '$escaped_value',
"
    done
    
    # Execute Python with complete script
    python3 -c "
import json
titles = {
${dict_entries}}
with open('$EPISODE_TITLES_FILE', 'w') as f:
    json.dump(titles, f, indent=2, ensure_ascii=False)
print('   ✅ Episode titles saved')
"
}

# ============================================
# Determine Processing Mode
# ============================================

if [ -n "$SINGLE_FILE" ]; then
    echo "📄 SINGLE FILE MODE"
    echo "==================="
    
    # Validate single file exists
    if [[ "$SINGLE_FILE" = /* ]]; then
        FULL_PATH="$SINGLE_FILE"
    elif [ -f "$SINGLE_FILE" ]; then
        FULL_PATH="$(realpath "$SINGLE_FILE")"
    else
        FULL_PATH="$AUDIO_INPUT_DIR/$(basename "$SINGLE_FILE")"
    fi
    
    if [ ! -f "$FULL_PATH" ]; then
        echo "❌ ERROR: File not found: $SINGLE_FILE"
        echo "   Checked paths:"
        echo "   - $SINGLE_FILE"
        echo "   - $FULL_PATH"
        exit 1
    fi
    
    # Validate file format
    case "${FULL_PATH,,}" in
        *.wav|*.mp3|*.m4a|*.flac|*.ogg|*.aac|*.wma)
            echo "   ✅ Valid audio file: $(basename "$FULL_PATH")"
            echo "   📊 Size: $(ls -lh "$FULL_PATH" | awk '{print $5}')"
            ;;
        *)
            echo "❌ ERROR: Unsupported audio format: $SINGLE_FILE"
            echo "Supported formats: WAV, MP3, M4A, FLAC, OGG, AAC, WMA"
            exit 1
            ;;
    esac
    
    AUDIO_COUNT=1
    BATCH_MODE=false
    CONVERSION_ARGS="$CONVERSION_ARGS --single-file \"$FULL_PATH\""
    
else
    echo "📁 BATCH MODE"
    echo "============="
    BATCH_MODE=true
    
    # Count audio files
    mapfile -t ALL_AUDIO_FILES < <(find "$AUDIO_INPUT_DIR" \( -name "*.wav" -o -name "*.WAV" -o -name "*.mp3" -o -name "*.MP3" -o -name "*.m4a" -o -name "*.M4A" -o -name "*.flac" -o -name "*.FLAC" -o -name "*.ogg" -o -name "*.OGG" -o -name "*.aac" -o -name "*.AAC" -o -name "*.wma" -o -name "*.WMA" \) -type f 2>/dev/null | sort)
    AUDIO_COUNT=${#ALL_AUDIO_FILES[@]}
    
    if [ $AUDIO_COUNT -eq 0 ]; then
        echo "❌ No audio files found in $AUDIO_INPUT_DIR"
        echo ""
        echo "Supported formats: WAV, MP3, M4A, FLAC, OGG, AAC, WMA"
        echo ""
        echo "💡 Upload audio files using:"
        echo "   scp your_audio.wav USER@arc-login.arc.ox.ac.uk:\$DATA/podcast_env/input/"
        exit 1
    fi
    
    echo "Found $AUDIO_COUNT audio file(s):"
    echo "-" | head -c 60 && echo ""
    for i in "${!ALL_AUDIO_FILES[@]}"; do
        num=$((i + 1))
        filename=$(basename "${ALL_AUDIO_FILES[$i]}")
        size=$(ls -lh "${ALL_AUDIO_FILES[$i]}" | awk '{print $5}')
        echo "  $num. $filename ($size)"
    done
    echo ""
    
    # Interactive file selection
    echo "🎯 Selection options:"
    echo "  • Enter numbers (e.g., 1,3,5): Process specific files"
    echo "  • Enter 'all': Process all files"
    echo "  • Enter 'q': Quit"
    echo ""
    read -p "Your choice: " selection
    
    if [ "$selection" = "q" ]; then
        echo "👋 Quitting..."
        exit 0
    elif [ "$selection" = "all" ]; then
        SELECTED_FILES=("${ALL_AUDIO_FILES[@]}")
        echo "✓ Selected all $AUDIO_COUNT file(s)"
    else
        # Parse comma-separated numbers
        SELECTED_FILES=()
        IFS=',' read -ra INDICES <<< "$selection"
        for idx in "${INDICES[@]}"; do
            idx=$(echo "$idx" | tr -d ' ')
            if [[ "$idx" =~ ^[0-9]+$ ]] && [ "$idx" -ge 1 ] && [ "$idx" -le "$AUDIO_COUNT" ]; then
                SELECTED_FILES+=("${ALL_AUDIO_FILES[$((idx - 1))]}")
            fi
        done
        
        if [ ${#SELECTED_FILES[@]} -eq 0 ]; then
            echo "❌ Invalid selection. Exiting."
            exit 1
        fi
        echo "✓ Selected ${#SELECTED_FILES[@]} file(s)"
    fi
    
    AUDIO_COUNT=${#SELECTED_FILES[@]}
    echo ""
    
    # Collect episode titles for selected files
    echo "📝 Setting up episode titles"
    echo "=" | head -c 60 && echo ""
    echo "Please provide episode titles for each file. You can:"
    echo "  • Press Enter to use the auto-generated title"
    echo "  • Type a custom title and press Enter"
    echo ""
    
    for i in "${!SELECTED_FILES[@]}"; do
        filepath="${SELECTED_FILES[$i]}"
        filename=$(basename "$filepath")
        basename="${filename%.*}"
        num=$((i + 1))
        
        # Check if we already have a title
        if [ -n "${EPISODE_TITLES[$basename]}" ]; then
            echo "[$num/${#SELECTED_FILES[@]}] $filename"
            echo "   ✓ Using saved title: '${EPISODE_TITLES[$basename]}'"
        else
            # Generate suggested title from filename
            suggested="$basename"
            if [[ "$suggested" == *"_"* ]]; then
                suggested="${suggested//_/:}"
                # Normalize multiple spaces to single space
                suggested=$(echo "$suggested" | sed 's/  \+/ /g')
            fi
            
            echo "[$num/${#SELECTED_FILES[@]}] $filename"
            echo "   Suggested: '$suggested'"
            read -p "   Enter title (or press Enter for suggested): " user_title
            
            if [ -n "$user_title" ]; then
                EPISODE_TITLES["$basename"]="$user_title"
                echo "   ✓ Set title: '$user_title'"
            else
                EPISODE_TITLES["$basename"]="$suggested"
                echo "   ✓ Set title: '$suggested'"
            fi
        fi
        echo ""
    done
    
    # Save episode titles
    save_episode_titles
    
    # Create a file list for the batch job
    SELECTED_FILES_LIST="$DATA/podcast_env/.selected_files.txt"
    printf '%s\n' "${SELECTED_FILES[@]}" > "$SELECTED_FILES_LIST"
    echo "✅ Episode titles saved and file list created"
fi

echo ""

# ============================================
# Job Configuration
# ============================================
if [ "$BATCH_MODE" = true ]; then
    echo "⚙️  Batch Job Configuration:"
    echo "   Files: $AUDIO_COUNT"
    echo "   Array range: 1-$AUDIO_COUNT"
else
    echo "⚙️  Single File Job Configuration:"
    echo "   File: $(basename "$SINGLE_FILE")"
fi

# Set defaults
if [ -z "$TIME_LIMIT" ]; then
    TIME_LIMIT="08:00:00"
fi
if [ -z "$MEMORY" ]; then
    MEMORY="32G"
fi

echo "   Time limit: $TIME_LIMIT per task"
echo "   Memory: $MEMORY per task"
echo "   CPUs: 4 per task"
if [ -n "$ENHANCE_AUDIO" ]; then
    echo "   🎛️  Audio enhancement: ENABLED"
else
    echo "   🎛️  Audio enhancement: disabled"
fi
if [ -n "$TRANSCRIPTION" ]; then
    echo "   📝 Transcription: ENABLED"
    if [ -n "$TRANSCRIPTION_ARGS" ]; then
        echo "   📝 Transcription options:$TRANSCRIPTION_ARGS"
    fi
else
    echo "   📝 Transcription: disabled"
fi

echo ""

# ============================================
# Final Confirmation
# ============================================
echo "📋 Summary of files to process:"
echo "-" | head -c 60 && echo ""
if [ "$BATCH_MODE" = true ]; then
    for i in "${!SELECTED_FILES[@]}"; do
        num=$((i + 1))
        filepath="${SELECTED_FILES[$i]}"
        filename=$(basename "$filepath")
        basename="${filename%.*}"
        title="${EPISODE_TITLES[$basename]:-$basename}"
        echo "  $num. $filename"
        echo "     → \"$title\""
    done
else
    filename=$(basename "$SINGLE_FILE")
    basename="${filename%.*}"
    title="${EPISODE_TITLES[$basename]:-$basename}"
    echo "  1. $filename"
    echo "     → \"$title\""
fi
echo ""

read -p "🚀 Submit job(s) to SLURM? [Y/n]: " confirm
confirm=${confirm:-Y}
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "👋 Job submission cancelled."
    exit 0
fi

echo ""
echo "🚀 Submitting job..."

# ============================================
# Submit Job
# ============================================
if [ "$BATCH_MODE" = true ]; then
    # Batch mode: submit job array
    JOB_ID=$(sbatch \
        --clusters=htc \
        --array=1-$AUDIO_COUNT \
        --partition=short \
        --time=$TIME_LIMIT \
        --mem=$MEMORY \
        --cpus-per-task=4 \
        --output="$LOGS_DIR/video_conversion_%A_%a.out" \
        --error="$LOGS_DIR/video_conversion_%A_%a.err" \
        --parsable \
        "$SCRIPT_DIR/batch_video_conversion.sh" $CONVERSION_ARGS 2>&1)
else
    # Single file mode: submit single job
    JOB_ID=$(sbatch \
        --clusters=htc \
        --partition=short \
        --time=$TIME_LIMIT \
        --mem=$MEMORY \
        --cpus-per-task=4 \
        --output="$LOGS_DIR/video_conversion_%A.out" \
        --error="$LOGS_DIR/video_conversion_%A.err" \
        --parsable \
        "$SCRIPT_DIR/batch_video_conversion.sh" $CONVERSION_ARGS 2>&1)
fi

# ============================================
# Check Submission Result
# ============================================
echo ""
echo "📊 Submission result: '$JOB_ID'"

# Extract numeric job ID
JOB_ID_NUM=$(echo "$JOB_ID" | cut -d';' -f1)

if [[ ! $JOB_ID_NUM =~ ^[0-9]+$ ]]; then
    echo "❌ Failed to submit job"
    echo "   Error details: $JOB_ID"
    echo ""
    echo "💡 Troubleshooting:"
    echo "   - Check logs directory exists: ls -la ~/podcast/logs/"
    echo "   - Check SLURM configuration: sacctmgr show qos"
    echo "   - Try manual submission: sbatch hpc/batch_video_conversion.sh"
    exit 1
fi

if [ $? -eq 0 ] && [[ $JOB_ID_NUM =~ ^[0-9]+$ ]]; then
    if [ "$BATCH_MODE" = true ]; then
        echo "✅ Job array submitted successfully!"
        echo "   Job ID: $JOB_ID_NUM"
        echo "   Tasks: $AUDIO_COUNT (1-$AUDIO_COUNT)"
        LOG_FILES="video_conversion_${JOB_ID_NUM}_*.out"
    else
        echo "✅ Single job submitted successfully!"
        echo "   Job ID: $JOB_ID_NUM"
        echo "   File: $(basename "$SINGLE_FILE")"
        LOG_FILES="video_conversion_${JOB_ID_NUM}.out"
    fi
    
    echo "   Time: $TIME_LIMIT per task"
    echo "   Memory: $MEMORY per task"
    echo ""
    echo "📊 Monitor your job(s):"
    echo "   squeue -u \$USER -j $JOB_ID_NUM"
    echo "   tail -f ~/podcast/logs/$LOG_FILES"
    echo ""
    echo "📁 Results will be saved to:"
    echo "   \$DATA/podcast_env/output/"
else
    echo "❌ Failed to submit job"
    exit 1
fi
