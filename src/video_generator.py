import os
import numpy as np
try:
    # Try moviepy 2.x imports
    from moviepy import VideoClip, AudioFileClip, CompositeVideoClip
except ImportError:
    # Fall back to moviepy 1.x imports
    from moviepy.editor import VideoClip, AudioFileClip, CompositeVideoClip
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import cv2
from waveform_visualizer import WaveformVisualizer


class VideoGenerator:
    """Generates the final MP4 video with logo, waveform, and text overlays."""
    
    def __init__(self, width=1920, height=1080, fps=30):
        self.width = width
        self.height = height
        self.fps = fps
        self.podcast_name = "Codex Mentis: Science and technology to study cognition"
        
        # Colors matching the waveform visualizer
        self.colors = {
            'background': (20, 25, 35),
            'waveform_light': (245, 230, 200),
            'waveform_mid': (220, 190, 150),
            'waveform_dark': (180, 140, 100),
            'text': (240, 235, 220),
            'accent': (255, 200, 120),
            'text_bg': (0, 0, 0, 120),  # Semi-transparent background
            'podcast': (180, 190, 200)  # Cool silver-grey for podcast name
        }
    
    def load_and_prepare_logo(self, logo_path):
        """Load and prepare the podcast logo for animation."""
        try:
            if not os.path.exists(logo_path):
                print(f"⚠ Warning: Logo file not found at {logo_path}")
                print("Please place your podcast_logo.jpeg in the assets/ folder")
                return None
            
            # Load logo
            logo = Image.open(logo_path)
            
            # Convert to RGBA if not already
            if logo.mode != 'RGBA':
                logo = logo.convert('RGBA')
            
            # Resize logo to fit nicely (max 400x400 pixels)
            logo.thumbnail((400, 400), Image.Resampling.LANCZOS)
            
            # Create a circular mask for the logo
            mask = Image.new('L', logo.size, 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0) + logo.size, fill=255)
            
            # Apply circular mask
            logo.putalpha(mask)
            
            # Add subtle glow effect
            glow = logo.copy()
            glow = glow.filter(ImageFilter.GaussianBlur(radius=10))
            
            # Combine logo with glow
            final_logo = Image.new('RGBA', (logo.width + 40, logo.height + 40), (0, 0, 0, 0))
            final_logo.paste(glow, (20, 20), glow)
            final_logo.paste(logo, (20, 20), logo)
            
            print(f"✓ Logo loaded and prepared: {logo.size}")
            return final_logo
            
        except Exception as e:
            print(f"✗ Error loading logo: {e}")
            return None
    
    def create_text_overlay(self, episode_title):
        """Create elegant text overlay with episode title at top and podcast name at bottom, with smaller side margins."""
        # Margins - smaller side margins for larger episode title
        margin_x = int(self.width * 0.05)  # Reduced from 10% to 5%
        margin_y = int(self.height * 0.10)
        usable_width = self.width - 2 * margin_x
        usable_height = self.height - 2 * margin_y
        
        # Font sizes - larger starting size for episode title
        title_font_size = int(0.09 * self.height)  # Increased from 7% to 9% of height
        podcast_font_size = int(0.045 * self.height)  # Starting size for podcast name
        
        # Load fonts first to measure text
        try:
            episode_font = ImageFont.truetype("times.ttf", title_font_size)
        except:
            try:
                episode_font = ImageFont.truetype("Georgia.ttf", title_font_size)
            except:
                episode_font = ImageFont.load_default()
        
        # Create temporary draw object to measure text
        temp_img = Image.new('RGBA', (1, 1), (0, 0, 0, 0))
        temp_draw = ImageDraw.Draw(temp_img)
        
        # Remove 'Episode: ' prefix if present for measurement
        clean_title = episode_title
        if episode_title.lower().startswith('episode: '):
            clean_title = episode_title[9:]
        
        # Adaptive font sizing for episode title
        episode_bbox = temp_draw.textbbox((0, 0), clean_title, font=episode_font)
        episode_width = episode_bbox[2] - episode_bbox[0]
        
        # If title is too wide, reduce font size
        while episode_width > usable_width and title_font_size > 20:
            title_font_size = int(title_font_size * 0.9)
            try:
                episode_font = ImageFont.truetype("times.ttf", title_font_size)
            except:
                try:
                    episode_font = ImageFont.truetype("Georgia.ttf", title_font_size)
                except:
                    episode_font = ImageFont.load_default()
            episode_bbox = temp_draw.textbbox((0, 0), clean_title, font=episode_font)
            episode_width = episode_bbox[2] - episode_bbox[0]
        
        # Load podcast font with adaptive sizing
        try:
            podcast_font = ImageFont.truetype("arial.ttf", podcast_font_size)  # Sans-serif for distinction
        except:
            try:
                podcast_font = ImageFont.truetype("verdana.ttf", podcast_font_size)  # Alternative sans-serif
            except:
                podcast_font = ImageFont.load_default()
        
        # Adaptive font sizing for podcast name
        podcast_bbox = temp_draw.textbbox((0, 0), self.podcast_name, font=podcast_font)
        podcast_width = podcast_bbox[2] - podcast_bbox[0]
        
        # If podcast name is too wide, reduce font size
        while podcast_width > usable_width and podcast_font_size > 15:
            podcast_font_size = int(podcast_font_size * 0.9)
            try:
                podcast_font = ImageFont.truetype("arial.ttf", podcast_font_size)
            except:
                try:
                    podcast_font = ImageFont.truetype("verdana.ttf", podcast_font_size)
                except:
                    podcast_font = ImageFont.load_default()
            podcast_bbox = temp_draw.textbbox((0, 0), self.podcast_name, font=podcast_font)
            podcast_width = podcast_bbox[2] - podcast_bbox[0]
        
        # Create transparent image for text overlays
        text_img = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(text_img)
        
        # --- Episode Title ---
        # Use the cleaned title (already handled above)
        episode_title = clean_title
        # Calculate final text size with adjusted font
        episode_bbox = draw.textbbox((0, 0), episode_title, font=episode_font)
        episode_width = episode_bbox[2] - episode_bbox[0]
        episode_height = episode_bbox[3] - episode_bbox[1]
        # Centered horizontally within margins, positioned lower
        episode_x = margin_x + (usable_width - episode_width) // 2
        episode_y = margin_y + int(self.height * 0.06)  # Move down by 6% of screen height (increased from 4%)
        # Draw shadow
        shadow_offset = 3
        shadow_color = (0, 0, 0, 120)
        draw.text((episode_x + shadow_offset, episode_y + shadow_offset), episode_title, font=episode_font, fill=shadow_color)
        # Draw title
        draw.text((episode_x, episode_y), episode_title, font=episode_font, fill=self.colors['accent'])
        
        # --- Podcast Name ---
        # Calculate final text size with adjusted font
        podcast_bbox = draw.textbbox((0, 0), self.podcast_name, font=podcast_font)
        podcast_width = podcast_bbox[2] - podcast_bbox[0]
        podcast_height = podcast_bbox[3] - podcast_bbox[1]
        podcast_x = margin_x + (usable_width - podcast_width) // 2
        podcast_y = self.height - margin_y - podcast_height - int(self.height * 0.03)  # Move up by 3% of screen height
        # Draw shadow
        draw.text((podcast_x + shadow_offset, podcast_y + shadow_offset), self.podcast_name, font=podcast_font, fill=shadow_color)
        # Draw podcast name in distinct color
        draw.text((podcast_x, podcast_y), self.podcast_name, font=podcast_font, fill=self.colors['podcast'])
        
        return text_img
    
    def animate_logo_scale(self, time_position, duration, base_scale=1.0, amplitude=0.05, frequency=0.5):
        """Create breathing animation for the logo."""
        # Simple sine wave animation
        animation_progress = (time_position / duration) * 2 * np.pi * frequency
        scale_factor = base_scale + amplitude * np.sin(animation_progress)
        return scale_factor
    
    def composite_frame(self, waveform_frame, logo, text_overlay, time_position, duration):
        """Composite all elements into final frame with waveform over logo."""
        # Start with the background color
        frame = Image.new('RGB', (self.width, self.height), (20, 25, 35))  # Background color
        frame = frame.convert('RGBA')
        
        # Add logo first (underneath everything)
        if logo is not None:
            # Calculate logo position - integrated with waveform
            logo_scale = self.animate_logo_scale(time_position, duration)
            
            # Resize logo based on animation
            animated_size = (int(logo.width * logo_scale), int(logo.height * logo_scale))
            animated_logo = logo.resize(animated_size, Image.Resampling.LANCZOS)
            
            # Position logo on left side, integrated with waveform area
            logo_x = 50  # Left margin
            logo_y = self.height // 2 - animated_logo.height // 2  # Vertically centered with waveform
            
            # Ensure logo doesn't go off screen
            logo_y = max(50, min(self.height - animated_logo.height - 50, logo_y))
            
            # Composite logo onto background
            frame.paste(animated_logo, (logo_x, logo_y), animated_logo)
        
        # Convert waveform frame to RGBA and make it semi-transparent for overlay effect
        waveform_rgba = Image.fromarray(waveform_frame).convert('RGBA')
        
        # Create a semi-transparent version of the waveform
        waveform_overlay = Image.new('RGBA', waveform_rgba.size, (0, 0, 0, 0))
        waveform_overlay.paste(waveform_rgba, (0, 0))
        
        # Apply the waveform over the frame with logo
        frame = Image.alpha_composite(frame, waveform_overlay)
        
        # Add text overlay (positioned at top as specified)
        frame.paste(text_overlay, (0, 0), text_overlay)
        
        # Convert back to RGB array
        frame_rgb = frame.convert('RGB')
        return np.array(frame_rgb)
    
    def apply_video_fade(self, frames, fade_duration_seconds=2.0):
        """Apply fade-in and fade-out effects to video frames."""
        fade_frames = int(fade_duration_seconds * self.fps)
        total_frames = len(frames)
        
        print(f"🎬 Applying fade effects ({fade_duration_seconds}s)...")
        
        for i in range(total_frames):
            alpha = 1.0
            
            # Fade in
            if i < fade_frames:
                alpha = i / fade_frames
            # Fade out
            elif i > total_frames - fade_frames:
                alpha = (total_frames - i) / fade_frames
            
            if alpha < 1.0:
                # Apply fade by blending with black
                frames[i] = (frames[i] * alpha).astype(np.uint8)
        
        print("✓ Video fade effects applied!")
        return frames
    
    def create_video(self, audio_path, waveform_frame_generator, episode_title, output_path, logo_path=None):
        """Create the final MP4 video using frame generator for memory efficiency."""
        print(f"\n🎬 Creating video: {os.path.basename(output_path)}")
        print("-" * 50)
        
        try:
            # Load and prepare logo
            logo = None
            if logo_path and os.path.exists(logo_path):
                logo = self.load_and_prepare_logo(logo_path)
            
            # Create text overlay
            text_overlay = self.create_text_overlay(episode_title)
            print("✓ Text overlay created")
            
            # Load audio to get duration
            audio_clip = AudioFileClip(audio_path)
            duration = audio_clip.duration
            
            print(f"🎨 Creating video frames on-demand (Duration: {duration:.1f}s)...")
            
            # Create a generator for final composited frames
            def final_frame_generator():
                frame_count = 0
                total_frames = int(duration * self.fps)
                last_percent = -1
                
                for waveform_frame in waveform_frame_generator:
                    time_position = frame_count / self.fps
                    
                    # Progress reporting (every 5%)
                    percent = int((frame_count / total_frames) * 100)
                    if percent >= last_percent + 5:
                        print(f"  Progress: {percent}% ({frame_count}/{total_frames} frames, {time_position:.1f}/{duration:.1f}s)")
                        last_percent = percent
                    
                    # Composite this frame
                    final_frame = self.composite_frame(
                        waveform_frame, logo, text_overlay, time_position, duration
                    )
                    
                    # Apply fade if needed
                    fade_frames = int(2.0 * self.fps)  # 2-second fade
                    
                    alpha = 1.0
                    if frame_count < fade_frames:
                        alpha = frame_count / fade_frames
                    elif frame_count > total_frames - fade_frames:
                        alpha = (total_frames - frame_count) / fade_frames
                    
                    if alpha < 1.0:
                        final_frame = (final_frame * alpha).astype(np.uint8)
                    
                    frame_count += 1
                    yield final_frame
            
            # Create video clip using frame generator
            def make_frame(t):
                frame_idx = int(t * self.fps)
                # We need to create a list to store frames as we generate them
                # This is still memory efficient as we only keep what we need
                if not hasattr(make_frame, 'frame_cache'):
                    make_frame.frame_cache = {}
                    make_frame.generator = final_frame_generator()
                    make_frame.last_idx = -1
                
                # Generate frames up to the requested index
                while make_frame.last_idx < frame_idx:
                    try:
                        next_frame = next(make_frame.generator)
                        make_frame.last_idx += 1
                        make_frame.frame_cache[make_frame.last_idx] = next_frame
                        
                        # Keep only recent frames to save memory
                        if len(make_frame.frame_cache) > 100:
                            oldest_key = min(make_frame.frame_cache.keys())
                            del make_frame.frame_cache[oldest_key]
                            
                    except StopIteration:
                        break
                
                # Return the requested frame
                if frame_idx in make_frame.frame_cache:
                    return make_frame.frame_cache[frame_idx]
                else:
                    # Return the last available frame if requested frame is beyond end
                    last_available = max(make_frame.frame_cache.keys()) if make_frame.frame_cache else 0
                    return make_frame.frame_cache.get(last_available, np.zeros((self.height, self.width, 3), dtype=np.uint8))
            
            video_clip = VideoClip(make_frame, duration=duration)
            
            # Combine video and audio (compatible with moviepy 1.x and 2.x)
            if hasattr(video_clip, 'set_audio'):
                # moviepy 1.x
                final_clip = video_clip.set_audio(audio_clip)
            else:
                # moviepy 2.x
                video_clip.audio = audio_clip
                final_clip = video_clip
            
            # Write final video with optimized settings
            print(f"💾 Saving video to: {output_path}")
            
            # Build write_videofile parameters (compatible with moviepy 1.x and 2.x)
            write_params = {
                'fps': self.fps,
                'codec': 'libx264',
                'audio_codec': 'aac',
                'temp_audiofile': 'temp-audio.m4a',
                'remove_temp': True,
                'preset': 'medium',  # Balance between speed and file size
                'ffmpeg_params': ['-crf', '23']  # Good quality with reasonable file size
            }
            
            # Add verbose and logger only for moviepy 1.x
            if hasattr(video_clip, 'set_audio'):
                write_params['verbose'] = False
                write_params['logger'] = None
            
            final_clip.write_videofile(output_path, **write_params)
            
            # Clean up
            final_clip.close()
            audio_clip.close()
            video_clip.close()
            
            print("✅ Video creation complete!")
            return True
            
        except Exception as e:
            print(f"✗ Error creating video: {e}")
            return False
