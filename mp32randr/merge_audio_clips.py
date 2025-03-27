import sys
import os
from pydub import AudioSegment
from tqdm import tqdm  # ✅ Import tqdm for progress bar
from pydub.utils import which

# Ensure ffmpeg is set correctly
AudioSegment.converter = which("ffmpeg")


def merge_audio_clips_limited(folder_path, file_format="mp3", max_duration=360 * 60 * 1000):
    """
    Merges audio files into multiple segments to avoid struct errors.

    :param folder_path: Path to folder containing audio files.
    :param file_format: Audio format to process ('mp3' or 'wav').
    :param max_duration: Maximum duration per output file (default: 1 hour).
    """
    merged_audio = AudioSegment.silent(duration=0)  # Empty audio segment
    total_files = len([f for f in os.listdir(folder_path) if f.endswith(f".{file_format}")])

    index = 0
    file_count = 0  # Track how many merged files are created
    output_audio = AudioSegment.silent(duration=0)  # Current merged chunk

    with tqdm(total=total_files, desc="Merging Audio", unit="file") as progress_bar:
        while True:
            audio_file = os.path.join(folder_path, f"{index}_000.{file_format}")
            if not os.path.exists(audio_file):
                audio_file = os.path.join(folder_path, f"{index}.{file_format}")

            if not os.path.exists(audio_file):
                print(f"*****\nFile does not exist: {audio_file}")
                break  # Stop when no more files exist

            try:
                sound = AudioSegment.from_file(audio_file, format=file_format)

                # Check if adding this file exceeds max_duration
                if len(output_audio) + len(sound) > max_duration:
                    # Save current merged chunk before starting a new one
                    output_path = os.path.join(folder_path, f"merged_output{file_count}.mp3")
                    output_audio.export(output_path, format="mp3", parameters=["-b:a", "192k"])
                    print(f"✅ Merged audio saved as: {output_path}")

                    # Start a new segment
                    file_count += 1
                    output_audio = AudioSegment.silent(duration=0)

                output_audio += sound  # Add new audio file

            except Exception as e:
                print(f"❌ Error processing {audio_file}: {e}")

            index += 1  # Move to the next file
            progress_bar.update(1)

    # Save the last chunk if it contains audio
    if len(output_audio) > 0:
        output_path = os.path.join(folder_path, f"merged_output{file_count}.mp3")
        output_audio.export(output_path, format="mp3", parameters=["-b:a", "192k"])
        print(f"✅ Final merged audio saved as: {output_path}")


def merge_audio_clips(folder_path, file_format="mp3"):
    """
    Merges audio files in sequence and saves the output.
    """
    merged_audio = AudioSegment.silent(duration=0)  # Start with an empty audio segment
    total_files = len([f for f in os.listdir(folder_path) if f.endswith(f".{file_format}")])

    index = 0
    with tqdm(total=total_files, desc="Merging Audio", unit="file") as progress_bar:
        while True:
            audio_file = os.path.join(folder_path, f"{index}_000.{file_format}")
            if not os.path.exists(audio_file):
                audio_file = os.path.join(folder_path, f"{index}.{file_format}")

            if not os.path.exists(audio_file):
                print(f"*****\nFile does not exist: {audio_file}")
                break  # Stop if no more audio files exist

            try:
                sound = AudioSegment.from_file(audio_file, format=file_format)
                merged_audio += sound  # Append audio
            except Exception as e:
                print(f"❌ Error processing {audio_file}: {e}")

            index += 1
            progress_bar.update(1)

    if len(merged_audio) == 0:
        print("❌ No valid audio files found.")
        return

    # Define output path
    output_path = os.path.join(folder_path, "merged_output.mp3")

    # ✅ Use proper codec for MP3
    merged_audio.export(output_path, format="mp3", codec="libmp3lame")

    print(f"✅ Merged audio saved as: {output_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python merge_audio_clips.py <path_to_abook> <format[wav|mp3]>")
        sys.exit(1)

    path_to_abook = sys.argv[1]
    format_choice = sys.argv[2].strip().lower()

    if format_choice not in ['mp3']:
        print("Invalid format. Defaulting to mp3.")
        format_choice = 'mp3'

    merge_audio_clips(
        folder_path=path_to_abook,
        file_format=format_choice
    )
