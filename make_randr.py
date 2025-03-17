import os
import sys
import shutil
import zipfile


def create_book_zip(folder_path):
    # Ensure the provided folder exists
    if not os.path.isdir(folder_path):
        print(f"❌ Error: The folder '{folder_path}' does not exist.")
        return

    # Extract book name from folder path
    bookname = os.path.basename(os.path.normpath(folder_path))
    zip_filename = f"{bookname}.randr"

    # Define input file paths
    audio_source = os.path.join(folder_path, "merged_output.mp3")
    text_source = os.path.join(folder_path, "merged_text.json")

    # Validate source files exist
    if not os.path.isfile(audio_source) or not os.path.isfile(text_source):
        print(f"❌ Error: Required files ('merged_output.mp3' or 'merged_text.json') not found in '{folder_path}'.")
        return

    # Create a temporary directory for structured files
    temp_dir = os.path.join(folder_path, "temp")
    book_dir = os.path.join(temp_dir, bookname)
    book_dir = f"{book_dir}.randr"
    os.makedirs(book_dir, exist_ok=True)

    # Copy files to structured directory
    audio_dest = os.path.join(book_dir, "audio.mp3")
    text_dest = os.path.join(book_dir, "book.json")
    shutil.copy(audio_source, audio_dest)
    shutil.copy(text_source, text_dest)

    # Create the ZIP archive
    zip_path = os.path.join(os.path.dirname(folder_path), zip_filename)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, temp_dir)
                zipf.write(file_path, arcname)

    # Clean up temporary directory
    shutil.rmtree(temp_dir)

    print(f"✅ Successfully created '{zip_filename}' in '{os.path.dirname(folder_path)}'.")


# Entry point for command-line execution
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("❌ Usage: python script.py <folder_path>")
    else:
        create_book_zip(sys.argv[1])
