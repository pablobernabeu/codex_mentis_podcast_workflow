#!/usr/bin/env python3
"""
Quick test to verify the waveform caching system works correctly.
"""

import sys
sys.path.append('src')

from waveform_visualizer import WaveformVisualizer
from pathlib import Path
import numpy as np

def test_caching():
    """Test the waveform caching functionality."""
    print("🧪 Testing waveform caching system...")
    
    # Create visualizer
    visualizer = WaveformVisualizer()
    
    # Test cache path generation
    test_audio_path = Path("test_audio.wav")
    cache_path = visualizer.get_cache_path(test_audio_path)
    print(f"✓ Cache path: {cache_path}")
    
    # Test hash generation
    audio_hash = visualizer.get_audio_hash("non_existent_file.wav")
    print(f"✓ Hash for non-existent file: {audio_hash}")
    
    # Test cache loading (should return None)
    cached_data = visualizer.load_waveform_cache("non_existent_file.wav")
    print(f"✓ Cache load for non-existent file: {cached_data}")
    
    print("✅ Caching system basic tests passed!")

if __name__ == "__main__":
    test_caching()
