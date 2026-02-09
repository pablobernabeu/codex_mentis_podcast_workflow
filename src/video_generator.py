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

print(f"[DIAGNOSTIC] video_generator.py loaded from: {__file__}")


class VideoGenerator:
    """Generates the final MP4 video with logo, waveform, and text overlays."""
    
    def __init__(self, width=1920, height=1080, fps=30):
        self.width = width
        self.height = height
        self.fps = fps
        self.podcast_name = "Codex Mentis: Science and technology to study cognition"
        
        # Timing for thematic image display pattern (in seconds)
        self.initial_composite_duration = 60  # Show composite for 1 minute at start
        self.fullscreen_image_duration = 300  # Show full-screen image for 5 minutes (300s)
        self.composite_interval_duration = 30  # Show composite for 30s between full-screen segments
        self.zoom_transition_duration = 1.5  # Duration of zoom transition in seconds
        
        # Colors matching the waveform visualizer
        self.colors = {
            'background': (20, 25, 35),
            'waveform_light': (245, 230, 200),
            'waveform_mid': (220, 190, 150),
            'waveform_dark': (180, 140, 100),
            'text': (240, 235, 220),
            'accent': (255, 200, 120),
            'text_bg': (0, 0, 0, 120),
            'podcast': (180, 190, 200)
        }
    
    def get_view_state(self, time_position, duration):
        """Determine the current view state based on time position.
        
        Returns:
            tuple: (state, transition_progress)
            - state: 'composite', 'fullscreen', 'zoom_in', or 'zoom_out'
            - transition_progress: 0.0-1.0 for transitions, None otherwise
        """
        # Pattern: 1min composite -> 5min fullscreen -> 30s composite -> 5min fullscreen -> ...
        # With zoom transitions between states
        # Always show composite during the last minute
        
        final_composite_duration = 60.0  # Last 1 minute always composite
        
        # Check if we're in the final composite period
        time_remaining = duration - time_position
        if time_remaining <= final_composite_duration:
            # Last minute - always show composite
            return ('composite', None)
        
        cycle_duration = self.fullscreen_image_duration + self.composite_interval_duration
        
        if time_position < self.initial_composite_duration:
            # Initial composite period
            return ('composite', None)
        
        # Check if we're in the zoom-in transition after initial composite
        if time_position < self.initial_composite_duration + self.zoom_transition_duration:
            progress = (time_position - self.initial_composite_duration) / self.zoom_transition_duration
            return ('zoom_in', progress)
        
        # Time after initial composite and first zoom-in
        time_after_initial = time_position - self.initial_composite_duration - self.zoom_transition_duration
        
        # Calculate which cycle we're in
        cycle_index = int(time_after_initial / cycle_duration)
        time_in_cycle = time_after_initial % cycle_duration
        
        # Within each cycle: fullscreen (5min) -> zoom_out -> composite (30s) -> zoom_in
        if time_in_cycle < self.fullscreen_image_duration - self.zoom_transition_duration:
            # Full-screen image period (before zoom-out starts)
            return ('fullscreen', None)
        elif time_in_cycle < self.fullscreen_image_duration:
            # Zoom-out transition
            progress = (time_in_cycle - (self.fullscreen_image_duration - self.zoom_transition_duration)) / self.zoom_transition_duration
            return ('zoom_out', progress)
        elif time_in_cycle < self.fullscreen_image_duration + self.composite_interval_duration - self.zoom_transition_duration:
            # Composite period
            return ('composite', None)
        else:
            # Zoom-in transition
            progress = (time_in_cycle - (self.fullscreen_image_duration + self.composite_interval_duration - self.zoom_transition_duration)) / self.zoom_transition_duration
            if time_remaining <= final_composite_duration + self.zoom_transition_duration:
                return ('composite', None)
            return ('zoom_in', progress)
    
    def load_and_prepare_logo(self, logo_path):
        """Load and prepare the podcast logo for animation."""
        try:
            if not os.path.exists(logo_path):
                print(f"⚠ Warning: Logo file not found at {logo_path}")
                print("Please place your podcast_logo.jpeg in the assets/ folder")
                return None
            
            # Load logo
            logo = Image.open(logo_path)
            
            if logo.mode != 'RGBA':
                logo = logo.convert('RGBA')
            
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
    
    def load_and_prepare_episode_image(self, episode_image_path):
        """Load and prepare an optional episode-specific image with golden yellow gradient frame.
        Dynamically sizes to fit available space while respecting margins."""
        try:
            if not episode_image_path or not os.path.exists(episode_image_path):
                return None
            
            # Load image
            img = Image.open(episode_image_path)
            
            # Convert to RGBA if not already
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # Calculate available space - tight margins to stay close to titles
            # Top margin: minimal space after episode title
            top_margin = int(self.height * 0.001)  # Nearly zero - 0.1%
            # Bottom margin: minimal space before podcast name
            bottom_margin = int(self.height * 0.001)  # Nearly zero - 0.1%
            # Left margin: account for logo
            left_margin = 520
            # Right margin: minimal spacing from edge
            right_margin = 50
            # Additional vertical margins for spacing
            vertical_spacing = 2
            
            # Calculate maximum available dimensions
            max_height = self.height - top_margin - bottom_margin - vertical_spacing
            max_width = self.width - left_margin - right_margin
            
            # Get original aspect ratio
            aspect_ratio = img.width / img.height
            
            # Calculate target dimensions to fit within available space
            # Try fitting by height first
            target_height = max_height
            target_width = int(target_height * aspect_ratio)
            
            # If too wide, fit by width instead
            if target_width > max_width:
                target_width = max_width
                target_height = int(target_width / aspect_ratio)
            
            # Resize image maintaining aspect ratio
            img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
            
            frame_width = 12
            frame_size = (target_width + frame_width * 2, target_height + frame_width * 2)
            frame = Image.new('RGBA', frame_size, (0, 0, 0, 0))
            frame_draw = ImageDraw.Draw(frame)
            
            orange_colors = [
                (255, 220, 90),   # Darker yellow
                (255, 230, 100),  # Medium yellow
                (255, 235, 105),  # Light yellow
                (255, 240, 110),  # Bright yellow
                (255, 245, 115)
            ]
            
            num_layers = len(orange_colors)
            layer_thickness = frame_width / num_layers
            
            for i, color in enumerate(orange_colors):
                inset = int(i * layer_thickness)
                frame_draw.rectangle(
                    [inset, inset, frame_size[0] - inset - 1, frame_size[1] - inset - 1],
                    fill=color
                )
            
            # Add outer glow effect
            glow = Image.new('RGBA', (frame_size[0] + 40, frame_size[1] + 40), (0, 0, 0, 0))
            glow_draw = ImageDraw.Draw(glow)
            glow_draw.rectangle(
                [10, 10, frame_size[0] + 30, frame_size[1] + 30],
                fill=(255, 230, 100, 60)  # Semi-transparent bright yellow glow
            )
            glow = glow.filter(ImageFilter.GaussianBlur(radius=15))
            
            # Composite everything together
            final_size = (frame_size[0] + 40, frame_size[1] + 40)
            final_img = Image.new('RGBA', final_size, (0, 0, 0, 0))
            
            # Add glow
            final_img.paste(glow, (0, 0), glow)
            
            # Add frame
            final_img.paste(frame, (20, 20), frame)
            
            # Add image in center
            img_offset = 20 + frame_width
            final_img.paste(img, (img_offset, img_offset), img)
            
            print(f"✓ Episode image loaded and prepared: {img.size} with golden yellow gradient frame")
            print(f"  Available space: {max_width}x{max_height}, Final size: {final_size}")
            return final_img
        except Exception as e:
            print(f"✗ Error loading episode image: {e}")
            return None
    
    def add_animated_light_to_frame(self, image, time_position, duration, episode_x, episode_y):
        """Add a subtle shiny light that travels around the frame in circles.
        
        Args:
            image: PIL Image with the framed thematic image
            time_position: Current time in seconds
            duration: Total duration in seconds
            episode_x: X position of the image on the canvas
            episode_y: Y position of the image on the canvas
        
        Returns:
            PIL Image with animated light overlay
        """
        if image is None:
            return None
        
        light_overlay = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(light_overlay)
        
        cycle_duration = 24.0
        progress = (time_position % cycle_duration) / cycle_duration
        
        glow_offset = 20
        frame_width = 12
        frame_center_offset = glow_offset + frame_width // 2
        
        # Get the total framed image dimensions
        img_width = image.width
        img_height = image.height
        
        frame_rect_width = img_width - 2 * frame_center_offset
        frame_rect_height = img_height - 2 * frame_center_offset
        
        perimeter = 2 * (frame_rect_width + frame_rect_height)
        starting_offset = frame_rect_width + frame_rect_height / 2
        
        current_pos = (progress * perimeter + starting_offset) % perimeter
        
        if current_pos < frame_rect_width:
            light_x = episode_x + frame_center_offset + current_pos
            light_y = episode_y + frame_center_offset
        elif current_pos < frame_rect_width + frame_rect_height:
            light_x = episode_x + img_width - frame_center_offset
            light_y = episode_y + frame_center_offset + (current_pos - frame_rect_width)
        elif current_pos < 2 * frame_rect_width + frame_rect_height:
            light_x = episode_x + img_width - frame_center_offset - (current_pos - frame_rect_width - frame_rect_height)
            light_y = episode_y + img_height - frame_center_offset
        else:
            light_x = episode_x + frame_center_offset
            light_y = episode_y + img_height - frame_center_offset - (current_pos - 2 * frame_rect_width - frame_rect_height)
        
        light_color = (255, 255, 255)
        golden_color = (255, 235, 110)
        draw.ellipse(
            [light_x - 20, light_y - 20, light_x + 20, light_y + 20],
            fill=golden_color + (20,)  # Outer glow
        )
        draw.ellipse(
            [light_x - 14, light_y - 14, light_x + 14, light_y + 14],
            fill=golden_color + (40,)
        )
        draw.ellipse(
            [light_x - 9, light_y - 9, light_x + 9, light_y + 9],
            fill=(255, 255, 240, 70)
        )
        draw.ellipse(
            [light_x - 5, light_y - 5, light_x + 5, light_y + 5],
            fill=light_color + (100,)
        )
        draw.ellipse(
            [light_x - 2, light_y - 2, light_x + 2, light_y + 2],
            fill=light_color + (140,)  # Core
        )
        
        # Apply Gaussian blur for smooth, natural glow
        light_overlay = light_overlay.filter(ImageFilter.GaussianBlur(radius=6))
        
        return light_overlay
    
    def load_and_prepare_fullscreen_image(self, episode_image_path):
        """Load and prepare a full-screen version of the episode image for zoom transitions.
        The image fills the screen while maintaining aspect ratio, with dark background fill."""
        try:
            if not episode_image_path or not os.path.exists(episode_image_path):
                return None
            
            # Load image
            img = Image.open(episode_image_path)
            
            # Convert to RGBA if not already
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # Calculate dimensions to fill screen while maintaining aspect ratio
            aspect_ratio = img.width / img.height
            screen_aspect = self.width / self.height
            
            if aspect_ratio > screen_aspect:
                # Image is wider than screen - fit by width
                target_width = self.width
                target_height = int(target_width / aspect_ratio)
            else:
                # Image is taller than screen - fit by height
                target_height = self.height
                target_width = int(target_height * aspect_ratio)
            
            # Resize image maintaining aspect ratio
            img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
            
            # Create full-screen frame with background color
            fullscreen_img = Image.new('RGBA', (self.width, self.height), self.colors['background'])
            
            # Center the image on the screen
            x_offset = (self.width - target_width) // 2
            y_offset = (self.height - target_height) // 2
            
            fullscreen_img.paste(img, (x_offset, y_offset), img)
            
            print(f"✓ Full-screen episode image prepared: {target_width}x{target_height}")
            return fullscreen_img
        except Exception as e:
            print(f"✗ Error loading full-screen episode image: {e}")
            return None

    def create_text_overlay(self, episode_title, episode_image=None, time_position=0, duration=1, cached_fonts=None):
        """Create elegant text overlay with episode title at top and podcast name at bottom.
        Dynamically sizes fonts to maximize available space between screen edges and thematic image.
        
        Args:
            episode_title: Title text to display
            episode_image: Optional episode image for layout calculation
            time_position: Current time position in seconds for animations
            duration: Total video duration in seconds
            cached_fonts: Dict with pre-computed font info to skip binary search
        """
        
        # If fonts are already cached, skip the expensive binary search
        if cached_fonts is not None:
            episode_font = cached_fonts['episode_font']
            podcast_font = cached_fonts['podcast_font']
            episode_x = cached_fonts['episode_x']
            episode_y = cached_fonts['episode_y']
            podcast_x = cached_fonts['podcast_x']
            podcast_y = cached_fonts['podcast_y']
            clean_title = cached_fonts['clean_title']
            print(f"  ♻️ Using cached fonts")
        else:
            # First-time calculation - run binary search for optimal font sizes
            # Calculate available vertical space based on whether we have an episode image
            if episode_image is not None:
                # Image is vertically centered, so calculate space above and below it
                image_height = episode_image.height
                image_top_y = (self.height - image_height) // 2
                image_bottom_y = image_top_y + image_height
                
                # Available space for titles - account for the gap we'll add during positioning
                title_to_image_gap = int(self.height * 0.038)  # Gap between title and image
                available_top_space = image_top_y - title_to_image_gap
                available_bottom_space = self.height - image_bottom_y
            else:
                # No image - use percentage-based spacing
                available_top_space = int(self.height * 0.4)
                available_bottom_space = int(self.height * 0.4)
            
            # Horizontal margins
            margin_x = int(self.width * 0.005)  # 0.5% side margins
            usable_width = self.width - 2 * margin_x
            
            # Remove 'Episode: ' prefix if present
            clean_title = episode_title
            if episode_title.lower().startswith('episode: '):
                clean_title = episode_title[9:]
            
            # Create temporary draw object to measure text
            temp_img = Image.new('RGBA', (1, 1), (0, 0, 0, 0))
            temp_draw = ImageDraw.Draw(temp_img)
            
            # --- Dynamically size episode title to fill available top space ---
            # Use binary search to find the largest font that fits
            min_title_font_size = 40
            max_title_font_size = max(int(available_top_space * 2.5), 150)  # Moderate sizing
            title_font_size = max_title_font_size
            best_title_font_size = min_title_font_size
            episode_font = None
            font_loaded_successfully = False
            
            # Binary search for optimal font size
            while max_title_font_size - min_title_font_size > 2:
                title_font_size = (min_title_font_size + max_title_font_size) // 2
                
                # Try to load TrueType font (cross-platform compatible)
                test_font = None
                home_fonts = os.path.expanduser("~/.fonts/DejaVuSerif.ttf")  # User-installed fonts
                for font_name in [
                    home_fonts,  # User's font directory (HPC)
                    "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",  # Linux
                    "/usr/share/fonts/dejavu/DejaVuSerif.ttf",  # Alternative Linux path
                    "/System/Library/Fonts/Supplemental/Times New Roman.ttf",  # macOS
                    "C:\\Windows\\Fonts\\times.ttf",  # Windows
                    "times.ttf",  # Fallback
                    "Georgia.ttf",
                ]:
                    try:
                        test_font = ImageFont.truetype(font_name, title_font_size)
                        font_loaded_successfully = True
                        break
                    except Exception as e:
                        continue
                
                if test_font is None:
                    # Fonts not available - print warning but continue with PIL default rendering
                    if not font_loaded_successfully:
                        print(f"  ⚠️ No TrueType fonts available (tried Linux/Mac/Windows paths)")
                        print(f"     Using PIL ImageDraw text rendering with size {title_font_size}")
                        print(f"     ⚠️⚠️⚠️ WARNING: Default font ignores size - text will be tiny!")
                    # Use PIL text drawing instead - create a font-like object
                    test_font = ImageFont.load_default()
                    # For default font, we'll use text drawing directly later
                
                episode_bbox = temp_draw.textbbox((0, 0), clean_title, font=test_font)
                episode_width = episode_bbox[2] - episode_bbox[0]
                episode_height = episode_bbox[3] - episode_bbox[1]
                
                # Check if it fits within screen bounds
                if episode_width <= self.width * 0.95 and episode_height <= available_top_space * 0.9:
                    # Fits! Try larger
                    best_title_font_size = title_font_size
                    episode_font = test_font
                    min_title_font_size = title_font_size
                else:
                    # Too big, try smaller
                    max_title_font_size = title_font_size
            
            # Use the best size we found
            title_font_size = best_title_font_size
            if episode_font is None:
                font_loaded = False
                home_fonts = os.path.expanduser("~/.fonts/DejaVuSerif.ttf")
                for font_name in [
                    home_fonts,  # User's font directory (HPC)
                    "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",  # Linux
                    "/System/Library/Fonts/Supplemental/Times New Roman.ttf",  # macOS
                    "C:\\Windows\\Fonts\\times.ttf",  # Windows
                    "times.ttf",
                    "Georgia.ttf",
                ]:
                    try:
                        episode_font = ImageFont.truetype(font_name, title_font_size)
                        print(f"  ✓ Episode font loaded: {font_name} @ {title_font_size}px")
                        font_loaded = True
                        break
                    except:
                        continue
                if episode_font is None:
                    print(f"  ⚠️⚠️⚠️ CRITICAL: Using default font for episode title (TrueType fonts not found)")
                    print(f"  ⚠️⚠️⚠️ TEXT WILL BE TINY! Install DejaVu fonts or liberation-fonts on HPC")
                    episode_font = ImageFont.load_default()
            else:
                print(f"  ✓ Episode title font loaded successfully @ {title_font_size}px")
                # Verify it's not the default font
                if hasattr(episode_font, 'path'):
                    print(f"  ✓ Using TrueType font: {episode_font.path}")
            
            print(f"  📏 Episode title font size: {title_font_size}px (available space: {available_top_space}px)")
            
            min_podcast_font_size = 40
            max_podcast_font_size = max(int(available_bottom_space * 2.5), 150)
            podcast_font_size = max_podcast_font_size
            best_podcast_font_size = min_podcast_font_size
            podcast_font = None
            
            while max_podcast_font_size - min_podcast_font_size > 2:
                podcast_font_size = (min_podcast_font_size + max_podcast_font_size) // 2
                
                test_font = None
                home_fonts_sans = os.path.expanduser("~/.fonts/DejaVuSans.ttf")
                for font_name in [
                    home_fonts_sans,  # User's font directory (HPC)
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
                    "/usr/share/fonts/dejavu/DejaVuSans.ttf",  # Alternative Linux path
                    "/System/Library/Fonts/Supplemental/Arial.ttf",  # macOS
                    "C:\\Windows\\Fonts\\arial.ttf",  # Windows
                    "arial.ttf",  # Fallback
                    "verdana.ttf",
                ]:
                    try:
                        test_font = ImageFont.truetype(font_name, podcast_font_size)
                        break
                    except Exception as e:
                        continue
                
                if test_font is None:
                    test_font = ImageFont.load_default()
                
                podcast_bbox = temp_draw.textbbox((0, 0), self.podcast_name, font=test_font)
                podcast_width = podcast_bbox[2] - podcast_bbox[0]
                podcast_height = podcast_bbox[3] - podcast_bbox[1]
                
                if podcast_width <= self.width * 0.95 and podcast_height <= available_bottom_space * 0.9:
                    best_podcast_font_size = podcast_font_size
                    podcast_font = test_font
                    min_podcast_font_size = podcast_font_size
                else:
                    max_podcast_font_size = podcast_font_size
            
            podcast_font_size = best_podcast_font_size
            if podcast_font is None:
                font_loaded = False
                home_fonts_sans = os.path.expanduser("~/.fonts/DejaVuSans.ttf")
                for font_name in [
                    home_fonts_sans,  # User's font directory (HPC)
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
                    "/System/Library/Fonts/Supplemental/Arial.ttf",  # macOS
                    "C:\\Windows\\Fonts\\arial.ttf",  # Windows
                    "arial.ttf",
                    "verdana.ttf",
                ]:
                    try:
                        podcast_font = ImageFont.truetype(font_name, podcast_font_size)
                        print(f"  ✓ Podcast font loaded: {font_name} @ {podcast_font_size}px")
                        font_loaded = True
                        break
                    except:
                        continue
                if podcast_font is None:
                    print(f"  ⚠️⚠️⚠️ CRITICAL: Using default font for podcast name (TrueType fonts not found)")
                    print(f"  ⚠️⚠️⚠️ TEXT WILL BE TINY! Install DejaVu fonts or liberation-fonts on HPC")
                    podcast_font = ImageFont.load_default()
            else:
                print(f"  ✓ Podcast name font loaded successfully @ {podcast_font_size}px")
                # Verify it's not the default font
                if hasattr(podcast_font, 'path'):
                    print(f"  ✓ Using TrueType font: {podcast_font.path}")
            
            print(f"  📏 Podcast name font size: {podcast_font_size}px (available space: {available_bottom_space}px)")
            
            # Calculate positions for text
            # Horizontal margins
            episode_bbox = temp_draw.textbbox((0, 0), clean_title, font=episode_font)
            episode_width = episode_bbox[2] - episode_bbox[0]
            episode_height = episode_bbox[3] - episode_bbox[1]
            
            # Centered horizontally
            episode_x = margin_x + (usable_width - episode_width) // 2
            
            # Vertically centered in available top space if we have an image, otherwise use margin
            if episode_image is not None:
                # Position title just below the top of the screen with larger gap to image
                title_to_image_gap = int(self.height * 0.038)  # Gap between title and image
                # Calculate where the image starts
                image_top_y = (self.height - episode_image.height) // 2
                # Position title so its bottom edge is at the gap distance from the image top
                episode_y = image_top_y - title_to_image_gap - episode_height
            else:
                episode_y = int(self.height * 0.05)
            
            # Podcast name positions
            podcast_bbox = temp_draw.textbbox((0, 0), self.podcast_name, font=podcast_font)
            podcast_width = podcast_bbox[2] - podcast_bbox[0]
            podcast_height = podcast_bbox[3] - podcast_bbox[1]
            
            # Centered horizontally
            podcast_x = margin_x + (usable_width - podcast_width) // 2
            
            # Vertically centered in available bottom space if we have an image, otherwise use margin
            if episode_image is not None:
                image_bottom_y = (self.height + episode_image.height) // 2
                visual_image_bottom = image_bottom_y - 32
                midpoint = (visual_image_bottom + self.height) // 2
                podcast_y = midpoint - podcast_height // 2
            else:
                podcast_y = self.height - int(self.height * 0.05) - podcast_height
        
        text_img = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(text_img)
        
        if not hasattr(self, '_logged_text_size'):
            print(f"  📐 Text overlay size: {text_img.size} (should be {self.width}x{self.height})")
            self._logged_text_size = True
        
        glow_alpha = 100
        
        for offset in [5, 4, 3]:
            glow_layer_alpha = int(glow_alpha * (offset / 5.0) * 0.4)
            draw.text(
                (episode_x + offset, episode_y + offset),
                episode_title,
                font=episode_font,
                fill=(0, 0, 0, min(255, max(0, glow_layer_alpha)))
            )
        
        golden_yellow = (255, 235, 100)
        draw.text((episode_x, episode_y), clean_title, font=episode_font, fill=golden_yellow)
        

        for offset in [5, 4, 3]:
            glow_layer_alpha = int(glow_alpha * (offset / 5.0) * 0.4)
            draw.text(
                (podcast_x + offset, podcast_y + offset),
                self.podcast_name,
                font=podcast_font,
                fill=(0, 0, 0, min(255, max(0, glow_layer_alpha)))
            )
        
        # Draw podcast name in distinct color
        draw.text((podcast_x, podcast_y), self.podcast_name, font=podcast_font, fill=self.colors['podcast'])
        
        # Title fade-in effect (first 2 seconds) - only applied when time_position > 0
        fade_duration = 2.0
        if time_position < fade_duration and time_position > 0:
            alpha_multiplier = time_position / fade_duration  # 0.0 to 1.0
            # Apply fade by modulating alpha channel
            alpha_channel = text_img.split()[3]  # Get alpha channel
            alpha_array = np.array(alpha_channel)
            alpha_array = (alpha_array * alpha_multiplier).astype(np.uint8)
            text_img.putalpha(Image.fromarray(alpha_array))
        
        # Return overlay and font cache for future frames
        font_cache = {
            'episode_font': episode_font,
            'podcast_font': podcast_font,
            'episode_x': episode_x,
            'episode_y': episode_y,
            'podcast_x': podcast_x,
            'podcast_y': podcast_y,
            'clean_title': clean_title
        }
        
        return text_img, font_cache
    
    def animate_logo_scale(self, time_position, duration, base_scale=1.0, amplitude=0.05, frequency=0.5):
        """Create breathing animation for the logo."""
        # Simple sine wave animation
        animation_progress = (time_position / duration) * 2 * np.pi * frequency
        scale_factor = base_scale + amplitude * np.sin(animation_progress)
        return scale_factor
    
    def calculate_logo_shake(self, waveform_data, time_position):
        """Calculate logo shake offset based on audio peaks.
        
        Args:
            waveform_data: Current waveform amplitude data
            time_position: Current time position
        
        Returns:
            Tuple of (x_offset, y_offset) for logo shake
        """
        if waveform_data is None or len(waveform_data) == 0:
            return (0, 0)
        
        # Calculate average intensity from waveform
        avg_intensity = np.abs(waveform_data).mean()
        
        # Detect peaks (loud moments)
        peak_threshold = 0.15  # Adjust based on your audio levels
        is_peak = avg_intensity > peak_threshold
        
        if is_peak:
            # Generate small random shake
            shake_amount = min(avg_intensity * 10, 5)  # Max 5 pixels
            # Use time-based randomness for smooth shake
            seed_offset = int(time_position * 100)  # Change seed frequently but deterministically
            np.random.seed(seed_offset)
            x_offset = np.random.randint(-shake_amount, shake_amount + 1)
            y_offset = np.random.randint(-shake_amount, shake_amount + 1)
            return (int(x_offset), int(y_offset))
        else:
            return (0, 0)
    
    def composite_frame(self, waveform_frame, logo, text_overlay, time_position, duration, episode_image=None, fullscreen_image=None, waveform_data=None):
        """Composite all elements into final frame with dynamic view transitions.
        
        Handles transitions between composite view and full-screen thematic image based on time.
        
        Args:
            waveform_data: Raw waveform amplitude data for audio-reactive effects
        """
        # Determine current view state
        view_state, transition_progress = self.get_view_state(time_position, duration)
        
        # Create the composite frame (always needed for transitions)
        composite = self._create_composite_view(waveform_frame, logo, text_overlay, time_position, duration, episode_image, waveform_data)
        
        # If no fullscreen image is available, always return composite
        if fullscreen_image is None:
            return composite
        
        # Handle different view states
        if view_state == 'composite':
            return composite
        elif view_state == 'fullscreen':
            return self._create_fullscreen_view(fullscreen_image)
        elif view_state == 'zoom_in':
            # Transition from composite to fullscreen
            return self._create_zoom_transition(composite, fullscreen_image, transition_progress, zoom_in=True)
        elif view_state == 'zoom_out':
            # Transition from fullscreen to composite
            return self._create_zoom_transition(composite, fullscreen_image, transition_progress, zoom_in=False)
        
        return composite
    
    def _create_composite_view(self, waveform_frame, logo, text_overlay, time_position, duration, episode_image=None, waveform_data=None):
        """Create the standard composite view with logo, waveform, and episode image."""
        # Start with the background color
        frame = Image.new('RGB', (self.width, self.height), (20, 25, 35))  # Background color
        frame = frame.convert('RGBA')
        
        # Add logo first (underneath everything)
        if logo is not None:
            # Logo at original size (no animation for performance)
            animated_logo = logo
            
            # Position logo on left side, integrated with waveform area
            base_logo_x = 30  # Left margin (moved further left)
            base_logo_y = self.height // 2 - animated_logo.height // 2  # Vertically centered with waveform
            
            # Apply shake effect on audio peaks
            shake_x, shake_y = self.calculate_logo_shake(waveform_data, time_position)
            logo_x = base_logo_x + shake_x
            logo_y = base_logo_y + shake_y
            
            # Ensure logo doesn't go off screen
            logo_y = max(50, min(self.height - animated_logo.height - 50, logo_y))
            logo_x = max(10, min(self.width - animated_logo.width - 10, logo_x))
            
            # Composite logo onto background
            frame.paste(animated_logo, (logo_x, logo_y), animated_logo)
        
        # Only apply waveform overlay if it's not just a plain background
        # Check if waveform has visual content (not just background color)
        waveform_rgba = Image.fromarray(waveform_frame).convert('RGBA')
        waveform_np = np.array(waveform_rgba)
        background_color = np.array([20, 25, 35, 255])
        
        # Check if waveform has any pixels different from background
        has_waveform_content = not np.all(waveform_np[:, :, :3] == background_color[:3])
        
        if has_waveform_content:
            # Create a semi-transparent version of the waveform
            waveform_overlay = Image.new('RGBA', waveform_rgba.size, (0, 0, 0, 0))
            waveform_overlay.paste(waveform_rgba, (0, 0))
            # Apply the waveform over the frame with logo
            frame = Image.alpha_composite(frame, waveform_overlay)
        
        # Add episode-specific image on top of waveform (if provided)
        if episode_image is not None:
            # Calculate available horizontal space (accounting for logo on left)
            logo_space = 520  # Left space occupied by logo
            available_width = self.width - logo_space
            # Center in the available space to the right of logo, with slight right margin
            right_margin_adjustment = int(self.width * 0.02)  # 2% right margin
            episode_x = logo_space + (available_width - episode_image.width) // 2 - right_margin_adjustment
            # Vertically centered
            episode_y = (self.height - episode_image.height) // 2
            
            # Composite episode image on top of waveform
            frame.paste(episode_image, (episode_x, episode_y), episode_image)
            
            # Add animated light effect traveling around the frame
            light_overlay = self.add_animated_light_to_frame(episode_image, time_position, duration, episode_x, episode_y)
            if light_overlay is not None:
                frame = Image.alpha_composite(frame, light_overlay)
        
        # Add text overlay (positioned at top as specified)
        frame.paste(text_overlay, (0, 0), text_overlay)
        
        # Convert back to RGB array
        frame_rgb = frame.convert('RGB')
        return np.array(frame_rgb)
    
    def _create_fullscreen_view(self, fullscreen_image):
        """Create the full-screen thematic image view."""
        if fullscreen_image is None:
            # Fallback to solid background
            frame = Image.new('RGB', (self.width, self.height), self.colors['background'])
            return np.array(frame)
        
        # Convert fullscreen image to RGB array
        frame_rgb = fullscreen_image.convert('RGB')
        return np.array(frame_rgb)
    
    def _create_zoom_transition(self, composite_frame, fullscreen_image, progress, zoom_in=True):
        """Create a smooth zoom transition between composite and fullscreen views.
        
        Args:
            composite_frame: numpy array of the composite view
            fullscreen_image: PIL Image of the fullscreen view
            progress: float 0.0-1.0 indicating transition progress
            zoom_in: if True, zooming from composite to fullscreen; if False, zooming out
        """
        # Use easing function for smoother transition
        # Ease in-out cubic: smoother acceleration and deceleration
        if progress < 0.5:
            eased_progress = 4 * progress * progress * progress
        else:
            eased_progress = 1 - pow(-2 * progress + 2, 3) / 2
        
        if not zoom_in:
            # Reverse the progress for zoom-out
            eased_progress = 1 - eased_progress
        
        # Convert frames to PIL Images for blending
        composite_img = Image.fromarray(composite_frame).convert('RGBA')
        fullscreen_img = fullscreen_image.convert('RGBA') if fullscreen_image else composite_img
        
        # Calculate zoom scale (1.0 = normal, up to 1.3 for zoom effect)
        # During zoom-in: composite zooms in and fades out, fullscreen fades in
        # During zoom-out: fullscreen zooms out and fades out, composite fades in
        
        zoom_scale = 1.0 + (0.15 * eased_progress)  # Subtle zoom from 1.0 to 1.15
        
        # Scale the composite image (zoom effect)
        scaled_width = int(self.width * zoom_scale)
        scaled_height = int(self.height * zoom_scale)
        
        # Zoom the composite view
        composite_zoomed = composite_img.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)
        
        # Crop to center
        left = (scaled_width - self.width) // 2
        top = (scaled_height - self.height) // 2
        composite_cropped = composite_zoomed.crop((left, top, left + self.width, top + self.height))
        
        # Blend composite and fullscreen based on progress
        # Alpha blend: composite fades out, fullscreen fades in
        alpha = eased_progress
        
        # Create blended result
        result = Image.blend(composite_cropped.convert('RGB'), fullscreen_img.convert('RGB'), alpha)
        
        return np.array(result)
    
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
    
    def create_video(self, audio_path, waveform_frame_generator, episode_title, output_path, logo_path=None, episode_image_path=None):
        """Create the final MP4 video using frame generator for memory efficiency."""
        print(f"\n🎬 Creating video: {os.path.basename(output_path)}")
        print("-" * 50)
        
        try:
            # Load and prepare logo
            logo = None
            if logo_path and os.path.exists(logo_path):
                logo = self.load_and_prepare_logo(logo_path)
            
            # Load and prepare episode-specific image (optional)
            episode_image = None
            fullscreen_image = None
            if episode_image_path:
                episode_image = self.load_and_prepare_episode_image(episode_image_path)
                fullscreen_image = self.load_and_prepare_fullscreen_image(episode_image_path)
            
            # Note: text_overlay will be created dynamically per frame for fade-in and glow pulse effects
            print("✓ Text overlay will be generated dynamically for animations")
            
            # Load audio to get duration
            audio_clip = AudioFileClip(audio_path)
            duration = audio_clip.duration
            
            print(f"🎨 Creating video frames on-demand (Duration: {duration:.1f}s)...")
            if fullscreen_image:
                print(f"📸 Thematic image transitions: {self.initial_composite_duration}s composite → {self.fullscreen_image_duration}s fullscreen (repeating)")
            print("⚡ Performance optimizations: Static text (no glow pulse), static logo (no breathing)")
            
            # Create a generator for final composited frames  
            font_cache = None  # Will be populated on first frame to avoid re-searching
            
            def final_frame_generator():
                nonlocal font_cache
                frame_count = 0
                total_frames = int(duration * self.fps)
                last_percent = -1
                font_cache = None  # Will be populated on first frame
                static_text_overlay = None  # Cache for static text (performance optimization)
                fade_duration = 2.0
                fade_frames = int(fade_duration * self.fps)
                
                for waveform_frame, waveform_data in waveform_frame_generator:
                    time_position = frame_count / self.fps
                    
                    # Progress reporting (every 5%)
                    percent = int((frame_count / total_frames) * 100)
                    if percent >= last_percent + 5:
                        print(f"  Progress: {percent}% ({frame_count}/{total_frames} frames, {time_position:.1f}/{duration:.1f}s)")
                        last_percent = percent
                    
                    # Create text overlay: render once, then reuse (except during fade-in)
                    if static_text_overlay is None:
                        # Render the static text overlay once at full opacity
                        print(f"  🎨 Creating static text overlay (fonts will be calculated once)")
                        static_text_overlay, font_cache = self.create_text_overlay(
                            episode_title, episode_image, fade_duration, duration, cached_fonts=font_cache
                        )
                        print(f"  ✓ Static text overlay created and cached for reuse")
                    
                    # Apply fade-in effect for first 2 seconds, then reuse static overlay
                    if frame_count < fade_frames:
                        # During fade-in: create text with fade applied
                        text_overlay, _ = self.create_text_overlay(
                            episode_title, episode_image, time_position, duration, cached_fonts=font_cache
                        )
                    else:
                        # After fade-in: reuse static overlay (major performance gain)
                        text_overlay = static_text_overlay
                    
                    # Composite this frame with view state transitions
                    final_frame = self.composite_frame(
                        waveform_frame, logo, text_overlay, time_position, duration, episode_image, fullscreen_image, waveform_data
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
            # Explicitly set video size to prevent scaling issues
            video_clip.size = (self.width, self.height)
            
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
            print(f"📐 Video resolution: {self.width}x{self.height} @ {self.fps}fps")
            
            # Build write_videofile parameters (compatible with moviepy 1.x and 2.x)
            write_params = {
                'fps': self.fps,
                'codec': 'libx264',
                'audio_codec': 'aac',
                'temp_audiofile': 'temp-audio.m4a',
                'remove_temp': True,
                'preset': 'medium',  # Balance between speed and file size
                'ffmpeg_params': [
                    '-crf', '23',  # Good quality with reasonable file size
                    '-pix_fmt', 'yuv420p'  # Ensure consistent pixel format for compatibility
                ]
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
