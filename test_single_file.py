#!/usr/bin/env python3
"""
Quick test script to process a single file for debugging.
"""

import os
import sys
from src.audio_processor import AudioProcessor
from src.waveform_visualizer import WaveformVisualizer
from src.video_generator import VideoGenerator


def test_single_file():
    """Test processing with a single file."""
    
    # Initialize components
    audio_processor = AudioProcessor()
    waveform_viz = WaveformVisualizer()
    video_gen = VideoGenerator()
    
    # Test with the first WAV file found
    input_dir = "input"
    if not os.path.exists(input_dir):
        print(f"❌ Input directory '{input_dir}' not found!")
        return
    
    wav_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.wav')]
    if not wav_files:
        print(f"❌ No WAV files found in '{input_dir}'!")
        return
    
    # Use the first file
    wav_file = wav_files[0]
    input_path = os.path.join(input_dir, wav_file)
    
    print(f"🧪 Testing with file: {wav_file}")
    print(f"📁 Input path: {input_path}")
    
    # Get file size
    file_size = os.path.getsize(input_path) / (1024 * 1024)  # MB
    print(f"📊 File size: {file_size:.1f} MB")
    
    # Estimate duration (rough estimate: 1 MB ≈ 60 seconds at 22kHz)
    estimated_duration = file_size * 60 / 10  # Rough estimate
    print(f"⏱ Estimated duration: {estimated_duration:.1f} seconds ({estimated_duration/60:.1f} minutes)")
    
    # For very long files, ask user confirmation
    if estimated_duration > 1800:  # 30 minutes
        response = input(f"\n⚠ This file appears to be very long ({estimated_duration/60:.1f} minutes). Continue? (y/n): ")
        if response.lower() != 'y':
            print("Cancelled.")
            return
    
    # Process audio
    print("\n🎵 Processing audio...")
    try:
        processed_audio, sr = audio_processor.process_audio(input_path)
        actual_duration = len(processed_audio) / sr
        print(f"✓ Audio processed successfully!")
        print(f"📊 Actual duration: {actual_duration:.1f} seconds ({actual_duration/60:.1f} minutes)")
        print(f"📊 Sample rate: {sr} Hz")
        print(f"📊 Channels: {processed_audio.shape}")
        
        # Save processed audio
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        
        base_name = os.path.splitext(wav_file)[0]
        wav_output = os.path.join(output_dir, f"{base_name}_enhanced.wav")
        
        # Save (audio processor should have already saved it, but let's be sure)
        if not os.path.exists(wav_output):
            import soundfile as sf
            sf.write(wav_output, processed_audio, sr)
            print(f"✓ Enhanced audio saved: {wav_output}")
        
        # Test video generation (with user consent for long files)
        if actual_duration > 300:  # 5 minutes
            response = input(f"\n🎬 Generate video for {actual_duration/60:.1f} minute file? This may take a while... (y/n): ")
            if response.lower() != 'y':
                print("Audio processing completed. Video generation skipped.")
                return
        
        print("\n🎬 Generating video...")
        episode_title = input("Enter episode title (or press Enter for test title): ").strip()
        if not episode_title:
            episode_title = f"Test Episode - {base_name}"
        
        # Create waveform generator
        waveform_generator = waveform_viz.create_frame_generator(
            processed_audio, sr, video_gen.width, video_gen.height, video_gen.fps
        )
        
        # Generate video
        video_output = os.path.join(output_dir, f"{base_name}.mp4")
        logo_path = os.path.join("assets", "podcast_logo.jpeg")
        
        video_gen.create_video(
            wav_output,
            waveform_generator,
            episode_title,
            video_output,
            logo_path if os.path.exists(logo_path) else None
        )
        
        print(f"\n✅ Test completed successfully!")
        print(f"📁 Enhanced audio: {wav_output}")
        print(f"📁 Video output: {video_output}")
        
    except Exception as e:
        print(f"\n❌ Error during processing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_single_file()
