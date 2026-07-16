from PIL import Image
import numpy as np

img_path = r"C:\Users\myane\.gemini\antigravity\brain\fb4773c8-7646-44ca-a50e-eabf85b2f0df\media__1784182447701.jpg"
img = Image.open(img_path).convert("RGB")
width, height = img.size

# Let's count grid size
# The image is 212 x 148.
# If grid is 32 x 22:
# 212 / 32 = 6.625
# 148 / 22 = 6.727
# Let's use numpy to find grid lines exactly.
# Let's check:
cols = 32
rows = 22

grid = []
for r in range(rows):
    row_chars = []
    # y range for this cell
    y_start = int(r * height / rows)
    y_end = int((r + 1) * height / rows)
    y_center = (y_start + y_end) // 2
    
    for c in range(cols):
        # x range for this cell
        x_start = int(c * width / cols)
        x_end = int((c + 1) * width / cols)
        x_center = (x_start + x_end) // 2
        
        # Sample a 3x3 region at the center of the cell
        pixels = []
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                px = x_center + dx
                py = y_center + dy
                if 0 <= px < width and 0 <= py < height:
                    pixels.append(img.getpixel((px, py)))
        
        avg_r = np.mean([p[0] for p in pixels])
        avg_g = np.mean([p[1] for p in pixels])
        avg_b = np.mean([p[2] for p in pixels])
        
        # Classify based on average colors
        if avg_r < 65 and avg_g < 65 and avg_b < 65:
            row_chars.append("D") # Black outline
        elif abs(avg_r - avg_g) < 12 and abs(avg_g - avg_b) < 12 and 100 < avg_r < 185:
            row_chars.append("B") # Grey body
        else:
            row_chars.append(".") # Background
            
    grid.append("".join(row_chars))

# Print grid
for row in grid:
    print(row)
