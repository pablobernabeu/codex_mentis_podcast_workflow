#!/bin/bash
# Helper script to run the podcast video converter with FFmpeg in PATH

# Add FFmpeg to PATH
export PATH="$LOCALAPPDATA/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-8.0-full_build/bin:$PATH"

# Activate virtual environment
source .venv/Scripts/activate

# Run the application
python src/main.py
