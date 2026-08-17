"""
Self-contained Qwen3-TTS wrapper for RunAndRead-Audiobook.

Runs Qwen3-TTS entirely locally and in-process via mlx-audio (Apple's MLX
framework - Apple Silicon only). There is no server and no API key; the
only thing downloaded is the model itself, once, on first use (cached
under ~/.cache/huggingface).

This module has no dependency on anything outside this folder except the
`mlx-audio` package (see requirements.txt). It does not import from, or
require, any other RunAndRead-Audiobook file.
"""

from __future__ import annotations

import os
from typing import Dict, List, Optional, Tuple

import numpy as np
import mlx.core as mx
from mlx_audio.tts.utils import load_model as _load_mlx_model
from mlx_audio.audio_io import write as _write_audio


# ---------------------------------------------------------------------------
# Model registry
# ---------------------------------------------------------------------------
# CustomVoice models: preset speakers + emotion/style instructions.
# The 1.7B model gives noticeably better emotion/instruction control; the
# 0.6B model is smaller and faster. Both run comfortably on Apple Silicon.

MODELS: Dict[str, str] = {
    "1.7b": "mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-bf16",
    "0.6b": "mlx-community/Qwen3-TTS-12Hz-0.6B-CustomVoice-bf16",
}
DEFAULT_MODEL = "1.7b"

# Preset CustomVoice speakers. Any speaker can read any supported language;
# the mapping below is just each voice's native/best-quality language.
VOICES: Dict[str, str] = {
    "Ryan": "English",
    "Aiden": "English",
    "Vivian": "Chinese",
    "Serena": "Chinese",
    "Uncle_Fu": "Chinese",
    "Dylan": "Chinese",     # Beijing dialect
    "Eric": "Chinese",      # Sichuan dialect
    "Ono_Anna": "Japanese",
    "Sohee": "Korean",
}
DEFAULT_VOICE = "Ryan"

LANGUAGES: List[str] = [
    "Auto", "Chinese", "English", "Japanese", "Korean",
    "German", "French", "Russian", "Portuguese", "Spanish", "Italian",
]
DEFAULT_LANGUAGE = "English"

# Named instruct (style/emotion) presets - swap DEFAULT_INSTRUCT_PRESET below to
# change the default for every script that doesn't pass its own --instruct, or
# select one directly: Qwen3TTSConverter(instruct=INSTRUCT_PRESETS["steady"])
INSTRUCT_PRESETS: Dict[str, str] = {
    "dramatic": "Speak naturally and clearly, as if reading a dramatic book to an adult audience.",
    "steady": (
        "Narrate at a steady, natural audiobook pace with clear articulation and a warm, "
        "engaged tone. Use brief, natural pauses at commas and periods, and let emotion "
        "follow the text subtly, without overacting or rushing."
    ),
}
DEFAULT_INSTRUCT_PRESET = "dramatic"
DEFAULT_INSTRUCT = INSTRUCT_PRESETS[DEFAULT_INSTRUCT_PRESET]

# mlx-audio's own default (4096) is far too generous: at the tokenizer's 12Hz
# rate that's ~340s of audio. Qwen3-TTS occasionally fails to predict a stop
# token (a known autoregressive-decode failure mode) and, left unbounded,
# will generate several minutes of trailing silence/noise after the real
# speech instead of stopping. 2048 (~170s) still comfortably covers even a
# slow, dramatic reading of our largest chunks, while sharply limiting how
# much damage a single bad decode can do.
DEFAULT_MAX_TOKENS = 2048

# If a generated clip is way longer than the text could plausibly justify,
# it's almost certainly a runaway decode rather than genuine narration -
# retry (generation is stochastic, so a retry usually succeeds) instead of
# silently shipping a mostly-silent clip.
MAX_GENERATION_ATTEMPTS = 3
MAX_SECONDS_PER_WORD = 0.9  # generous even for slow, dramatic pacing
MIN_SANITY_SECONDS = 5.0    # flat slack so short chunks aren't flagged unfairly

# Observed directly: a single long-lived process making many consecutive
# generation calls (e.g. converting a full book in one run) sees the
# runaway-decode failure rate climb dramatically over time - one real run
# hit it on 71/92 chunks after several hours, while the exact same texts
# succeeded cleanly (4/4) in a fresh process. Reloading the model
# periodically is cheap (well under a second once weights are cached) and
# resets whatever internal state accumulates, so it's done proactively
# rather than only on failure.
DEFAULT_RELOAD_EVERY = 10  # reload after this many raw generation calls (attempts count, not just successes)

# CustomVoice pitch, pacing, and energy are themselves autoregressively
# sampled tokens, not fixed per speaker - so mlx-audio's defaults
# (temperature=0.9, top_p=1.0) let two calls with the identical voice and
# instruct land on audibly different "performances" (pitch contour, pace,
# energy). That reads as random drift between chunks in a book-length run.
# Tightening sampling here trades a little spontaneity for a narrator that
# reads consistently from chunk to chunk.
DEFAULT_TEMPERATURE = 0.6
DEFAULT_TOP_P = 0.85
DEFAULT_TOP_K = 50
DEFAULT_REPETITION_PENALTY = 1.05


