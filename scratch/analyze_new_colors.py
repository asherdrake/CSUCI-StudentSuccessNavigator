from PIL import Image
from collections import Counter

img_path = r"C:\Users\myane\.gemini\antigravity\brain\fb4773c8-7646-44ca-a50e-eabf85b2f0df\media__1784182878143.png"
img = Image.open(img_path).convert("RGBA")
width, height = img.size

colors = []
for y in range(height):
    for x in range(width):
        r, g, b, a = img.getpixel((x, y))
        if a > 50: # Only count visible pixels
            colors.append((r, g, b))

counter = Counter(colors)
print("Top 10 most common colors:")
for color, count in counter.most_common(10):
    print(f"Color: {color}, Count: {count}")
