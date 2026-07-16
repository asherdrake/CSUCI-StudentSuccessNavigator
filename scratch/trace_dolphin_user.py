import os

colors = {
    '.': None,       # Transparent
    'D': '#000000',  # Black outline / Eye
    'B': '#94a3b8',  # Grey body
}

# Manually cleaned 32x22 grid of the user's dolphin image
grid = [
    "................................", # 0
    "................................", # 1
    "...............DDDD.............", # 2  (dorsal fin top)
    ".........DDDDDDBBBBD............", # 3  (head top / dorsal fin back)
    ".......DDBBBBDBBBDD.............", # 4  (head / dorsal fin base)
    "......DBBBBBBBBBDBD.............", # 5
    ".....DBBBBBBBBBBBBBD............", # 6
    "....DBBBBBBBBBBBBBBBD...........", # 7
    "....DBBDBBBBBBBBBBBBBD..........", # 8  (eye is at col 7)
    "....DBBBBBBBBBBBBBBBBBD.........", # 9  (beak starts on left)
    "....DBBBBBBBBBBBBBBBBBD.........", # 10
    "...DBBBBBBBBBBBBBBBBD...........", # 11
    "...DBBBBBBBBBBBBBBBD............", # 12
    "....DDBBBBBBBBBBBBD.............", # 13
    "......DDDDDBBBBDDD..............", # 14
    "..........DBBBBD................", # 15
    ".........DBBBBBBD...............", # 16 (tail flukes)
    ".........DBD.DDDD...............", # 17
    ".........DBD....................", # 18
    "..........D.....................", # 19
    "................................", # 20
    "................................"  # 21
]

def make_svg():
    width = 32
    height = 22
    
    svg = []
    svg.append(f'<svg width="{width*10}" height="{height*10}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" style="image-rendering:pixelated; background:#e2e8f0;">')
    
    for y, row in enumerate(grid):
        for x, char in enumerate(row):
            color = colors.get(char)
            if color:
                svg.append(f'  <rect x="{x}" y="{y}" width="1" height="1" fill="{color}" />')
                
    svg.append('</svg>')
    
    with open('scratch/user_dolphin_cleaned.svg', 'w') as f:
        f.write('\n'.join(svg))
    print("Generated scratch/user_dolphin_cleaned.svg")

if __name__ == "__main__":
    make_svg()
