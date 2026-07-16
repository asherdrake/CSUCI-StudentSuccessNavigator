from PIL import Image
import numpy as np

img_path = r"C:\Users\myane\.gemini\antigravity\brain\fb4773c8-7646-44ca-a50e-eabf85b2f0df\media__1784182447701.jpg"
img = Image.open(img_path)
width, height = img.size

# Let's find grid lines by looking at color variations
# Convert to numpy array
arr = np.array(img)

# Let's count how many grid lines we can find by looking at columns
# Grid lines in this kind of pixel art template are often darker/lighter blue lines.
# Let's plot the average color of each column to find the periodic grid lines.
col_averages = np.mean(arr, axis=0) # average over rows
row_averages = np.mean(arr, axis=1) # average over columns

# Let's print out the column averages to see if there is a pattern
# Grid lines will show up as periodic local minima/maxima in brightness.
brightness_col = np.mean(col_averages, axis=1)
brightness_row = np.mean(row_averages, axis=1)

print("Column brightness peaks/valleys:")
for i in range(10, width - 10):
    # Check if local minimum or maximum compared to neighbors
    if brightness_col[i] < brightness_col[i-1] and brightness_col[i] < brightness_col[i+1]:
        print(f"Col {i} is a valley: {brightness_col[i]:.1f}")
    elif brightness_col[i] > brightness_col[i-1] and brightness_col[i] > brightness_col[i+1]:
        print(f"Col {i} is a peak: {brightness_col[i]:.1f}")
