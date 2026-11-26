from collections import Counter
from pathlib import Path

import pymupdf as fitz

HEADING_SCALE = 1.3


def get_body_font_size(doc):
    sizes = Counter()
    for page in doc:
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                for span in line["spans"]:
                    sizes[round(span["size"], 1)] += len(span["text"].strip())
    return sizes.most_common(1)[0][0]


def find_heading(page, body_size):
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            if not line["spans"]:
                continue
            text = "".join(span["text"] for span in line["spans"]).strip()
            size = max(span["size"] for span in line["spans"])
            if text and size >= body_size * HEADING_SCALE:
                return text
    return None


def load_pdf(path):
    path = Path(path)
    pages = []
    with fitz.open(path) as doc:
        body_size = get_body_font_size(doc)
        section = None
        for page in doc:
            heading = find_heading(page, body_size)
            if heading:
                section = heading
            text = page.get_text().strip()
            if text:
                pages.append({"text": text, "page": page.number + 1, "section": section})
    return pages
