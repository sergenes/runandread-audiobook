import os
import sys
import json
from pydub import AudioSegment
import textwrap


def merge_audio_with_text(folder_path, file_format='mp3', output_filename='merged_output.mp3'):
    """
    Merges audio files in sequence and stores corresponding text with timestamps in a JSON file.

    :param folder_path: Path to the folder containing audio and text files.
    :param file_format: File format to merge ('wav' or 'mp3').
    :param output_filename: Name of the merged output file.
    """
    merged_audio = AudioSegment.silent(duration=0)  # Start with an empty audio segment
    text_data = []  # List to hold text with timestamps

    index = 0
    current_time = 0  # Tracks the starting time of each audio clip

    while True:
        audio_file = os.path.join(folder_path, f"{index}.{file_format}")
        text_file = os.path.join(folder_path, f"{index}.txt")

        if not os.path.exists(audio_file):
            print(f"*****\nFile does not exist: {audio_file}")
            break  # Stop if no more audio files exist

        text = ""
        if os.path.exists(text_file):
            with open(text_file, 'r', encoding='utf-8') as f:
                text = f.read().strip()
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
            print(f"Error processing {audio_file}: {e}")

        index += 1  # Move to the next file

    if not text_data and len(merged_audio) == 0:
        print("No valid audio or text files found.")
        return

    # Save merged audio
    output_path = os.path.join(folder_path, output_filename)
    merged_audio.export(output_path, format=file_format)

    # Save merged text with timestamps in JSON
    json_output_path = os.path.join(folder_path, "merged_text.json")
    with open(json_output_path, 'w', encoding='utf-8') as f:
        json.dump(text_data, f, ensure_ascii=False, indent=4)

    print(f"\n✅ Merged audio saved as: {output_path}")
    print(f"✅ Merged text JSON saved as: {json_output_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python merge_audio_clips.py <path_to_abook> <format[wav|mp3]>")
        sys.exit(1)

    path_to_abook = sys.argv[1]
    format_choice = sys.argv[2].strip().lower()

    if format_choice not in ['wav', 'mp3']:
        print("Invalid format. Defaulting to wav.")
        format_choice = 'wav'

    merge_audio_with_text(path_to_abook, format_choice)
