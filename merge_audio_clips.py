import os
import sys
import json
from pydub import AudioSegment
import textwrap


import os
import json
import textwrap
from pydub import AudioSegment
from tqdm import tqdm  # ✅ Import tqdm for progress bar


def merge_audio_with_text(folder_path,
                          file_format='mp3',
                          author='unknown',
                          title='unknown'):
    """
    Merges audio files in sequence and stores corresponding text with timestamps in a JSON file.

    :param folder_path: Path to the folder containing audio and text files.
    :param file_format: File format to merge ('wav' or 'mp3').
    :param author: Book's author.
    :param title: Book's title.
    """
    merged_audio = AudioSegment.silent(duration=0)  # Start with an empty audio segment
    book_data = {
        "title": title,
        "author": author,
        "language": "en_GB",
        "rate": 1.0,
        "voice": "George",
        "model": "Kokoro-82M",
        "book_source": "www.gutenberg.org"
    }
    text_data = []  # List to hold text with timestamps

    # ✅ Count total number of mp3 files for progress bar
    total_files = len([f for f in os.listdir(folder_path) if f.endswith(f".{file_format}")])

    index = 0
    current_time = 0  # Tracks the starting time of each audio clip

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
                sound = AudioSegment.from_file(audio_file, format=file_format)
                duration = len(sound)  # Duration of current audio clip in milliseconds

                # Store text with the starting timestamp
                if text:
                    text_data.append({"start_time_ms": current_time, "text": text})

                merged_audio += sound  # + AudioSegment.silent(duration=500)  # Add 0.5s silence between segments
                current_time += duration  # + 500  # Update the start time for the next clip
            except Exception as e:
                print(f"❌ Error processing {audio_file}: {e}")

            index += 1  # Move to the next file
            progress_bar.update(1)  # ✅ Update progress bar

    if not text_data and len(merged_audio) == 0:
        print("❌ No valid audio or text files found.")
        return

    # Save merged audio
    output_path = os.path.join(folder_path, "merged_output.mp3")
    merged_audio.export(output_path, format=file_format)

    # Save merged text with timestamps in JSON
    json_output_path = os.path.join(folder_path, "merged_text.json")

    book_data["text"] = text_data
    with open(json_output_path, 'w', encoding='utf-8') as file:
        json.dump(book_data, file, ensure_ascii=False, indent=4)

    print(f"✅ Merged audio saved as: {output_path}")
    print(f"✅ Merged text JSON saved as: {json_output_path}")


# def merge_audio_with_text(folder_path,
#                           file_format='mp3',
#                           author='unknown',
#                           title='unknown'):
#     """
#     Merges audio files in sequence and stores corresponding text with timestamps in a JSON file.
#
#     :param folder_path: Path to the folder containing audio and text files.
#     :param file_format: File format to merge ('wav' or 'mp3').
#     :param author: Book's author.
#     :param title: Book's title.
#     """
#     merged_audio = AudioSegment.silent(duration=0)  # Start with an empty audio segment
#     book_data = {
#         "title": title,
#         "author": author,
#         "language": "en_GB",
#         "rate": 1.0,
#         "voice": "George",
#         "model": "Kokoro-82M",
#         "book_source": "www.gutenberg.org"
#     }
#     text_data = []  # List to hold text with timestamps
#
#     index = 0
#     current_time = 0  # Tracks the starting time of each audio clip
#
#     while True:
#         audio_file = os.path.join(folder_path, f"{index}.{file_format}")
#         text_file = os.path.join(folder_path, f"{index}.txt")
#
#         if not os.path.exists(audio_file):
#             print(f"*****\nFile does not exist: {audio_file}")
#             break  # Stop if no more audio files exist
#
#         text = ""
#         if os.path.exists(text_file):
#             with open(text_file, 'r', encoding='utf-8') as file:
#                 text = file.read().strip()
#                 text = "\n".join(textwrap.wrap(text))
#
#         try:
#             sound = AudioSegment.from_file(audio_file, format=file_format)
#             duration = len(sound)  # Duration of current audio clip in milliseconds
#
#             # Store text with the starting timestamp
#             if text:
#                 text_data.append({"start_time_ms": current_time, "text": text})
#
#             merged_audio += sound  # + AudioSegment.silent(duration=500)  # Add 0.5s silence between segments
#             current_time += duration  # + 500  # Update the start time for the next clip
#         except Exception as e:
#             print(f"Error processing {audio_file}: {e}")
#
#         index += 1  # Move to the next file
#
#     if not text_data and len(merged_audio) == 0:
#         print("No valid audio or text files found.")
#         return
#
#     # Save merged audio
#     output_path = os.path.join(folder_path, "merged_output.mp3")
#     merged_audio.export(output_path, format=file_format)
#
#     # Save merged text with timestamps in JSON
#     json_output_path = os.path.join(folder_path, "merged_text.json")
#
#     book_data["text"] = text_data
#     with open(json_output_path, 'w', encoding='utf-8') as file:
#         json.dump(book_data, file, ensure_ascii=False, indent=4)
#
#     print(f"✅ Merged audio saved as: {output_path}")
#     print(f"✅ Merged text JSON saved as: {json_output_path}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python merge_audio_clips.py <path_to_json> <path_to_abook> <format[wav|mp3]>")
        sys.exit(1)

    path_to_json = sys.argv[1]
    path_to_abook = sys.argv[2]
    format_choice = sys.argv[3].strip().lower()

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
        title=data["title"]
    )
