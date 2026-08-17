#!/usr/bin/env python3
"""
Standalone Qwen3-TTS demo/test CLI - independent of the RunAndRead pipeline.

Use this to generate a single audio clip and sanity-check your setup
(model download, voice, language) before running the full book pipeline
via ../make_abook_qwen3.py.

Usage:
    python cli.py "Text to speak" --voice Ryan --language English --out test.mp3
    python cli.py --list-voices
"""

import argparse
import sys

try:
    from .converter import (
        Qwen3TTSConverter, MODELS, VOICES, LANGUAGES, INSTRUCT_PRESETS,
        DEFAULT_MODEL, DEFAULT_VOICE, DEFAULT_LANGUAGE, DEFAULT_INSTRUCT_PRESET,
        DEFAULT_MAX_TOKENS, DEFAULT_RELOAD_EVERY,
        DEFAULT_TEMPERATURE, DEFAULT_TOP_P, DEFAULT_TOP_K, DEFAULT_REPETITION_PENALTY,
    )
except ImportError:
    # Allows running directly as `python cli.py` (no package context)
    from converter import (
        Qwen3TTSConverter, MODELS, VOICES, LANGUAGES, INSTRUCT_PRESETS,
        DEFAULT_MODEL, DEFAULT_VOICE, DEFAULT_LANGUAGE, DEFAULT_INSTRUCT_PRESET,
        DEFAULT_MAX_TOKENS, DEFAULT_RELOAD_EVERY,
        DEFAULT_TEMPERATURE, DEFAULT_TOP_P, DEFAULT_TOP_K, DEFAULT_REPETITION_PENALTY,
    )


def main():
    parser = argparse.ArgumentParser(description="Generate a single audio clip with Qwen3-TTS.")
    parser.add_argument("text", nargs="?", help="Text to speak")
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
                              f"drift (default: {DEFAULT_RELOAD_EVERY}; 0 disables)")
    parser.add_argument("--temperature", type=float, default=DEFAULT_TEMPERATURE,
                         help=f"Sampling temperature - lower is more consistent/less expressive across "
                              f"clips, higher is more varied (default: {DEFAULT_TEMPERATURE})")
    parser.add_argument("--top-p", type=float, default=DEFAULT_TOP_P,
                         help=f"Nucleus sampling threshold (default: {DEFAULT_TOP_P})")
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K,
                         help=f"Top-k sampling (default: {DEFAULT_TOP_K})")
    parser.add_argument("--repetition-penalty", type=float, default=DEFAULT_REPETITION_PENALTY,
                         help=f"Repetition penalty (default: {DEFAULT_REPETITION_PENALTY})")
    parser.add_argument("--seed", type=int, default=None,
                         help="Fixed RNG seed, for reproducing a prior run exactly (default: random)")
    parser.add_argument("--out", default="qwen3_test_output.mp3", help="Output file path")
    parser.add_argument("--list-voices", action="store_true", help="List available voices and languages, then exit")
    args = parser.parse_args()

    if args.list_voices:
        print("Voices (native language):")
        for voice, lang in VOICES.items():
            print(f"  {voice:<10} {lang}")
        print("\nLanguages:")
        for lang in LANGUAGES:
            print(f"  {lang}")
        print("\nModels:")
        for size, model_id in MODELS.items():
            print(f"  {size:<6} {model_id}")
        print("\nInstruct presets:")
        for name, text in INSTRUCT_PRESETS.items():
            print(f"  {name:<10} {text}")
        return

    if not args.text:
        parser.error("text is required unless --list-voices is given")

    instruct = args.instruct if args.instruct is not None else INSTRUCT_PRESETS[args.instruct_preset]
    converter = Qwen3TTSConverter(
        model=args.model, voice=args.voice, language=args.language, instruct=instruct,
        max_tokens=args.max_tokens, reload_every=args.reload_every,
        temperature=args.temperature, top_p=args.top_p, top_k=args.top_k,
        repetition_penalty=args.repetition_penalty, seed=args.seed,
    )
    output_path = converter.generate_to_file(args.text, args.out)
    print(f"✅ Saved: {output_path}")


if __name__ == "__main__":
    sys.exit(main())
