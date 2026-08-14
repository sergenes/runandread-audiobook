import os
import sys
import json
import subprocess
import tempfile
import textwrap
from pydub import AudioSegment
from tqdm import tqdm  # ✅ Import tqdm for progress bar


def _write_part(folder_path, file_format, audio_files, text_data, book_data, suffix):
    """
    Concatenates audio_files (via ffmpeg's concat demuxer, stream copy) into a
    single output file and writes its matching timestamped-text JSON.
    """
    output_path = os.path.join(folder_path, f"merged_output{suffix}.{file_format}")
    json_output_path = os.path.join(folder_path, f"merged_text{suffix}.json")

    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as list_file:
        for f in audio_files:
            escaped = os.path.abspath(f).replace("'", "'\\''")
            list_file.write(f"file '{escaped}'\n")
        list_path = list_file.name

    try:
        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_path, "-c", "copy", output_path],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
    finally:
        os.remove(list_path)

    book_data = dict(book_data, text=text_data)
    with open(json_output_path, 'w', encoding='utf-8') as file:
        json.dump(book_data, file, ensure_ascii=False, indent=4)

    print(f"✅ Merged audio saved as: {output_path}")
    print(f"✅ Merged text JSON saved as: {json_output_path}")


def merge_audio_with_text(folder_path,
                          file_format='mp3',
                          author='unknown',
                          title='unknown',
                          max_minutes_per_part=None):
    """
    Merges audio files in sequence and stores corresponding text with timestamps in a JSON file.

    Concatenation is done via ffmpeg's concat demuxer (stream copy) instead of
    loading every clip into one in-memory pydub AudioSegment and exporting it.
    pydub's export() always serializes to a WAV container first (32-bit size
    field, ~4GB raw-PCM limit) even when the target format is mp3, so long
    audiobooks (many hours of raw PCM) overflow it with a struct.error.

    When max_minutes_per_part is set, clips are grouped into multiple parts so
    that no single output file exceeds that duration (and therefore doesn't
    balloon to a multi-GB file). Each part gets its own
    merged_output_partN.<format> / merged_text_partN.json pair, with
    timestamps restarting at 0 for that part. When left unset (or the whole
    book fits within one part), the original single-file naming
    (merged_output.<format> / merged_text.json) is preserved.

    :param folder_path: Path to the folder containing audio and text files.
    :param file_format: File format to merge ('wav' or 'mp3').
    :param author: Book's author.
    :param title: Book's title.
    :param max_minutes_per_part: Max duration (in minutes) per output part. None/0 = single file.
    """
    book_data_base = {
        "title": title,
        "author": author,
        "language": "en_GB",
        "rate": 1.0,
        "voice": "George",
        "model": "Kokoro-82M",
        "book_source": "www.gutenberg.org"
    }

    max_duration_ms = int(max_minutes_per_part * 60 * 1000) if max_minutes_per_part else None

    # ✅ Count total number of mp3 files for progress bar
    total_files = len([f for f in os.listdir(folder_path) if f.endswith(f".{file_format}")])

    parts = []  # Finalized parts: [{"audio_files": [...], "text_data": [...]}, ...]
    part_audio_files = []
    part_text_data = []
    part_duration_ms = 0  # Tracks the starting time of each clip within the current part

    index = 0

    # ✅ Use tqdm for progress bar
    with tqdm(total=total_files, desc="Merging Audio", unit="file") as progress_bar:
        while True:
            text_file = os.path.join(folder_path, f"{index}.txt")
            audio_file = os.path.join(folder_path, f"{index}_000.{file_format}")
            if not os.path.exists(audio_file):
                audio_file = os.path.join(folder_path, f"{index}.{file_format}")

            if not os.path.exists(audio_file):
                print(f"*****\nFile does not exist: {audio_file}")
                break  # Stop if no more audio files exist

            text = ""
            if os.path.exists(text_file):
                with open(text_file, 'r', encoding='utf-8') as file:
                    text = file.read().strip()
                    text = "\n".join(textwrap.wrap(text))

            try:
                duration = len(AudioSegment.from_file(audio_file, format=file_format))

                # Start a new part if this clip would push the current one past the limit
                if (max_duration_ms and part_audio_files
                        and part_duration_ms + duration > max_duration_ms):
                    parts.append({"audio_files": part_audio_files, "text_data": part_text_data})
                    part_audio_files = []
                    part_text_data = []
                    part_duration_ms = 0

                # Store text with the starting timestamp (relative to the current part)
                if text:
                    part_text_data.append({"start_time_ms": part_duration_ms, "text": text})

                part_audio_files.append(audio_file)
                part_duration_ms += duration  # Update the start time for the next clip
            except Exception as e:
                print(f"❌ Error processing {audio_file}: {e}")

            index += 1  # Move to the next file
            progress_bar.update(1)  # ✅ Update progress bar

    if part_audio_files:
        parts.append({"audio_files": part_audio_files, "text_data": part_text_data})

    if not parts:
        print("❌ No valid audio or text files found.")
        return

    total_parts = len(parts)
    width = len(str(total_parts))

    for i, part in enumerate(parts, start=1):
        if total_parts == 1:
            suffix = ""
            book_data = dict(book_data_base)
        else:
            suffix = f"_part{i:0{width}d}"
            book_data = dict(book_data_base, title=f"{title} (Part {i} of {total_parts})")
            book_data["part"] = i
            book_data["total_parts"] = total_parts

        _write_part(folder_path, file_format, part["audio_files"], part["text_data"], book_data, suffix)


if __name__ == "__main__":
    if len(sys.argv) not in (4, 5):
        print("Usage: python merge_audio_clips.py <path_to_json> <path_to_abook> <format[wav|mp3]> [max_minutes_per_part]")
        sys.exit(1)

    path_to_json = sys.argv[1]
    path_to_abook = sys.argv[2]
    format_choice = sys.argv[3].strip().lower()

    max_minutes_per_part = None
    if len(sys.argv) == 5:
        try:
            max_minutes_per_part = float(sys.argv[4])
            if max_minutes_per_part <= 0:
                max_minutes_per_part = None
        except ValueError:
            print(f"⚠️ Invalid max_minutes_per_part value: {sys.argv[4]!r}. Ignoring (single output file).")

    with open(path_to_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "title" not in data or "author" not in data:
        print("⚠️ No valid 'text' field found.")
        exit(1)

    if format_choice not in ['wav', 'mp3']:
        print("Invalid format. Defaulting to wav.")
        format_choice = 'wav'

    merge_audio_with_text(
        folder_path=path_to_abook,
        file_format=format_choice,
        author=data["author"],
        title=data["title"],
        max_minutes_per_part=max_minutes_per_part
    )
