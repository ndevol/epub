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
    book: epub.EpubBook, book_dir: str, chapters: list[tuple[str, str]]
) -> None:
    """Convert HTML files in a book directory to EPUB format."""
    chapter_list = []
    for ch_label, chapter_title in chapters:
        c, img_items = create_chapter(book_dir, ch_label, chapter_title)
        for img_item in img_items:
            book.add_item(img_item)

        book.add_item(c)
        chapter_list.append(c)

    # Create spine (list of content documents in reading order)
    book.spine = ["nav"] + chapter_list

    # Add basic CSS
    with open("style/main.css", "r", encoding="utf-8") as f:
        style_content = f.read()

    style = epub.EpubItem()
    style.file_name = "style/main.css"
    style.media_type = "text/css"
    style.content = style_content

    book.add_item(style)

    # Define Table of Contents
    book.toc = tuple(chapter_list)  # pyright: ignore

    # Add navigation files
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    output_file = f"{book_dir}.epub"
    output_path = os.path.join(book_dir, output_file)
    epub.write_epub(output_path, book, {})
    print(f"✓ {os.path.getsize(output_path) / 1024:.1f} KB EPUB created")


def create_chapter(
    book_dir: str, ch_label: str, ch_title: str
) -> tuple[epub.EpubHtml, list[epub.EpubImage]]:
    """Process a chapter's HTML file and extract images for EPUB."""
    HTML_NAME_TEMPLATE = "Ch_{ch_label}/processed_article.html"
    html_file = os.path.join(book_dir, HTML_NAME_TEMPLATE.format(ch_label=ch_label))

    if not os.path.exists(html_file):
        raise FileNotFoundError(f"Missing HTML file for chapter {ch_label}: {html_file}")

    with open(html_file, "r", encoding="utf-8") as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, "html.parser")
    content_div = soup.body if soup.body else soup

    img_items = extract_img_items(content_div, html_file)

    c = epub.EpubHtml()
    c.file_name = f"{ch_label}.xhtml"
    c.title = ch_title
    c.content = str(content_div)

    return c, img_items


def extract_img_items(content_div, html_file: str) -> list[epub.EpubImage]:
    """Extract images from HTML content and prepare them for EPUB."""
    img_items = []
    for img in content_div.find_all("img"):
        src = str(img.get("src", ""))

        if src.split("/")[0] != "images":
            raise ValueError(
                f"Expecting images to be in images dir instead got {src} for {html_file}."
            )

        if not src:
            continue

        html_dir = os.path.dirname(html_file)
        with open(os.path.join(html_dir, src), "rb") as img_file:
            img_data = img_file.read()

        # Add image to EPUB
        img_item = epub.EpubImage()
        img_item.file_name = src
        img_item.content = img_data

        # Set correct media type
        mime_type, _ = mimetypes.guess_type(src)
        if mime_type:
            img_item.media_type = mime_type

        img_items.append(img_item)

    return img_items


def ddia():
    """Designing Data-Intensive Applications, 2nd Edition"""
    book_dir = "ddia"

    # List chapter titles. Folders are expected like "Ch_1", "Ch_2", etc.
    chapters = [
        ("preface", "Preface"),
        ("1", "1. Trade-offs in Data Systems Architecture"),
        ("2", "2. Defining Nonfunctional Requirements"),
        ("3", "3. Data Models and Query Languages"),
        ("4", "4. Storage and Retrieval"),
        ("5", "5. Encoding and Evolution"),
        ("6", "6. Replication"),
        ("7", "7. Sharding"),
        ("8", "8. Transactions"),
        ("9", "9. The Trouble with Distributed Systems"),
        ("10", "10. Consistency and Consensus"),
        ("11", "11. Batch and Stream Processing"),
        ("12", "12. Stream Processing"),
        ("13", "13. A Philosophy of Streaming Systems"),
        ("14", "14. Doing the Right Thing"),
        ("glossary", "Glossary"),
        ("index", "Index"),
        ("authors", "About the Authors"),
    ]

    # Create EPUB book instance with metadata
    book = epub.EpubBook()
    book.set_identifier("ddia-" + datetime.now().strftime("%Y%m%d%H%M%S"))
    book.set_title("Designing Data-Intensive Applications, 2nd Edition")
    book.set_language("en")
    for author in ["Martin Kleppmann", "Chris Riccomini"]:
        book.add_author(author)
    book.set_cover("cover.jpg", open("ddia/cover.jpg", "rb").read())

    create_epub_from_html(book, book_dir, chapters)

if __name__ == "__main__":
    ddia()
