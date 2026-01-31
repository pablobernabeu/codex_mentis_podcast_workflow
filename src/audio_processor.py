import librosa
import numpy as np
import soundfile as sf
from scipy import signal
import os

# Note: Noise reduction disabled for AI-generated speech (no noise present)


class AudioProcessor:
    """Handles audio enhancement and processing for podcast files."""
    
    def __init__(self):
        self.sample_rate = 44100
        self.target_lufs = -16  # Industry standard for podcast loudness
        self._intro_music_cache = None
        self._outro_music_cache = None
        self.intro_duration = 18.0  # seconds (3 + 15)
        self.outro_duration = 17.5  # seconds (2.5 + 15)
    
    def _find_ffmpeg(self):
        """Find FFmpeg executable in common installation locations."""
        import shutil
        
        # First, check if ffmpeg is in PATH
        ffmpeg_path = shutil.which('ffmpeg')
        if ffmpeg_path:
            return ffmpeg_path
        
        # On Windows, check common installation locations
        if os.name == 'nt':
            potential_paths = [
                # WinGet installation path
                os.path.join(os.environ.get('LOCALAPPDATA', ''), 
                            'Microsoft', 'WinGet', 'Packages', 
                            'Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe',
                            'ffmpeg-8.0-full_build', 'bin', 'ffmpeg.exe'),
                # Chocolatey installation path
                r'C:\ProgramData\chocolatey\bin\ffmpeg.exe',
                # Manual installation paths
                r'C:\ffmpeg\bin\ffmpeg.exe',
                r'C:\Program Files\ffmpeg\bin\ffmpeg.exe',
            ]
            
            for path in potential_paths:
                if os.path.isfile(path):
                    return path
        
        return None
    
    def load_audio(self, file_path):
        """Load audio file and return audio data and sample rate."""
        import subprocess
        import tempfile
        
        # Check if file is a compressed format that might need FFmpeg
        compressed_formats = ['.m4a', '.aac', '.mp3', '.ogg', '.wma']
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext in compressed_formats:
            print(f"ℹ Detected compressed format {file_ext}, using FFmpeg conversion...")
            
            # Find FFmpeg executable
            ffmpeg_exe = self._find_ffmpeg()
            if not ffmpeg_exe:
                print("✗ FFmpeg not found. Please ensure FFmpeg is installed.")
                print("  Windows: winget install Gyan.FFmpeg")
                print("  macOS: brew install ffmpeg")
                print("  Linux: sudo apt-get install ffmpeg")
                print("  After installation, restart your terminal.")
                return None, None
            
            try:
                # Convert to WAV using FFmpeg directly
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
                    temp_path = temp_wav.name
                
                # Use FFmpeg to convert to WAV
                ffmpeg_cmd = [
                    ffmpeg_exe,
                    '-i', file_path,
                    '-acodec', 'pcm_s16le',
                    '-ar', str(self.sample_rate),
                    '-ac', '1',
                    '-y',
                    temp_path
                ]
                
                result = subprocess.run(
                    ffmpeg_cmd,
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                
                if result.returncode != 0:
                    print(f"✗ FFmpeg conversion failed:")
                    print(f"  {result.stderr}")
                    return None, None
                
                # Load the converted WAV file
                audio, sr = librosa.load(temp_path, sr=self.sample_rate)
                
                # Clean up temp file
                try:
                    os.unlink(temp_path)
                except:
                    pass
                
                print(f"✓ Loaded audio: {os.path.basename(file_path)}")
                print(f"  Duration: {len(audio) / sr:.2f} seconds")
                print(f"  Sample rate: {sr} Hz")
                return audio, sr
                
            except Exception as e:
                print(f"✗ Error during FFmpeg conversion:")
                print(f"  {type(e).__name__}: {str(e)}")
                return None, None
        
        # For WAV and FLAC files, use librosa directly
        try:
            audio, sr = librosa.load(file_path, sr=self.sample_rate)
            print(f"✓ Loaded audio: {os.path.basename(file_path)}")
            print(f"  Duration: {len(audio) / sr:.2f} seconds")
            print(f"  Sample rate: {sr} Hz")
            return audio, sr
        except Exception as e:
            print(f"✗ Error loading audio file:")
            print(f"  File: {file_path}")
            print(f"  Error type: {type(e).__name__}")
            print(f"  Error message: {str(e)}")
            import traceback
            print(f"  Traceback: {traceback.format_exc()}")
            return None, None
    
    def normalize_volume(self, audio):
        """Normalize audio volume with gentle dynamic range compression."""
        try:
            # Remove DC offset first
            audio = audio - np.mean(audio)
            
            # Apply very gentle compression to avoid artifacts
            threshold = 0.5
            ratio = 2.0  # Much gentler ratio
            attack = 0.003  # 3ms attack
            release = 0.1   # 100ms release
            
            # Simple soft-knee compression with smooth transitions
            compressed = np.copy(audio)
            
            # Apply compression with smooth knee
            for i in range(len(compressed)):
                sample = compressed[i]
                abs_sample = abs(sample)
                
                if abs_sample > threshold:
                    # Soft knee compression
                    over_threshold = abs_sample - threshold
                    compressed_amount = over_threshold / ratio
                    compressed[i] = np.sign(sample) * (threshold + compressed_amount)
            
            # Gentle normalization to prevent clipping
            peak = np.max(np.abs(compressed))
            if peak > 0:
                target_peak = 0.7  # Conservative headroom
                compressed = compressed * (target_peak / peak)
            
            # Apply gentle limiter to catch any remaining peaks
            compressed = np.tanh(compressed * 0.9) * 0.8
            
            print("✓ Applied gentle volume normalization and compression")
            return compressed
        except Exception as e:
            print(f"⚠ Warning: Could not normalize volume: {e}")
            return audio
    
    def apply_eq(self, audio, sr):
        """Apply gentle EQ to enhance speech clarity."""
        try:
            # Design a gentle high-pass filter to remove low-frequency rumble
            nyquist = sr // 2
            low_cutoff = 80  # Hz
            high_cutoff = 12000  # Hz
            
            # High-pass filter
            sos_hp = signal.butter(2, low_cutoff / nyquist, btype='high', output='sos')
            audio_filtered = signal.sosfilt(sos_hp, audio)
            
            # Gentle low-pass filter to soften harsh frequencies
            sos_lp = signal.butter(2, high_cutoff / nyquist, btype='low', output='sos')
            audio_filtered = signal.sosfilt(sos_lp, audio_filtered)
            
            print("✓ Applied EQ filtering")
            return audio_filtered
        except Exception as e:
            print(f"⚠ Warning: Could not apply EQ: {e}")
            return audio
    
    def remove_clicks_and_pops(self, audio, sr):
        """Remove clicks, pops, and digital artifacts - optimized for long files."""
        try:
            # For very long files, use a more efficient approach
            audio_duration = len(audio) / sr
            if audio_duration > 1800:  # 30 minutes
                print(f"  Optimizing click removal for long file ({audio_duration/60:.1f} minutes)...")
                # Use faster method for long files
                return self._fast_click_removal(audio, sr)
            
            # Standard method for shorter files
            window_size = int(0.002 * sr)  # 2ms window
            if window_size < 3:
                window_size = 3
            
            # Process in chunks for memory efficiency
            chunk_size = sr * 30  # 30 second chunks
            if len(audio) <= chunk_size:
                # Process small files normally
                return self._process_clicks_chunk(audio, window_size)
            
            # Process large files in chunks
            print(f"  Processing in chunks for efficiency...")
            processed_chunks = []
            for i in range(0, len(audio), chunk_size):
                chunk = audio[i:i + chunk_size]
                processed_chunk = self._process_clicks_chunk(chunk, window_size)
                processed_chunks.append(processed_chunk)
                
                # Progress indicator for long files
                progress = (i + chunk_size) / len(audio) * 100
                if progress <= 100:
                    print(f"    Progress: {progress:.0f}%")
            
            cleaned_audio = np.concatenate(processed_chunks)
            print("✓ Removed clicks and pops")
            return cleaned_audio
            
        except Exception as e:
            print(f"⚠ Warning: Could not remove clicks/pops: {e}")
            return audio
    
    def _fast_click_removal(self, audio, sr):
        """Fast click removal for very long files."""
        # Use a simpler but faster method for long files
        # Apply a gentle median filter only to extreme outliers
        threshold = 0.8  # Higher threshold for speed
        
        # Find extreme outliers (potential clicks)
        audio_abs = np.abs(audio)
        outliers = audio_abs > threshold
        
        if np.any(outliers):
            # Simple interpolation for outliers
            audio_clean = audio.copy()
            outlier_indices = np.where(outliers)[0]
            
            for idx in outlier_indices:
                # Simple average with neighbors
                start = max(0, idx - 2)
                end = min(len(audio), idx + 3)
                neighbors = audio[start:end]
                neighbors = neighbors[neighbors != audio[idx]]  # Exclude the outlier itself
                if len(neighbors) > 0:
                    audio_clean[idx] = np.median(neighbors)
            
            return audio_clean
        
        return audio
    
    def _process_clicks_chunk(self, audio_chunk, window_size):
        """Process a chunk of audio for click removal."""
        # Pad audio for edge handling
        padded_audio = np.pad(audio_chunk, window_size//2, mode='edge')
        
        # Apply median filter to detect outliers
        filtered = np.copy(padded_audio)
        for i in range(window_size//2, len(padded_audio) - window_size//2):
            window = padded_audio[i - window_size//2:i + window_size//2 + 1]
            median = np.median(window)
            
            # If sample is significantly different from median, it's likely a click
            if abs(padded_audio[i] - median) > 0.1:  # Threshold for click detection
                filtered[i] = median
        
        # Remove padding
        return filtered[window_size//2:-window_size//2]
    
    def process_audio(self, input_path, output_path=None, enhance_audio=False):
        """Complete audio processing pipeline.
        
        Args:
            input_path: Path to the input audio file
            output_path: Optional path to save processed audio
            enhance_audio: If True, apply audio enhancement (EQ, normalization, click removal).
                          If False (default), only load audio and add intro/outro music.
        """
        print(f"\n🎵 Processing audio: {os.path.basename(input_path)}")
        print("-" * 50)
        
        # Load audio
        audio, sr = self.load_audio(input_path)
        if audio is None:
            return None, None
        
        if enhance_audio:
            # Apply processing steps optimized for AI-generated speech
            audio = self.remove_clicks_and_pops(audio, sr)  # Keep this for any digital artifacts
            audio = self.apply_eq(audio, sr)  # Gentle EQ for speech clarity
            audio = self.normalize_volume(audio)  # Volume stabilization only
        else:
            print("ℹ Audio enhancement disabled, skipping EQ/normalization/click removal")
        
        # Add intro and outro music for professional presentation
        audio = self.add_intro_outro_music(audio, sr)
        
        # No noise reduction (AI-generated speech is clean)
        # No fade effects (music handles intro/outro)
        
        # Save processed audio if output path provided
        if output_path:
            try:
                sf.write(output_path, audio, sr, format='WAV')
                print(f"✓ Saved processed audio to: {os.path.basename(output_path)}")
            except Exception as e:
                print(f"✗ Error saving audio: {e}")
        
        print("✓ Audio processing complete!")
        return audio, sr
    
    def add_intro_outro_music(self, speech_audio, sr):
        """Add pre-generated intro and outro music to the speech audio."""
        try:
            speech_duration = len(speech_audio) / sr
            print(f"🎵 Adding intro and outro music...")
            print(f"  Speech duration: {speech_duration:.1f}s")
            
            # Generate music once and cache for efficiency
            intro_music = self._get_cached_intro_music()
            outro_music = self._get_cached_outro_music()
            
            # Simple concatenation - much faster than complex mixing
            print("  Combining audio segments...")
            final_audio = np.concatenate([intro_music, speech_audio, outro_music])
            
            total_duration = len(final_audio) / sr
            print(f"✓ Added intro and outro music (total duration: {total_duration:.1f}s)")
            return final_audio
            
        except Exception as e:
            print(f"⚠ Warning: Could not add intro/outro music: {e}")
            return speech_audio
    
    def _get_cached_intro_music(self):
        """Get cached intro music, generating it once if needed."""
        if self._intro_music_cache is None:
            duration = 3.0  # 3 seconds intro
            samples = int(self.sample_rate * duration)
            self._intro_music_cache = self.generate_intro_music(samples, self.sample_rate)
            print("  Generated intro music (cached for future episodes)")
        return self._intro_music_cache.copy()
    
    def _get_cached_outro_music(self):
        """Get cached outro music, generating it once if needed."""
        if self._outro_music_cache is None:
            duration = 2.5  # 2.5 seconds outro
            samples = int(self.sample_rate * duration)
            self._outro_music_cache = self.generate_outro_music(samples, self.sample_rate)
            print("  Generated outro music (cached for future episodes)")
        return self._outro_music_cache.copy()
    
    def generate_intro_music(self, samples, sr):
        """Generate a varied, professional intro music (longer, with chord/melody/rhythm variation)."""
        duration = samples / sr
        t = np.linspace(0, duration, samples)
        # Chord progression: C - Am - F - G (4 bars, 4s each, repeat)
        chords = [
            (261.63, 329.63, 392.00),   # C major
            (220.00, 261.63, 329.63),   # A minor
            (174.61, 220.00, 349.23),   # F major
            (196.00, 246.94, 392.00)    # G major
        ]
        bar_length = int(sr * 4)
        intro = np.zeros(samples)
        for i in range(0, samples, bar_length):
            bar_idx = (i // bar_length) % len(chords)
            root, third, fifth = chords[bar_idx]
            bar_t = t[i:i+bar_length]
            # Melody: rising/falling sine
            melody = 0.08 * np.sin(2 * np.pi * (root * 2) * bar_t + np.sin(bar_t * 2))
            # Rhythm: gentle pulsing
            rhythm = 0.5 * (1 + np.sin(2 * np.pi * 0.5 * bar_t))
            bar = (
                0.18 * np.sin(2 * np.pi * root * bar_t) +
                0.14 * np.sin(2 * np.pi * third * bar_t) +
                0.12 * np.sin(2 * np.pi * fifth * bar_t) +
                melody
            ) * rhythm
            intro[i:i+bar_length] = bar[:min(bar_length, samples - i)]
        # Fade in/out
        fade_samples = int(1.5 * sr)
        if fade_samples > 0:
            intro[:fade_samples] *= np.linspace(0, 1, fade_samples)
            intro[-fade_samples:] *= np.linspace(1, 0, fade_samples)
        return intro

    def generate_outro_music(self, samples, sr):
        """Generate a varied, professional outro music (longer, with chord/melody/rhythm variation, different from intro)."""
        duration = samples / sr
        t = np.linspace(0, duration, samples)
        # Chord progression: Dm - G - C - Am (4 bars, 4s each, repeat)
        chords = [
            (293.66, 349.23, 440.00),   # D minor
            (196.00, 246.94, 392.00),   # G major
            (261.63, 329.63, 392.00),   # C major
            (220.00, 261.63, 329.63)    # A minor
        ]
        bar_length = int(sr * 4)
        outro = np.zeros(samples)
        for i in range(0, samples, bar_length):
            bar_idx = (i // bar_length) % len(chords)
            root, third, fifth = chords[bar_idx]
            bar_t = t[i:i+bar_length]
            # Melody: falling/rising sine
            melody = 0.08 * np.sin(2 * np.pi * (fifth * 1.5) * bar_t + np.cos(bar_t * 2))
            # Rhythm: gentle pulsing, slightly different from intro
            rhythm = 0.5 * (1 + np.sin(2 * np.pi * 0.33 * bar_t))
            bar = (
                0.16 * np.sin(2 * np.pi * root * bar_t) +
                0.13 * np.sin(2 * np.pi * third * bar_t) +
                0.11 * np.sin(2 * np.pi * fifth * bar_t) +
                melody
            ) * rhythm
            outro[i:i+bar_length] = bar[:min(bar_length, samples - i)]
        # Fade in/out
        fade_samples = int(1.5 * sr)
        if fade_samples > 0:
            outro[:fade_samples] *= np.linspace(0, 1, fade_samples)
            outro[-fade_samples:] *= np.linspace(1, 0, fade_samples)
        return outro
    
    def get_audio_duration(self, audio, sr):
        """Get audio duration in seconds."""
        return len(audio) / sr if audio is not None else 0
