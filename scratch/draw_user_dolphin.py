import os

colors = {
    '.': None,       # Transparent
    'D': '#000000',  # Black outline / Eye
    'B': '#94a3b8',  # Grey body (CSUCI Silver/Grey)
    'W': '#ffffff',  # White highlight
}

# Initial trace of the dolphin from the user's image
grid = [
    # 0
    "..............................",
    # 1
    "..............................",
    # 2
    "...............DDDD...........",
    # 3
    "............DDD.BB.D..........",
    # 4
    ".........DDD.B..BB.D..........",
    # 5
    ".......DD.BBBB.B.B.D..........",
    # 6
    "......D.BBBBBBB.B.B.D.........",
    # 7
    ".....D.BB.BBBBB.B.B.D.........", # Eye at index 8 (D)
    # 8
    "....D.BBBBBBBB..B..D..........",
    # 9
    "....D.BBBBBBBBBB..D...........",
    # 10
    "....D.BBBBBBBBBB.D............",
    # 11
    ".....D.BBBBBBBBB.D............",
    # 12
    "......DDBBBBBBB.D.............",
    # 13
    "........DD.BBBD.D.............",
    # 14
    "..........D.BD.D..............",
    # 15
    "...........D.D.D..............",
    # 16
    "............D.D...............",
    # 17
    ".............D................",
    # 18
    "..............................",
    # 19
    ".............................."
]

def make_svg():
    width = 30
    height = 20
    
    svg = []
    svg.append(f'<svg width="{width*10}" height="{height*10}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" style="image-rendering:pixelated; background:#e2e8f0;">')
    
    # Draw grid lines to help match the image
    for x in range(width):
        svg.append(f'  <line x1="{x}" y1="0" x2="{x}" y2="{height}" stroke="#cbd5e1" stroke-width="0.05" />')
    for y in range(height):
        svg.append(f'  <line x1="0" y1="{y}" x2="{width}" y2="{y}" stroke="#cbd5e1" stroke-width="0.05" />')
        
    for y, row in enumerate(grid):
        for x, char in enumerate(row):
            color = colors.get(char)
            if color:
                svg.append(f'  <rect x="{x}" y="{y}" width="1" height="1" fill="{color}" />')
                
    svg.append('</svg>')
    
    with open('scratch/user_dolphin.svg', 'w') as f:
        f.write('\n'.join(svg))
    print("Generated scratch/user_dolphin.svg")

if __name__ == "__main__":
    make_svg()
