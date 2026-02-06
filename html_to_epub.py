#!/usr/bin/env python3
"""
Convert HTML article to EPUB format suitable for Kindle.
"""

import os
import mimetypes
from datetime import datetime
from dataclasses import dataclass

from bs4 import BeautifulSoup
from ebooklib import epub


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


def create_epub_from_html(html_file: str, output_file: str, meta_data: MetaData) -> None:
    """
    Convert an HTML file to EPUB format.

    Args:
        html_file: Path to the HTML file
        output_file: Path where the EPUB will be saved
    """
    with open(html_file, "r", encoding="utf-8") as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, "html.parser")

    book = epub.EpubBook()

    # Set metadata
    book.set_identifier(meta_data.identifier_root + datetime.now().strftime("%Y%m%d%H%M%S"))
    book.set_title(meta_data.title)
    book.set_language(meta_data.language)
    for author in meta_data.authors:
        book.add_author(author)

    # Get the main content
    content_div = soup.find("div", {"id": "sbo-rt-content"})
    if not content_div:
        print("Warning: No div with id 'sbo-rt-content' found, trying 'book-content'...")
        content_div = soup.find("div", {"id": "book-content"})
    if not content_div:
        print("Warning: No specific content div found, using body or entire document...")
        # If no specific div found, use the body
        content_div = soup.body if soup.body else soup

    # Remove link tags (stylesheets)
    for link in content_div.find_all("link"):
        link.decompose()

    # Process images: extract them and update src paths
    for img in content_div.find_all("img"):
        src = img.get("src", "")
        if not src:
            continue

        # Normalize the path
        img_path = src.replace("./", "")
        img_path = os.path.join(os.path.dirname(html_file), img_path)

        if not os.path.exists(img_path):
            continue

        # Get original filename
        original_name = os.path.basename(img_path)
        epub_img_name = f"images/{original_name}"

        with open(img_path, "rb") as img_file:
            img_data = img_file.read()

        # Add image to EPUB
        img_item = epub.EpubImage()
        img_item.file_name = epub_img_name
        img_item.content = img_data

        # Set correct media type
        mime_type, _ = mimetypes.guess_type(img_path)
        if mime_type:
            img_item.media_type = mime_type

        book.add_item(img_item)

        # Update img src to point to EPUB resource
        img["src"] = epub_img_name

        # Remove fixed width/height to allow responsive sizing
        if "width" in img.attrs:
            del img["width"]
        if "height" in img.attrs:
            del img["height"]

    # Create a chapter
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
    book.toc = (c1,)

    # Add navigation files
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    epub.write_epub(output_file, book, {})
    print(f"✓ EPUB created successfully: {output_file}")


def main():
    input_file = "ddia/Ch1/article.html"
    output_file = "ddia/Ch1/ddia-chapter1.epub"
    meta_data = MetaData(
        identifier_root="ddia-ch1",
        title="Designing Data-Intensive Applications, 2nd Edition",
        language="en",
        authors=["Martin Kleppmann", "Chris Riccomini"],
    )

    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file '{input_file}' not found.")

    print(f"Converting {input_file} to EPUB...")
    create_epub_from_html(input_file, output_file, meta_data)
    print(f"File size: {os.path.getsize(output_file) / 1024:.1f} KB")

if __name__ == "__main__":
    main()
