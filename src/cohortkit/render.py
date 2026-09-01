"""Build the two artifacts a cohort's source actually compiles to."""

from __future__ import annotations

from pathlib import Path

from ._html import render_page
from .book_content import load_chapter_content
from .schema import Cohort


def build(
    cohort: Cohort, out_dir: Path | str, *, book_path: Path | None = None
) -> tuple[Path, Path]:
    """Render the student handout and facilitator guide, write both under
    `out_dir`, and return their paths. Both are build artifacts — derived
    from the session/rubric source, never hand-edited, never committed.

    `book_path`, when given, embeds each session's actual chapter text from
    the real book (its own repo root) — reading along needs nothing but the
    handout itself, no separate PDF or EPUB."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    book_chapters = load_chapter_content(book_path) if book_path is not None else None

    handout_path = out_dir / "handout.html"
    handout_path.write_text(
        render_page(cohort, audience="handout", book_chapters=book_chapters), encoding="utf-8"
    )

    guide_path = out_dir / "facilitator-guide.html"
    guide_path.write_text(
        render_page(cohort, audience="facilitator", book_chapters=book_chapters),
        encoding="utf-8",
    )

    return handout_path, guide_path
