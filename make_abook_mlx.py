import os
import sys
import json

from mlx_audio.tts.generate import generate_audio
from word_tokens_tools import split_into_words, scan_next, split_into_sentences, save_text


def process_text(text, file_name, uid_folder):
    """Processes text using the Kokoro model and saves it as an audio file."""

    voices = ["af_heart", "bm_george", "bf_emma", "bf_isabella", "af_bella", "am_liam"]
    voice_index = 1
    # Define parameters
    text = text
    speed = 1.1
    model = "prince-canuma/Kokoro-82M"
    voice = voices[voice_index]
    lang_code = voices[voice_index][0]
    file_path = os.path.join(uid_folder, f"{file_name}")
    generate_audio(
        model_path=model,
        text=text,
        voice=voice,
        speed=speed,
        lang_code=lang_code,
        file_prefix=file_path,
        audio_format="mp3"
    )

    print(f"✅ Saved: {file_path}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: uv run python make_abook_mlx.py <path_to_json>")
        sys.exit(1)

    path_to_json = sys.argv[1]

    uid = os.path.splitext(os.path.basename(path_to_json))[0]
    uid_folder = os.path.join("audio", uid)
    os.makedirs(uid_folder, exist_ok=True)

    index_file = os.path.join(uid_folder, "last_index.txt")
    last_word_index, next_window_index = 0, 0

    if os.path.exists(index_file):
        with open(index_file, "r") as f:
            last_word_index, next_window_index = map(int, f.read().strip().split(":"))

    print(
        f"🚀 Processing {path_to_json}, resuming from index {last_word_index}; {next_window_index}")

    with open(path_to_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "text" not in data or not isinstance(data["text"], list):
        print("⚠️ No valid 'text' field found.")
        exit(1)

    max_word_number = 50
    sentences = [sentence.strip() for paragraph in data["text"] for sentence in split_into_sentences(paragraph) if
                 sentence.strip()]
    words = split_into_words(sentences)
    while True:
        paragraph, next_word_index = scan_next(words, last_word_index, max_word_number)

        if next_word_index >= len(words):
            print(f"🎉 Finished processing {path_to_json}")
            break

        process_text(paragraph, next_window_index, uid_folder)
        save_text(paragraph, next_window_index, uid_folder)

        next_window_index += 1
        with open(index_file, "w") as f:
            f.write(f"{next_word_index}:{next_window_index}")

        last_word_index = next_word_index
        words_total = len(words)
        print(f"In processing: {last_word_index} of {words_total}")
