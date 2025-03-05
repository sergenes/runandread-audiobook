import os
import sys
import json
from word_tokens_tools import split_into_words, scan_next, split_into_sentences, save_text

from zyphra import ZyphraClient

API_KEY = os.getenv("ZYPHRA_API_KEY")  # Get API key from environment variable
if not API_KEY:
    raise ValueError("ZYPHRA_API_KEY is not set")

print(f"API_KEY: {API_KEY}")

client = ZyphraClient(api_key=API_KEY)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python zyphra_api.py <path_to_json>")
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

    max_word_number = 512
    sentences = [sentence.strip() for paragraph in data["text"] for sentence in split_into_sentences(paragraph) if
                 sentence.strip()]
    words = split_into_words(sentences)
    while next_window_index < 3:
        paragraph, next_word_index = scan_next(words, last_word_index, max_word_number)

        if next_word_index >= len(words):
            print(f"🎉 Finished processing {path_to_json}")
            break
        emotion_scores = {
            "happiness": 0.5,
            "neutral": 0.1,
            "sadness": 0.05,
            "disgust": 0.05,
            "fear": 0.05,
            "surprise": 0.05,
            "anger": 0.1,
            "other": 0.4
        }
        file_path = os.path.join(uid_folder, f"{next_window_index}.mp3")
        audio_data = client.audio.speech.create(
            text=paragraph,
            speaking_rate=20,
            model="zonos-v0.1-transformer",
            emotion=emotion_scores,
            mime_type="audio/mp3",
            output_path=file_path
        )

        save_text(paragraph, next_window_index, uid_folder)

        next_window_index += 1
        with open(index_file, "w") as f:
            f.write(f"{next_word_index}:{next_window_index}")

        last_word_index = next_word_index
