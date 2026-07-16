from PIL import Image
from collections import Counter

img_path = r"C:\Users\myane\.gemini\antigravity\brain\fb4773c8-7646-44ca-a50e-eabf85b2f0df\media__1784182447701.jpg"
img = Image.open(img_path).convert("RGB")
width, height = img.size

# Find neutral grey pixels
grey_pixels = []
black_pixels = []
for y in range(height):
    for x in range(width):
        r, g, b = img.getpixel((x, y))
        # Black
        if r < 50 and g < 50 and b < 50:
            black_pixels.append((r, g, b))
        # Grey
        elif abs(r - g) < 8 and abs(g - b) < 8 and r > 80 and r < 180:
            grey_pixels.append((r, g, b))

counter_grey = Counter(grey_pixels)
counter_black = Counter(black_pixels)

print("Top 5 grey colors:")
for color, count in counter_grey.most_common(5):
    print(f"Color: {color}, Count: {count}")
    
print("\nTop 5 black colors:")
for color, count in counter_black.most_common(5):
    print(f"Color: {color}, Count: {count}")
