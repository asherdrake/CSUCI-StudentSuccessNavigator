# Transcribe the dolphin from the image
# Grid is 30 columns x 20 rows.
# Let's define the character map:
# '.' = transparent / grid bg
# 'D' = Black outline
# 'B' = Grey body
# 'E' = Eye (black)
# 'W' = Light grey/white highlight (optional, let's check if the image has a highlight.
# The image has grey body and black outline/eye. It doesn't seem to have a white belly or highlights, it is a single grey tone.
# Wait, let's check the grey body color: it's a solid grey, similar to #99aab5 or #8a9ba8. The outline is black #000000.

frame_data = [
    # Row 0
    "..............................",
    # Row 1
    "..............................",
    # Row 2
    "...............DDDD...........",
    # Row 3
    ".........DDDDDD.BB.D..........",
    # Row 4
    ".......DD.BBBBBD.B.D..........",
    # Row 5
    "......D.BBBBBBBD.B.DD.........",
    # Row 6
    ".....D.BBBBBBBB.B.B..D........",
    # Row 7
    "....D.BBBBBBBBBBBB.B..D.......",
    # Row 8
    "....D.B.B.BBBBBBBBB..D........",
    # Row 9
    "....D.BBBBBBBBBBBBBDD.........",
    # Row 10
    "...D.BBBBBBBBBBBD.............",
    # Row 11
    "..D.D.BBBBBBBD.D..............",
    # Row 12
    "..DD.D.BBBBBD.D...............",
    # Row 13
    "......DD.BBD.D................",
    # Row 14
    "........D.B.D.................",
    # Row 15
    ".........D.D..................",
    # Row 16
    "..........D...................",
    # Row 17
    "..............................",
    # Row 18
    "..............................",
    # Row 19
    ".............................."
]

def print_grid():
    for r in frame_data:
        print("".join(['#' if c == 'D' else ('o' if c == 'B' else ' ') for c in r]))

if __name__ == "__main__":
    print_grid()
