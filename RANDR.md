# RunAndRead-Audiobook

<div align="center">
<img src="assets/ic_launcher.png"
     alt="Run & Read"
     style="width: 256px;
            height: auto;
            object-position: center top;">
</div>

---

## Overview

**RunAndRead-Audiobook** is an open-source pipeline for creating high-quality audiobooks using **open-source AI models**. It leverages **MLX-AUDIO** (via either **make_abook_mlx.py** for Kokoro-82M, or **make_abook_qwen3.py** for the self-contained, multi-voice/multi-language [Qwen3-TTS engine](qwen3_tts/README.md)) to generate **RANDR format audiobooks**, which can be played in the **Run & Read** app for Android and iOS.

**Ensure your app version supports RANDR format:**
- **Android**: Version **1.5 (6)** or later.
- **iOS**: Version **1.6 (18)** or later.

**Apps**  
**App Store**: [Run & Read for Apple Devices](https://apps.apple.com/us/app/run-read-listen-on-the-go/id6741396289)  
**Google Play**: [Run & Read for Android](https://play.google.com/store/apps/details?id=com.answersolutions.runandread)

**QR codes**

<div align="center">
<img src="assets/apple_runandread_qr_code.png" width="150px"> &nbsp;&nbsp;&nbsp; <img src="assets/google_runandread_qr_code.png" width="150px">
</div>

---

## Features

- Convert **EPUB** to **JSON** for structured text extraction.
- Manually verify extracted text to remove unwanted sections.
- Generate TTS audio using **MLX-AUDIO (Kokoro-82M TTS model)**, or the self-contained **Qwen3-TTS** engine (9 voices, 10 languages - see [qwen3_tts/README.md](qwen3_tts/README.md)).
- Merge audio clips into a single audiobook file.
- Package audio and JSON into **RANDR format** for playback.
- Compatible with **Run & Read** apps on **iOS** and **Android**.
- Optimized for **Apple Silicon (M-series processors)**.

---

## Dependencies

- **Python 3.9+**
- **[MLX-AUDIO](https://github.com/Blaizzy/mlx-audio)** (TTS framework optimized for macOS/Apple M-series chips)
- **ffmpeg** (for audio processing)
- **EbookLib** (EPUB parsing)

---

## Installation

### **1) Set Up MLX-AUDIO**
```bash
pip install -e ~/projects/voice/mlx-audio
```

Ensure `espeak-ng` is installed to prevent Kokoro-82M from skipping words:
```bash
echo 'export ESPEAK_DATA_PATH=/opt/homebrew/share/espeak-ng-data' >> ~/.zshrc
source ~/.zshrc
```

### **2) Set Up ffmpeg**

- **macOS**: `brew install ffmpeg`
- **Ubuntu**: `sudo apt install ffmpeg`
- **Windows**: [Download from ffmpeg.org](https://ffmpeg.org/download.html) and add to system PATH.

---

## Pipeline Workflow

### **Step 1: Convert EPUB to JSON**
```bash
python epub_to_json.py epub/book.epub library/book.json 0
```
Manually inspect the output and rerun with adjusted parameters if necessary.
Check the terminal output to find how many lines should be skipped, then rerun the script with the number of the first
line to keep:

```bash
python epub_to_json.py epub/pg11.epub library/pg11.json 10
```

This ensures that the book starts from the correct position, e.g.:

> **10: CHAPTER I. Down the Rabbit-Hole**

Add `--split-sentences` to split each paragraph into individual sentence/clause chunks
(on `. ! ? : ;`) instead of one JSON entry per paragraph — small local TTS models
generate more reliably on short, single-sentence chunks:

```bash
python epub_to_json.py epub/pg11.epub library/pg11.json 10 --split-sentences
```

### **Step 2: Generate TTS Audio using MLX-AUDIO**

Kokoro-82M (single voice, requires the MLX-AUDIO setup above):
```bash
python make_abook_mlx.py library/book.json
```

Or Qwen3-TTS (self-contained, own `qwen3_tts/requirements.txt`, no extra setup beyond that - 9 voices, 10 languages):
```bash
cd qwen3_tts && pip install -r requirements.txt && cd ..
python make_abook_qwen3.py library/book.json --voice Ryan --language English
```
See [qwen3_tts/README.md](qwen3_tts/README.md) for the full voice/language list and options.

### **Step 3: Merge Audio Clips**
```bash
python merge_audio_clips.py library/book.json audio/book mp3
```

### **Step 4: Package as RANDR Format**
```bash
python make_randr.py audio/book/
```

📌 **Transfer the `.randr` file to your mobile device and open it in the Run & Read app!**

---

## Pipeline Schema

```mermaid
flowchart LR
    A[EPUB] --> B[epub_to_json.py]
    B --> C[JSON book]
    C --> D[make_abook_mlx.py / make_abook_qwen3.py]
    D --> E[Audio clips]
    E --> F[merge_audio_clips.py]
    F --> G[make_randr.py]
    C --> G
    G --> H[RANDR file]
```

## Project Structure

```
runandread-audiobook/
├── epub_to_json.py      # Extracts text from EPUB into JSON
├── make_abook_mlx.py    # Generates audio using MLX-AUDIO (Kokoro-82M)
├── make_abook_qwen3.py  # Generates audio using Qwen3-TTS (self-contained, see qwen3_tts/)
├── merge_audio_clips.py # Merges TTS-generated clips
├── make_randr.py        # Packages audio & JSON into RANDR format
├── qwen3_tts/            # Self-contained Qwen3-TTS engine (own README + requirements.txt)
├── assets/              # Icons, QR codes, and app store assets
├── epub/                # EPUB source files
├── audio/               # Generated audio files
├── library/             # JSON book structure
├── audiobooks/          # RANDR audiobooks samples
     ├── pg2680.randr    # Meditations by Emperor of Rome Marcus Aurelius
     ├── pg20203.randr   # Autobiography of Benjamin Franklin
├── README.md            # Documentation
├── CHANGELOG.md         # Notable changes
└── requirements.txt     # Dependencies
```

---

## Contributions

We welcome contributions! Open an **issue** or submit a **pull request**.

---

## References

- **[MLX-AUDIO](https://github.com/Blaizzy/mlx-audio)** - TTS & STS library optimized for Apple M-series.
- **[Kokoro-TTS](https://huggingface.co/spaces/hexgrad/Kokoro-TTS)** - Open-weight TTS model.
- **[Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS)** - Multilingual, multi-voice TTS model, integrated self-contained in [`qwen3_tts/`](qwen3_tts/).
- **[EbookLib](https://pypi.org/project/EbookLib/)** - EPUB parsing.
- **[Project Gutenberg](https://www.gutenberg.org)** - Free eBooks.

---

## Contact

- **[Sergey N](https://www.linkedin.com/in/sergey-neskoromny/)**

---

## License

This project is open-source under the **MIT License**.
