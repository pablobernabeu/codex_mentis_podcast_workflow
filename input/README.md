# Input Directory

Place your WAV audio files here for processing.

## Supported Formats:

- .wav
- .WAV (case variations)

## File Naming:

- Use descriptive names (e.g., `episode_001.wav`, `intro_to_ai.wav`)
- Avoid special characters except underscores and hyphens
- The output MP4 will have the same base name as your WAV file

## Audio Quality:

- Any sample rate (will be processed to 44.1kHz)
- Any bit depth
- Mono or stereo (will be processed appropriately)

## File Size:

- No specific limits, but larger files take longer to process
- Typical podcast episodes (30-60 minutes) work well

## Processing:

The converter will automatically:

1. Add professional intro and outro music
2. Generate animated waveform visualization
3. Create MP4 video with logo animation

### Optional Audio Enhancement (disabled by default):

When audio enhancement is enabled, the converter also:

- Enhances audio quality
- Stabilizes volume levels
- Applies gentle EQ for speech clarity
- Removes clicks and pops

To enable audio enhancement, run with `--enhance-audio` flag:

```bash
python src/main.py --enhance-audio
```

Simply place your audio files here and run the main application!
