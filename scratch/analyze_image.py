from PIL import Image

img_path = r"C:\Users\myane\.gemini\antigravity\brain\fb4773c8-7646-44ca-a50e-eabf85b2f0df\media__1784182447701.jpg"

try:
    img = Image.open(img_path)
    print(f"Image Dimensions: {img.size}")
    print(f"Image Mode: {img.mode}")
except Exception as e:
    print(f"Error opening image: {e}")
