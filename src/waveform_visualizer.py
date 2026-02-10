import numpy as np
import librosa
import cv2
import hashlib
import pickle
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap


class WaveformVisualizer:
    """Creates waveform visualizations with beige color scheme."""
    
    def __init__(self, width=1920, height=1080):
        self.width = width
        self.height = height
        self.fps = 30
        
        self.colors = {
            'background': (20, 25, 35),      # Dark blue-gray background
            'waveform_light': (255, 245, 115),
            'waveform_mid': (255, 235, 100),
            'waveform_dark': (255, 220, 90),
            'text': (240, 235, 220),
            'accent': (255, 235, 100)
        }
        
        self.waveform_center_y = height // 2
        self.waveform_amplitude = 900
        self.waveform_area_height = 900
        self.waveform_line_thickness = 1
        
        self.samples_per_pixel = 100
        self.history_width = width
        self.scroll_speed = 2
        
    def analyze_audio_frame(self, audio, sr, start_time, window_duration=3.0):
        """Analyze audio segment and extract waveform amplitudes."""
        start_sample = int(start_time * sr)
        window_samples = int(window_duration * sr)
        end_sample = min(start_sample + window_samples, len(audio))
        
        if start_sample >= len(audio):
            return np.zeros(self.history_width)
        
        window_audio = audio[start_sample:end_sample]
        if len(window_audio) == 0:
            return np.zeros(self.history_width)
        
        samples_per_pixel = max(1, len(window_audio) // self.history_width)
        downsampled = []
        for i in range(0, len(window_audio), samples_per_pixel):
            chunk = window_audio[i:i + samples_per_pixel]
            if len(chunk) > 0:
                # Use RMS for volume representation
                rms_value = np.sqrt(np.mean(chunk**2))
                avg_value = np.mean(chunk)
                # Create spiky brainwave pattern
                combined = avg_value * (0.3 + 5.5 * rms_value)
                spike_variation = np.random.normal(0, 0.35) * rms_value
                combined += spike_variation
                # Add frequent sharp spikes
                if np.random.random() < 0.25:
                    combined *= np.random.uniform(1.8, 3.2)
                downsampled.append(combined)
        
        # Pad or trim to exact width
        if len(downsampled) < self.history_width:
            downsampled.extend([0] * (self.history_width - len(downsampled)))
        else:
            downsampled = downsampled[:self.history_width]
        
        return np.array(downsampled)
    
    def create_waveform_frame(self, waveform_data, time_position, total_duration):
        """Create a single frame of the waveform visualization."""
        # Create transparent RGBA frame
        frame = np.zeros((self.height, self.width, 4), dtype=np.uint8)
        
        # Draw center baseline
        center_line_color = [*[int(c * 0.3) for c in self.colors['waveform_dark']], 128]
        cv2.line(frame, (0, self.waveform_center_y), (self.width, self.waveform_center_y), 
                center_line_color, 1)
        
        # Convert waveform amplitudes to pixel coordinates
        if len(waveform_data) > 1:
            points = []
            for i, amplitude in enumerate(waveform_data):
                x = i
                if x >= self.width:
                    break
                
                # Scale amplitude to pixels
                y_offset = amplitude * self.waveform_amplitude
                y = self.waveform_center_y - int(y_offset)
                y = max(50, min(self.height - 50, y))  # Clamp to screen bounds
                
                points.append((x, y))
            
            # Draw waveform line
            if len(points) > 1:
                self.draw_smooth_waveform(frame, points, waveform_data[:len(points)])
        
        return frame
    
    def draw_smooth_waveform(self, frame, points, amplitude_data):
        """Draw smooth waveform with minimal glow effect."""
        for pass_idx in range(4):
            # Ultra-thin core with minimal glow
            if pass_idx < 1:
                thickness = max(1, self.waveform_line_thickness + 2)
            else:
                thickness = 1
            if pass_idx == 0:  # Outermost glow
                color = [255, 230, 100]  # Medium yellow (minimal glow)
            elif pass_idx == 1:  # Inner glow
                color = [255, 235, 105]  # Bright yellow
            elif pass_idx == 2:  # Near core
                color = [255, 240, 110]  # Brighter yellow
            else:  # Core (pass_idx == 3)
                color = [255, 245, 115]  # Brightest yellow (matches frame)
            
            # Draw line segments with full opacity
            for i in range(len(points) - 1):
                amp_intensity = min(1.0, abs(amplitude_data[i] if i < len(amplitude_data) else 0) * 30)
                brightness_boost = 0.85 + 0.15 * amp_intensity
                adjusted_color = [int(c * brightness_boost) for c in color] + [255]
                
                cv2.line(frame, points[i], points[i + 1], adjusted_color, thickness)
    
    def add_progress_bar(self, frame, time_position, total_duration):
        """Add a subtle progress bar at the bottom."""
        if total_duration <= 0:
            return frame
        
        progress = time_position / total_duration
        bar_width = self.width - 200
        bar_height = 4
        bar_x = 100
        bar_y = self.height - 30
        
        # Background of progress bar
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), 
                     self.colors['waveform_dark'], -1)
        
        # Progress fill
        fill_width = int(bar_width * progress)
        if fill_width > 0:
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + fill_width, bar_y + bar_height), 
                         self.colors['accent'], -1)
        
        return frame
    
    def get_audio_hash(self, audio_path):
        """Generate a hash of the audio file for cache validation."""
        audio_path = Path(audio_path)
        if not audio_path.exists():
            return None
        
        # Use file size and modification time for quick hash
        stat = audio_path.stat()
        hash_string = f"{audio_path.name}_{stat.st_size}_{stat.st_mtime}"
        return hashlib.md5(hash_string.encode()).hexdigest()
    
    def get_cache_path(self, audio_path):
        """Get the cache file path for waveform analysis data."""
        audio_path = Path(audio_path)
        cache_dir = audio_path.parent / ".waveform_cache"
        cache_dir.mkdir(exist_ok=True)
        return cache_dir / f"{audio_path.stem}_waveform.pkl"
    
    def save_waveform_cache(self, audio_path, waveform_cache, audio_hash):
        """Save waveform analysis data to cache."""
        cache_path = self.get_cache_path(audio_path)
        cache_data = {
            'audio_hash': audio_hash,
            'waveform_cache': waveform_cache,
            'cache_version': '1.0'  # For future compatibility
        }
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(cache_data, f)
            print(f"  ✓ Waveform analysis cached to: {cache_path.name}")
        except Exception as e:
            print(f"  ⚠ Warning: Could not save waveform cache: {e}")
    
    def load_waveform_cache(self, audio_path):
        """Load waveform analysis data from cache if available and valid."""
        cache_path = self.get_cache_path(audio_path)
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'rb') as f:
                cache_data = pickle.load(f)
            
            # Validate cache version and audio hash
            if cache_data.get('cache_version') != '1.0':
                print(f"  ⚠ Cache version mismatch, regenerating analysis...")
                return None
            
            current_hash = self.get_audio_hash(audio_path)
            if cache_data.get('audio_hash') != current_hash:
                print(f"  ⚠ Audio file changed, regenerating analysis...")
                return None
            
            print(f"  ✓ Using cached waveform analysis from: {cache_path.name}")
            return cache_data['waveform_cache']
        
        except Exception as e:
            print(f"  ⚠ Warning: Could not load waveform cache: {e}")
            return None
    
    def smooth_waveform_data(self, current_data, previous_data, smoothing_factor=0.8):
        """Apply temporal smoothing to waveform data for smoother animation."""
        if previous_data is None:
            return current_data
        
        return (smoothing_factor * previous_data + 
                (1 - smoothing_factor) * current_data)
    
    def generate_waveform_frames(self, audio_path, total_duration):
        """Generate waveform frames on-demand with caching support."""
        frame_count = int(total_duration * self.fps)
        frame_duration = 1.0 / self.fps
        
        print(f"🎨 Preparing waveform generator for {frame_count} frames...")
        
        # Try to load cached waveform analysis
        audio_hash = self.get_audio_hash(audio_path)
        cached_waveform_data = None
        
        if audio_hash:
            cached_waveform_data = self.load_waveform_cache(audio_path)
        
        # Use cached data or generate new analysis
        if cached_waveform_data is not None:
            print("  ✓ Using cached waveform analysis data")
            waveform_cache = cached_waveform_data
        else:
            print("  🎵 Loading audio for fresh waveform analysis...")
            audio, sr = librosa.load(audio_path, sr=22050)
            
            print("  📊 Computing waveform analysis...")
            waveform_cache = []
            previous_data = None
            
            for frame_idx in range(frame_count):
                if frame_idx % 500 == 0:
                    print(f"    Waveform analysis: {frame_idx}/{frame_count} frames ({frame_idx/frame_count*100:.1f}%)")
                
                time_position = frame_idx * frame_duration
                waveform_data = self.analyze_audio_frame(audio, sr, time_position)
                waveform_data = self.smooth_waveform_data(waveform_data, previous_data)
                previous_data = waveform_data.copy()
                waveform_cache.append(waveform_data)
            
            # Save to cache if we have a valid hash
            if audio_hash:
                self.save_waveform_cache(audio_path, waveform_cache, audio_hash)
            
            print("✓ Waveform analysis complete!")
        
        print("  Note: Frames will be generated on-demand to save memory")
        
        # Return a generator function instead of all frames at once
        def frame_generator():
            for frame_idx in range(frame_count):
                if frame_idx % 100 == 0:
                    print(f"  Generating frame: {frame_idx}/{frame_count} ({frame_idx/frame_count*100:.1f}%)")
                
                time_position = frame_idx * frame_duration
                waveform_data = waveform_cache[frame_idx] if frame_idx < len(waveform_cache) else np.zeros(self.history_width)
                
                # Create waveform frame
                frame = self.create_waveform_frame(waveform_data, time_position, total_duration)
                frame = self.add_progress_bar(frame, time_position, total_duration)
                
                # Yield both frame and waveform data for audio-reactive effects
                yield frame, waveform_data
        
        return frame_generator()
