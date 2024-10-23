import os
import io
from PIL import Image
from pdf2image import convert_from_path
from PyPDF2 import PdfMerger, PdfReader

def compress_pdf(file_path, max_size_mb=4, quality=90, initial_scale_factor=0.5, tolerance=0.1):
    if not file_path.lower().endswith('.pdf') or not os.path.exists(file_path):
        print("Invalid file or file does not exist.")
        return

    base_name = os.path.splitext(os.path.basename(file_path))[0]
    temp_dir = f"temp_{base_name}"
    os.makedirs(temp_dir, exist_ok=True)

    def get_file_size_mb(file_path):
        return os.path.getsize(file_path) / (1024 * 1024)

    try:
        # Convert PDF pages to images
        pages = convert_from_path(file_path)
        scale_factor = initial_scale_factor
        best_file_path = None
        best_file_size = None

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

            current_file_size = get_file_size_mb(compressed_file_path)
            print(f"Current file size: {current_file_size:.2f} MB with scale factor: {scale_factor}")

            if current_file_size <= max_size_mb:
                # Save the best version so far
                best_file_path = compressed_file_path
                best_file_size = current_file_size

                # Check if we can increase the scale factor to get closer to the max_size_mb
                if current_file_size >= (1 - tolerance) * max_size_mb:
                    print(f"Final compressed PDF saved as {best_file_path} with size {best_file_size:.2f} MB")
                    break
                else:
                    scale_factor *= 1.1  # Try increasing the scale factor by 10%
            else:
                # If we're overshooting, reduce the scale factor and retry
                scale_factor *= 0.9

            # If the scale factor gets too small or too large
            if scale_factor < 0.1:
                print("Unable to compress further without severe quality loss.")
                break
            if scale_factor > 1.0 and best_file_path:
                print(f"Final compressed PDF saved as {best_file_path} with size {best_file_size:.2f} MB")
                break

        # If no better version is found, use the best one
        if best_file_path and best_file_size:
            print(f"Final compressed PDF saved as {best_file_path}")
            print(f"File size: {best_file_size:.2f} MB")

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