import os
import re
import mlx_whisper

# Define model path (set to your local or HF repo path)
model_path = "../models/large"

# Folder containing the MP3 files (current folder)
folder_path = os.getcwd()

# Regex pattern to match file names like part_1.mp3, part_2.mp3, etc.
pattern = re.compile(r"part_(\d+)\.mp3", re.IGNORECASE)

def convert_to_srt(transcription, output_file):
    """Convert transcription result with word timestamps into SRT format."""
    with open(output_file, "w", encoding="utf-8") as f:
        for i, segment in enumerate(transcription["segments"], start=1):
            start = segment["start"]
            end = segment["end"]
            text = segment["text"].strip()

            start_time = format_timestamp(start)
            end_time = format_timestamp(end)

            f.write(f"{i}\n{start_time} --> {end_time}\n{text}\n\n")

def format_timestamp(seconds):
    """Convert seconds to SRT timestamp format."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"

def main():
    for filename in sorted(os.listdir(folder_path)):
        match = pattern.match(filename)
        if match:
            part_number = match.group(1)
            audio_path = os.path.join(folder_path, filename)
            print(f"Transcribing {filename}...")

            result = mlx_whisper.transcribe(audio_path, path_or_hf_repo=model_path, word_timestamps=True)

            output_srt = os.path.join(folder_path, f"part_{part_number}.srt")
            convert_to_srt(result, output_srt)
            print(f"Saved subtitles to {output_srt}")

if __name__ == "__main__":
    main()
