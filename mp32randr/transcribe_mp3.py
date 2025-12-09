import argparse
import os
import sys
import shutil
import zipfile
import mlx_whisper
from huggingface_hub import snapshot_download
import json
from datetime import datetime

# Define model path
model_path = "../models/large"


# https://huggingface.co/mlx-community/whisper-large-v3-mlx
# https://huggingface.co/mlx-community/whisper-tiny.en-mlx-q4


def transcribe_mp3(folder_path, title, author, language, voice, granularity="paragraph"):
    # Ensure the provided folder exists
    if not os.path.isdir(folder_path):
        print(f"❌ Error: The folder '{folder_path}' does not exist.")
        return

    # Ensure the model is downloaded
    if not os.path.exists(model_path):
        print(f"Downloading model: {model_path} ...")
        snapshot_download(repo_id="mlx-community/whisper-large-v3-mlx", local_dir=model_path)
        print("Model download complete.")

    # Save merged text with timestamps in JSON
    json_output_path = os.path.join(folder_path, "merged_text.json")

    # Extract book name from folder path
    bookname = os.path.basename(os.path.normpath(folder_path))
    zip_filename = f"{bookname}.randr"

    book_data = {
        "title": title,
        "author": author,
        "language": language,
        "rate": 1.0,
        "voice": voice,
        "model": "unknown",
        "book_source": "unknown"
    }
    text_data = []
    current_segment = []
    segment_start_time = None

    # Define the desired number of words per segment
    WORDS_PER_SEGMENT = 100

    # Define input file paths
    audio_source = os.path.join(folder_path, "merged_output.mp3")
    output = mlx_whisper.transcribe(audio_source, path_or_hf_repo=model_path, word_timestamps=True)
    if granularity == 'paragraph':
        # Iterate through transcription segments  (timestamp per paragraph)
        for segment in output["segments"]:
            for word_info in segment["words"]:
                if segment_start_time is None:
                    segment_start_time = int(word_info["start"] * 1000)  # Set start time for the segment

                # Add word to the current segment
                current_segment.append(word_info)

                # When we reach 100 words, save the segment
                if len(current_segment) >= WORDS_PER_SEGMENT:
                    segment_end_time = int(current_segment[-1]["end"] * 1000)  # Set end time as last word's time
                    segment_text = " ".join([w["word"] for w in current_segment])  # Combine words into a paragraph

                    text_data.append({
                        "start_time_ms": segment_start_time,
                        "end_time_ms": segment_end_time,
                        "text": segment_text
                    })

                    # Reset for next segment
                    current_segment = []
                    segment_start_time = None

                    # If there are remaining words, save the last segment
        if current_segment:
            segment_end_time = int(current_segment[-1]["end"] * 1000)
            segment_text = " ".join([w["word"] for w in current_segment])

            text_data.append({
                "start_time_ms": segment_start_time,
                "end_time_ms": segment_end_time,
                "text": segment_text
            })
    else:
        # Iterate over all segments and their words (timestamp per word)
        for segment in output["segments"]:
            for word_info in segment["words"]:
                text_data.append({
                    "start_time_ms": int(word_info["start"] * 1000),  # Convert seconds to milliseconds
                    "end_time_ms": int(word_info["end"] * 1000),  # Convert seconds to milliseconds
                    "text": word_info["word"]
                })

    # # Print or process the text_data list
    # print(text_data)
    book_data["text"] = text_data
    with open(json_output_path, 'w', encoding='utf-8') as file:
        json.dump(book_data, file, ensure_ascii=False, indent=4)

    print(f"✅ Merged text JSON saved as: {json_output_path}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Transcribe mp3 audio using whisper model and save transcription into a json file.")
    parser.add_argument(
        "--path",
        type=str,
        default=None,
        help="Path folder with the merged_output.mp3 file",
    )
    parser.add_argument(
        "--title",
        type=str,
        default="Unknown",
        help="The audiobook title",
    )
    parser.add_argument(
        "--author",
        type=str,
        default="Unknown",
        help="The audiobook author",
    )
    parser.add_argument(
        "--language",
        type=str,
        default="en_US",
        help="The audiobook language, in format en_US",
    )
    parser.add_argument(
        "--voice",
        type=str,
        default="Unknown",
        help="The narator name, a model or an Actor/Actress",
    )

    parser.add_argument(
        "--granularity",
        type=str,
        default="paragraph",
        help="The timestamp granularity in resulted json",
    )
    # python transcribe_mp3.py --path ../audio/lra --title "Лунная Радуга. Часть Первая." --author "Сергей Павлов" --language ru_RU --voice Арестович
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
    start_time = datetime.now()
    print("Process started at:", start_time.strftime("%Y-%m-%d %H:%M:%S"))
    transcribe_mp3(
        folder_path=args.path,
        title=args.title,
        author=args.author,
        language=args.language,
        voice=args.voice,
        granularity=args.granularity
    )
    end_time = datetime.now()
    print("Process ended at:", end_time.strftime("%Y-%m-%d %H:%M:%S"))

    # Optional: Print duration
    duration = end_time - start_time
    print("Total duration:", duration)
