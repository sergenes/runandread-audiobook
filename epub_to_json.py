import os
import sys
import re
from ebooklib import epub
from bs4 import BeautifulSoup
import json


def clean_text(text):
    """Cleans extracted text by removing unnecessary symbols and normalizing spaces."""
    text = text.replace("\n", " ")  # Replace newlines with spaces
    text = re.sub(r"[^a-zA-Z0-9.,!?'\"]+", " ", text)  # Keep only letters, numbers, and basic punctuation
    text = re.sub(r"\s+", " ", text).strip()  # Normalize multiple spaces
    # Ensure the line ends with proper punctuation
    if text and not re.search(r"[.!?]$", text):
        text += "."  # Add a period if missing
    return text


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
    if len(sys.argv) != 4:
        print("Usage: python epub_to_json.py <path_to_epub> <output_json> <skip_lines>")
        sys.exit(1)

    epub_path = sys.argv[1]
    output_json = sys.argv[2]
    skip_lines = sys.argv[3]

    if epub_path is None:
        epub_path = "epub/pg11.epub"
    if output_json is None:
        output_json = "library/pg11.json"

    title, author, content = read_epub(epub_path)

    print(f"Title: {title}")
    print(f"Author: {author}")
    print(f"Extracted {len(content)} sections of text")
    content = content
    for i, text in enumerate(content[:100], start=0):
        print(f"{i}: {text}")

    # Look into log to see how much items in the text array you need to skip you should
    # skip the content table
    skip = int(skip_lines)
    if skip > 0:
        # Convert data to JSON correctly
        json_out = json.dumps({
            "title": title,
            "author": author,
            "text": content[skip:]  # This remains a list of strings
        }, ensure_ascii=False, indent=4)  # Pretty print, keep Unicode characters

        # Create output folder
        os.makedirs(os.path.dirname(output_json), exist_ok=True)
        with open(output_json, "w", encoding="utf-8") as f:
            f.write(json_out)

    print(f"✅ Successfully converted '{epub_path}' to '{output_json}'")
