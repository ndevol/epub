#!/usr/bin/env python3
"""Prepare html data for use in epub."""

import os
import shutil
from dataclasses import dataclass

from bs4 import BeautifulSoup


@dataclass
class MetaData:
    identifier_root: str
    title: str
    language: str
    authors: list[str]


def clean_html_for_epub(html_content):
    """Clean and prepare HTML content for EPUB."""
    soup = BeautifulSoup(html_content, "html.parser")

    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()

    # Remove navigation elements
    for nav in soup(["nav", "header", "footer"]):
        nav.decompose()

    # Find the main content
    content_div = soup.find("div", {"id": "book-content"})
    if content_div:
        # Remove the link tags from head
        for link in content_div.find_all("link"):
            link.decompose()
        return str(content_div)

    return str(soup.body) if soup.body else str(soup)


def create_epub_from_html(html_file: str, output_dir: str) -> None:
    """
    Convert an HTML file to EPUB format.

    Args:
        html_file: Path to the HTML file
        output_file: Path where the EPUB will be saved
    """
    with open(html_file, "r", encoding="utf-8") as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, "html.parser")
    content_div = soup.body if soup.body else soup

    # Remove link tags (stylesheets)
    for link in content_div.find_all("link"):
        link.decompose()

    # Process images: extract them and update src paths
    os.makedirs(os.path.join(output_dir, "images"), exist_ok=True)
    for img in content_div.find_all("img"):
        src = img.get("src", "")
        if not src:
            continue

        # Normalize the path
        img_path = src.replace("./", "")  # pyright: ignore
        img_path = os.path.join(os.path.dirname(html_file), img_path)

        if not os.path.exists(img_path):
            continue

        original_name = os.path.basename(img_path)
        new_img_path = os.path.join(output_dir, "images", original_name)
        shutil.copy(img_path, new_img_path)

        # Update img src to point to EPUB resource
        img["src"] = f"images/{original_name}"

        # Remove fixed width/height to allow responsive sizing
        if "width" in img.attrs:
            del img["width"]
        if "height" in img.attrs:
            del img["height"]

    # Save the processed HTML content
    processed_html_output_path = os.path.join(output_dir, "processed_article.html")
    with open(processed_html_output_path, "w", encoding="utf-8") as f:
        f.write(str(content_div))
    print(f"✓ Processed HTML saved: {processed_html_output_path}")

def main():
    input_file = "ddia/article.html"
    output_dir = "ddia/Ch1/"

    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file '{input_file}' not found.")

    os.makedirs(output_dir, exist_ok=True)
    create_epub_from_html(input_file, output_dir)

if __name__ == "__main__":
    main()
