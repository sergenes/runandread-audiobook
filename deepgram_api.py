import os
import sys
import json
from word_tokens_tools import split_into_words, scan_next, split_into_sentences, save_text
from deepgram import (
    DeepgramClient,
    SpeakOptions
)

API_KEY = os.getenv("DEEPGRAM_API_KEY")  # Get API key from environment variable
if not API_KEY:
    raise ValueError("API_KEY is not set")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python deepgram_api.py <path_to_json>")
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

    print(f"🚀 Processing {path_to_json}, resuming from index {last_word_index}; {next_window_index}")

    with open(path_to_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "text" not in data or not isinstance(data["text"], list):
        print("⚠️ No valid 'text' field found.")
        exit(1)

    max_word_number = 128
    sentences = [sentence.strip() for paragraph in data["text"] for sentence in split_into_sentences(paragraph) if
                 sentence.strip()]
    words = split_into_words(sentences)
    deepgram = DeepgramClient(api_key=API_KEY)
    options = SpeakOptions(
        model="aura-asteria-en",
    )
    while next_window_index < 3:
        paragraph, next_word_index = scan_next(words, last_word_index, max_word_number)

        if next_word_index >= len(words):
            print(f"🎉 Finished processing {path_to_json}")
            break

        file_path = os.path.join(uid_folder, f"{next_window_index}.mp3")
        options = SpeakOptions(
            model="aura-asteria-en",
        )
        response = deepgram.speak.rest.v("1").save(file_path, {"text": paragraph}, options)
        print(response.to_json(indent=4))

        save_text(paragraph, next_window_index, uid_folder)

        next_window_index += 1
        with open(index_file, "w") as f:
            f.write(f"{next_word_index}:{next_window_index}")

        last_word_index = next_word_index
