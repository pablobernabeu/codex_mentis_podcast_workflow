# Audio to Video Converter for Codex Mentis Podcast

A Python tool to convert WAV audio files into visually appealing MP4 videos with animated waveforms, logo animations and professional audio processing. This workflow was vibe-coded by Pablo Bernabeu for the Codex Mentis podcast, available on [Youtube](https://www.youtube.com/playlist?list=PLJ8d7PauMiCs6TkzJfv5cT88oAJhzoy0N), [Spotify](https://open.spotify.com/show/4QXENVjprdaGkTvOexGvD3), [Apple Podcasts](https://podcasts.apple.com/au/podcast/codex-mentis-science-and-tech-to-study-cognition/id1836910507) and [iVoox](https://www.ivoox.com/en/podcast-codex-mentis-science-and-tech-to-study-cognition_sq_f12741704_1.html).

## Features

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

```bash
pip install -r requirements.txt
```

### 2. Project Structure

Place your files in the following structure:

```
podcast/
├── assets/
│   └── podcast_logo.*             # Place your podcast logo here (any image format, REQUIRED)
├── input/                        # Place your WAV files here
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
python src/main.py
```

The tool will:

1. Show available WAV files in the `input/` directory
2. Let you select which file(s) to process
3. Process each file with audio enhancement
4. Generate MP4 with animated waveform and logo
5. Save results in the `output/` directory

### 5. Episode Title Configuration

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
