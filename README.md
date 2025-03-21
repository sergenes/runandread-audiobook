# RunAndRead-Audiobook

<div align="center">
<img src="assets/ic_launcher.png" 
     alt="Alt text" 
     style="width: 256px;
            height: auto;
            object-position: center top;">
</div>

---

## 📖 Overview

RunAndRead-Audiobook is an open-source project aimed at generating high-quality text-to-speech (TTS) audiobooks using
open-source models like **Zyphra/Zonos**.

The ultimate goal is to make **Run & Read**, the audiobook player app, sound more natural by using high-quality voices.
Currently, it relies on the standard voices embedded in **Apple** and **Android** devices, which are still not perfect.
Starting from Android v1.5 (6) and iOS v1.6 (18), Run & Read supports MP3 audiobooks generated using the RANDR pipeline in this repository. [See instructions here](https://github.com/sergenes/runandread-audiobook/blob/main/RANDR.md).

**Download and try the apps for free!**  

🍏 **App Store**: [Ran & Read for Apple Devices](https://apps.apple.com/us/app/run-read-listen-on-the-go/id6741396289)  
🤖 **Google Play**: [Ran & Read for Android](https://play.google.com/store/apps/details?id=com.answersolutions.runandread)


📱 **Scan QR Codes to Download:**

<div align="center">
<img src="assets/apple_runandread_qr_code.png" width="150px"> &nbsp;&nbsp;&nbsp; <img src="assets/google_runandread_qr_code.png" width="150px">
</div>
---

## 📢 New: Create Audiobooks with AI (RANDR Format)

Generate **high-quality audiobooks** at home using open-source AI models! We’ve built a **pipeline** using **MLX-AUDIO** to create audiobooks in the **RANDR format**, optimized for playback in the **Run & Read** app.

📖 **[Dedicated document with step-by-step instructions](https://github.com/sergenes/runandread-audiobook/blob/main/RANDR.md)**

## 🚀 Features
✅ A fully functional pipeline for generating audiobooks compatible with the Run & Read app.
---
✅ Convert EPUB to JSON for text extraction.\
✅ Generate audio files using **Zonos TTS model**.\
✅ Generate audio files using **Kokoro-TTS** by **AUDIO-MLX**.\
✅ Clone voices from provided MP3 sample.\
✅ Play audio clips sequentially while displaying text in the terminal.\
✅ Merge audio clips into one file.\
✅ Zyphra API support for cloud-based TTS.\
✅ Deepgram API support for cloud-based TTS.\
✅ Wrap produced audio and json files into zip file readable by Run & Read App.\
✅ Transfer audio files to a mobile phone and play them in the Run & Read App.
🔜 Calculate the Self-Cost of Complete Book Generation: Cloud vs. Local.\
🔜 On-device TTS model for **mobile apps** (Android/iOS).

---

## 🎧 Audio Samples

Here are some audiobook samples generated using RunAndRead-Audiobook with **Zonos TTS voice cloning**:

[[Sample 1 - *Alice in Wonderland*]](https://www.youtube.com/shorts/cy8pdPn7gNk)

📌 You can find examples under the **audio/pg11/** folder, and generate your own samples using the steps outlined in the **Usage** section below.

---

## 📦 Dependencies & Technologies

- **Python 3.9+**
- **[Zyphra/Zonos](https://github.com/Zyphra/Zonos)** (open-source TTS engine)
- **ffmpeg** (audio conversion)
- **[EbookLib](https://pypi.org/project/EbookLib/)** (EPUB parsing)
- **PyAudio** / `playsound` (for playback)
- **yt-dlp** (to download MP3 files from YouTube for voice cloning)

---

## 🛠 Installation

### **1️⃣ Install Python Dependencies**

```bash
pip install -r requirements.txt
```

### **2️⃣ Set Up Zyphra/Zonos**

Follow the official installation instructions from [Zyphra/Zonos](https://github.com/Zyphra/Zonos). Using a `uv` virtual
environment is recommended for running RunAndRead scripts. After installing the Zonos project, run the `sample.py`
script:

```bash
uv run sample.py
```

This will download the **"Zyphra/Zonos-v0.1-transformer"** base model from Hugging Face and store it in your
environment.

### **3️⃣ Set Up ffmpeg**

- **macOS**: `brew install ffmpeg`
- **Ubuntu**: `sudo apt install ffmpeg`
- **Windows**: [Download from ffmpeg.org](https://ffmpeg.org/download.html) and add to system PATH.

### **4️⃣ Download a Voice Sample from YouTube**

To train a **Zonos voice clone**, you'll need an MP3 sample of the speaker. A **10-20 minute video** with a single
speaker (e.g., a tutorial or audiobook) is recommended. You can download an MP3 track from YouTube using `yt-dlp`:

```bash
yt-dlp -x --audio-format mp3 "https://www.youtube.com/watch?v=MkLBNUMc26Y" -o "assets/exampleaudio.mp3"
```

This `exampleaudio.mp3` file will be used by the Zonos model to fine-tune the voice sample before actual synthesis.

---

## 📚 Usage

### **Step 1: Convert EPUB to JSON**

First, run this script with `0` as the third parameter:

```bash
python epub_to_json.py epub/pg11.epub library/pg11.json 0
```

Check the terminal output to find how many lines should be skipped, then rerun the script with the number of the first
line to keep:

```bash
python epub_to_json.py epub/pg11.epub library/pg11.json 10
```

This ensures that the book starts from the correct position, e.g.:

> **10: CHAPTER I. Down the Rabbit-Hole**

🚨 **Note**: Without an NVIDIA GPU, converting an entire book to audio takes a long time. A **30-second** audio clip
takes approximately **3 minutes** to generate on macbook pro, m1. A full book can take **dozens of hours**. For example,
*Alice’s Adventures in Wonderland* is **3 hours long**, meaning **18 hours of processing** on a MacBook Pro with an M1
processor. **However, the `make_abook` script can be interrupted at any time, and it will resume from the position where
it was stopped.**

### **Step 2: Generate TTS Audio Files**

```bash
uv run python make_abook.py library/pg21279.json assets/kurt_v.mp3
```

### **Step 3: Play Audiobook in CLI**

```bash
python play_audio.py audio/pg11 mp3
```

### **Step 4: Merge a set of audio clips into one audio file**

```bash
python merge_audio_clips.py library/pg11.json audio/pg11 mp3
```

### **Step 5: Prepare audio clip for YouTube/LinkedIn**

```bash
# YouTube
ffmpeg -loop 1 -i assets/ic_launcher.png -i audio/pg11/merged_output.mp3 -c:v libx264 -c:a aac -b:a 192k -shortest output.mp4 
```

```bash
# LinkedIn
ffmpeg -loop 1 -i appGoogle.png -i merged_output.mp3 -vf "scale=1080:1080,format=yuv420p" -c:v libx264 -tune stillimage -c:a aac -b:a 192k -shortest output.mp4

# X
ffmpeg -loop 1 -i appGoogle.png -i merged_output.mp3 -vf "scale=1080:1080,format=yuv420p" -c:v libx264 -tune stillimage -c:a aac -b:a 192k -pix_fmt yuv420p -shortest output.mp4

```

### **Step 6: Setup Rest Zyphra/Deepgram/OpenAI SDK**

```bash
# Zyphra
export ZYPHRA_API_KEY="your-zyphra-api-key"
python zyphra_api.py library/pg11.json
```

```bash
# DeepGarm
export DEEPGRAM_API_KEY="your-deepgram-api-key"
python deepgram_api.py library/pg11.json
```

```bash
# OpenAI MINI TTS
export OPENAI_API_KEY="your-deepgram-api-key"
python make_abook_open_ai.py library/pg11.json
```

### **Step 7: Setup MLX-AUDIO (cloned local repo)**

```bash
pip install -e ~/projects/voice/mlx-audio
```
---
🚨 **Note**: Kokoro-82M TTS model skips names and other out-of-dictionary (OOD) words due to its reliance on an external grapheme-to-phoneme (g2p) conversion tool called espeak-ng2. This behavior occurs when espeak-ng is not properly installed or detected by the system.
To prevent Kokoro-82M from skipping names and OOD words, you need to install `espeak-ng`

```bash
echo 'export ESPEAK_DATA_PATH=/opt/homebrew/share/espeak-ng-data' >> ~/.zshrc
source ~/.zshrc

# make audio book
python make_abook_mlx.py library/pg2680.json 
```

### **Step 8: Make RANDR Audiobook**
```bash
python make_randr.py audio/pg20203/
```

## 📂 Project Structure

```
runandread-audiobook/
├── epub_to_json.py      # Extracts text from EPUB into JSON
├── make_abook.py        # Converts text into audio files with Zonos TTS
├── make_abook_mlx.py    # Converts text into audio files using the Kokoro-82M TTS model with mlx-audio (optimized for Apple M-series processors).
├── make_randr.py        # Wrap the produced audio and JSON files into a ZIP file readable by the Run & Read app.
├── play_audio.py        # Play audio clips sequentially while displaying text
├── merge_audio_clips.py # Merges audio files into one and generates a timestamped JSON file
├── word_tokens_tools.py # Utility to normalize the text before pass it to the TTS
├── test_scan_next.py    # Unit tests to make sure text normalization works as expected
├── zyphra_api.py        # Converts text into audio files with Zyphra SDK/Rest API API
├── deepgram_api.py      # Converts text into audio files with Deepgram SDK/Rest API API
├── make_abook_open_ai.py# Converts text into audio files with OpenAI TTS
├── assets/              # Stores MP3 files for voice cloning
├── epub/                # EPUB books from the Gutenberg Project
├── audio/               # Output audio files
├── audiobooks/          # RAND audiobooks samples
     ├── pg2680.randr    # Meditations by Emperor of Rome Marcus Aurelius
     ├── pg20203.randr   # Autobiography of Benjamin Franklin
├── library/             # Output JSON book files
├── README.md            # Documentation
├── requirements.txt     # Dependencies
└── LICENSE              # Open-source license
```

---

## 🤝 Contributions

Contributions are welcome! Feel free to open an issue or submit a pull request.

---

## 🛣️ Roadmap
- 🎯 **Ultimate Goal:** On-device TTS model.

---

## 📜 References & Kudos

- **[Zonos](https://github.com/Zyphra/Zonos)** - Open-source TTS model.
- **[AUDIO-MLX](https://github.com/Blaizzy/mlx-audio)** - A TTS and STS library built on Apple's MLX framework.
- **[Kokoro-TTS](https://huggingface.co/spaces/hexgrad/Kokoro-TTS)** - An open-weight TTS model with 82 million parameters.
- **[Deepgram](https://deepgram.com/)** - Commercial cloud-based TTS (future integration).
- **[EbookLib](https://pypi.org/project/EbookLib/)** - EPUB parsing in Python.
- **[yt-dlp](https://github.com/yt-dlp/yt-dlp)** - YouTube audio downloader for voice cloning.
- **[Gutenberg Project](https://www.gutenberg.org)** - A library of over 75,000 free eBooks.
- **[Python Simplified, MariyaSha](https://www.youtube.com/@PythonSimplified)** - Python Simplified. Kudos to Mariya for
  her beautiful voice that I did clone from one of her videos.

---

## 📞 Contact

- **[Sergey N](https://www.linkedin.com/in/sergey-neskoromny/)** - Connect and follow me on LinkedIn.

---

## 📄 License

This project is open-source and available under the **MIT License**.
