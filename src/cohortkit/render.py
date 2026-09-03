"""Build the two artifacts a cohort's source actually compiles to."""

from __future__ import annotations

from pathlib import Path

from ._html import render_page
from .book_content import load_chapter_content
from .schema import Cohort


def build(
    cohort: Cohort,
    out_dir: Path | str,
    *,
    book_path: Path | None = None,
    self_paced: bool = False,
) -> tuple[Path, Path]:
    """Render the cohort's documents, write them under `out_dir`, and return
    their paths. All are build artifacts — derived from the session/rubric
    source, never hand-edited, never committed.

    By default that is a facilitated cohort: a student handout and a
    facilitator guide, differing in exactly one field. `self_paced` renders
    the same curriculum for a reader working alone instead — one handbook, no
    guide, and no live segment, because "as a group" and "live walk" read as
    instructions for a room that reader is not in.

    `book_path`, when given, embeds each session's actual chapter text from
    the real book (its own repo root) — reading along needs nothing but the
    handout itself, no separate PDF or EPUB."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    book_chapters = load_chapter_content(book_path) if book_path is not None else None

    if self_paced:
        handbook_path = out_dir / "self-paced-handbook.html"
        handbook_path.write_text(
            render_page(cohort, audience="self-paced", book_chapters=book_chapters),
            encoding="utf-8",
        )
        return handbook_path, handbook_path

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
