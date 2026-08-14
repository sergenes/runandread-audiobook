import os
import sys
import json
import argparse

from qwen3_tts.converter import (
    Qwen3TTSConverter, MODELS, VOICES, LANGUAGES, INSTRUCT_PRESETS,
    DEFAULT_MODEL, DEFAULT_VOICE, DEFAULT_LANGUAGE, DEFAULT_INSTRUCT_PRESET,
    DEFAULT_MAX_TOKENS, DEFAULT_RELOAD_EVERY,
)
from word_tokens_tools import build_chunk_list, next_chunk, save_text


def process_text(converter, text, file_name, uid_folder):
    """Generates audio for `text` using Qwen3-TTS and saves it as an mp3 file."""
    file_path = os.path.join(uid_folder, f"{file_name}.mp3")
    converter.generate_to_file(text, file_path, audio_format="mp3")
    print(f"✅ Saved: {file_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate RunAndRead audiobook clips using Qwen3-TTS "
                    "(runs entirely locally on Apple Silicon via MLX - see qwen3_tts/README.md).",
    )
    parser.add_argument("path_to_json", help="Path to the JSON book file (see epub_to_json.py)")
    parser.add_argument("--voice", default=DEFAULT_VOICE, choices=sorted(VOICES),
                         help=f"Speaker voice (default: {DEFAULT_VOICE})")
    parser.add_argument("--language", default=DEFAULT_LANGUAGE, choices=LANGUAGES,
                         help=f"Language (default: {DEFAULT_LANGUAGE})")
    parser.add_argument("--model", default=DEFAULT_MODEL, choices=sorted(MODELS),
                         help=f"Model size (default: {DEFAULT_MODEL})")
    parser.add_argument("--instruct-preset", default=DEFAULT_INSTRUCT_PRESET, choices=sorted(INSTRUCT_PRESETS),
                         help=f"Named style/emotion instruction (default: {DEFAULT_INSTRUCT_PRESET})")
    parser.add_argument("--instruct", default=None,
                         help="Custom style/emotion instruction text, overrides --instruct-preset")
    parser.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS,
                         help=f"Generation length cap, in speech tokens at 12Hz (default: {DEFAULT_MAX_TOKENS})")
    parser.add_argument("--reload-every", type=int, default=DEFAULT_RELOAD_EVERY,
                         help=f"Reload the model after this many generations, to counter long-run decode "
                              f"drift observed on multi-hour book conversions (default: {DEFAULT_RELOAD_EVERY}; 0 disables)")
    args = parser.parse_args()
    instruct = args.instruct if args.instruct is not None else INSTRUCT_PRESETS[args.instruct_preset]

    path_to_json = args.path_to_json

    uid = os.path.splitext(os.path.basename(path_to_json))[0]
    uid_folder = os.path.join("audio", uid)
    os.makedirs(uid_folder, exist_ok=True)

    index_file = os.path.join(uid_folder, "last_index.txt")
    last_word_index, next_window_index = 0, 0

    if os.path.exists(index_file):
        with open(index_file, "r") as f:
            last_word_index, next_window_index = map(int, f.read().strip().split(":"))

    print(
        f"🚀 Processing {path_to_json} with Qwen3-TTS "
        f"(voice={args.voice}, language={args.language}, model={args.model}), "
        f"resuming from index {last_word_index}; {next_window_index}"
    )

    with open(path_to_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "text" not in data or not isinstance(data["text"], list):
        print("⚠️ No valid 'text' field found.")
        sys.exit(1)

    converter = Qwen3TTSConverter(
        model=args.model, voice=args.voice, language=args.language, instruct=instruct,
        max_tokens=args.max_tokens, reload_every=args.reload_every,
    )

    max_word_number = 50
    chunks, sentence_mode = build_chunk_list(data)
    while True:
        if last_word_index >= len(chunks):
            print(f"🎉 Finished processing {path_to_json}")
            break

        paragraph, next_word_index = next_chunk(chunks, sentence_mode, last_word_index, max_word_number)

        process_text(converter, paragraph, next_window_index, uid_folder)
        save_text(paragraph, next_window_index, uid_folder)

        next_window_index += 1
        with open(index_file, "w") as f:
            f.write(f"{next_word_index}:{next_window_index}")

        last_word_index = next_word_index
        chunks_total = len(chunks)
        print(f"In processing: {last_word_index} of {chunks_total}")
