#!/usr/bin/env python3
"""
Simple test to debug the input issue
"""

def test_selection():
    print("🎙️  Codex Mentis Podcast Video Converter")
    print("=" * 60)
    
    print("📁 Found 2 WAV file(s) in input directory:")
    print("-" * 60)
    print(" 1. Behind the curtains_ Methods used to investigate conceptual processing.wav (45.2 MB)")
    print(" 2. The architecture of meaning_ Inside the words we use.wav (38.7 MB)")
    
    print("\n🎯 Selection options:")
    print("  • Enter numbers (e.g., 1,3,5): Process specific files")
    print("  • Enter 'all': Process all files")
    print("  • Enter 'q': Quit")
    
    while True:
        selection = input("\nYour choice: ").strip().lower()
        print(f"You entered: '{selection}'")
        
        if selection == 'q':
            print("Quitting...")
            break
        elif selection == 'all':
            print("Selected all files!")
            break
        else:
            print("❌ Invalid format. Please enter numbers separated by commas (e.g., 1,3,5).")

if __name__ == "__main__":
    test_selection()
