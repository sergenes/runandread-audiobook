import os
import json
import re


def split_into_words(sentences):
    words = []
    for sentence in sentences:
        words.extend(re.findall(r"\w+(?:['’]\w+)?[.,!?;:-]?|\S", sentence))
    return words


def split_into_sentences(text):
    """Splits text into sentences based on multiple punctuation marks."""
    # Split on periods, exclamation marks, question marks
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]


def scan_next(words, next_word_index, max_word_number, lookahead_limit=50):
    """Returns paragraph of text with max_word_number plus the number of words to the next punctuation symbol."""
    if next_word_index >= len(words):
        return "", len(words)  # No more words left

    paragraph = []
    word_count = 0
    current_word_index = next_word_index

    while current_word_index < len(words) and word_count < max_word_number:
        word = words[current_word_index]
        paragraph.append(word)
        word_count += 1
        current_word_index += 1

    if re.match(r".*[.!?,:;-]$", word):
        return " ".join(paragraph), current_word_index
    else:
        # scan to the next punctuation

        while current_word_index < len(words) and word_count < max_word_number + lookahead_limit:
            word = words[current_word_index]
            paragraph.append(word)
            word_count += 1
            current_word_index += 1
            if re.match(r".*[.!?,:;-]$", word):
                return " ".join(paragraph), current_word_index

    return " ".join(paragraph), current_word_index


def save_text(content, file_name, uid_folder):
    """Saves text content to a file."""
    with open(os.path.join(uid_folder, f"{file_name}.txt"), "w", encoding="utf-8") as f:
        f.write(content)


if __name__ == "__main__":
    path_to_json = "library/pg11.json" # sys.argv[1]
    last_word_index, next_window_index = 0, 0
    print(f"🚀 Processing {path_to_json}, resuming from index {last_word_index}; {next_window_index}")

    with open(path_to_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "text" not in data or not isinstance(data["text"], list):
        print("⚠️ No valid 'text' field found.")
        exit(1)

    max_word_number = 60
    sentences = [sentence.strip() for paragraph in data["text"] for sentence in split_into_sentences(paragraph) if
                 sentence.strip()]
    words = split_into_words(sentences)
    while True:
        paragraph, next_word_index = scan_next(words, last_word_index, max_word_number)

        if next_word_index >= len(words):
            print(f"🎉 Finished processing {path_to_json}")
            break

        print(f"🎉 {len(paragraph)} ------------------------")
        print(f"🎉 paragraph =>{paragraph}")
        next_window_index += 1
        last_word_index = next_word_index
