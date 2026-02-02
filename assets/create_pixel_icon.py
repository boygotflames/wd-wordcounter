"""
Create pixel-art WD icon
"""

from PIL import Image, ImageDraw
import os

def create_pixel_icon():
    """Create a pixel-art WD icon"""
    
    # Create 64x64 image (will be scaled)
    size = 64
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw pixelated "WD" using block pixels
    pixels = [
        # W letter (8x8 grid)
        [0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [1,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0],
        [1,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0],
        [1,0,0,1,0,0,1,0,0,0,0,1,0,0,0,0],
        [1,0,0,1,0,1,0,1,0,0,1,0,1,0,0,0],
        [1,0,0,1,1,0,0,0,1,1,0,0,0,1,0,0],
        [1,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0],
        
        # D letter (8x8 grid)
        [0,0,0,0,1,1,1,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,1,0,0,1,0,0,0,0,0,0,0,0],
        [0,0,0,0,1,0,0,1,0,0,0,0,0,0,0,0],
        [0,0,0,0,1,0,0,1,0,0,0,0,0,0,0,0],
        [0,0,0,0,1,0,0,1,0,0,0,0,0,0,0,0],
        [0,0,0,0,1,0,0,1,0,0,0,0,0,0,0,0],
        [0,0,0,0,1,0,0,1,0,0,0,0,0,0,0,0],
        [0,0,0,0,1,1,1,0,0,0,0,0,0,0,0,0],
    ]
    
    # Draw pixels
    pixel_size = size // 16
    for y in range(16):
        for x in range(16):
            if pixels[y][x] == 1:
                # Terminal green color
                draw.rectangle([
                    x * pixel_size, y * pixel_size,
                    (x + 1) * pixel_size - 1, (y + 1) * pixel_size - 1
                ], fill=(0, 255, 0))
    
    # Add subtle glow effect
    for i in range(3):
        border = i + 1
        draw.rectangle(
            [border, border, size - border - 1, size - border - 1],
            outline=(0, 100 + i * 50, 0, 100),
            width=1
        )
    
    # Save in multiple sizes for icon
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    icons = []
    
    for sz in sizes:
        resized = img.resize(sz, Image.NEAREST)
        icons.append(resized)
    
    # Save as ICO
    icons[0].save('assets/wd_pixel.ico', format='ICO', append_images=icons[1:])
    
    print("✅ Pixel icon created: assets/wd_pixel.ico")
    
    # Also save as PNG for reference
    img.save('assets/wd_pixel.png', 'PNG')

if __name__ == "__main__":
    os.makedirs("assets", exist_ok=True)
    create_pixel_icon()