import argparse
import os
import sys
import shutil
import zipfile


def create_book_zip(folder_path):
    # Ensure the provided folder exists
    if not os.path.isdir(folder_path):
        print(f"❌ Error: The folder '{folder_path}' does not exist.")
        return

    # Save merged text with timestamps in JSON
    json_output_path = os.path.join(folder_path, "merged_text.json")

    # Extract book name from folder path
    bookname = os.path.basename(os.path.normpath(folder_path))
    zip_filename = f"{bookname}.randr"
    audio_source = os.path.join(folder_path, "merged_output.mp3")

    # Create a temporary directory for structured files
    temp_dir = os.path.join(folder_path, "temp")
    book_dir = os.path.join(temp_dir, bookname)
    book_dir = f"{book_dir}.randr"
    os.makedirs(book_dir, exist_ok=True)

    # Copy files to structured directory
    audio_dest = os.path.join(book_dir, "audio.mp3")
    text_dest = os.path.join(book_dir, "book.json")
    shutil.copy(audio_source, audio_dest)
    shutil.copy(json_output_path, text_dest)

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


def parse_args():
    parser = argparse.ArgumentParser(
        description="Transcribe mp3 audio using whisper model and make an audiobook in RANDR format.")
    parser.add_argument(
        "--path",
        type=str,
        default=None,
        help="Path folder with the merged_output.mp3 and merged_text.json files",
    )
    # python mp3_to_randr.py --path ../audio/lra --title "Лунная Радуга. Часть Первая." --author "Сергей Павлов" --language ru_RU --voice Арестович
    args = parser.parse_args()

    if args.path is None:
        if not sys.stdin.isatty():
            args.path = sys.stdin.read().strip()
        else:
            print("Please enter the path to the mp3 file")
            args.text = input("> ").strip()

    return args


# Entry point for command-line execution
if __name__ == "__main__":
    args = parse_args()
    create_book_zip(folder_path=args.path)
