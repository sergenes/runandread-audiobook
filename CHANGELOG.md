# Changelog

All notable changes to RunAndRead-Audiobook are documented here.

## 2026-08-15

### Added
- **`epub_to_json.py --split-sentences`**: splits each paragraph into individual sentence/clause chunks (on `. ! ? : ;`) before saving, instead of one JSON entry per paragraph. Small local TTS models generate more reliably on short, single-sentence input than on long multi-sentence paragraphs. `make_abook*.py` scripts detect this automatically from the new `split_by_sentence` JSON field (`word_tokens_tools.build_chunk_list()`/`next_chunk()`) and synthesize one clip per sentence instead of re-merging everything into word-count windows - falls back to the original word-window behavior byte-for-byte when the flag is absent, so existing resume checkpoints stay valid.
- **`merge_audio_clips.py` multi-part output**: pass a max-minutes-per-part argument to split a long book's merged audio into several `merged_output_partN.<format>` / `merged_text_partN.json` files instead of one multi-GB one. `make_randr.py` now packages each part into its own `.randr` file automatically.
- **Qwen3-TTS sampling/consistency controls**: `--temperature`, `--top-p`, `--top-k`, `--repetition-penalty`, `--seed` exposed on both `make_abook_qwen3.py` and `qwen3_tts/cli.py` (defaults tightened to `temperature=0.6, top_p=0.85` for more consistent narration - see [Sampling & consistency](qwen3_tts/README.md#sampling--consistency)). The RNG is now seeded once per run instead of before every clip, and `make_abook_qwen3.py` persists the seed to `audio/<book>/qwen3_seed.txt` so an interrupted multi-hour/multi-day conversion resumes on the same seed rather than drifting to a new one partway through.

### Fixed
- **`merge_audio_clips.py` crashed (`struct.error`) on long audiobooks.** It loaded every clip into one in-memory pydub `AudioSegment` and exported it; pydub's `export()` always serializes to a WAV container first (32-bit size field, ~4GB raw-PCM limit) even when the target format is mp3, so a long enough book overflowed it partway through the merge. Rewrote the merge to stream clips through ffmpeg's concat demuxer (stream copy) instead, which has no such limit and is significantly faster.
- **`epub_to_json.py`'s `clean_text()` was silently stripping `:`, `;`, and dashes to spaces**, discarding punctuation that matters for both TTS prosody and the new sentence-splitting feature.

## 2026-08-12

### Added
- **Qwen3-TTS support**, fully self-contained in [`qwen3_tts/`](qwen3_tts/) — its own dependencies (`qwen3_tts/requirements.txt`), its own README, no dependency on any other project. Runs entirely locally and in-process on Apple Silicon via [mlx-audio](https://github.com/Blaizzy/mlx-audio); no server, no API key.
  - New root script `make_abook_qwen3.py`, matching the existing `make_abook_mlx.py` pattern (resumable, same chunking, same output naming) so it drops into the existing pipeline unchanged.
  - New standalone test CLI `qwen3_tts/cli.py` for generating a single clip without touching the book pipeline.
  - **9 preset voices across 10 languages**, selectable per run (`--voice`, `--language`), instead of a single hardcoded voice/language.
  - **Instruct presets** (`--instruct-preset dramatic|steady`, or custom text via `--instruct`) for tuning narration tone/pacing, with named constants in `qwen3_tts/converter.py` for easy extension.
  - Selectable model size (`--model 1.7b|0.6b`).
- **Automatic decode-stability safeguards** for Qwen3-TTS generation (`qwen3_tts/converter.py`):
  - Duration sanity-check with automatic retry: if a generated clip is far longer than its word count could justify (a real Qwen3-TTS failure mode - the model occasionally fails to predict a stop token and generates mostly silence), it's detected and retried automatically instead of silently saved.
  - Generation length capped at 2048 tokens (~170s) instead of the library default of 4096 (~340s), bounding the worst case of any single bad decode.
  - Fresh RNG reseed before every generation attempt, so retries can't correlate with a prior failure.
  - **Periodic model reload** (`--reload-every`, default 10 generations): a long-running single process converting a full book was observed to have a dramatically higher decode-failure rate over time (measured: 81% of chunks corrupted after several hours in one real run, vs. 0% for the identical content in a fresh process). Reloading the model periodically (cheap - well under a second once weights are cached) resets whatever internal state was accumulating.
- `CHANGELOG.md` (this file).

### Fixed
- **Last chunk of every book was silently dropped.** `word_tokens_tools.scan_next`'s caller pattern checked "are we done" using the *result* of the next scan rather than the *current* position, so whenever a chunk's word-window landed exactly on the end of the text, it never got processed. This was duplicated (copy-pasted) across all six TTS engine scripts - `make_abook.py`, `make_abook_mlx.py`, `make_abook_qwen3.py`, `make_abook_open_ai.py`, `zyphra_api.py`, `deepgram_api.py` - and is now fixed identically in all of them (check `last_word_index` before scanning, not `next_word_index` after).
- **`epub_to_json.py` printed a false "✅ Successfully converted" message on preview-only runs.** Running with `skip_lines=0` (the documented first pass, meant only to preview extracted sections so you can find the right cutoff) never wrote a file, but the success message printed unconditionally anyway. It now prints an accurate preview notice with the next command to run instead.

### Notes
- If Qwen3-TTS generation keeps failing even with retries and reload, check `pip show mlx-audio` in the *exact* environment running your scripts - an old editable install (e.g. `pip install -e ~/projects/voice/mlx-audio`, left over from the original Kokoro setup) can be a much older, less stable version than the current PyPI release even when everything else looks correctly configured. See [qwen3_tts/README.md Troubleshooting](qwen3_tts/README.md#troubleshooting).