class Qwen3TTSConverter:
    """Loads a Qwen3-TTS MLX model once, then generates narration audio from text."""

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        voice: str = DEFAULT_VOICE,
        language: str = DEFAULT_LANGUAGE,
        instruct: str = DEFAULT_INSTRUCT,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        reload_every: int = DEFAULT_RELOAD_EVERY,
        temperature: float = DEFAULT_TEMPERATURE,
        top_p: float = DEFAULT_TOP_P,
        top_k: int = DEFAULT_TOP_K,
        repetition_penalty: float = DEFAULT_REPETITION_PENALTY,
        seed: Optional[int] = None,
    ):
        if model not in MODELS:
            raise ValueError(f"Unknown model '{model}'. Choices: {sorted(MODELS)}")
        if language not in LANGUAGES:
            raise ValueError(f"Unknown language '{language}'. Choices: {LANGUAGES}")

        self.model_id = MODELS[model]
        self.voice = voice
        self.language = language
        self.instruct = instruct
        self.max_tokens = max_tokens
        self.reload_every = reload_every
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.repetition_penalty = repetition_penalty
        # Seeded once (see generate()) rather than per-call, so a whole book
        # draws from one continuous, reproducible RNG stream instead of each
        # chunk landing on an unrelated random draw. None picks a fresh
        # random base seed at first use; pass an explicit int to reproduce a
        # prior run exactly.
        self.seed = seed
        self._seeded = False
        self._model = None
        self._calls_since_load = 0

    def _load(self):
        print(f"[qwen3_tts] Loading {self.model_id} ... (first run downloads several GB)")
        self._model = _load_mlx_model(self.model_id)
        self._calls_since_load = 0
        print(f"[qwen3_tts] Model loaded (sample rate {self._model.sample_rate} Hz)")

    @property
    def model(self):
        """Lazily loads the MLX model on first use (not at construction time)."""
        if self._model is None:
            self._load()
        return self._model

    @property
    def sample_rate(self) -> int:
        return self.model.sample_rate

    def generate(self, text: str) -> Tuple[np.ndarray, int]:
        """Generate narration audio for `text`. Returns (audio_samples, sample_rate).

        Automatically retries if the model appears to have failed to stop
        (see MAX_SECONDS_PER_WORD) - a rare but real failure mode of
        autoregressive TTS decoding.
        """
        word_count = max(1, len(text.split()))
        sanity_limit = word_count * MAX_SECONDS_PER_WORD + MIN_SANITY_SECONDS

        audio, sample_rate, duration = None, None, None
        for attempt in range(1, MAX_GENERATION_ATTEMPTS + 1):
            if self.reload_every and self._calls_since_load >= self.reload_every:
                print(f"[qwen3_tts] Reloading model after {self._calls_since_load} generations "
                      f"(counters apparent decode-stability drift on long runs)")
                self._load()
            self._calls_since_load += 1

            if not self._seeded:
                if self.seed is None:
                    self.seed = int.from_bytes(os.urandom(4), "big")
                mx.random.seed(self.seed)
                self._seeded = True
                print(f"[qwen3_tts] RNG seed: {self.seed} (fixed for this run)")
            elif attempt > 1:
                # Retry after a runaway decode: force a genuinely fresh,
                # uncorrelated draw so we don't just repeat the same failure.
                mx.random.seed(int.from_bytes(os.urandom(4), "big"))

            results = list(self.model.generate_custom_voice(
                text=text,
                speaker=self.voice,
                language=self.language,
                instruct=self.instruct,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
                top_k=self.top_k,
                repetition_penalty=self.repetition_penalty,
            ))
            if not results:
                raise RuntimeError("Qwen3-TTS returned no audio")

            # Long text may come back as multiple segments - join them into one clip.
            segments = [r.audio for r in results]
            audio = mx.concatenate(segments, axis=0) if len(segments) > 1 else segments[0]
            sample_rate = results[0].sample_rate
            duration = audio.shape[0] / sample_rate
            mx.clear_cache()

            if duration <= sanity_limit:
                return np.array(audio), sample_rate

            print(
                f"[qwen3_tts] Generated {duration:.1f}s of audio for {word_count} words "
                f"(expected under {sanity_limit:.1f}s) - looks like a runaway decode, "
                f"retrying ({attempt}/{MAX_GENERATION_ATTEMPTS})..."
            )

        print(f"[qwen3_tts] Still {duration:.1f}s after {MAX_GENERATION_ATTEMPTS} attempts - using it anyway")
        return np.array(audio), sample_rate

    def generate_to_file(self, text: str, output_path: str, audio_format: str = "mp3") -> str:
        """Generate narration audio for `text` and write it directly to `output_path`."""
        audio, sample_rate = self.generate(text)
        _write_audio(output_path, audio, sample_rate, format=audio_format)
        return output_path


if __name__ == "__main__":
    # Minimal smoke test: `python converter.py`
    converter = Qwen3TTSConverter()
    saved_path = converter.generate_to_file(
        "Hello from Run and Read. This is a quick Qwen3 text to speech test.",
        "qwen3_smoke_test.mp3",
    )
    print(f"Saved: {saved_path}")
