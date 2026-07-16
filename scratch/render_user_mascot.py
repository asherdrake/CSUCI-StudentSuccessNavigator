import os

# We will fill the gaps in the body based on the super_accurate_extractor.py output.
# The body is grey 'B', outline is black 'D', background is '.'
grid = [
    "................................", # 0
    "................................", # 1
    "...............DDDD.............", # 2
    ".........DDDDDDBBBBD............", # 3
    ".......DDBBBBDBBBDD.............", # 4
    "......DBBBBBBBBBDBD.............", # 5
    ".....DBBBBBBBBBBBBBD............", # 6
    "....DBBBBBBBBBBBBBBBD...........", # 7
    "....DBBDBBBBBBBBBBBBBD..........", # 8  (Eye at index 7 is D)
    "....DBBBBBBBBBBBBBBBBDB.........", # 9
    "....DBBBBBBBBBBBBBBBBBD.........", # 10
    "...DBBBBBBBBBBBBBBBBBBD.........", # 11
    "...DBBBBBBBBBBBBBBBBBBD.........", # 12
    "....DDBBBBBBBBBBBBBBD...........", # 13
    "......DDDDDBBBBBBDDD............", # 14
    "..........DBBBBD................", # 15
    ".........DBBBBBBD...............", # 16
    ".........DBD.DDDD...............", # 17
    ".........DBD....................", # 18
    "..........D.....................", # 19
    "................................", # 20
    "................................"  # 21
]

# Let's verify the body filling:
# In the original extraction:
# Row 10 had: ....DBB.....BBD..BBBBBD.........
# Row 11 had: ...DBB.......B.D...BBBD.........
# Row 12 had: ...D..D......BBD.DD.BBD.........
# Row 13 had: ...............D.....BB.........
# These gaps are now fully filled with 'B' to form the solid body of the dolphin!

def make_svg():
    width = 32
    height = 22
    colors = {
        '.': None,       # Transparent
        'D': '#000000',  # Black outline / Eye
        'B': '#94a3b8',  # Grey body
    }
    
    svg = []
    svg.append(f'<svg width="{width*10}" height="{height*10}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" style="image-rendering:pixelated; background:#e2e8f0;">')
    
    for y, row in enumerate(grid):
        for x, char in enumerate(row):
            color = colors.get(char)
            if color:
                svg.append(f'  <rect x="{x}" y="{y}" width="1" height="1" fill="{color}" />')
                
    svg.append('</svg>')
    
    with open('scratch/user_dolphin_completed.svg', 'w') as f:
        f.write('\n'.join(svg))
    print("Generated scratch/user_dolphin_completed.svg")

if __name__ == "__main__":
    make_svg()
