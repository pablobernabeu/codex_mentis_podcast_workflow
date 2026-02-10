#!/usr/bin/env python3
"""
Quick test script to generate a single composite frame for layout verification.
"""

import sys
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

from video_generator import VideoGenerator
from waveform_visualizer import WaveformVisualizer

def main():
    # Initialize video generator
    generator = VideoGenerator()
    visualizer = WaveformVisualizer()
    
    # Configuration
    episode_title = "The dead salmon problem: Multiple tests, minimality and data-driven alternatives"
    logo_path = Path("assets/podcast_logo.jpeg")
    thematic_image_path = Path("input/The dead salmon problem_ Multiple tests, minimality and data-driven alternatives.png")
    output_path = Path("output/test_composite_frame.png")
    
    # Check if files exist
    if not logo_path.exists():
        print(f"❌ Logo not found: {logo_path}")
        print("   Looking for any logo file...")
        logo_files = [f for f in Path("assets").glob("podcast_logo.*") if f.stem == "podcast_logo"]
        if logo_files:
            logo_path = logo_files[0]
            print(f"   ✓ Found: {logo_path}")
        else:
            print("   ❌ No logo file found in assets/")
            return
    
    if not thematic_image_path.exists():
        print(f"❌ Thematic image not found: {thematic_image_path}")
        print("   Looking for any image files in input/...")
        image_files = list(Path("input").glob("*.png")) + list(Path("input").glob("*.jpg"))
        if image_files:
            thematic_image_path = image_files[0]
            print(f"   ✓ Using: {thematic_image_path}")
        else:
            print("   ℹ️  No thematic image found, will use logo only")
            thematic_image_path = None
    
    print("\n🎨 Generating test composite frame...")
    print(f"   Episode: {episode_title}")
    print(f"   Logo: {logo_path}")
    if thematic_image_path:
        print(f"   Thematic image: {thematic_image_path}")
    
    # Generate composite frame
    try:
        # Load and prepare logo using the generator's method
        print(f"   Loading logo from: {logo_path}")
        logo = generator.load_and_prepare_logo(str(logo_path))
        if logo:
            print(f"   ✓ Logo loaded: {logo.size}")
        else:
            print(f"   ❌ Logo failed to load")
        
        # Load and prepare thematic image using the generator's method
        episode_image = None
        if thematic_image_path:
            print(f"   Loading thematic image from: {thematic_image_path}")
            episode_image = generator.load_and_prepare_episode_image(str(thematic_image_path))
            if episode_image:
                print(f"   ✓ Thematic image loaded: {episode_image.size}")
        
        # Create text overlay using generator's method (now with episode_image for dynamic sizing)
        # Pass time_position for testing effects (1.5 seconds to show partial fade-in and some glow)
        text_overlay, _ = generator.create_text_overlay(episode_title, episode_image, time_position=1.5, duration=100)
        
        # Create a plain background waveform (no actual waveform visualization)
        waveform_img = Image.new('RGB', (generator.width, generator.height), (20, 25, 35))
        waveform_frame = np.array(waveform_img)
        
        # Create dummy waveform data for shake effect testing
        dummy_waveform_data = np.zeros(visualizer.history_width)
        
        # Use the generator's actual composite method but with plain waveform
        # This ensures we get the exact same layout as the real video
        composite_array = generator._create_composite_view(
            waveform_frame=waveform_frame,
            logo=logo,
            text_overlay=text_overlay,
            time_position=1.5,
            duration=100,
            episode_image=episode_image,
            waveform_data=dummy_waveform_data
        )
        
        # Convert to PIL Image
        frame = Image.fromarray(composite_array)
        
        # Save output
        output_path.parent.mkdir(exist_ok=True)
        frame.save(output_path)
        
        print(f"\n✅ Test composite frame saved: {output_path}")
        print(f"   Size: {frame.size[0]}x{frame.size[1]}")
        print("\n💡 Open this image to verify:")
        print(f"   • Title font sizes (dynamic per episode)")
        print(f"   • Gap between titles and thematic image")
        print(f"   • Overall layout and spacing")
        
    except Exception as e:
        print(f"\n❌ Error generating composite: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
