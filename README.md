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

📲 **Download and try the apps for free!**  
🛠️ **The Android (Kotlin Compose) and iOS (SwiftUI) projects will be open-sourced soon.**

🍏 **App Store**: [https://lnkd.in/eGaY62Jw](https://lnkd.in/eGaY62Jw)  
🤖 **Google Play**: [https://lnkd.in/e3t5UGfw](https://lnkd.in/e3t5UGfw)

---

## 🚀 Features

✅ Convert EPUB to JSON for text extraction.\
✅ Generate audio files using **Zonos TTS model**.\
✅ Clone voices from provided MP3 samples.\
✅ Play audio clips sequentially while displaying text in the terminal.\
✅ Merge audio clips into one file.\
🔜 Text preprocessing to improve speech output (e.g., adding punctuation, removing problematic characters).  
🔜 Deepgram API support for cloud-based TTS.\
🔜 On-device TTS model for **mobile apps** (Android/iOS).

---

## 🎧 Audio Samples

Here are some audiobook samples generated using RunAndRead-Audiobook with **Zonos TTS voice cloning**:

[![Sample 1 - *Alice in Wonderland*](https://img.youtube.com/vi/cy8pdPn7gNk/0.jpg)](https://www.youtube.com/shorts/cy8pdPn7gNk)  
🔊 **Click the image to listen!**

📌 You can generate your own samples using the steps outlined in the **Usage** section below.

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
uv run python make_abook.py library/pg11.json
```

### **Step 3: Play Audiobook in CLI**

```bash
python play_audio.py audio/pg11 mp3
```

### **Step 4: Merge a set of audio clips into one audio file**

```bash
python python merge_audio_clips.py audio/pg11 mp3
```

### **Step 5: Prepare audio clip for youtube**

```bash
ffmpeg -loop 1 -i assets/ic_launcher.png -i audio/pg11/merged_output.mp3 -c:v libx264 -c:a aac -b:a 192k -shortest output.mp4 
```

---

## 📂 Project Structure

```
runandread-audiobook/
├── epub_to_json.py      # Extracts text from EPUB into JSON
├── make_abook.py        # Converts text into audio files with Zonos TTS
├── play_audio.py        # Play audio clips sequentially while displaying text
├── merge_audio_clips.py # Merges audio files into one and generates a timestamped JSON file
├── word_tokens_tools.py # Utility to normalize the text before pass it to the TTS
├── test_scan_next.py    # Unit tests to make sure text normalization works as expected
├── assets/              # Stores MP3 files for voice cloning
├── epub/                # EPUB books from the Gutenberg Project
├── audio/               # Output audio files
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

- ✅ **Current:** Zonos TTS support with voice cloning.
- 🚀 **Next:** Deepgram API integration.
- 🚀 **Next:** Transfer audio files to a mobile phone and play them in the Run & Read app.
- 🎯 **Ultimate Goal:** On-device TTS model.

---

## 📜 References & Kudos

- **[Zonos](https://github.com/Zyphra/Zonos)** - Open-source TTS model.
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
