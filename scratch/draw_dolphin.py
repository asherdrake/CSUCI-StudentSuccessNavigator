import os

colors = {
    '.': None,       # Transparent
    'D': '#002D62',  # Navy outline / Eye
    'B': '#005A9C',  # Dolphin Body Blue
    'L': '#00B5E2',  # Dolphin Highlights (Teal)
    'W': '#FFFFFF',  # White belly / highlights
    'S': '#A1E3F9',  # Splash Light Blue
    'P': '#E8F9FF',  # Splash White
}

frames = []

# Frame 0: Horizontal Swimming (Prep)
# Dolphin is in/near water, starting to arc.
frame0 = [
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "..........DDD...........",
    ".........DBBBD..........",
    "......DD.DBBBD..........",
    ".....DBBDBBBBD..........",
    "....DBBBBBBBBDD.........",
    "...DBBBBBBBBBBBD........",
    "..DBBBBBBBBBBBBBD.......",
    ".DBBBBBBDDBBBBBBBD......", # Eye D at (12, 8)
    "DBBBBBBWWWWWWBBBBD......",
    ".DBBBBBWWWWWWBBBD.......",
    "..DDDBBWWWWWWD..........",
    "....DDBWWWWWD...........",
    "......DDWWWDD...........",
    "........DDD.............",
    "........................",
    "........................",
    "....SSSSSSSSSSSSSS......",
    "...SSSSSSSSSSSSSSSS.....",
    "........................"
]
frames.append(frame0)

# Frame 1: Leaping Up (Breaking water)
# Nose points up-right, body tilted ~45 degrees. Splash at the bottom.
frame1 = [
    "........................",
    "........................",
    "........................",
    "..............DD........",
    ".............DBBD.......",
    "............DBBBD.......",
    "...........DBBBBD.......",
    "..........DBBBBD........",
    ".........DBBBBD.........",
    "........DBBBBD..........",
    "......DDBBBBD...........",
    ".....DBBBBBBD...........",
    "....DBBBDDBBD...........", # Eye at (12, 10)
    "...DBBBWWWBBD...........",
    "..DBBBWWWWWD............",
    "..DBBBWWWWD.............",
    "...DBBWWWD..............",
    "....DBWWD...............",
    ".....DDD................",
    "........................",
    "......SS..SS............",
    "....SSSPSSPSSS..........",
    "...SSSSSSSSSSSS.........",
    "........................"
]
frames.append(frame1)

# Frame 2: Apex of the Leap (Highest point)
# Dolphin is arched horizontally, high in the air.
frame2 = [
    "........................",
    "........................",
    "..........DDD...........",
    "........DDBBBDD.........",
    ".......DBBBBBBBD........",
    "......DBBBBBBBBBD.......",
    ".....DBBDDBBBBBBBD......", # Eye at (6, 10)
    "....DBBBWWWWWWBBBD......",
    "...DBBBWWWWWWWWBD.......",
    "..DBBBWWWWWWWWWD........",
    ".DBBBWWWWWWWWWD.........",
    "DBBBWWWWWWWWDD..........",
    "DDBBWWWWWDDD............",
    ".DDWWWWDDD..............",
    "..DDDDD.................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "....SS........SS........",
    "...SSS........SSS......."
]
frames.append(frame2)

# Frame 3: Diving Down (Entering water)
# Head points down-right, tail is high up-left.
frame3 = [
    "........................",
    ".....DDD................",
    "....DBWWD...............",
    "...DBBWWWD..............",
    "..DBBBWWWWD.............",
    "..DBBBWWWWWD............",
    "...DBBBWWWBBD...........",
    "....DBBBDDBBD...........", # Eye at (7, 12)
    ".....DBBBBBBD...........",
    "......DDBBBBD...........",
    "........DBBBBD..........",
    ".........DBBBBD.........",
    "..........DBBBBD........",
    "...........DBBBBD.......",
    "............DBBBD.......",
    ".............DBBD.......",
    "..............DD........",
    "........................",
    "........................",
    "........................",
    "........................",
    "......SS..SS............",
    "....SSSPSSPSSS..........",
    "...SSSSSSSSSSSS........."
]
frames.append(frame3)

# Frame 4: Splashdown (Impact)
# Dolphin is half submerged, large splash.
frame4 = [
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "..........DDD...........",
    ".........DBBBD..........",
    "......DD.DBBBD..........",
    ".....DBBDBBBBD..........",
    "....DBBBBBBBBDD.........",
    "...DBBBBBBBBBBBD........",
    "..DBBBBBBBBBBBBBD.......",
    ".DBBBBBBDDBBBBBBBD......", # Eye at (12, 8)
    "DBBBBBBWWWWWWBBBBD......",
    ".DBBBBBWWWWWWBBBD.......",
    "..DDDBBWWWWWWD..........",
    "....DDBWWWWWD...P..P....",
    "......DDWWWDD..SPSPS....",
    "..P..P..DDD...SSSSSS....",
    ".SPSPS.......SSSSSSSS...",
    "SSSSSS......SSSSSSSSSS..",
    "SSSSSSS....SSSSSSSSSSSS.",
    "SSSSSSSSSSSSSSSSSSSSSSSS",
    "SSSSSSSSSSSSSSSSSSSSSSSS"
]
frames.append(frame4)

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
