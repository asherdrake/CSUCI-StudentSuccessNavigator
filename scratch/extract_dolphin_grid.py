from PIL import Image
import numpy as np

img_path = r"C:\Users\myane\.gemini\antigravity\brain\fb4773c8-7646-44ca-a50e-eabf85b2f0df\media__1784182447701.jpg"
img = Image.open(img_path).convert("RGB")
width, height = img.size

# Grid is exactly 32 columns x 22 rows
grid_w = 32
grid_h = 22
step_x = 6.5
step_y = 6.5

# Let's try multiple start offsets to find the best alignment
alignments = [
    (9.75, 8.25),
    (9.75, 7.75),
    (10.25, 8.25),
    (10.25, 7.75),
    (9.5, 8.0),
    (10.0, 8.5)
]

for idx, (start_x, start_y) in enumerate(alignments):
    grid_chars = []
    for j in range(grid_h):
        y = int(start_y + j * step_y)
        row = []
        for i in range(grid_w):
            x = int(start_x + i * step_x)
            if x < width and y < height:
                r, g, b = img.getpixel((x, y))
                # Refined Classifier
                if r < 40 and g < 40 and b < 40:
                    row.append("D") # Black outline
                elif abs(r - g) < 8 and abs(g - b) < 8 and 110 < r < 170:
                    row.append("B") # Grey body
                else:
                    row.append(".") # Background
            else:
                row.append(".")
        grid_chars.append("".join(row))
        
    print(f"\nAlignment {idx}: start_x={start_x}, start_y={start_y}")
    for row in grid_chars:
        print(row)
