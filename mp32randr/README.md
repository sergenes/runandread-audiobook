# RunAndRead-Audiobook

<div align="center">
<img src="../assets/ic_launcher.png"
     alt="Run & Read"
     style="width: 256px;
            height: auto;
            object-position: center top;">
</div>

---

## 📖 Overview

RunAndRead-Audiobook is an open-source pipeline for creating high-quality audiobooks using open-source AI models. It
generates RANDR format audiobooks, which can be played in the Run & Read app for Android and iOS.

This document provides a step-by-step guide on how to convert existing long or multiple short **MP3** files into a **RANDR**
audiobook, download MP3 audio from YouTube and transform it into a RANDR audiobook, and transcribe audio into text to
ensure a consistent experience. The transcription allows users to create bookmarks not only by timestamp but also with
the surrounding text, enhancing navigation and usability.

📌 **Ensure your app version supports RANDR format:**

- **Android**: Version **1.5 (6)** or later.
- **iOS**: Version **1.6 (18)** or later.

**Download and try the apps for free!**  
🍏 **App Store**: [Ran & Read for Apple Devices](https://apps.apple.com/us/app/run-read-listen-on-the-go/id6741396289)  
🤖 **Google Play**: [Ran & Read for Android](https://play.google.com/store/apps/details?id=com.answersolutions.runandread)

📱 **Scan QR Codes to Download:**

<div align="center">
<img src="../assets/apple_runandread_qr_code.png" width="150px"> &nbsp;&nbsp;&nbsp; <img src="../assets/google_runandread_qr_code.png" width="150px">
</div>

---

## 🚀 Features  

✅ **Merge** MP3 audio clips into a single file.  
✅ **Transcribe** MP3 files into a timestamped JSON file describing the book.  
✅ Package audio + JSON into the **RANDR format**, compatible with **Run & Read** apps on **iOS & Android** for seamless playback on mobile.  
✅ Transcription with `mlx-whisper` is optimized for **Apple Silicon (M-series processors)**.  

---  

## 📦 Dependencies  

- **Python 3.9+**  
- **[mlx-whisper](https://github.com/ml-explore/mlx-examples/tree/main/whisper)** – Speech recognition with Whisper in MLX  
- **[Whisper-Models-HuggingFace](https://huggingface.co/mlx-community/)** – Speech recognition models for transcription
- **FFmpeg** (for audio processing)  

---

## 🛠 Installation

### **1️⃣ Set Up MLX-WHISPER**

```bash
# STT
pip install mlx-whisper
```

### **2️⃣ Set Up ffmpeg**

- **macOS**: `brew install ffmpeg`
- **Ubuntu**: `sudo apt install ffmpeg`
- **Windows**: [Download from ffmpeg.org](https://ffmpeg.org/download.html) and add to system PATH.

---

## 📚 Pipeline Workflow  

### **Step 1: Prepare/Download MP3**  

If you have multiple MP3 files or one large file, place them all into the `audio/book_name/` folder and rename them sequentially: `0.mp3`, `1.mp3`, `2.mp3`, etc.  

Alternatively, you can download an MP3 track (course, book, etc.) from YouTube using `yt-dlp`:  

```bash
yt-dlp -x --audio-format mp3 "https://www.youtube.com/watch?v=6e-S8qzlQRU" -o "audio/book_name/0.mp3"
```

### **Step 2: Merge Audio Clips**

For better organization, merge smaller audio clips into larger ones using the merge script:

```bash
python merge_audio_clips.py ../audio/book_name mp3
```

### **Step 3: Transcribe MP3 With Whisper**

Transcribe your MP3 file using Whisper:

```bash
python transcribe_mp3.py --path ../audio/lra --title "Лунная Радуга. Часть Первая." --author "Сергей Павлов" --language ru_RU --voice Арестович
```

### **Step 4: Package as RANDR Format**
Finally, package the audio and JSON files into a RANDR audiobook:

```bash
python make_randr.py ../audio/lra/
```

📌 **Transfer the `.randr` file to your mobile device and open it in the Run & Read app!**

---

## 📂 Project Structure

```
runandread-audiobook/
├── assets/              # Icons, QR codes, and app store assets
├── epub/                # EPUB source files
├── audio/               # Generated audio files
├── library/             # JSON book structure
├── mp32randr/           # MP3 TO RAND audiobooks pipeline
  ├── merge_audio_clips.py    # Merges mp3 files into one
  ├── transcribe_mp3.py       # Transcribes mp3 files and creates json with the book properies
  ├── make_randr.py           # Packages audio & JSON into RANDR format
  ├── README.md               # Documentation
├── audiobooks/       # RAND audiobooks samples
  ├── pg2680.randr    # Meditations by Emperor of Rome Marcus Aurelius
  ├── pg20203.randr   # Autobiography of Benjamin Franklin
├── README.md         # General Repo's Documentation
└── requirements.txt  # Dependencies
```

---

## 🤝 Contributions

We welcome contributions! Open an **issue** or submit a **pull request**.

---

## 📜 References

- **[mlx-whisper](https://github.com/ml-explore/mlx-examples/tree/main/whisper)** - Speech recognition with Whisper in MLX.
- **[MLX Community on HuggingFace](https://huggingface.co/mlx-community/)** – Speech recognition models for transcription and more.

---

## 📞 Contact

- **[Sergey N](https://www.linkedin.com/in/sergey-neskoromny/)**

---

## 📄 License

This project is open-source under the **MIT License**.
