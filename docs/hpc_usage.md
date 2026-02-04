# HPC Usage Guide

## Oxford ARC HPC Workflow

This guide covers usage of the Podcast Video Converter on the Oxford ARC (Advanced Research Computing) HPC cluster.

## Quick Start

### 1. Initial Setup (One-time)

```bash
# SSH into ARC
ssh USER@arc-login.arc.ox.ac.uk

# Clone or upload the project
cd ~
# Upload files via scp or git clone

# Run directory setup
cd ~/podcast/hpc
./setup_arc_structure.sh

# Activate environment
source activate_project_env_arc.sh

# Install Python packages
pip install -r ~/podcast/requirements.txt
```

### 2. Upload Your Files

```bash
# Upload podcast logo (required)
scp podcast_logo.png USER@arc-login.arc.ox.ac.uk:$DATA/podcast_env/assets/

# Upload audio files
scp episode1.wav USER@arc-login.arc.ox.ac.uk:$DATA/podcast_env/input/
scp episode2.mp3 USER@arc-login.arc.ox.ac.uk:$DATA/podcast_env/input/

# Optional: Upload episode-specific images
scp episode1.png USER@arc-login.arc.ox.ac.uk:$DATA/podcast_env/input/
```

### 3. Submit Jobs

```bash
# Activate environment (each session)
source ~/podcast/hpc/activate_project_env_arc.sh

# Submit batch job (all files)
cd ~/podcast/hpc
./submit_video_conversion.sh

# Or with audio enhancement
./submit_video_conversion.sh --enhance-audio

# Or single file
./submit_video_conversion.sh --single-file input/episode1.wav
```

### 4. Monitor & Retrieve Results

```bash
# Check job status
squeue -u $USER --clusters=htc

# View logs
tail -f ~/podcast/logs/video_conversion_*.out

# Download results
scp USER@arc-login.arc.ox.ac.uk:$DATA/podcast_env/output/*.mp4 ./
```

---

## Directory Structure

The workflow uses a split directory structure to respect ARC quotas:

### Personal Space (`~/podcast/`)
- **Quota**: Limited (~20GB)
- **Contents**: Scripts, source code, logs
- **Purpose**: Lightweight files

```
~/podcast/
├── hpc/
│   ├── submit_video_conversion.sh
│   ├── batch_video_conversion.sh
│   ├── setup_arc_structure.sh
│   ├── activate_project_env_arc.sh
│   └── verify_arc_upload.sh
├── src/
│   ├── main.py
│   ├── audio_processor.py
│   ├── video_generator.py
│   └── waveform_visualizer.py
├── logs/
├── requirements.txt
└── episode_titles.json
```

### Project Space (`$DATA/podcast_env/`)
- **Quota**: Large (~200GB+)
- **Contents**: Audio files, videos, assets, cache
- **Purpose**: Heavy data files

```
$DATA/podcast_env/
├── input/                  # Audio files go here
├── output/                 # Generated MP4 videos
├── transcripts/            # Transcription output (optional)
├── assets/                 # podcast_logo.png
├── older_input/            # Archived files
├── .waveform_cache/        # Analysis cache
└── venv/                   # Python virtual environment
```

---

## Batch Processing

Process all audio files in the input directory:

```bash
# Basic batch processing (includes transcription by default)
./submit_video_conversion.sh

# With audio enhancement (EQ, normalisation, click removal)
./submit_video_conversion.sh --enhance-audio

# Video only (disable transcription)
./submit_video_conversion.sh --no-transcription

# With transcription and name masking
./submit_video_conversion.sh --mask-personal-names

# Combine video enhancement and transcription options
./submit_video_conversion.sh --enhance-audio --mask-personal-names --language english

# With custom time limit (for very long episodes)
./submit_video_conversion.sh --time-limit 06:00:00

# With more memory (for high-resolution processing)
./submit_video_conversion.sh --memory 64G
```

### How Batch Mode Works

1. The script counts audio files in `$DATA/podcast_env/input/`
2. Submits a SLURM job array with one task per file
3. Each task processes one audio file independently
4. Results appear in `$DATA/podcast_env/output/`

---

## Single File Processing

Process one specific file:

```bash
# Basic single file
./submit_video_conversion.sh --single-file input/episode.wav

# With full path
./submit_video_conversion.sh --single-file $DATA/podcast_env/input/episode.wav

# With audio enhancement
./submit_video_conversion.sh --single-file input/episode.wav --enhance-audio

# With transcription
./submit_video_conversion.sh --single-file input/episode.wav --transcription --mask-personal-names
```

