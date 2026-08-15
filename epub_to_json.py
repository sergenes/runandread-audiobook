import os
import sys
import re
import argparse
from ebooklib import epub
from bs4 import BeautifulSoup
import json


def clean_text(text):
    """Cleans extracted text by removing unnecessary symbols and normalizing spaces.
       Supports Latin, Cyrillic, and other Unicode scripts.
    """
    text = text.replace("\n", " ")  # Replace newlines with spaces
    text = re.sub(
        r"[^\w.,!?;:\-–—'\"’Ѐ-ӿͰ-Ͽ؀-ۿ一-鿿]+",
        " ", text, flags=re.UNICODE)
    # Keep letters, numbers, and basic punctuation (incl. ; : and dashes, which are meaningful
    # in narration even though they aren't sentence-split boundaries - see split_sentences()),
    # allowing for Cyrillic, Greek, Arabic, and CJK characters

    text = re.sub(r"\s+", " ", text).strip()  # Normalize multiple spaces

    # Ensure the line ends with proper punctuation
    if text and not re.search(r"[.!?]$", text, re.UNICODE):
        text += "."  # Add a period if missing

    return text


_SENTENCE_BOUNDARY_RE = re.compile(r"(?<=[.!?:;])\s+")


def split_sentences(text):
    """Splits a paragraph into sentence/clause-level chunks on . ! ? : ; boundaries.

    Dashes are deliberately excluded: they're commonly used for parentheticals
    ("The result — surprising to no one — was clear.") and dialogue-attribution
    insertions ("— Да, — ответил он."), and splitting on them would break a
    single grammatical unit into disconnected fragments. Leading dialogue
    dashes (as in Russian "— Кто здесь?") stay attached to their sentence
    since the actual split still happens at the "?" / "." that follows.

    Any punctuation-only fragment that can still occur is folded into the
    following chunk instead of being emitted as its own near-empty TTS clip.
    """
    raw_parts = [s.strip() for s in _SENTENCE_BOUNDARY_RE.split(text) if s.strip()]

    chunks = []
    carry = ""
    for part in raw_parts:
        if not re.search(r"\w", part, re.UNICODE):
            carry = f"{carry} {part}".strip() if carry else part
            continue
        chunks.append(f"{carry} {part}".strip() if carry else part)
        carry = ""
    if carry:
        if chunks:
            chunks[-1] = f"{chunks[-1]} {carry}".strip()
        else:
            chunks.append(carry)

    return chunks


def extract_content(book):
    # Unwanted sections that should be stripped out
    stripped_sections = {"title", "section", "cover", "colophon", "imprint", "endnote", "copyright"}

    # Extract spine items (document structure)
    content_files = []
    for item in book.spine:
        idref = item[0]  # Extract the ID from the tuple
        manifest_item = book.get_item_with_id(idref)  # Directly fetch the item
        if manifest_item:
            content_files.append(manifest_item)

    extracted_texts = []

    for item in content_files:
        file_name = os.path.splitext(os.path.basename(item.file_name))[0].lower()  # Remove extension and lowercase
        if any(section in file_name for section in stripped_sections):
            continue  # Skip unwanted sections

        try:
            soup = BeautifulSoup(item.content, "html.parser")
            texts = [
                clean_text(tag.get_text(strip=True))
                for tag in soup.select("p,h1,h2,h3,h4,h5,h6,pre")
                if tag.get_text(strip=True)
            ]

            extracted_texts.extend([text for text in texts if text])  # Remove empty items before append
        except Exception as e:
            print(f"Failed to parse section: {item.file_name} -> {e}")

    return extracted_texts


def read_epub(epub_path):
    # Load the EPUB file
    try:
        book = epub.read_epub(epub_path)
    except Exception as e:
        print(f"Error reading EPUB file: {e}")
        return None, None, []

    # Get metadata: title and author
    title = book.get_metadata('DC', 'title')
    author = book.get_metadata('DC', 'creator')

    title = title[0][0] if title else "Unknown Title"
    author = author[0][0] if author else "Unknown Author"

    # Extract text from each chapter
    content_array = extract_content(book)

    return title, author, content_array


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Converts an EPUB book into RunAndRead's library JSON format.",
    )
    parser.add_argument("epub_path", help="Path to the source .epub file")
    parser.add_argument("output_json", help="Path to write the output JSON to")
    parser.add_argument("skip_lines", type=int,
                         help="Number of leading extracted sections to skip (e.g. table of contents). "
                              "Pass 0 to preview the extracted sections without writing a file.")
    parser.add_argument("--split-sentences", action="store_true",
                         help="Split each paragraph into individual sentence/clause chunks "
                              "(on . ! ? : ;) instead of one JSON entry per paragraph. "
                              "Small local TTS models generate more reliably on short, "
                              "single-sentence chunks than on long multi-sentence paragraphs.")
    args = parser.parse_args()

    epub_path = args.epub_path
    output_json = args.output_json

    title, author, content = read_epub(epub_path)

    if args.split_sentences:
        content = [sentence for paragraph in content for sentence in split_sentences(paragraph)]

    print(f"Title: {title}")
    print(f"Author: {author}")
    print(f"Extracted {len(content)} sections of text")
    for i, text in enumerate(content[:100], start=0):
        print(f"{i}: {text}")

    # Look into log to see how much items in the text array you need to skip you should
    # skip the content table
    skip = args.skip_lines
    if skip > 0:
        # Convert data to JSON correctly
        json_out = json.dumps({
            "title": title,
            "author": author,
            "split_by_sentence": args.split_sentences,
            "text": content[skip:]  # This remains a list of strings
        }, ensure_ascii=False, indent=4)  # Pretty print, keep Unicode characters

        # Create output folder
        os.makedirs(os.path.dirname(output_json), exist_ok=True)
        with open(output_json, "w", encoding="utf-8") as f:
            f.write(json_out)

        print(f"✅ Successfully converted '{epub_path}' to '{output_json}'")
    else:
        print(f"ℹ️  Preview only - no file written (skip_lines was {skip}).")
        print("Check the numbered sections above, find where the real content starts, "
              "then rerun with that number as the third argument, e.g.:")
        print(f"  python epub_to_json.py {epub_path} {output_json} 10")
