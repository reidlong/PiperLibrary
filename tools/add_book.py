#!/usr/bin/env python3
"""Add a book to books.js from a store link or an ISBN.

Usage:
    python3 tools/add_book.py <amazon-or-other-link | ISBN> [--notes "board book"] [--series "..."]

The script finds the book's ISBN, looks up its title and author on
Open Library (falling back to Google Books), downloads the cover into
covers/, and appends an entry to books.js.

Amazon links work for print books, whose product id is the ISBN-10.
Kindle-only links (ids starting with B0) carry no ISBN; use the print
edition's link or type the ISBN from the back of the book.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOOKS_JS = ROOT / "books.js"
COVERS_DIR = ROOT / "covers"

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"


# ---------------------------------------------------------------- ISBNs

def isbn10_valid(s: str) -> bool:
    if not re.fullmatch(r"\d{9}[\dX]", s):
        return False
    total = sum((10 - i) * (10 if c == "X" else int(c)) for i, c in enumerate(s))
    return total % 11 == 0


def isbn13_valid(s: str) -> bool:
    if not re.fullmatch(r"97[89]\d{10}", s):
        return False
    total = sum(int(c) * (1 if i % 2 == 0 else 3) for i, c in enumerate(s))
    return total % 10 == 0


def to_isbn13(s: str) -> str:
    if len(s) == 13:
        return s
    core = "978" + s[:9]
    check = (10 - sum(int(c) * (1 if i % 2 == 0 else 3) for i, c in enumerate(core)) % 10) % 10
    return core + str(check)


def find_isbn(text: str) -> str | None:
    """Return the first checksum-valid ISBN in text, as ISBN-13."""
    for m in re.finditer(r"(?<![\dX])97[89][\d-]{10,14}(?![\d])", text):
        digits = m.group().replace("-", "")
        if isbn13_valid(digits):
            return digits
    for m in re.finditer(r"(?<![\dA-Z])[\dX]{10}(?![\dA-Z])", text.upper()):
        if isbn10_valid(m.group()):
            return to_isbn13(m.group())
    return None


# ---------------------------------------------------------------- HTTP

def fetch(url: str) -> tuple[str, bytes]:
    """GET url, returning (final_url, body). Raises on failure."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.geturl(), resp.read()


def fetch_json(url: str):
    return json.loads(fetch(url)[1])


def isbn_from_url_text(url: str) -> str | None:
    # Amazon product ids, e.g. /dp/0064430170 or /gp/product/0064430170
    m = re.search(r"/(?:dp|gp/product|gp/aw/d|product)/([\dX]{10})(?:[/?]|$)", url, re.I)
    if m and isbn10_valid(m.group(1).upper()):
        return to_isbn13(m.group(1).upper())
    return find_isbn(urllib.parse.unquote(url))


def isbn_from_link(link: str) -> str | None:
    isbn = isbn_from_url_text(link)
    if isbn:
        return isbn

    # Short links (a.co, amzn.to) and stores that keep the ISBN in the page
    # body rather than the URL: follow the link and search what comes back.
    try:
        final_url, body = fetch(link)
    except urllib.error.HTTPError as e:
        # Amazon often refuses the page itself but still reveals the
        # redirected product URL.
        final_url, body = e.geturl() or link, b""
    except urllib.error.URLError as e:
        print(f"Could not open {link}: {e.reason}", file=sys.stderr)
        return None
    if final_url != link:
        isbn = isbn_from_url_text(final_url)
        if isbn:
            return isbn
    return find_isbn(body.decode("utf-8", "replace"))


# ---------------------------------------------------------------- metadata

def lookup_open_library(isbn: str) -> dict | None:
    url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data"
    try:
        data = fetch_json(url).get(f"ISBN:{isbn}")
    except (urllib.error.URLError, ValueError):
        return None
    if not data or not data.get("title"):
        return None
    return {
        "title": data["title"],
        "author": ", ".join(a["name"] for a in data.get("authors", [])),
        "cover_urls": [f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg?default=false"],
    }


def lookup_google_books(isbn: str) -> dict | None:
    url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
    try:
        items = fetch_json(url).get("items") or []
    except (urllib.error.URLError, ValueError):
        return None
    if not items:
        return None
    info = items[0]["volumeInfo"]
    covers = []
    thumb = (info.get("imageLinks") or {}).get("thumbnail")
    if thumb:
        covers.append(thumb.replace("http://", "https://").replace("&edge=curl", ""))
    return {
        "title": info.get("title", ""),
        "author": ", ".join(info.get("authors", [])),
        "cover_urls": covers,
    }


def download_cover(isbn: str, urls: list[str]) -> str | None:
    for url in urls:
        try:
            _, body = fetch(url)
        except urllib.error.URLError:
            continue
        # Skip blank 1x1 placeholder images some services return.
        if len(body) < 1000:
            continue
        COVERS_DIR.mkdir(exist_ok=True)
        path = COVERS_DIR / f"{isbn}.jpg"
        path.write_bytes(body)
        return f"covers/{isbn}.jpg"
    return None


# ---------------------------------------------------------------- books.js

def append_entry(entry: dict) -> None:
    text = BOOKS_JS.read_text()
    if f'"{entry["isbn"]}"' in text:
        sys.exit(f'Already in the library: {entry["title"]} ({entry["isbn"]})')
    fields = ", ".join(f"{k}: {json.dumps(v, ensure_ascii=False)}" for k, v in entry.items() if v)
    line = f"  {{ {fields} }},\n"
    end = text.rindex("];")
    BOOKS_JS.write_text(text[:end] + line + text[end:])


def main() -> None:
    parser = argparse.ArgumentParser(description="Add a book to books.js from a link or ISBN.")
    parser.add_argument("source", help="Amazon/other store link, or an ISBN")
    parser.add_argument("--notes", help='e.g. "board book"')
    parser.add_argument("--series", help='e.g. "Elephant & Piggie"')
    parser.add_argument("--title", help="override the looked-up title")
    parser.add_argument("--author", help="override the looked-up author")
    parser.add_argument("--no-author", action="store_true",
                        help="leave the author off, e.g. for a Bible")
    args = parser.parse_args()

    source = args.source.strip()
    if source.lower().startswith(("http://", "https://")) or "." in source.split("/")[0]:
        if not source.lower().startswith("http"):
            source = "https://" + source
        isbn = isbn_from_link(source)
    else:
        isbn = find_isbn(re.sub(r"[\s-]", "", source).upper())
    if not isbn:
        sys.exit("No ISBN found. Kindle links have none; try the print edition's link, "
                 "or pass the ISBN from the back of the book.")

    meta = lookup_open_library(isbn) or {}
    google = lookup_google_books(isbn) or {}
    title = args.title or meta.get("title") or google.get("title")
    author = None if args.no_author else (args.author or meta.get("author") or google.get("author"))
    if not title:
        sys.exit(f"Couldn't find a title for ISBN {isbn}. "
                 "Re-run with --title (and --author) to add it by hand.")

    cover = download_cover(isbn, meta.get("cover_urls", []) + google.get("cover_urls", []))

    entry = {"title": title, "author": author, "isbn": isbn, "series": args.series,
             "notes": args.notes, "cover": cover}
    append_entry(entry)
    print(f"Added: {title}{f' by {author}' if author else ''} (ISBN {isbn})")
    print(f"  cover: {cover or 'none found; the page shows a colored title card'}")


if __name__ == "__main__":
    main()
