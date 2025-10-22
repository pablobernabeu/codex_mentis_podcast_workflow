# Audio to Video Converter for Codex Mentis Podcast

A Python tool to convert audio files (WAV, MP3, FLAC, M4A, AAC, OGG, WMA) into visually appealing MP4 videos with animated waveforms, logo animations and professional audio processing. This workflow was vibe-coded by Pablo Bernabeu for the Codex Mentis podcast, available on [Youtube](https://www.youtube.com/playlist?list=PLJ8d7PauMiCs6TkzJfv5cT88oAJhzoy0N), [Spotify](https://open.spotify.com/show/4QXENVjprdaGkTvOexGvD3), [Apple Podcasts](https://podcasts.apple.com/au/podcast/codex-mentis-science-and-tech-to-study-cognition/id1836910507) and [iVoox](https://www.ivoox.com/en/podcast-codex-mentis-science-and-tech-to-study-cognition_sq_f12741704_1.html).

## Initial Workflow

The current repository focusses on the video creation workflow. However, before that, the podcast is created using artificial intelligence tools. A good option is to begin by creating a script using Google Gemini Pro by providing the key materials. An example of the prompt is available in [Gemini prompt.txt](https://github.com/pablobernabeu/codex_mentis_podcast_workflow/blob/main/Gemini%20prompt.txt). Next, the audio is created using NotebookLM using a prompt like [NotebookLM prompt.txt](https://github.com/pablobernabeu/codex_mentis_podcast_workflow/blob/main/NotebookLM%20prompt.txt).

## Video Creation Workflow

- **Audio Enhancement**: Automatic volume stabilisation optimised for AI-generated speech
- **Professional Intro/Outro**: Royalty-free musical intro and outro added to each episode
- **Audio Waveform**: Continuous waveform visualisation representing real audio amplitude
- **Logo Animation**: Subtle breathing animation effect for the podcast logo
- **Professional Typography**: Elegant serif fonts with proper text hierarchy
- **Smooth Effects**: Professional transitions and animations
- **YouTube Ready**: 1920x1080 HD resolution output
- **Batch Processing**: Process individual files with easy selection
- **Smart Caching**: Intelligent waveform analysis caching for faster repeat processing
- **Auto-Validation**: Automatic logo file validation with helpful error guidance

## Setup Instructions

### 1. Install Dependencies

First, ensure you have **FFmpeg** installed on your system (required for audio format conversion):

**Windows (easiest method using winget):**

```bash
winget install Gyan.FFmpeg
```

After installation, **restart your terminal** for FFmpeg to be available.

**Alternative Windows methods:**

```bash
# Using chocolatey
choco install ffmpeg

# Or download manually from https://www.gyan.dev/ffmpeg/builds/
# Extract to C:\ffmpeg and add C:\ffmpeg\bin to your PATH
```

**macOS:**

```bash
brew install ffmpeg
```

**Linux:**

```bash
sudo apt-get install ffmpeg  # Ubuntu/Debian
sudo yum install ffmpeg      # CentOS/RHEL
```

Then, create and activate a virtual environment (recommended):

```bash
# Create virtual environment
python -m venv .venv

# Activate it (Windows Git Bash)
source .venv/Scripts/activate

# Or on Windows Command Prompt
.venv\Scripts\activate

# Or on Windows PowerShell
.venv\Scripts\Activate.ps1
```

Then install the required packages:

```bash
pip install -r requirements.txt
```

### 2. Project Structure

Place your files in the following structure:

```
podcast/
├── assets/
│   └── podcast_logo.*             # Place your podcast logo here (any image format, REQUIRED)
├── input/                        # Place your audio files here (WAV, MP3, FLAC, M4A, AAC, OGG, WMA)
├── output/                       # Generated MP4 files will be saved here
├── .waveform_cache/              # Auto-generated cache directories (created automatically)
├── src/
│   ├── audio_processor.py
│   ├── video_generator.py
│   ├── waveform_visualizer.py
│   └── main.py
├── episode_titles.json           # Auto-generated episode title storage
├── requirements.txt
└── README.md
```

### 3. Logo Requirements

- **File name**: `podcast_logo.*` (with any supported image extension)
- **Location**: `assets/podcast_logo.[extension]`
- **Recommended size**: 500x500 pixels or larger (square format works best)
- **Format**: Any format supported by Pillow (JPG, JPEG, PNG, GIF, BMP, TIFF, WEBP, AVIF, etc.)
- **Important**: Only place ONE logo file in the `assets/` directory to avoid conflicts
- **Required**: A logo file is mandatory - the application will exit if no logo is found

The tool will automatically validate your logo setup and exit with an error if no logo is detected.

### 4. Usage

Run the main script:

```bash
# Using the helper script (recommended - handles FFmpeg PATH automatically)
./run.sh

# Or manually:
python src/main.py
```

**Note:** If FFmpeg isn't found, you may need to restart your terminal or use the `run.sh` script which automatically adds FFmpeg to your PATH.

The tool will:

1. Show available audio files in the `input/` directory (supports WAV, MP3, FLAC, M4A, AAC, OGG, WMA)
2. Let you select which file(s) to process
3. Process each file with audio enhancement
4. Generate MP4 with animated waveform and logo
5. Save results in the `output/` directory

### 5. Audio Format Support

The tool supports multiple audio formats:
- **WAV** - Uncompressed audio (recommended for best quality)
- **MP3** - Compressed audio
- **FLAC** - Lossless compressed audio
- **M4A/AAC** - Advanced Audio Coding
- **OGG** - Ogg Vorbis
- **WMA** - Windows Media Audio

All formats are automatically converted and processed with the same quality output.

### 6. Episode Title Configuration

For each WAV file, you can specify a custom episode title. The tool will prompt you for this during processing or you can modify the `episode_titles.json` file.

## Cache Management

### Automatic Caching

The tool automatically creates cache files to improve performance:

- **Location**: `.waveform_cache/` directories next to your audio files
- **Purpose**: Stores pre-computed waveform analysis data
- **Behaviour**: Created automatically on first processing, reused on subsequent runs

### Cache Benefits

- **Speed**: Dramatically faster video regeneration for existing audio files
- **Reliability**: Cache is invalidated automatically when source files change
- **Storage**: Minimal disk space usage with efficient binary storage

### Manual Cache Management

If needed, you can manually manage cache files:

```bash
# Remove all cache files to force fresh analysis
find . -name ".waveform_cache" -type d -exec rm -rf {} +

# Remove cache for specific file
rm -rf input/.waveform_cache/your_episode_waveform.pkl
```

## Troubleshooting

### Logo Issues

- **Multiple logos detected**: Remove extra files from `assets/` directory, keep only one
- **Logo not found**: Application will exit with error - ensure logo file is in `assets/` directory with supported format (any image format)
- **Logo not displaying**: Check file permissions and ensure file isn't corrupted

### Performance Issues

- **Slow first run**: Normal behaviour - waveform analysis cache is being built
- **Slow subsequent runs**: Check if audio files were modified (triggers cache rebuild)
- **High memory usage**: Normal for long audio files during initial processing

## Technical Details

- **Output Resolution**: 1920x1080 (YouTube HD)
- **Audio Enhancement**: Volume normalisation and gentle EQ optimised for AI speech
- **Intro/Outro Music**: 3-second intro and 2.5-second outro with royalty-free harmonic progressions
- **Music Efficiency**: Intro/outro music cached during batch processing for maximum speed
- **Waveform Style**: Real-time amplitude visualisation with smooth scrolling animation
- **Logo Animation**: Subtle scale animation (breathing effect) integrated with waveform
- **Typography**: Professional serif fonts with episode title prominence
- **Performance**: Optimised for long audio files with efficient memory usage
- **Smart Caching**: Waveform analysis results cached for instant regeneration of existing files
- **Cache Management**: Automatic cache invalidation when source audio files are modified
- **Validation System**: Comprehensive logo file checking with clear error messages

### Performance Optimisations

#### Waveform Analysis Caching

The tool implements intelligent caching to dramatically improve performance on repeat video generations:

- **First Processing**: Audio waveform analysis is performed and cached in `.waveform_cache/` directories
- **Subsequent Processing**: Cached analysis data is loaded instantly, skipping expensive audio processing
- **Smart Invalidation**: Cache is automatically regenerated when source audio files are modified
- **Cache Validation**: File hash verification ensures cache integrity and freshness

#### Logo Validation System

Enhanced logo file validation provides better user experience:

- **Automatic Detection**: Scans `assets/` directory for logo files during startup
- **Conflict Prevention**: Warns if multiple logo files are detected and provides guidance
- **Error Guidance**: Clear instructions when logo setup is incorrect or missing
- **Seamless Integration**: Validation runs automatically without interrupting workflow

## Dependencies

- moviepy: Video editing and generation
- librosa: Audio analysis and processing
- numpy: Numerical computations
- opencv-python: Image processing
- pillow: Image manipulation
- scipy: Signal processing
