#!/usr/bin/env python3
"""
Generate favicon.ico from SVG for Bleta
"""

import os
import sys

def create_ico_from_svg():
    """Create ICO file from SVG favicon."""
    try:
        # Try to use cairosvg if available
        import cairosvg
        
        svg_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "public", "favicon.svg")
        ico_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "public", "favicon.ico")
        
        # Convert SVG to PNG first, then to ICO
        png_data = cairosvg.svg2png(url=svg_path, output_width=32, output_height=32)
        
        # For now, we'll just create a simple ICO file
        # In a real implementation, you'd use PIL or similar to create proper ICO
        with open(ico_path, 'wb') as f:
            # Write a minimal ICO header
            f.write(b'\x00\x00')  # Reserved
            f.write(b'\x01\x00')  # Type (ICO)
            f.write(b'\x01\x00')  # Number of images
            f.write(b'\x20')      # Width
            f.write(b'\x20')      # Height
            f.write(b'\x00')      # Color count
            f.write(b'\x00')      # Reserved
            f.write(b'\x01\x00')  # Color planes
            f.write(b'\x20\x00')  # Bits per pixel
            f.write(b'\x00\x00\x00\x00')  # Size of image data
            f.write(b'\x16\x00\x00\x00')  # Offset of image data
            
            # Write PNG data
            f.write(png_data)
            
        print(f"✅ Generated favicon.ico from SVG")
        
    except ImportError:
        print("⚠️  cairosvg not available. Using SVG favicon only.")
        print("   Install with: pip install cairosvg")
    except Exception as e:
        print(f"❌ Error generating ICO: {e}")

if __name__ == "__main__":
    create_ico_from_svg()
