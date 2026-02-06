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
        
        # Bright yellow/golden brainwave color palette (RGB values)
        self.colors = {
            'background': (20, 25, 35),      # Dark blue-gray background
            'waveform_light': (255, 255, 180),  # Bright yellow-white
            'waveform_mid': (255, 240, 120),    # Golden yellow
            'waveform_dark': (255, 220, 80),    # Deep golden
            'text': (240, 235, 220),            # Light beige for text
            'accent': (255, 240, 100)           # Intense golden accent
        }
        
        # Waveform parameters - configured for sharp, spiky brainwave appearance
        self.waveform_center_y = height // 2  # Center line aligned with logo center
        self.waveform_amplitude = 380  # High amplitude for dramatic spikes
        self.waveform_area_height = 400  # Total height for waveform area
        self.waveform_line_thickness = 2  # Thin line for sharp, precise brainwave look
        
        # Scrolling waveform parameters
        self.samples_per_pixel = 100  # How many audio samples per pixel
        self.history_width = width  # Full width - no margins
        self.scroll_speed = 2  # Pixels per frame to scroll left
        
    def analyze_audio_frame(self, audio, sr, start_time, window_duration=3.0):
        """Analyze audio for waveform - get actual amplitude data."""
        start_sample = int(start_time * sr)
        window_samples = int(window_duration * sr)
        end_sample = min(start_sample + window_samples, len(audio))
        
        if start_sample >= len(audio):
            return np.zeros(self.history_width)
        
        # Extract audio window for scrolling display
        window_audio = audio[start_sample:end_sample]
        
        # Downsample to match pixel width for smooth scrolling
        if len(window_audio) == 0:
            return np.zeros(self.history_width)
        
        # Calculate samples per pixel for this window
        samples_per_pixel = max(1, len(window_audio) // self.history_width)
        
        # Downsample by taking RMS values in chunks for smooth representation
        downsampled = []
        for i in range(0, len(window_audio), samples_per_pixel):
            chunk = window_audio[i:i + samples_per_pixel]
            if len(chunk) > 0:
                # Use RMS for better volume representation
                rms_value = np.sqrt(np.mean(chunk**2))
                # Keep some of the original waveform character
                avg_value = np.mean(chunk)
                # Combine RMS and average for sharp, spiky brainwave pattern
                combined = avg_value * (0.5 + 1.8 * rms_value)  # Higher multiplier for dramatic spikes
                # Add high-frequency variation for spiky appearance
                spike_variation = np.random.normal(0, 0.08) * rms_value  # Much more variation for spikes
                combined += spike_variation
                downsampled.append(combined)
        
        # Pad or trim to exact width
        if len(downsampled) < self.history_width:
            downsampled.extend([0] * (self.history_width - len(downsampled)))
        else:
            downsampled = downsampled[:self.history_width]
        
        return np.array(downsampled)
    
    def create_waveform_frame(self, waveform_data, time_position, total_duration):
        """Create a single frame of the waveform visualization."""
        # Create transparent background so logo can show through
        frame = np.zeros((self.height, self.width, 4), dtype=np.uint8)  # RGBA with transparent background
        
        # Draw continuous center line (baseline) across entire width
        center_line_color = [*[int(c * 0.3) for c in self.colors['waveform_dark']], 128]  # Semi-transparent
        cv2.line(frame, (0, self.waveform_center_y), (self.width, self.waveform_center_y), 
                center_line_color, 1)
        
        # Convert waveform data to pixel coordinates
        if len(waveform_data) > 1:
            # Draw continuous waveform across entire width - logo will be overlaid on top
            points = []
            for i, amplitude in enumerate(waveform_data):
                x = i
                if x >= self.width:  # Don't go beyond screen width
                    break
                
                # Scale amplitude to pixel coordinates
                y_offset = amplitude * self.waveform_amplitude
                y = self.waveform_center_y - int(y_offset)
                y = max(50, min(self.height - 50, y))
                
                points.append((x, y))
            
            # Draw continuous waveform
            if len(points) > 1:
                self.draw_smooth_waveform(frame, points, waveform_data[:len(points)])
        
        return frame
    
    def draw_smooth_waveform(self, frame, points, amplitude_data):
        """Draw a smooth, gradient waveform line."""
        if len(points) < 2:
            return
        
        # Create thin, bright, spiky brainwave with intense glow
        for pass_idx in range(6):  # Multiple passes for maximum shine
            # Thin lines with decreasing thickness for glow effect
            thickness = max(1, self.waveform_line_thickness + (5 - pass_idx))
            
            # Choose intensely bright yellow/golden colors
            if pass_idx == 0:  # Outer glow - brightest white-yellow
                color = [255, 255, 220]
            elif pass_idx == 1:  # Second layer - very bright yellow
                color = [255, 255, 190]
            elif pass_idx == 2:  # Third layer - bright golden yellow
                color = self.colors['waveform_light']
            elif pass_idx == 3:  # Fourth layer - golden
                color = self.colors['waveform_mid']
            elif pass_idx == 4:  # Inner layer - deep golden
                color = self.colors['accent']
            else:  # Core - intense golden
                color = self.colors['waveform_dark']
            
            # Draw line segments with full opacity for bright, shiny appearance
            for i in range(len(points) - 1):
                # Enhance brightness on high amplitudes for dramatic spikes
                amp_intensity = min(1.0, abs(amplitude_data[i] if i < len(amplitude_data) else 0) * 20)  # Very high multiplier for spikes
                brightness_boost = 0.7 + 0.3 * amp_intensity  # Brighter base with spike enhancement
                adjusted_color = [int(c * brightness_boost) for c in color] + [255]  # Full opacity
                
                cv2.line(frame, points[i], points[i + 1], adjusted_color, thickness)
        
        # Intense glow effect on spikes for brainwave appearance
        for i, (point, amp) in enumerate(zip(points, amplitude_data)):
            if abs(amp) > 0.04:  # Lower threshold to highlight more spikes
                glow_intensity = min(255, int(255 * abs(amp) * 1.2))  # Very intense glow
                # Bright yellow-white glow
                glow_color = [255, 255, min(255, 150 + glow_intensity)] + [255]  # Full opacity
                cv2.circle(frame, point, 8, glow_color, -1)  # Larger glow for dramatic effect
    
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
                
                yield frame
        
        return frame_generator()
