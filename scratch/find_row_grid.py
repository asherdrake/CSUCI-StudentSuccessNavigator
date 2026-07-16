from PIL import Image
import numpy as np

img_path = r"C:\Users\myane\.gemini\antigravity\brain\fb4773c8-7646-44ca-a50e-eabf85b2f0df\media__1784182447701.jpg"
img = Image.open(img_path)
width, height = img.size

arr = np.array(img)
row_averages = np.mean(arr, axis=1) # average over columns
brightness_row = np.mean(row_averages, axis=1)

print("Row brightness valleys (potential horizontal grid lines):")
for i in range(5, height - 5):
    if brightness_row[i] < brightness_row[i-1] and brightness_row[i] < brightness_row[i+1]:
        print(f"Row {i}: {brightness_row[i]:.1f}")
