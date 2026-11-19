#!/usr/bin/env python3
"""Add a book to books.js from a store link or an ISBN.

Usage:
    python3 tools/add_book.py <amazon-or-other-link | ISBN> [--notes "board book"] [--series "..."]
    python3 tools/add_book.py <link | ISBN> --cover ~/Downloads/cover.avif

--cover uses an image you saved (any format macOS can open, e.g. an .avif
from Amazon) instead of downloading one. For a book already in books.js it
replaces that book's cover and changes nothing else.

The script finds the book's ISBN, looks up its title and author on
Open Library (falling back to Google Books), downloads the cover into
covers/, and appends an entry to books.js.

Amazon links for most print books carry the ISBN-10 as the product id.
Links whose id starts with B0 (many board books, and all Kindle editions)
carry no ISBN; for those the script searches Open Library using the title
words in the link and prints the match so you can check the edition.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import string
import subprocess
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


def find_isbn13(text: str) -> str | None:
    """Like find_isbn, but ISBN-13 only, for searching whole web pages,
    where stray 10-digit numbers would pass the ISBN-10 checksum."""
    for m in re.finditer(r"(?<![\dX])97[89][\d-]{10,14}(?![\d])", text):
        digits = m.group().replace("-", "")
        if isbn13_valid(digits):
            return digits
    return None


# ---------------------------------------------------------------- HTTP

def fetch(url: str) -> tuple[str, bytes]:
    """GET url, returning (final_url, body). Raises on failure."""
    # Percent-encode non-ASCII characters (e.g. an accented author name in an
    # Amazon slug); existing %-escapes and URL punctuation pass through.
    url = urllib.parse.quote(url, safe=string.punctuation)
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
        final_url, body = e.filename or link, b""
    except urllib.error.URLError as e:
        print(f"Could not open {link}: {e.reason}", file=sys.stderr)
        final_url, body = link, b""
    if final_url != link:
        isbn = isbn_from_url_text(final_url)
        if isbn:
            return isbn
    isbn = find_isbn13(body.decode("utf-8", "replace"))
    if isbn:
        return isbn
    return isbn_from_title_search(final_url) or isbn_from_title_search(link)


def slug_words(url: str) -> str | None:
    """Title/author words from a store URL's slug, e.g.
    amazon.com/Dressed-Belly-Button-Lucie-Brunellière/dp/B0D6KR8CGT."""
    path = urllib.parse.unquote(urllib.parse.urlsplit(url).path)
    m = re.search(r"/([^/]+)/(?:dp|gp/product)/", path)
    if m:
        slug = m.group(1)
    else:
        # Other stores: the longest path segment that contains letters.
        parts = [p for p in path.split("/") if re.search(r"[^\W\d_]", p)]
        slug = max(parts, key=len, default="")
    words = re.sub(r"[-_+]+", " ", slug).strip()
    return words if len(words.split()) >= 2 else None


def isbn_from_title_search(url: str) -> str | None:
    words = slug_words(url)
    if not words:
        return None
    query = urllib.parse.urlencode({"q": words, "fields": "title,author_name,isbn", "limit": 5})
    try:
        docs = fetch_json(f"https://openlibrary.org/search.json?{query}").get("docs") or []
    except (urllib.error.URLError, ValueError):
        return None
    for doc in docs:
        isbn = next((i for i in doc.get("isbn", []) if isbn13_valid(i)), None)
        if isbn:
            authors = ", ".join(doc.get("author_name", [])) or "unknown author"
            print(f'No ISBN in the link; searched Open Library for "{words}" and matched:\n'
                  f'  {doc.get("title")} by {authors} (ISBN {isbn})\n'
                  "  If that's the wrong book or edition, re-run with the ISBN from the book.")
            return isbn
    return None


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


def save_local_cover(isbn: str, image: str) -> str:
    """Convert an image file to covers/<isbn>.jpg, at most 800px on a side."""
    src = Path(image).expanduser()
    if not src.is_file():
        sys.exit(f"Cover image not found: {src}")
    COVERS_DIR.mkdir(exist_ok=True)
    dst = COVERS_DIR / f"{isbn}.jpg"
    if shutil.which("sips"):
        result = subprocess.run(
            ["sips", "-s", "format", "jpeg", "-s", "formatOptions", "85", "-Z", "800",
             str(src), "--out", str(dst)],
            capture_output=True, text=True)
        if result.returncode != 0 or not dst.is_file():
            sys.exit(f"Couldn't convert {src} to JPEG:\n{result.stderr or result.stdout}")
    elif src.suffix.lower() in (".jpg", ".jpeg"):
        shutil.copyfile(src, dst)
    else:
        sys.exit("Converting images needs macOS's sips; pass a .jpg instead.")
    return f"covers/{isbn}.jpg"


# ---------------------------------------------------------------- books.js

def find_entry_line(isbn: str) -> str | None:
    for line in BOOKS_JS.read_text().splitlines():
        if f'isbn: "{isbn}"' in line:
            return line
    return None


def set_cover(line: str, cover: str) -> None:
    field = f"cover: {json.dumps(cover)}"
    if re.search(r'cover: "[^"]*"', line):
        new = re.sub(r'cover: "[^"]*"', field, line)
    else:
        new = re.sub(r"\s*\},\s*$", f", {field} }},", line)
    text = BOOKS_JS.read_text()
    BOOKS_JS.write_text(text.replace(line, new, 1))


def append_entry(entry: dict) -> None:
    text = BOOKS_JS.read_text()
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
    parser.add_argument("--cover", metavar="IMAGE",
                        help="use this image file as the cover (also updates an existing book)")
    args = parser.parse_args()

    source = args.source.strip()
    if source.lower().startswith(("http://", "https://")) or "." in source.split("/")[0]:
        if not source.lower().startswith("http"):
            source = "https://" + source
        isbn = isbn_from_link(source)
    else:
        isbn = find_isbn(re.sub(r"[\s-]", "", source).upper())
    if not isbn:
        sys.exit("No ISBN found in the link, and a title search came up empty. "
                 "Pass the ISBN from the back of the book instead.")

    existing = find_entry_line(isbn)
    if existing:
        if not args.cover:
            sys.exit(f"Already in the library (ISBN {isbn}):\n{existing.strip()}\n"
                     "Use --cover to change its cover.")
        cover = save_local_cover(isbn, args.cover)
        set_cover(existing, cover)
        print(f"Updated cover for ISBN {isbn}: {cover}")
        return

    meta = lookup_open_library(isbn) or {}
    google = lookup_google_books(isbn) or {}
    title = args.title or meta.get("title") or google.get("title")
    author = None if args.no_author else (args.author or meta.get("author") or google.get("author"))
    if not title:
        sys.exit(f"Couldn't find a title for ISBN {isbn}. "
                 "Re-run with --title (and --author) to add it by hand.")

    if args.cover:
        cover = save_local_cover(isbn, args.cover)
    else:
        cover = download_cover(isbn, meta.get("cover_urls", []) + google.get("cover_urls", []))

    entry = {"title": title, "author": author, "isbn": isbn, "series": args.series,
             "notes": args.notes, "cover": cover}
    append_entry(entry)
    print(f"Added: {title}{f' by {author}' if author else ''} (ISBN {isbn})")
    print(f"  cover: {cover or 'none found; the page shows a colored title card'}")


if __name__ == "__main__":
    main()
