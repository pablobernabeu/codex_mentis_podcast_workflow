# HPC Scripts

This directory contains SLURM job scripts for Oxford ARC HPC cluster.

## Quick Start

```bash
# 1. Set up directory structure (one-time)
./setup_arc_structure.sh

# 2. Activate environment
source activate_project_env_arc.sh

# 3. Submit video conversion jobs
./submit_video_conversion.sh
```

## Scripts Overview

| Script | Purpose |
|--------|---------|
| `submit_video_conversion.sh` | Main job submission script |
| `batch_video_conversion.sh` | SLURM batch script (called by submit) |
| `setup_arc_structure.sh` | One-time directory setup |
| `activate_project_env_arc.sh` | Environment activation |
| `verify_arc_upload.sh` | Verify installation |
| `clear_caches.sh` | Clear Python bytecode cache (ensures latest code) |

## Documentation

For comprehensive HPC usage documentation, see: **[docs/hpc_usage.md](../docs/hpc_usage.md)**

## Troubleshooting

### Code Changes Not Applied

**Architecture Overview:**
```
┌─────────────────────────────────────────────────────────┐
│ $HOME/podcast/src/          (Personal space, 20GB)      │
│ ├── main.py                 ← Your source code runs here│
│ ├── video_generator.py      ← Modified code is here     │
│ ├── waveform_visualizer.py                              │
│ └── audio_processor.py                                  │
└─────────────────────────────────────────────────────────┘
                              ↑
                    Jobs execute from here
                    
┌─────────────────────────────────────────────────────────┐
│ $DATA/podcast_env/          (Project space, unlimited)  │
│ ├── venv/                   ← Python packages installed │
│ │   └── lib/site-packages/  (moviepy, PIL, etc.)        │
│ ├── input/                  ← Audio files               │
│ ├── output/                 ← Videos generated          │
│ └── assets/                 ← Logo, images              │
└─────────────────────────────────────────────────────────┘
```

**How Python Imports Work:**
1. Job `cd` into `$HOME/podcast/src/`
2. Runs `python main.py` (Python from `$DATA/venv/bin/python`)
3. Imports YOUR .py files from current directory (`$HOME/podcast/src/`)
4. Imports packages (moviepy, etc.) from `$DATA/venv/lib/site-packages/`

**Your code in `$HOME/podcast/src/` is what executes!**

**Verification in Job Logs:**
Look for these diagnostic lines confirming code location:
```
📍 Working directory: /home/username/podcast/src
� Python executable: /data/username/podcast_env/venv/bin/python
[DIAGNOSTIC] video_generator.py loaded from: /home/username/podcast/src/video_generator.py
📏 Episode title font size: 56px (available space: 110px)
```

This proves:
- Code executes from `$HOME/podcast/src/` (your personal space)
- Python binary from `$DATA/venv/` (packages from project space)
- Your modified .py files are being used

**To Update Code:**
```bash
# Upload your modified .py files
rsync -av ~/podcast/src/ arc:~/podcast/src/
rsync -av ~/podcast/hpc/ arc:~/podcast/hpc/

# Submit job - will use fresh code from $HOME with PYTHONDONTWRITEBYTECODE=1
ssh arc -t 'cd ~/podcast && ./hpc/submit_video_conversion.sh'
```
