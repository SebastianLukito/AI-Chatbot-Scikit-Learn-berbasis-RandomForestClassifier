from pdf2image import convert_from_path
import img2pdf
import os
import tkinter as tk
from tkinter import filedialog

def open_file():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename()
    return file_path

def save_file():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.asksaveasfilename(defaultextension=".pdf")
    return file_path

input_file = open_file()
output_file = save_file()

# Convert PDF pages to images
pages = convert_from_path(input_file)

# Save each image to a file
image_files = []
for i, page in enumerate(pages):
    image_file = f'page{i}.png'
    page.save(image_file, 'PNG')
    image_files.append(image_file)

# Convert images back to PDF
with open(output_file, "wb") as f:
    f.write(img2pdf.convert(image_files))

# Remove image files
for image_file in image_files:
    os.remove(image_file)
