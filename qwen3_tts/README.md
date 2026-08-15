# qwen3_tts

Self-contained [Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS) engine for RunAndRead-Audiobook, running entirely **locally, in-process, on Apple Silicon** via [mlx-audio](https://github.com/Blaizzy/mlx-audio) (Apple's MLX framework). No server, no API key, no cloud calls.

This folder has no dependency on anything else in this repository or on any other project — the only external dependency is the `mlx-audio` Python package (see `requirements.txt`), and the only thing downloaded is the model itself, once, on first use (cached under `~/.cache/huggingface`).

## Requirements

- **Apple Silicon Mac** (M1/M2/M3/M4) — MLX does not run on Intel Macs, Windows, or Linux.
- Python 3.10+
- Internet connection for the first run only (model download, a few GB, cached afterward)

## How to add support

```bash
cd qwen3_tts
pip install -r requirements.txt
```

That's it — no separate server, no extra environment, no account/API key. The model downloads automatically the first time it's used.

## How to use it

### Standalone (generate one test clip)

```bash
cd qwen3_tts
python cli.py "Hello from Run and Read." --voice Ryan --language English --out test.mp3
python cli.py "шла саша по шоссе и сосала сушку" --language Russian --out test.mp3
```

List available voices, languages, and models:

```bash
python cli.py --list-voices
```

### As a library

```python
from qwen3_tts import Qwen3TTSConverter

converter = Qwen3TTSConverter(voice="Ryan", language="English")
converter.generate_to_file("Hello from Run and Read.", "output.mp3")

# Or get raw samples instead of writing straight to a file:
audio, sample_rate = converter.generate("Hello from Run and Read.")
```

The model loads lazily on first use (not when `Qwen3TTSConverter` is constructed), so you can build a converter up front and only pay the load cost when you actually generate the first clip.

### As part of the RunAndRead pipeline

This is how the rest of the repo uses it — see the root [README.md](../README.md#qwen3-tts-support) for the full pipeline. In short:

```bash
# From the repo root, with qwen3_tts's requirements installed
python make_abook_qwen3.py library/pg11.json --voice Ryan --language English
python merge_audio_clips.py library/pg11.json audio/pg11 mp3
python make_randr.py audio/pg11/
```

## Voices

Any voice can read any supported language; the table below is each voice's native/highest-quality language.

| Voice      | Native language |
|------------|-----------------|
| `Ryan`     | English |
| `Aiden`    | English |
| `Vivian`   | Chinese |
| `Serena`   | Chinese |
| `Uncle_Fu` | Chinese |
| `Dylan`    | Chinese (Beijing dialect) |
| `Eric`     | Chinese (Sichuan dialect) |
| `Ono_Anna` | Japanese |
| `Sohee`    | Korean |

## Languages

`Auto`, `Chinese`, `English`, `Japanese`, `Korean`, `German`, `French`, `Russian`, `Portuguese`, `Spanish`, `Italian`

`Auto` lets the model infer the language from the text itself — useful for mixed-language books.

## Models

| Flag value | Model | Notes |
|------------|-------|-------|
| `1.7b` (default) | `mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-bf16` | Best quality and emotion/style control |
| `0.6b` | `mlx-community/Qwen3-TTS-12Hz-0.6B-CustomVoice-bf16` | Smaller, faster, slightly lower quality |

Select with `--model 0.6b` on either `cli.py` or `make_abook_qwen3.py`, or `Qwen3TTSConverter(model="0.6b")` as a library.

## Instruct presets

The `instruct` parameter steers Qwen3-TTS's tone, pacing, and emotional delivery. Named presets in `INSTRUCT_PRESETS` (`qwen3_tts/converter.py`) make it easy to try alternatives without retyping the full text:

| Preset | Text |
|--------|------|
| `dramatic` (default) | "Speak naturally and clearly, as if reading a dramatic book to an adult audience." |
| `steady` | "Narrate at a steady, natural audiobook pace with clear articulation and a warm, engaged tone. Use brief, natural pauses at commas and periods, and let emotion follow the text subtly, without overacting or rushing." |

Select one with `--instruct-preset steady`, or pass fully custom text with `--instruct "..."` (which overrides `--instruct-preset`). To change the default for every script, edit `DEFAULT_INSTRUCT_PRESET` in `converter.py`. As a library: `Qwen3TTSConverter(instruct=INSTRUCT_PRESETS["steady"])`.

To add your own preset, just add an entry to the `INSTRUCT_PRESETS` dict.

## Sampling & consistency

CustomVoice's pitch, pacing, and energy are themselves autoregressively sampled tokens, not
fixed per speaker — so two calls with the identical voice and instruct can still land on
audibly different "performances" if sampling is loose. `Qwen3TTSConverter` tightens
mlx-audio's defaults for this reason, and exposes the knobs on both `cli.py` and
`make_abook_qwen3.py`:

| Flag | Default | Effect |
|------|---------|--------|
| `--temperature` | `0.6` | Lower = more consistent/less expressive delivery across clips. Raise (e.g. `0.75`) if it starts sounding flat. |
| `--top-p` | `0.85` | Nucleus sampling threshold; lower narrows the token choices further. |
| `--top-k` | `50` | Top-k sampling. |
| `--repetition-penalty` | `1.05` | Discourages the model from repeating itself. |
| `--seed` | random | Fixes the RNG for reproducibility. |

The RNG is seeded **once per run** (not before every clip), so a whole book draws from one
continuous, reproducible stream instead of each chunk landing on an unrelated random draw —
a retry after a runaway decode still forces a fresh, uncorrelated seed so it doesn't just
repeat the same failure. `make_abook_qwen3.py` additionally **persists the chosen seed** to
`audio/<book>/qwen3_seed.txt`, so interrupting and resuming a multi-hour/multi-day conversion
continues on the same seed instead of drifting to a new one partway through.

**Even with a fixed seed and tightened sampling, an individual clip can still land on an
odd/emphatic delivery** — most often on very short chunks. Each chunk (especially under
`epub_to_json.py --split-sentences`, where a chunk can be as short as two or three words) is
synthesized as a **completely independent, stateless call**: the model never sees the
sentence before or after it, so a short, terse, dramatic-sounding fragment (e.g. Russian
"Нас качает.") combined with the `dramatic` instruct preset can occasionally get an
exclamatory reading despite ending in a period. If that's happening a lot:
- Try `--instruct-preset steady`, which explicitly asks for delivery "without overacting."
- Lower `--temperature` further (e.g. `0.4`).
- Avoid over-splitting: `--split-sentences` chunks on every `. ! ? : ;`, which can produce
  very short fragments from clause-heavy prose; not using it (or merging very short chunks
  with a neighbor before generation) gives the model more context to anchor its delivery.

## Troubleshooting

**`ImportError` for `mlx` / `mlx_audio`?**
- Confirm you're on Apple Silicon: `python3 -c "import platform; print(platform.machine())"` should print `arm64`
- Re-run `pip install -r requirements.txt` from this folder

**First run seems to hang?**
- That's the one-time model download (a few GB) — check your internet connection. Progress isn't shown live; it prints `[qwen3_tts] Model loaded` when done.

**Slow generation?**
- Try `--model 0.6b` for faster (slightly lower quality) generation
- Generation speed and memory are stable and bounded on Apple Silicon (no known leak, unlike the PyTorch/MPS Gradio-server path this module deliberately avoids)

**Getting the "few words then silence" failure constantly, even with retries and `--reload-every`?**
- Check which `mlx-audio` you're actually running: `pip show mlx-audio`. If it says `Editable project location: ...`, you likely have an old local clone installed (e.g. from following this repo's original Kokoro setup, `pip install -e ~/projects/voice/mlx-audio`) instead of the current PyPI release - this can be a much older, less stable version even if the reported version number looks recent. Fix it in whichever environment actually runs your scripts:
  ```bash
  pip uninstall -y mlx-audio
  pip install -U mlx-audio
  pip show mlx-audio  # confirm no "Editable project location" line, and version >= 0.4.8
  ```
- Double check you're fixing the right environment - if your shell prompt shows a name in parentheses (e.g. a conda env), that's not just cosmetic; run `which python3` and `pip show mlx-audio` from the same shell you actually launch `make_abook_qwen3.py` from.

**A clip has the right opening words then goes silent for a long time?**
- This is a known autoregressive-decode failure mode: the model occasionally fails to predict a stop token and keeps generating (mostly silence) until it hits the token cap. `Qwen3TTSConverter.generate()` guards against this automatically — it sanity-checks output duration against the input word count and retries (generation is stochastic, so a retry almost always succeeds) — but if you still see it, lower `--max-tokens` (default `2048`, ~170s of audio) to bound the worst case further, e.g. `--max-tokens 1024`.

## Extending

This module currently exposes Qwen3-TTS's **CustomVoice** mode (preset speakers + style instruction). Qwen3-TTS also supports **Voice Clone** (clone a voice from a reference audio sample) and **Voice Design** (describe a voice in words) — not wired up here to keep the initial integration focused, but `mlx-audio`'s `model.generate(...)` / `model.generate_voice_design(...)` APIs support them directly if you want to extend `converter.py`.

## Credits

- **[Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS)** — the underlying voice model, by the Qwen team at Alibaba Cloud
- **[mlx-audio](https://github.com/Blaizzy/mlx-audio)** — the MLX inference engine this module wraps
