"""
Create application icon (run this to generate icon.ico)
"""

from PIL import Image, ImageDraw
import os

def create_icon():
    """Create a terminal-style icon for WD"""
    
    # Create 256x256 image
    img = Image.new('RGB', (256, 256), color='#0a0a0a')
    draw = ImageDraw.Draw(img)
    
    # Draw WD letters in terminal green
    draw.text((80, 80), "WD", fill='#00ff00', font_size=80)
    
    # Draw underline
    draw.line([(80, 160), (176, 160)], fill='#00ff00', width=4)
    
    # Save as ICO
    img.save('assets/icon.ico', format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
    
    print("Icon created: assets/icon.ico")

if __name__ == "__main__":
    os.makedirs("assets", exist_ok=True)
    create_icon()