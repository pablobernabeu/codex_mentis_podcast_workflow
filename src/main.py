#!/usr/bin/env python3
"""
Codex Mentis Podcast Audio to Video Converter
Main application file for converting WAV files to MP4 videos with waveform visualization
"""

import os
import sys
import json
import hashlib
import pickle
from pathlib import Path
import tempfile

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from audio_processor import AudioProcessor
from waveform_visualizer import WaveformVisualizer
from video_generator import VideoGenerator


class PodcastVideoConverter:
    """Main application class for the podcast video converter."""
    
    # Supported audio formats
    SUPPORTED_AUDIO_FORMATS = {'.wav', '.mp3', '.flac', '.m4a', '.aac', '.ogg', '.wma'}
    
    def __init__(self, enhance_audio=False):
        """Initialize the podcast video converter.
        
        Args:
            enhance_audio: If True, apply audio enhancement (EQ, normalization, click removal).
                          If False (default), only load audio and add intro/outro music.
        """
        self.base_dir = Path(__file__).parent.parent
        
        # Check for environment variable overrides (for HPC)
        self.input_dir = Path(os.environ.get('PODCAST_INPUT_DIR', self.base_dir / "input"))
        self.output_dir = Path(os.environ.get('PODCAST_OUTPUT_DIR', self.base_dir / "output"))
        self.assets_dir = Path(os.environ.get('PODCAST_ASSETS_DIR', self.base_dir / "assets"))
        self.logo_path = self.assets_dir / "podcast_logo.jpeg"
        self.episode_titles_file = self.base_dir / "episode_titles.json"
        self.enhance_audio = enhance_audio
        
        # Initialize components
        self.audio_processor = AudioProcessor()
        self.waveform_visualizer = WaveformVisualizer()
        self.video_generator = VideoGenerator()
        
        # Ensure directories exist
        self.ensure_directories()
        
        # Episode titles (no caching)
        self.episode_titles = {}
    
    def ensure_directories(self):
        """Create necessary directories if they don't exist."""
        for directory in [self.input_dir, self.output_dir, self.assets_dir]:
            directory.mkdir(exist_ok=True)
    
    def load_episode_titles(self):
        """Load episode titles from JSON file."""
        if self.episode_titles_file.exists():
            try:
                with open(self.episode_titles_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load episode titles: {e}")
        return {}
    
    def save_episode_titles(self):
        """Save episode titles to JSON file."""
        try:
            with open(self.episode_titles_file, 'w', encoding='utf-8') as f:
                json.dump(self.episode_titles, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Could not save episode titles: {e}")
    
    def get_audio_files(self):
        """Get list of supported audio files in the input directory."""
        # Use case-insensitive search to avoid duplicates
        audio_files = []
        for file_path in self.input_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in self.SUPPORTED_AUDIO_FORMATS:
                audio_files.append(file_path)
        return sorted(audio_files)
    
    def generate_title_from_filename(self, filename):
        """Generate a clean title from a filename.
        
        Args:
            filename: The file stem (without extension)
            
        Returns:
            A cleaned title string
        """
        import re
        clean_filename = filename
        if clean_filename.lower().startswith('episode: '):
            clean_filename = clean_filename[9:]
        
        # Replace underscore with colon
        clean_filename = clean_filename.replace('_', ':')
        # Normalize any multiple spaces to single space
        clean_filename = re.sub(r'  +', ' ', clean_filename)
        return clean_filename
    
    def collect_all_episode_titles(self, selected_files):
        """Collect episode titles for all selected files upfront."""
        print(f"\n📝 Setting up episode titles for {len(selected_files)} file(s)")
        print("=" * 60)
        print("Please provide episode titles for each file. You can:")
        print("  • Press Enter to use the auto-generated title")
        print("  • Type a custom title and press Enter")
        print()
        
        for i, wav_file_path in enumerate(selected_files, 1):
            filename = wav_file_path.stem
            
            # Generate suggested title
            suggested_title = self.generate_title_from_filename(filename)
            
            # Prompt for title
            print(f"[{i}/{len(selected_files)}] {filename}")
            print(f"   Suggested: '{suggested_title}'")
            user_title = input("   Enter title (or press Enter for suggested): ").strip()
            
            episode_title = user_title if user_title else suggested_title
            self.episode_titles[filename] = episode_title
            print(f"   ✓ Set title: '{episode_title}'")
            print()
        
        print("✅ All episode titles collected!")
        return True
    
    def select_files_to_process(self, audio_files):
        """Interactive file selection from available audio files."""
        if not audio_files:
            print("❌ No audio files found in the input directory!")
            print(f"Please place your audio files (.wav, .mp3, .flac, etc.) in: {self.input_dir}")
            return []
        
        print(f"\n📁 Found {len(audio_files)} audio file(s) in input directory:")
        print("-" * 60)
        
        for i, audio_file in enumerate(audio_files, 1):
            size_mb = audio_file.stat().st_size / (1024 * 1024)
            print(f"{i:2d}. {audio_file.name} ({size_mb:.1f} MB)")
        
        print("\n🎯 Selection options:")
        print("  • Enter numbers (e.g., 1,3,5): Process specific files")
        print("  • Enter 'all': Process all files")
        print("  • Enter 'q': Quit")
        
        while True:
            try:
                selection = input("\nYour choice: ").strip().lower()
                print(f"[DEBUG] You entered: '{selection}'")  # Debug output
                
                if selection == 'q':
                    print("Quitting...")
                    return []
                elif selection == 'all':
                    print("✓ Selected all files")
                    return audio_files
                else:
                    try:
                        # Parse comma-separated numbers
                        indices = [int(x.strip()) - 1 for x in selection.split(',')]
                        selected_files = [audio_files[i] for i in indices if 0 <= i < len(audio_files)]
                        
                        if selected_files:
                            print(f"✓ Selected {len(selected_files)} file(s)")
                            return selected_files
                        else:
                            print("❌ Invalid selection. Please try again.")
                    except (ValueError, IndexError):
                        print("❌ Invalid format. Please enter numbers separated by commas (e.g., 1,3,5).")
            except KeyboardInterrupt:
                print("\n\n👋 Process interrupted by user.")
                return []
            except EOFError:
                print("\n❌ Input error occurred.")
                return []
    
    def check_logo_file(self):
        """Check if logo file exists and validate there's only one logo file."""
        # Find all files in assets that start with 'podcast_logo'
        logo_files = list(self.assets_dir.glob("podcast_logo.*"))
        
        if len(logo_files) == 0:
            print("❌ Logo file not found!")
            print(f"Please place your podcast logo at: {self.assets_dir}/podcast_logo.[extension]")
            print("\nLogo requirements:")
            print("  • File name: podcast_logo.* (with any supported image extension)")
            print("  • Recommended size: 500x500 pixels or larger")
            print("  • Format: Any format supported by Pillow (JPG, JPEG, PNG, GIF, BMP, TIFF, WEBP, AVIF, etc.)")
            print("\n🚨 ERROR: Logo file is required for video generation.")
            print("Please add a logo file and run again.")
            sys.exit(1)
        elif len(logo_files) > 1:
            print("❌ Multiple logo files found!")
            print(f"Found {len(logo_files)} logo files in assets/:")
            for logo_file in logo_files:
                print(f"  • {logo_file.name}")
            print("\n🚨 ERROR: Please keep only ONE logo file in the assets/ directory.")
            print("Remove the extra logo files and run again.")
            sys.exit(1)
        else:
            # Update logo_path to the found file
            self.logo_path = logo_files[0]
            print(f"✓ Logo found: {self.logo_path.name}")
            return True
    
    def get_episode_image_path(self, audio_file_path):
        """Check for an optional episode-specific image matching the audio filename."""
        # Supported image formats
        image_extensions = ['.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp']
        
        # Look in the same directory as the audio file
        base_name = audio_file_path.stem
        audio_dir = audio_file_path.parent
        
        for ext in image_extensions:
            potential_image = audio_dir / f"{base_name}{ext}"
            if potential_image.exists():
                return potential_image
        
        return None
    
    def get_episode_title(self, wav_file_path):
        """Get episode title for a file (should already be collected)."""
        filename = wav_file_path.stem
        return self.episode_titles.get(filename, filename)  # Fallback to filename if not found
    
    def process_single_file(self, wav_file_path):
        """Process a single WAV file to MP4."""
        filename = wav_file_path.stem
        
        # Sanitize filename for Windows compatibility
        # Remove or replace invalid characters: < > : " | ? * \
        sanitized_filename = filename.replace(':', ' -').replace('<', '').replace('>', '').replace('"', "'").replace('|', '-').replace('?', '').replace('*', '').replace('\\', '-').replace('/', '-')
        
        output_path = self.output_dir / f"{sanitized_filename}.mp4"
        # Name the audio file based on whether enhancement is enabled
        audio_suffix = "_enhanced" if self.enhance_audio else "_processed"
        processed_audio_path = self.output_dir / f"{sanitized_filename}{audio_suffix}.wav"
        
        print(f"\n🚀 Processing: {wav_file_path.name}")
        print("=" * 80)
        
        # Check file size and warn about memory usage
        file_size_mb = wav_file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > 100:  # Large file warning
            print(f"⚠️  Large file detected ({file_size_mb:.1f} MB)")
            print("   This may require significant memory. Consider:")
            print("   • Closing other applications")
            print("   • Using a shorter audio file for testing")
            print("   • Ensuring you have at least 4GB free RAM")
        
        try:
            # Get episode title
            episode_title = self.get_episode_title(wav_file_path)
            print(f"📝 Episode title: {episode_title}")
            
            # Step 1: Process and save audio (with or without enhancement)
            audio_type = "enhanced" if self.enhance_audio else "processed"
            print(f"\n💾 Saving {audio_type} audio to: {processed_audio_path.name}")
            processed_audio, sample_rate = self.audio_processor.process_audio(
                str(wav_file_path), str(processed_audio_path), enhance_audio=self.enhance_audio
            )
            
            if processed_audio is None:
                print("❌ Failed to process audio!")
                return False
            
            # Step 2: Generate waveform frames with caching support
            duration = self.audio_processor.get_audio_duration(processed_audio, sample_rate)
            print(f"⏱️  Audio duration: {duration:.2f} seconds")
            
            waveform_frame_generator = self.waveform_visualizer.generate_waveform_frames(
                str(processed_audio_path), duration  # Pass file path for caching support
            )
            
            # Step 3: Create final video
            # Logo is guaranteed to exist due to startup validation
            logo_path = self.logo_path
            
            # Check for optional episode-specific image
            episode_image_path = self.get_episode_image_path(wav_file_path)
            if episode_image_path:
                print(f"📸 Episode image found: {episode_image_path.name}")
            
            success = self.video_generator.create_video(
                str(processed_audio_path),  # Use the saved processed audio
                waveform_frame_generator,
                episode_title,
                str(output_path),
                str(logo_path) if logo_path else None,
                str(episode_image_path) if episode_image_path else None
            )
            
            # No need to clean up temporary file since we saved the audio permanently
            
            if success:
                print(f"✅ Successfully created: {output_path.name}")
                print(f"✅ {audio_type.capitalize()} audio saved: {processed_audio_path.name}")
                video_size_mb = output_path.stat().st_size / (1024 * 1024)
                audio_size_mb = processed_audio_path.stat().st_size / (1024 * 1024)
                print(f"📊 Video file size: {video_size_mb:.1f} MB")
                print(f"📊 {audio_type.capitalize()} audio size: {audio_size_mb:.1f} MB")
                return True
            else:
                print("❌ Failed to create video!")
                return False
                
        except Exception as e:
            print(f"❌ Error processing file: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run_batch(self, single_file=None):
        """Run in batch mode (non-interactive) for HPC/automated processing.
        
        Args:
            single_file: Optional path to a specific file to process.
                        If None, processes all audio files in input directory.
        """
        print("🎙️  Codex Mentis Podcast Video Converter")
        print("=" * 60)
        print("BATCH MODE - Non-interactive processing")
        print()
        
        # Check setup
        print("🔍 Checking setup...")
        self.check_logo_file()
        
        # Determine files to process
        if single_file:
            # Process specific file
            file_path = Path(single_file)
            if not file_path.is_absolute():
                # Check if it's in the input directory
                potential_path = self.input_dir / single_file
                if potential_path.exists():
                    file_path = potential_path
                elif not file_path.exists():
                    print(f"❌ File not found: {single_file}")
                    return
            
            if not file_path.exists():
                print(f"❌ File not found: {file_path}")
                return
            
            selected_files = [file_path]
            print(f"📄 Processing single file: {file_path.name}")
        else:
            # Process all files in input directory
            print("📂 Scanning for audio files...")
            selected_files = self.get_audio_files()
            
            if not selected_files:
                print("❌ No audio files found in input directory!")
                print(f"   Input directory: {self.input_dir}")
                return
            
            print(f"✓ Found {len(selected_files)} audio file(s)")
        
        # Auto-generate titles for files not in episode_titles.json
        print("\n📝 Setting up episode titles...")
        for audio_file in selected_files:
            filename = audio_file.stem
            if filename not in self.episode_titles:
                auto_title = self.generate_title_from_filename(filename)
                self.episode_titles[filename] = auto_title
                print(f"   ✓ Auto-generated title for '{filename}': '{auto_title}'")
            else:
                print(f"   ✓ Using title for '{filename}': '{self.episode_titles[filename]}'")
        
        # Process files
        print(f"\n🎯 Processing {len(selected_files)} file(s)...")
        print("💫 Optimizations: Intro/outro music will be cached for efficiency")
        
        successful = 0
        failed = 0
        
        for i, audio_file in enumerate(selected_files, 1):
            print(f"\n[{i}/{len(selected_files)}] " + "=" * 40)
            
            if self.process_single_file(audio_file):
                successful += 1
            else:
                failed += 1
        
        # Summary
        print("\n" + "=" * 80)
        print("📋 BATCH PROCESSING SUMMARY")
        print("-" * 30)
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")
        print(f"📁 Output directory: {self.output_dir}")
        
        if successful > 0:
            print("\n🎉 Batch processing complete!")
    
    def run(self):
        """Main application entry point (interactive mode)."""
        print("🎙️  Codex Mentis Podcast Video Converter")
        print("=" * 60)
        print("Converting audio files to MP4 videos with elegant waveform visualisation")
        print()
        
        # Check setup
        print("🔍 Checking setup...")
        self.check_logo_file()
        
        # Get available files
        print("📂 Scanning for audio files...")
        audio_files = self.get_audio_files()
        print(f"✓ Found {len(audio_files)} audio files")
        
        # Let user select files
        print("📝 File selection...")
        selected_files = self.select_files_to_process(audio_files)
        
        if not selected_files:
            print("\n👋 No files selected. Goodbye!")
            return
        
        print(f"✓ Selected {len(selected_files)} files for processing")
        
        # Collect episode titles for all selected files upfront
        print("📝 Collecting episode titles...")
        if not self.collect_all_episode_titles(selected_files):
            print("\n❌ Failed to collect episode titles. Exiting.")
            return
        
        # Process selected files
        print(f"\n🎯 Processing {len(selected_files)} file(s)...")
        print("💫 Optimizations: Intro/outro music will be cached for efficiency")
        
        successful = 0
        failed = 0
        
        for i, wav_file in enumerate(selected_files, 1):
            print(f"\n[{i}/{len(selected_files)}] " + "=" * 40)
            
            if self.process_single_file(wav_file):
                successful += 1
            else:
                failed += 1
        
        # Summary
        print("\n" + "=" * 80)
        print("📋 PROCESSING SUMMARY")
        print("-" * 30)
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")
        print(f"📁 Output directory: {self.output_dir}")
        
        if successful > 0:
            print("\n🎉 Processing complete!")
            print("💡 Output files:")
            print("  📹 MP4 videos: Ready for upload to YouTube!")
            print("  🎵 Enhanced WAV files: Professional quality audio")
            print("  📁 All files saved in the output directory")
            print("\n💡 File details:")
            print("  • Videos: 1920x1080 HD resolution, H.264 codec")
            print("  • Audio: Enhanced with noise reduction, EQ, and normalization")
            print("  • Waveform animations sync perfectly with your audio")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Codex Mentis Podcast Audio to Video Converter"
    )
    parser.add_argument(
        "--enhance-audio",
        action="store_true",
        help="Enable audio enhancement (EQ, normalization, click removal). Disabled by default."
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Run in batch mode (non-interactive). Processes all audio files using titles from episode_titles.json."
    )
    parser.add_argument(
        "--file",
        type=str,
        help="Process a specific audio file (path or filename in input directory)."
    )
    
    args = parser.parse_args()
    
    try:
        converter = PodcastVideoConverter(enhance_audio=args.enhance_audio)
        
        if args.batch or args.file:
            # Non-interactive batch mode
            converter.run_batch(single_file=args.file)
        else:
            # Interactive mode
            converter.run()
    except KeyboardInterrupt:
        print("\n\n👋 Process interrupted by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        print("Please check your setup and try again.")


if __name__ == "__main__":
    main()
