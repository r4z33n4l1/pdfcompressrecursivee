import os
import io
from PIL import Image
from pdf2image import convert_from_path
from PyPDF2 import PdfMerger, PdfReader

def compress_pdf(file_path, max_size_mb=2, quality=90, scale_factor=0.5):
    if not file_path.lower().endswith('.pdf') or not os.path.exists(file_path):
        print("Invalid file or file does not exist.")
        return

    base_name = os.path.splitext(os.path.basename(file_path))[0]
    temp_dir = f"temp_{base_name}"
    os.makedirs(temp_dir, exist_ok=True)

    try:
        # Convert PDF pages to images
        pages = convert_from_path(file_path)

        while True:
            merger = PdfMerger()
            for i, page in enumerate(pages):
                # Scale down the image
                new_width = int(page.width * scale_factor)
                new_height = int(page.height * scale_factor)
                resized_page = page.resize((new_width, new_height), Image.LANCZOS)

                # Compress and save each page as an image
                img_path = os.path.join(temp_dir, f'page_{i+1}.jpg')
                resized_page.save(img_path, 'JPEG', quality=quality)
                
                # Convert image to PDF and append to merger
                with Image.open(img_path) as img:
                    pdf_bytes = io.BytesIO()
                    img.save(pdf_bytes, format='PDF')
                    pdf_bytes.seek(0)
                    merger.append(PdfReader(pdf_bytes))

            compressed_file_path = f"compressedfinal_{os.path.basename(file_path)}"
            merger.write(compressed_file_path)
            merger.close()

            # Check if the file size is less than max_size_mb
            if os.path.getsize(compressed_file_path) <= max_size_mb * 1024 * 1024:
                break
            else:
                # If not, reduce the scale factor and try again
                scale_factor *= 0.5
                os.remove(compressed_file_path)
                if scale_factor < 0.1:  # Set a minimum scale to prevent infinite loop
                    print("Unable to compress further without severe quality loss.")
                    break

        print(f"Compressed PDF saved as {compressed_file_path}")
        print(f"File size: {os.path.getsize(compressed_file_path) / (1024 * 1024):.2f} MB")
        print(f"Final scale factor: {scale_factor}")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Clean up temporary files
        for file in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, file))
        os.rmdir(temp_dir)

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python main.py <relative_file_path>")
    else:
        compress_pdf(sys.argv[1])
