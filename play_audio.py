import os
import sys
from pydub import AudioSegment
import simpleaudio as sa
import textwrap


def merge_audio_with_text(folder_path, file_format='mp3', output_filename='merged_output.mp3'):
    """
    Merges audio files in sequence and prints corresponding text files.

    :param folder_path: Path to the folder containing audio and text files.
    :param file_format: File format to merge ('wav' or 'mp3').
    :param output_filename: Name of the merged output file.
    """
    merged_audio = AudioSegment.silent(duration=0)  # Start with an empty audio segment
    full_text = []

    index = 0
    while True:
        audio_file = os.path.join(folder_path, f"{index}.{file_format}")
        text_file = os.path.join(folder_path, f"{index}.txt")

        if not os.path.exists(audio_file):
            print(f"*****\nFile does not exist: {audio_file}")
            break  # Stop if no more audio files exist

        if os.path.exists(text_file):
            with open(text_file, 'r', encoding='utf-8') as f:
                text = f.read().strip()
                f.close()
                full_text.append(f"\n--- {audio_file} ---\n" + "\n".join(textwrap.wrap(text, width=MAX_LINE_WIDTH)))

        try:
            sound = AudioSegment.from_file(audio_file, format=file_format)
            merged_audio += sound + AudioSegment.silent(duration=500)  # Add 0.5s silence between segments
        except Exception as e:
            print(f"Error processing {audio_file}: {e}")

        index += 1  # Move to the next file

    if len(full_text) == 0 and len(merged_audio) == 0:
        print("No valid audio or text files found.")
        return

    # Save merged audio
    output_path = os.path.join(folder_path, output_filename)
    merged_audio.export(output_path, format=file_format)

    # Save merged text
    text_output_path = os.path.join(folder_path, "merged_text.txt")
    with open(text_output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(full_text))

    print(f"\n✅ Merged audio saved as: {output_path}")
    print(f"✅ Merged text saved as: {text_output_path}")


MAX_LINE_WIDTH = 80  # Adjust this to fit your screen width


def play_audio_with_text(folder_path, file_format='wav'):
    """
    Plays audio files in sequence and prints corresponding text files.

    :param folder_path: Path to the folder containing audio and text files.
    :param file_format: File format to play ('wav' or 'mp3').
    """
    index = 0
    while True:
        audio_file = os.path.join(folder_path, f"{index}.{file_format}")
        text_file = os.path.join(folder_path, f"{index}.txt")

        if not os.path.exists(audio_file):
            print("*****")
            print(f"File does not exist: {audio_file}")
            break  # Stop if no more audio files exist

        if os.path.exists(text_file):
            with open(text_file, 'r', encoding='utf-8') as f:
                text = f.read().strip()
                f.close()
                print(f"\n--- Playing {audio_file} ---")
                print("\n".join(textwrap.wrap(text, width=MAX_LINE_WIDTH)))  # Wraps text into multiple lines
                print("-------------------------------")

            # Load and play the audio file
            try:
                sound = AudioSegment.from_file(audio_file, format=file_format)
                playback = sa.play_buffer(sound.raw_data, num_channels=sound.channels,
                                          bytes_per_sample=sound.sample_width, sample_rate=sound.frame_rate)
                playback.wait_done()  # Wait until the audio finishes playing
            except Exception as e:
                print(f"Error playing {audio_file}: {e}")

        index += 1  # Move to the next file

    print("All audio files played.")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python play_audio.py <path_to_abook> <format[wav|mp3]>")
        sys.exit(1)

    path_to_abook = sys.argv[1]
    format_choice = sys.argv[2].strip().lower()

    if format_choice not in ['wav', 'mp3']:
        print("Invalid format. Defaulting to wav.")
        format_choice = 'wav'

    play_audio_with_text(path_to_abook, format_choice)
