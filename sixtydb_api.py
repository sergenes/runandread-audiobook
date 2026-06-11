import os
import sys
import json
import base64
import requests
from word_tokens_tools import split_into_words, scan_next, split_into_sentences, save_text

API_KEY = os.getenv("SIXTYDB_API_KEY")  # Get API key from environment variable
if not API_KEY:
    raise ValueError("SIXTYDB_API_KEY is not set")

# --- 60db (https://api.60db.ai) configuration -------------------------------
BASE_URL = "https://api.60db.ai"
SYNTHESIZE_URL = f"{BASE_URL}/tts-synthesize"
VOICES_URL = f"{BASE_URL}/myvoices"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

# Voice / synthesis settings. Run `python sixtydb_api.py --voices` to list the
# voice_ids available on your account, then paste one in here.
VOICE_ID = "default-voice"
ENHANCE = True       # audio quality improvement
SPEED = 1.0          # 0.5 - 2.0
STABILITY = 50       # 0 - 100 (lower = more expressive)
SIMILARITY = 75      # 0 - 100 (voice match closeness)
OUTPUT_FORMAT = "mp3"  # mp3 | wav | ogg | flac

MAX_WORD_NUMBER = 128  # words per audio chunk (matches deepgram_api.py)
MAX_WINDOWS = 3        # stop after this many chunks (demo cap; raise for full book)


def list_voices():
    """Print the voices available on the account (GET /myvoices)."""
    response = requests.get(VOICES_URL, headers=HEADERS, timeout=60)
    response.raise_for_status()
    body = response.json()
    voices = body.get("data", [])
    if not voices:
        print("No voices found on this account.")
        return
    for v in voices:
        labels = v.get("labels", {}) or {}
        print(
            f"{v.get('voice_id')}  |  {v.get('name')}  "
            f"|  {v.get('model')}  "
            f"|  {labels.get('language_name', '')} "
            f"{labels.get('gender', '')} {labels.get('accent', '')}"
        )


def synthesize(text, file_path):
    """Synthesize `text` with 60db and save the audio to `file_path`."""
    payload = {
        "text": text,
        "voice_id": VOICE_ID,
        "enhance": ENHANCE,
        "speed": SPEED,
        "stability": STABILITY,
        "similarity": SIMILARITY,
        "output_format": OUTPUT_FORMAT,
    }
    response = requests.post(SYNTHESIZE_URL, headers=HEADERS, json=payload, timeout=120)
    response.raise_for_status()
    body = response.json()

    if not body.get("success"):
        raise RuntimeError(f"60db TTS failed: {body.get('message')}")

    audio_bytes = base64.b64decode(body["audio_base64"])
    with open(file_path, "wb") as f:
        f.write(audio_bytes)

    # Drop the heavy base64 payload before logging the response metadata.
    body.pop("audio_base64", None)
    return body


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--voices":
        list_voices()
        sys.exit(0)

    if len(sys.argv) != 2:
        print("Usage: python sixtydb_api.py <path_to_json>")
        print("       python sixtydb_api.py --voices")
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

    sentences = [sentence.strip() for paragraph in data["text"] for sentence in split_into_sentences(paragraph) if
                 sentence.strip()]
    words = split_into_words(sentences)

    while next_window_index < MAX_WINDOWS:
        paragraph, next_word_index = scan_next(words, last_word_index, MAX_WORD_NUMBER)

        if next_word_index >= len(words):
            print(f"🎉 Finished processing {path_to_json}")
            break

        file_path = os.path.join(uid_folder, f"{next_window_index}.{OUTPUT_FORMAT}")
        response = synthesize(paragraph, file_path)
        print(json.dumps(response, indent=4))

        save_text(paragraph, next_window_index, uid_folder)

        next_window_index += 1
        with open(index_file, "w") as f:
            f.write(f"{next_word_index}:{next_window_index}")

        last_word_index = next_word_index
