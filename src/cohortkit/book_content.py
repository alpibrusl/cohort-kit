"""Load a book's actual chapter text, so a handout can let a student read the
material a session draws on right there — no separate PDF or EPUB needed,
and no dependency on bookkit itself, just the same book.yaml + Markdown
files every book in the series already is.

Chapter numbers come from the same convention `check.py` already relies on:
the leading digits in each chapter file's own name.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import markdown
import yaml
from content_kit_core._errors import NotFoundError

_CHAPTER_FILE_RE = re.compile(r"^(\d+)-")
_H1_RE = re.compile(r"^#\s+(.+?)\s*$")


@dataclass
class ChapterContent:
    number: int
    title: str
    html: str


def load_chapter_content(book_path: Path) -> dict[int, ChapterContent]:
    """Read every chapter book.yaml lists and render it to HTML, keyed by
    chapter number. A chapter file that's missing or whose name carries no
    leading number is skipped rather than failing the whole load — the same
    tolerance `check.py` already has, since it's `check` that's responsible
    for flagging a broken reference, not this."""
    book_yaml = book_path / "book.yaml"
    if not book_yaml.exists():
        raise NotFoundError(
            f"no book.yaml found at {book_path}",
            hint="Pass the book's own repo root as --book-path.",
        )
    with book_yaml.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)

    chapters: dict[int, ChapterContent] = {}
    for entry in data.get("chapters", []):
        filename = Path(entry["file"]).name
        match = _CHAPTER_FILE_RE.match(filename)
        if not match:
            continue
        number = int(match.group(1))
        chapter_path = book_path / entry["file"]
        if not chapter_path.exists():
            continue

        lines = chapter_path.read_text(encoding="utf-8").splitlines()
        title = None
        if lines and _H1_RE.match(lines[0]):
            title = _H1_RE.match(lines[0]).group(1).strip()
            lines = lines[1:]
        body_html = markdown.markdown(
            "\n".join(lines), extensions=["extra", "smarty", "sane_lists"]
        )
        chapters[number] = ChapterContent(
            number=number, title=title or f"Chapter {number}", html=body_html
        )
    return chapters
