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

# Define the 5 frames (24x24)
from draw_dolphin import frames

def make_animated_svg():
    width = 24
    height = 24
    num_frames = len(frames)
    sheet_width = width * num_frames
    
    svg = []
    svg.append(f'<svg width="128" height="128" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" style="image-rendering:pixelated; background:transparent;">')
    svg.append('  <style>')
    svg.append('    @keyframes play-sprite {')
    svg.append(f'      from {{ transform: translateX(0px); }}')
    svg.append(f'      to {{ transform: translateX(-{sheet_width}px); }}')
    svg.append('    }')
    svg.append('    .sprite-sheet {')
    svg.append(f'      animation: play-sprite 0.75s steps({num_frames}) infinite;')
    svg.append('    }')
    svg.append('  </style>')
    
    # Wrap in a group that performs the sprite-sheet translate animation
    svg.append('  <g class="sprite-sheet">')
    
    # Render all frames horizontally
    for f_idx, frame in enumerate(frames):
        offset_x = f_idx * 24
        # Group each frame to keep it clean
        svg.append(f'    <g id="frame-{f_idx}">')
        for y, row in enumerate(frame):
            for x, char in enumerate(row):
                color = colors.get(char)
                if color:
                    svg.append(f'      <rect x="{offset_x + x}" y="{y}" width="1" height="1" fill="{color}" />')
        svg.append('    </g>')
        
    svg.append('  </g>')
    svg.append('</svg>')
    
    with open('scratch/animated_dolphin.svg', 'w') as f:
        f.write('\n'.join(svg))
    print("Generated scratch/animated_dolphin.svg")

if __name__ == "__main__":
    make_animated_svg()
