# compress_photos.py
from PIL import Image
import os

input_folder = "../photos"
output_folder = "../photos/thumbs"
os.makedirs(output_folder, exist_ok = True)

for filename in os.listdir(input_folder):
    if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
        input_path = os.path.join(input_folder, filename)
        output_path = os.path.join(output_folder, filename)
        try:
            img = Image.open(input_path)
            img.thumbnail((800, 800))
            img.save(output_path, quality = 60, optimize = True)
            print(f"Compressed: {filename}")
        except Exception as e:
            print(f"Skipped {filename}: {e}")