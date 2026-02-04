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

## Documentation

For comprehensive HPC usage documentation, see: **[docs/hpc_usage.md](../docs/hpc_usage.md)**
