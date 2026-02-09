#!/usr/bin/env python3
"""Prepare html data for use in epub."""

import os
import shutil

from bs4 import BeautifulSoup


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


def create_epub_from_html(html_file: str, output_dir: str, chapter_label: str) -> None:
    """
    Convert an HTML file to EPUB format.

    Args:
        html_file: Path to the HTML file
        output_dir: Path to the output directory where the EPUB will be saved
        chapter_label: Label for the chapter (e.g., "Ch10"). The output will be saved to a directory
            with this name
    """
    output_path = os.path.join(output_dir, chapter_label)
    os.makedirs(output_path, exist_ok=True)

    with open(html_file, "r", encoding="utf-8") as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, "html.parser")
    content_div = soup.body if soup.body else soup

    # Remove link tags (stylesheets)
    for link in content_div.find_all("link"):
        link.decompose()

    # Process images: extract them and update src paths
    os.makedirs(os.path.join(output_path, "images"), exist_ok=True)
    for img in content_div.find_all("img"):
        src = str(img.get("src", ""))
        if not src:
            continue

        # Normalize the path
        img_path = src.replace("./", "")
        img_path = os.path.join(os.path.dirname(html_file), img_path)

        if not os.path.exists(img_path):
            continue

        original_name = os.path.basename(img_path)
        new_name = f"{chapter_label}_{original_name}"
        new_img_path = os.path.join(output_path, "images", new_name)
        shutil.copy(img_path, new_img_path)

        # Update img src to point to EPUB resource
        img["src"] = f"images/{new_name}"

        # Remove fixed width/height to allow responsive sizing
        if "width" in img.attrs:
            del img["width"]
        if "height" in img.attrs:
            del img["height"]

    # Save the processed HTML content
    processed_html_output_path = os.path.join(output_path, "processed_article.html")
    with open(processed_html_output_path, "w", encoding="utf-8") as f:
        f.write(str(content_div))
    print(f"✓ Processed HTML saved: {processed_html_output_path}")

def ddia():
    """Designing Data-Intensive Applications, 2nd Edition"""
    f_names = ["preface"] + list(range(1, 15)) + ["glossary", "index", "authors"]
    for f_name in f_names:
        output_dir = "ddia"
        input_file = f"{f_name}.html"
        chapter_label = f"Ch_{f_name}"

        input_path = os.path.join(output_dir, input_file)
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file '{input_path}' not found.")

        create_epub_from_html(input_path, output_dir, chapter_label)

if __name__ == "__main__":
    ddia()
