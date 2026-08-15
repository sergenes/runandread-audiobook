import os
import re
import sys
import shutil
import zipfile


def _find_parts(folder_path):
    """
    Finds the merged audio/text pairs produced by merge_audio_clips.py.

    Returns a list of (audio_path, text_path, suffix) tuples, sorted by part
    number. suffix is "" for a plain single-file merge (merged_output.mp3 /
    merged_text.json), or "_partN" for each part of a multi-part merge
    (merged_output_partN.mp3 / merged_text_partN.json).
    """
    parts = []
    for f in os.listdir(folder_path):
        m = re.fullmatch(r"merged_output(_part(\d+))?\.mp3", f)
        if not m:
            continue
        suffix = m.group(1) or ""
        text_path = os.path.join(folder_path, f"merged_text{suffix}.json")
        if os.path.isfile(text_path):
            part_num = int(m.group(2)) if m.group(2) else 0
            parts.append((os.path.join(folder_path, f), text_path, suffix, part_num))

    parts.sort(key=lambda p: p[3])
    return [(audio, text, suffix) for audio, text, suffix, _ in parts]


def _create_part_zip(folder_path, bookname, audio_source, text_source, suffix):
    zip_filename = f"{bookname}{suffix}.randr"

    # Create a temporary directory for structured files
    temp_dir = os.path.join(folder_path, f"temp{suffix}")
    book_dir = os.path.join(temp_dir, f"{bookname}{suffix}.randr")
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


def create_book_zip(folder_path):
    # Ensure the provided folder exists
    if not os.path.isdir(folder_path):
        print(f"❌ Error: The folder '{folder_path}' does not exist.")
        return

    # Extract book name from folder path
    bookname = os.path.basename(os.path.normpath(folder_path))

    parts = _find_parts(folder_path)
    if not parts:
        print(f"❌ Error: No 'merged_output(.|_partN.)mp3' / 'merged_text(.|_partN.)json' pair found in '{folder_path}'.")
        return

    for audio_source, text_source, suffix in parts:
        _create_part_zip(folder_path, bookname, audio_source, text_source, suffix)


# Entry point for command-line execution
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("❌ Usage: python script.py <folder_path>")
    else:
        create_book_zip(sys.argv[1])
