#!/usr/bin/env python3
"""
Convert HTML article to EPUB format suitable for Kindle.
"""

import os
import mimetypes
from datetime import datetime

from bs4 import BeautifulSoup
from ebooklib import epub


def extract_text(element):
    """Recursively extract text from an element."""
    if isinstance(element, str):
        return element
    if element.name is None:
        return element.string or ""

    text = ""
    for content in element.contents:
        text += extract_text(content)
    return text


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


def create_epub_from_html(html_file, output_file):
    """
    Convert an HTML file to EPUB format.

    Args:
        html_file: Path to the HTML file
        output_file: Path where the EPUB will be saved
    """

    # Read the HTML file
    with open(html_file, "r", encoding="utf-8") as f:
        html_content = f.read()

    # Parse and clean the HTML
    soup = BeautifulSoup(html_content, "html.parser")

    # Create EPUB book
    book = epub.EpubBook()

    # Set metadata
    book.set_identifier("ddia-ch1-" + datetime.now().strftime("%Y%m%d%H%M%S"))
    book.set_title("Trade-offs in Data Systems Architecture")
    book.set_language("en")
    book.add_author("Martin Kleppmann")

    # Get the main content
    content_div = soup.find("div", {"id": "sbo-rt-content"})
    if not content_div:
        content_div = soup.find("div", {"id": "book-content"})
    if not content_div:
        # If no specific div found, use the body
        content_div = soup.body if soup.body else soup

    # Remove link tags (stylesheets)
    for link in content_div.find_all("link"):
        link.decompose()

    # Process images: extract them and update src paths
    image_map = {}  # Maps original src to EPUB filename
    img_counter = 1

    for img in content_div.find_all("img"):
        src = img.get("src", "")
        if not src:
            continue

        # Normalize the path
        img_path = src.replace("./", "")
        img_path = os.path.join(os.path.dirname(html_file), img_path)

        # Check if file exists
        if os.path.exists(img_path):
            # Get original filename
            original_name = os.path.basename(img_path)
            epub_img_name = f"images/{original_name}"

            # Read the image
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
            image_map[src] = epub_img_name

            # Update img src to point to EPUB resource
            img["src"] = epub_img_name

            # Remove fixed width/height to allow responsive sizing
            if "width" in img.attrs:
                del img["width"]
            if "height" in img.attrs:
                del img["height"]

            img_counter += 1

    # Create chapter
    chapter_html = str(content_div)

    # Create a chapter
    c1 = epub.EpubHtml()
    c1.file_name = "chap_01.xhtml"
    c1.title = "Trade-offs in Data Systems Architecture"
    c1.content = chapter_html

    book.add_item(c1)

    # Create spine (list of content documents in reading order)
    book.spine = ["nav", c1]

    # Add basic CSS
    style = epub.EpubItem()
    style.file_name = "style/main.css"
    style.media_type = "text/css"
    style.content = """
    body {
        font-family: Georgia, serif;
        line-height: 1.6;
        margin: 0;
        padding: 0.5em;
    }
    h1, h2, h3, h4, h5, h6 {
        font-family: Arial, sans-serif;
        margin-top: 0.5em;
        margin-bottom: 0.5em;
    }
    p {
        margin: 0.5em 0;
        text-align: justify;
    }
    img {
        max-width: 100% !important;
        height: auto !important;
        display: block;
        margin: 0.5em auto;
    }
    a {
        color: #0066cc;
        text-decoration: none;
    }
    table {
        border-collapse: collapse;
        width: 100%;
        margin: 1em 0;
    }
    th, td {
        border: 1px solid #999;
        padding: 0.5em;
        text-align: left;
    }
    th {
        background-color: #f0f0f0;
    }
    blockquote {
        margin: 1em 1.5em;
        padding-left: 1em;
        border-left: 3px solid #999;
        font-style: italic;
    }
    .sidebar {
        border: 1px solid #ccc;
        padding: 1em;
        margin: 1em 0;
        background-color: #f9f9f9;
    }
    ul, ol {
        margin: 0.5em 0;
        padding-left: 2em;
    }
    li {
        margin: 0.25em 0;
    }
    """

    book.add_item(style)

    # Define Table of Contents
    book.toc = (c1,)

    # Add navigation files
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # Write the EPUB file
    epub.write_epub(output_file, book, {})
    print(f"✓ EPUB created successfully: {output_file}")


if __name__ == "__main__":
    input_file = "article.html"
    output_file = "ddia-chapter1.epub"

    if os.path.exists(input_file):
        print(f"Converting {input_file} to EPUB...")
        create_epub_from_html(input_file, output_file)
        print(f"File size: {os.path.getsize(output_file) / 1024:.1f} KB")
    else:
        print(f"Error: {input_file} not found")
