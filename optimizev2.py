import os
import io
from PIL import Image
from pdf2image import convert_from_path
from PyPDF2 import PdfMerger, PdfReader

def compress_pdf(file_path, max_size_mb=4, initial_quality=90, initial_scale_factor=0.5, tolerance=0.1):
    if not file_path.lower().endswith('.pdf') or not os.path.exists(file_path):
        print("Invalid file or file does not exist.")
        return

    base_name = os.path.splitext(os.path.basename(file_path))[0]
    temp_dir = f"temp_{base_name}"
    os.makedirs(temp_dir, exist_ok=True)

    def get_file_size_mb(file_path):
        return os.path.getsize(file_path) / (1024 * 1024)

    try:
        pages = convert_from_path(file_path)
        scale_factor = initial_scale_factor
        quality = initial_quality
        best_file_path = None
        best_file_size = None
        min_scale_factor = 0.1
        max_scale_factor = 1.0

        # Start compression with an adaptive adjustment loop
        while True:
            merger = PdfMerger()
            for i, page in enumerate(pages):
                new_width = int(page.width * scale_factor)
                new_height = int(page.height * scale_factor)
                resized_page = page.resize((new_width, new_height), Image.LANCZOS)

                img_path = os.path.join(temp_dir, f'page_{i+1}.jpg')
                resized_page.save(img_path, 'JPEG', quality=quality)

                with Image.open(img_path) as img:
                    pdf_bytes = io.BytesIO()
                    img.save(pdf_bytes, format='PDF')
                    pdf_bytes.seek(0)
                    merger.append(PdfReader(pdf_bytes))

            compressed_file_path = f"compressedfinal_{os.path.basename(file_path)}"
            merger.write(compressed_file_path)
            merger.close()

            current_file_size = get_file_size_mb(compressed_file_path)
            print(f"Current file size: {current_file_size:.2f} MB with scale factor: {scale_factor} and quality: {quality}")

            if current_file_size <= max_size_mb:
                best_file_path = compressed_file_path
                best_file_size = current_file_size

                if current_file_size >= (1 - tolerance) * max_size_mb:
                    print(f"Final compressed PDF saved as {best_file_path} with size {best_file_size:.2f} MB")
                    break
                else:
                    # Gradually increase scale factor and try again
                    scale_factor = min(scale_factor * 1.05, max_scale_factor)
                    quality = min(quality + 5, 100)  # Try improving quality
            else:
                # Reduce the scale factor and try again
                scale_factor = max(scale_factor * 0.95, min_scale_factor)
                quality = max(quality - 5, 10)  # Reduce quality to compress more

            # Stop if adjustments can't improve further
            if scale_factor <= min_scale_factor and quality <= 10:
                print("Unable to compress further without severe quality loss.")
                break

        if best_file_path and best_file_size:
            print(f"Final compressed PDF saved as {best_file_path}")
            print(f"File size: {best_file_size:.2f} MB")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        for file in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, file))
        os.rmdir(temp_dir)

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python main.py <relative_file_path>")
    else:
        compress_pdf(sys.argv[1])