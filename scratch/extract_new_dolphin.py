from PIL import Image

img_path = r"C:\Users\myane\.gemini\antigravity\brain\fb4773c8-7646-44ca-a50e-eabf85b2f0df\media__1784182878143.png"
img = Image.open(img_path).convert("RGBA")
width, height = img.size

# The grid is 20 cols x 28 rows
cols = 20
rows = 28
block_size = 16

grid_chars = []
for j in range(rows):
    y = int(8 + j * block_size)
    row = []
    for i in range(cols):
        x = int(8 + i * block_size)
        r, g, b, a = img.getpixel((x, y))
        
        if a < 50:
            row.append(".") # Transparent background
        elif r == 0 and g == 0 and b == 0:
            row.append("D") # Black outline
        elif r == 111 and g == 168 and b == 220:
            row.append("B") # Light blue body
        elif r == 118 and g == 165 and b == 175:
            row.append("T") # Darker teal back
        elif r == 255 and g == 255 and b == 255:
            row.append("W") # White belly/face
        else:
            row.append("?")
            
    grid_chars.append("".join(row))

for row in grid_chars:
    print(row)

print("\nPython format:")
print("[\n" + ",\n".join([f'    "{r}"' for r in grid_chars]) + "\n]")
