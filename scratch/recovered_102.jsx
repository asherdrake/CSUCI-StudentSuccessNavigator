import os

# Define the color palette
colors = {
    '.': None,       # Transparent
    'D': '#002D62',  # Navy outline / Eye
    'B': '#005A9C',  # Dolphin Body Blue
    'L': '#00B5E2',  # Dolphin Highlights (Teal)
    'W': '#FFFFFF',  # White belly / highlights
    'S': '#A1E3F9',  # Splash Light Blue
    'P': '#E8F9FF',  # Splash White
}

# 24x24 grids for 5 frames
frames = []

# Frame 0: Entering / Preparing (Horizontal swim)
frame0 = [
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "...........DD...........",
    ".........DDBBD..........",
    "........DBBBBD..........",
    ".......DBBBBD...........",
    "......DBBBBBDDD.........",
    ".....DBBBBBBBWWD........",
    "..DD.DBBBBBBWWWWD.......",
    ".DBBDBBBBBBWWWWWWD......",
    "DBBBBBBBBBWWWWWWWD......",
    ".DBBBBBBBWWWWWWWWD......",
    "..DBBBBBDWWWWWWWD.......",
    "...DBBBD.DDWWWD.........",
    "....DD.....DD...........",
    "........................",
    "......SSSSSSSSSS........",
    "....SSSSSSSSSSSSSS......",
    "........................",
    "........................",
    "........................"
]
frames.append(frame0)

# Let's write a python script to generate a single sprite-sheet SVG
def make_svg():
    width = 24 * len(frames)
    height = 24
    
    svg = []
    svg.append(f'<svg width="{width*4}" height="{height*4}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" style="image-rendering:pixelated; background:#1e1e24;">')
    
    for f_idx, frame in enumerate(frames):
        offset_x = f_idx * 24
        for y, row in enumerate(frame):
            for x, char in enumerate(row):
                color = colors.get(char)
                if color:
                    svg.append(f'  <rect x="{offset_x + x}" y="{y}" width="1" height="1" fill="{color}" />')
                    
    svg.append('</svg>')
    
    with open('scratch/dolphin_sprites.svg', 'w') as f:
        f.write('\n'.join(svg))
    print("Generated scratch/dolphin_sprites.svg")

if __name__ == "__main__":
    make_svg()
