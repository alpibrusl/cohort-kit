from __future__ import annotations

from pathlib import Path

import pytest
from content_kit_core._errors import NotFoundError

from cohortkit._html import render_page
from cohortkit.book_content import load_chapter_content
from cohortkit.loader import load

EXAMPLE = Path(__file__).parent.parent / "examples" / "minimal"


def _make_book(tmp_path: Path) -> Path:
    book_dir = tmp_path / "fake-book"
    (book_dir / "chapters").mkdir(parents=True)
    (book_dir / "book.yaml").write_text(
        "chapters:\n"
        "  - { file: chapters/01-intro.md, title: 'Chapter 1' }\n"
        "  - { file: chapters/02-second.md, title: 'Chapter 2' }\n",
        encoding="utf-8",
    )
    (book_dir / "chapters" / "01-intro.md").write_text(
        "# The Handoff\n\n"
        "> **Part I**\n\n"
        "This is the first paragraph, with *emphasis* and a `code span`.\n",
        encoding="utf-8",
    )
    (book_dir / "chapters" / "02-second.md").write_text(
        "# The Minimum Bar\n\nSecond chapter body.\n",
        encoding="utf-8",
    )
    return book_dir


def test_load_chapter_content_reads_title_and_renders_markdown(tmp_path):
    book_dir = _make_book(tmp_path)

    chapters = load_chapter_content(book_dir)

    assert set(chapters) == {1, 2}
    assert chapters[1].title == "The Handoff"
    assert "<em>emphasis</em>" in chapters[1].html
    assert "<code>code span</code>" in chapters[1].html
    assert "<blockquote>" in chapters[1].html
    assert "# The Handoff" not in chapters[1].html


def test_load_chapter_content_raises_without_book_yaml(tmp_path):
    with pytest.raises(NotFoundError):
        load_chapter_content(tmp_path / "nowhere")


def test_load_chapter_content_skips_a_missing_file(tmp_path):
    book_dir = _make_book(tmp_path)
    (book_dir / "chapters" / "02-second.md").unlink()

    chapters = load_chapter_content(book_dir)

    assert set(chapters) == {1}


def test_render_page_embeds_referenced_chapters(tmp_path):
    book_dir = _make_book(tmp_path)
    book_chapters = load_chapter_content(book_dir)
    cohort = load(EXAMPLE)
    cohort.sessions[0].chapters = [1]

    html = render_page(cohort, audience="handout", book_chapters=book_chapters)

    assert "The Handoff" in html
    assert "This is the first paragraph" in html
    assert html.count("<div") == html.count("</div>")


def test_render_page_without_book_chapters_has_no_reading_section():
    cohort = load(EXAMPLE)

    html = render_page(cohort, audience="handout")

    assert 'class="chapter-reading"' not in html
