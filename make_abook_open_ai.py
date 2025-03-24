import os
import sys
import json
from word_tokens_tools import split_into_words, scan_next, split_into_sentences, save_text
from openai import OpenAI

API_KEY = os.getenv("OPENAI_API_KEY")  # Get API key from environment variable
if not API_KEY:
    raise ValueError("API_KEY is not set")

client = OpenAI(api_key=API_KEY)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python deepgram_api.py <path_to_json>")
        sys.exit(1)

    path_to_json = sys.argv[1]

    uid = os.path.splitext(os.path.basename(path_to_json))[0]
    uid_folder = os.path.join("audio", uid)
    os.makedirs(uid_folder, exist_ok=True)

    index_file = os.path.join(uid_folder, "last_index.txt")
    last_word_index, next_window_index = 0, 0

    if os.path.exists(index_file):
        with open(index_file, "r") as f:
            last_word_index, next_window_index = map(int, f.read().strip().split(":"))

    print(f"🚀 Processing {path_to_json}, resuming from index {last_word_index}; {next_window_index}")

    with open(path_to_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "text" not in data or not isinstance(data["text"], list):
        print("⚠️ No valid 'text' field found.")
        exit(1)

    max_word_number = 128
    sentences = [sentence.strip() for paragraph in data["text"] for sentence in split_into_sentences(paragraph) if
                 sentence.strip()]
    words = split_into_words(sentences)
    available_voices = [
        "alloy",
        "ash",
        "ballad",
        "coral",
        "echo",
        "fable",
        "onyx",
        "nova",
        "sage",
        "shimmer",
        "verse"
    ]

    # instructions = """
    # Accent/Affect: Warm, refined, and gently instructive, reminiscent of a friendly art instructor.
    #
    # Tone: Calm, encouraging, and articulate, clearly describing each step with patience.
    #
    # Pacing: Slow and deliberate, pausing often to allow the listener to follow instructions comfortably.
    # """

    instructions = """
    Accent/Affect: Rich, expressive, and immersive, embodying the essence of each character and scene.  
    The voice should shift naturally between characters, giving each a unique tone and cadence.  

    Tone: Dynamic and emotionally resonant—soft and introspective for reflective moments,  
    powerful and commanding for climactic scenes, and playful or mysterious where needed.  
    The narration should feel alive, as if performed on stage.  

    Pacing: Natural and engaging, adjusting rhythm to match the tension of the story.  
    Dramatic pauses should be used to heighten suspense, while faster delivery conveys urgency or excitement.  
    Dialogue should feel conversational, with realistic pauses and inflections.  

    Additional Notes:  
    - Whisper slightly for secrets and inner thoughts.  
    - Laugh or sigh subtly when characters do.  
    - Let emotions drive the reading—joy, sorrow, fear, and wonder should be palpable.  
    - Ensure a seamless flow, making the audience feel as if they are inside the story.  
    """

    while next_window_index < 100:
        paragraph, next_word_index = scan_next(words, last_word_index, max_word_number)

        if next_word_index >= len(words):
            print(f"🎉 Finished processing {path_to_json}")
            break

        file_path = os.path.join(uid_folder, f"{next_window_index}.mp3")
        response = client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice=available_voices[7],
            input=paragraph,
            instructions=instructions,
        )
        response.stream_to_file(file_path)
        save_text(paragraph, next_window_index, uid_folder)

        next_window_index += 1
        with open(index_file, "w") as f:
            f.write(f"{next_word_index}:{next_window_index}")

        last_word_index = next_word_index