---

## Command Reference

### submit_video_conversion.sh Options

| Option | Description | Default |
|--------|-------------|---------|
| `--single-file <path>` | Process specific file | (batch mode) |
| `--enhance-audio` | Enable audio enhancement | Disabled |
| `--time-limit HH:MM:SS` | Maximum time per file | 04:00:00 |
| `--memory <size>` | Memory allocation | 32G |
| `-h, --help` | Show help | - |

### Transcription Options

Transcription is **enabled by default** and requires the [secure_local_HPC_speech_transcription](https://github.com/pablobernabeu/secure_local_HPC_speech_transcription) workflow to be installed.

| Option | Description | Default |
|--------|-------------|---------||
| `--no-transcription` | Disable audio transcription | Enabled |
| `--mask-personal-names` | Mask personal names in transcript | Disabled |
| `--language <lang>` | Transcription language | Auto-detect |
| `--fix-spurious-repetitions` | Remove repetitive patterns | Disabled |
| `--save-name-masking-logs` | Save detailed masking logs | Disabled |
| `--speaker-attribution` | Enable speaker diarisation | Disabled |
| `--exclude-names-from-masking <names>` | Comma-separated names to exclude | None |

### Examples

```bash
# Process all files with defaults (includes transcription)
./submit_video_conversion.sh

# Process all files with audio enhancement
./submit_video_conversion.sh --enhance-audio

# Process without transcription (video only)
./submit_video_conversion.sh --no-transcription

# Process with transcription and name masking
./submit_video_conversion.sh --mask-personal-names --language english

# Process single file
./submit_video_conversion.sh --single-file input/my_episode.wav

# Long episode with more time
./submit_video_conversion.sh --single-file input/long_episode.wav --time-limit 08:00:00

# High memory for complex processing
./submit_video_conversion.sh --memory 64G --enhance-audio
```

---

## Monitoring Jobs

### Check Job Status

```bash
# View your jobs
squeue -u $USER --clusters=htc

# Detailed job information
sacct -j <job_id> --format=JobID,JobName,State,ExitCode,Start,End,Elapsed

# View all recent jobs
sacct -u $USER --starttime=today --format=JobID,JobName,State,ExitCode,Elapsed
```

### View Logs

```bash
# Real-time log viewing
tail -f ~/podcast/logs/video_conversion_*.out

# View specific job log
cat ~/podcast/logs/video_conversion_<job_id>_<task_id>.out

# View errors
cat ~/podcast/logs/video_conversion_<job_id>_<task_id>.err
```

### Cancel Jobs

```bash
# Cancel specific job
scancel <job_id>

# Cancel all your jobs
scancel -u $USER --clusters=htc
```

---

## Resource Allocation

### Default Resources

| Resource | Value | Notes |
|----------|-------|-------|
| Partition | short | Max 12 hours |
| Time | 4 hours | Per file |
| Memory | 32GB | Per task |
| CPUs | 4 | Per task |
| GPU | None | CPU-based workflow |

### Adjusting Resources

```bash
# More time for long episodes (2+ hours)
./submit_video_conversion.sh --time-limit 08:00:00

# More memory for high-resolution or complex effects
./submit_video_conversion.sh --memory 64G

# Combine options
./submit_video_conversion.sh --time-limit 06:00:00 --memory 48G --enhance-audio
```

### Partition Limits

| Partition | Max Time | Use Case |
|-----------|----------|----------|
| short | 12 hours | Most episodes |
| medium | 48 hours | Very long episodes |
| long | 7 days | Batch of many files |

---

## Audio Format Support

The workflow supports multiple audio formats:

| Format | Extension | Notes |
|--------|-----------|-------|
| WAV | .wav | Best quality (recommended) |
| MP3 | .mp3 | Compressed |
| M4A | .m4a | Apple format |
| AAC | .aac | Advanced Audio Coding |
| FLAC | .flac | Lossless |
| OGG | .ogg | Ogg Vorbis |
| WMA | .wma | Windows Media |

All formats are automatically converted during processing.

---

## Troubleshooting

### Common Issues

#### "No audio files found"

```bash
# Check files are in correct location
ls -la $DATA/podcast_env/input/

# If empty, upload files
scp *.wav USER@arc-login.arc.ox.ac.uk:$DATA/podcast_env/input/
```

#### "Podcast logo not found"

```bash
# Check assets directory
ls -la $DATA/podcast_env/assets/

# Upload logo
scp podcast_logo.png USER@arc-login.arc.ox.ac.uk:$DATA/podcast_env/assets/
```

#### "Module not found" / Import errors

```bash
# Ensure environment is activated
source ~/podcast/hpc/activate_project_env_arc.sh

# Reinstall packages
pip install -r ~/podcast/requirements.txt
```

#### "FFmpeg not found"

```bash
# Load FFmpeg module
module load FFmpeg

# Or check available versions
module avail FFmpeg
```

#### Job timeout

```bash
# Use longer time limit
./submit_video_conversion.sh --time-limit 08:00:00

# Check episode duration vs time limit
# Rule of thumb: allow 2-3x episode duration
```

#### Out of memory

```bash
# Increase memory allocation
./submit_video_conversion.sh --memory 64G

# For very large files
./submit_video_conversion.sh --memory 128G
```

### Debug Steps

1. Check SLURM output files: `cat ~/podcast/logs/video_conversion_<jobid>_<taskid>.out`
2. Check error files: `cat ~/podcast/logs/video_conversion_<jobid>_<taskid>.err`
3. Verify environment: `source ~/podcast/hpc/activate_project_env_arc.sh && python --version`
4. Check disk space: `quota -s` and `du -sh $DATA/podcast_env/*`
5. Run verification: `~/podcast/hpc/verify_arc_upload.sh`

---

## Environment Setup Details

### Python Packages

Required packages (from requirements.txt):

```
moviepy>=1.0.3
librosa>=0.10.0
numpy>=1.24.0,<2.0.0
opencv-python>=4.8.0
Pillow>=10.0.0
scipy>=1.11.0
matplotlib>=3.7.0
soundfile>=0.12.0
```

### Manual Environment Setup

If automatic setup fails:

```bash
# Load Python module
module load Python/3.12

# Create virtual environment
python -m venv $DATA/podcast_env/venv

# Activate
source $DATA/podcast_env/venv/bin/activate

# Install packages
pip install --upgrade pip
pip install -r ~/podcast/requirements.txt

# Verify
python -c "import moviepy; print('MoviePy OK')"
python -c "import librosa; print('Librosa OK')"
```

---

## Workflow Integration

### Episode Titles

Episode titles are stored in `~/podcast/episode_titles.json`. On HPC, you may want to pre-configure titles:

```json
{
    "Episode 1 - Introduction": "Welcome to the Podcast",
    "Episode 2 - Deep Dive": "Exploring the Topic"
}
```

### Episode Images

Optional episode-specific images:

1. Name must match audio filename: `episode1.png` for `episode1.wav`
2. Place in same directory as audio: `$DATA/podcast_env/input/`
3. Supported formats: PNG, JPG, JPEG, WEBP, GIF, BMP

### Transcription Integration

The `--transcription` flag integrates with the [secure_local_HPC_speech_transcription](https://github.com/pablobernabeu/secure_local_HPC_speech_transcription) workflow.

#### Setup Requirements

1. Clone the transcription repository:
   ```bash
   cd ~
   git clone https://github.com/pablobernabeu/secure_local_HPC_speech_transcription.git speech_transcription
   ```

2. Set up the transcription environment:
   ```bash
   cd ~/speech_transcription
   ./hpc/setup_arc_structure.sh
   source activate_project_env_arc.sh
   pip install -r requirements.txt
   ```

3. (Optional) Download the transcription model:
   ```bash
   python setup/download_model.py
   ```

#### Using Transcription

```bash
# Basic transcription with video conversion
./submit_video_conversion.sh --transcription

# With name masking (privacy protection)
./submit_video_conversion.sh --transcription --mask-personal-names

# With language specification
./submit_video_conversion.sh --transcription --language english --mask-personal-names

# Full options
./submit_video_conversion.sh --enhance-audio --transcription \
    --mask-personal-names --fix-spurious-repetitions \
    --save-name-masking-logs
```

#### Output

Transcripts are saved to `$DATA/podcast_env/transcripts/`:
- `{filename}_transcription.txt` - Plain text transcript
- `{filename}_transcription.docx` - Word document (if python-docx available)

---

## Support

### ARC Documentation

- [ARC User Guide](https://arc-user-guide.readthedocs.io/)
- [SLURM Documentation](https://slurm.schedmd.com/documentation.html)
- [ARC Support](https://www.arc.ox.ac.uk/support)

### Project Issues

For issues with the video converter itself, check:

1. Logs in `~/podcast/logs/`
2. Run `~/podcast/hpc/verify_arc_upload.sh`
3. Test locally first if possible
