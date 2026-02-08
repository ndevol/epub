#!/usr/bin/env python3
"""
Convert HTML article to EPUB format suitable for Kindle.
"""

import os
import mimetypes
from datetime import datetime

from bs4 import BeautifulSoup
from ebooklib import epub


def create_epub_from_html(
    book: epub.EpubBook, html_file: str, output_dir: str, output_file: str
) -> None:
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

    for img in content_div.find_all("img"):
        src = str(img.get("src", ""))
        name = os.path.basename(src)
        if not src:
            continue

        html_dir = os.path.dirname(html_file)
        with open(os.path.join(html_dir, src), "rb") as img_file:
            img_data = img_file.read()

        # Add image to EPUB
        epub_img_name = f"images/{name}"
        img_item = epub.EpubImage()
        img_item.file_name = epub_img_name
        img_item.content = img_data

        # Set correct media type
        mime_type, _ = mimetypes.guess_type(src)
        if mime_type:
            img_item.media_type = mime_type

        book.add_item(img_item)


    c1 = epub.EpubHtml()
    c1.file_name = "chap_01.xhtml"
    c1.title = "Trade-offs in Data Systems Architecture"
    c1.content = str(content_div)

    book.add_item(c1)

    # Create spine (list of content documents in reading order)
    book.spine = ["nav", c1]

    # Add basic CSS
    with open("style/main.css", "r", encoding="utf-8") as f:
        style_content = f.read()

    style = epub.EpubItem()
    style.file_name = "style/main.css"
    style.media_type = "text/css"
    style.content = style_content

    book.add_item(style)

    # Define Table of Contents
    book.toc = (c1,)  # pyright: ignore

    # Add navigation files
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    output_path = os.path.join(output_dir, output_file)
    epub.write_epub(output_path, book, {})
    print(f"✓ EPUB created successfully: {output_file}")


def main():
    input_file = "ddia/Ch1/processed_article.html"
    output_dir = "ddia/"
    output_file = "ddia-chapter1.epub"

    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file '{input_file}' not found.")

    # Create EPUB book instance with metadata
    book = epub.EpubBook()
    book.set_identifier("ddia-" + datetime.now().strftime("%Y%m%d%H%M%S"))
    book.set_title("Designing Data-Intensive Applications, 2nd Edition")
    book.set_language("en")
    for author in ["Martin Kleppmann", "Chris Riccomini"]:
        book.add_author(author)

    os.makedirs(output_dir, exist_ok=True)
    create_epub_from_html(book, input_file, output_dir, output_file)
    output_path = os.path.join(output_dir, output_file)
    print(f"File size: {os.path.getsize(output_path) / 1024:.1f} KB")

if __name__ == "__main__":
    main()
