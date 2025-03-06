import os
import sys
import json
import torch
import torchaudio

from zonos.model import Zonos
from zonos.conditioning import make_cond_dict
from zonos.utils import DEFAULT_DEVICE as device

from word_tokens_tools import split_into_words, scan_next, split_into_sentences, save_text


def initialize_model(training_sample="assets/exampleaudio.mp3"):
    """Loads the Zonos model and prepares the speaker embedding."""
    model = Zonos.from_pretrained("Zyphra/Zonos-v0.1-transformer", device=device)
    wav, sampling_rate = torchaudio.load(training_sample)
    speaker = model.make_speaker_embedding(wav, sampling_rate)
    return model, speaker


def load_audio_prefix(file_path="assets/silence_100ms.wav"):
    """Loads an optional audio prefix for speech synthesis."""
    if file_path and os.path.exists(file_path):
        wav, sr = torchaudio.load(file_path)
        wav = wav.mean(0, keepdim=True)
        wav = model.autoencoder.preprocess(wav, sr)
        return model.autoencoder.encode(wav.unsqueeze(0).to(device, dtype=torch.float32))
    return None


def process_text(model, speaker, text, file_name, uid_folder):
    """Processes text using the Zonos model and saves it as an audio file."""
    cond_dict = make_cond_dict(
        text=text,
        speaker=speaker,
        language="en-us",
        emotion=[0.5, 0.1, 0.05, 0.05, 0.05, 0.05, 0.1, 0.4],
        speaking_rate=17.0,
        pitch_std=40.0,
        dnsmos_ovrl=5.0,
        vqscore_8=[0.85] * 8
    )
    conditioning = model.prepare_conditioning(cond_dict)
    codes = model.generate(
        prefix_conditioning=conditioning,
        audio_prefix_codes=audio_prefix_codes,
        max_new_tokens=86 * 30,
        sampling_params={"top_p": 0, "top_k": 0, "min_p": 0, "linear": 0.5, "conf": 0.4, "quad": 0}
    )
    wavs = model.autoencoder.decode(codes).cpu().detach()

    for fmt in ["wav", "flac", "mp3"]:
        file_path = os.path.join(uid_folder, f"{file_name}.{fmt}")
        torchaudio.save(file_path, wavs[0], model.autoencoder.sampling_rate, format=fmt)
        print(f"✅ Saved: {file_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: uv run python make_abook.py <path_to_json> <path_to_training_sample>")
        sys.exit(1)

    path_to_json = sys.argv[1]
    training_sample = sys.argv[2]

    uid = os.path.splitext(os.path.basename(path_to_json))[0]
    uid_folder = os.path.join("audio", uid)
    os.makedirs(uid_folder, exist_ok=True)

    index_file = os.path.join(uid_folder, "last_index.txt")
    last_word_index, next_window_index = 0, 0

    if os.path.exists(index_file):
        with open(index_file, "r") as f:
            last_word_index, next_window_index = map(int, f.read().strip().split(":"))

    print(f"🚀 Processing {path_to_json}, training_sample {training_sample}, resuming from index {last_word_index}; {next_window_index}")

    with open(path_to_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "text" not in data or not isinstance(data["text"], list):
        print("⚠️ No valid 'text' field found.")
        exit(1)

    global model, audio_prefix_codes
    model, speaker = initialize_model(training_sample=training_sample)
    audio_prefix_codes = load_audio_prefix()

    max_word_number = 70
    sentences = [sentence.strip() for paragraph in data["text"] for sentence in split_into_sentences(paragraph) if
                 sentence.strip()]
    words = split_into_words(sentences)
    while True:
        paragraph, next_word_index = scan_next(words, last_word_index, max_word_number)

        if next_word_index >= len(words):
            print(f"🎉 Finished processing {path_to_json}")
            break

        process_text(model, speaker, paragraph, next_window_index, uid_folder)
        save_text(paragraph, next_window_index, uid_folder)

        next_window_index += 1
        with open(index_file, "w") as f:
            f.write(f"{next_word_index}:{next_window_index}")

        last_word_index = next_word_index
