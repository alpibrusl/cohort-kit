from __future__ import annotations

from pathlib import Path

from cohortkit.check import check
from cohortkit.loader import load

EXAMPLE = Path(__file__).parent.parent / "examples" / "minimal"


def test_the_minimal_example_is_clean():
    cohort = load(EXAMPLE)
    result = check(cohort, EXAMPLE)
    assert result.ok
    assert result.errors == []


def test_duplicate_session_numbers_are_an_error():
    cohort = load(EXAMPLE)
    cohort.sessions[1].number = 1  # collide with session 1
    result = check(cohort, EXAMPLE)
    assert not result.ok
    assert any("no gaps or repeats" in e for e in result.errors)


def test_missing_fixture_is_an_error():
    cohort = load(EXAMPLE)
    cohort.sessions[0].exercise.fixture_ref = "fixture/does-not-exist.txt"
    result = check(cohort, EXAMPLE)
    assert not result.ok
    assert any("does-not-exist.txt" in e for e in result.errors)


def test_capstone_without_deliverable_is_an_error():
    cohort = load(EXAMPLE)
    cohort.sessions[1].deliverable = None
    result = check(cohort, EXAMPLE)
    assert not result.ok
    assert any("no deliverable set" in e for e in result.errors)


def test_non_capstone_without_exercise_is_an_error():
    cohort = load(EXAMPLE)
    cohort.sessions[0].exercise = None
    result = check(cohort, EXAMPLE)
    assert not result.ok
    assert any("has no exercise" in e for e in result.errors)


def test_empty_rubric_is_an_error():
    cohort = load(EXAMPLE)
    cohort.rubric = []
    result = check(cohort, EXAMPLE)
    assert not result.ok
    assert any("nothing to grade" in e for e in result.errors)


def test_capstone_not_last_is_an_error():
    cohort = load(EXAMPLE)
    cohort.sessions[0].capstone = True
    cohort.sessions[0].deliverable = "something"
    result = check(cohort, EXAMPLE)
    assert not result.ok
    assert any("2 sessions marked capstone" in e for e in result.errors)


def test_book_path_catches_a_chapter_that_does_not_exist(tmp_path):
    book_dir = tmp_path / "fake-book"
    book_dir.mkdir()
    (book_dir / "book.yaml").write_text(
        "chapters:\n  - { file: chapters/01-intro.md, title: 'Chapter 1' }\n"
    )
    cohort = load(EXAMPLE)
    cohort.sessions[1].chapters = [99]
    result = check(cohort, EXAMPLE, book_path=book_dir)
    assert not result.ok
    assert any("chapter 99" in e for e in result.errors)


def test_book_path_warns_about_orphaned_chapters(tmp_path):
    book_dir = tmp_path / "fake-book"
    book_dir.mkdir()
    (book_dir / "book.yaml").write_text(
        "chapters:\n"
        "  - { file: chapters/01-intro.md, title: 'Chapter 1' }\n"
        "  - { file: chapters/02-never-taught.md, title: 'Chapter 2' }\n"
    )
    cohort = load(EXAMPLE)
    cohort.sessions[0].chapters = [1]
    cohort.sessions[1].chapters = [1]
    result = check(cohort, EXAMPLE, book_path=book_dir)
    assert result.ok
    assert any("aren't referenced by any session" in w for w in result.warnings)


def test_session_count_mismatch_is_an_error():
    cohort = load(EXAMPLE)
    cohort.config.session_count = 99
    result = check(cohort, EXAMPLE)
    assert not result.ok
    assert any("session_count: 99" in e for e in result.errors)


def test_capstone_with_an_exercise_is_a_warning():
    cohort = load(EXAMPLE)
    cohort.sessions[1].exercise = cohort.sessions[0].exercise
    result = check(cohort, EXAMPLE)
    assert result.ok
    assert any("also sets an exercise" in w for w in result.warnings)


def test_fixture_outside_the_cohort_is_an_error(tmp_path):
    outside = tmp_path / "leak.txt"
    outside.write_text("x")
    cohort = load(EXAMPLE)
    cohort.sessions[0].exercise.fixture_ref = str(outside)
    result = check(cohort, EXAMPLE)
    assert not result.ok
    assert any("outside" in e for e in result.errors)


def _fake_book(tmp_path, h1: str):
    book_dir = tmp_path / "fake-book"
    (book_dir / "chapters").mkdir(parents=True)
    (book_dir / "book.yaml").write_text(
        "chapters:\n  - { file: chapters/01-intro.md, title: 'Chapter 1 — Retitled' }\n"
    )
    (book_dir / "chapters" / "01-intro.md").write_text(f"# {h1}\n\nBody.\n")
    return book_dir


def test_book_path_catches_a_stale_chapter_title(tmp_path):
    book_dir = _fake_book(tmp_path, "The Real Title")
    cohort = load(EXAMPLE)
    cohort.sessions[0].chapters = [1]
    cohort.sessions[0].chapter_titles = ["An Old Title"]
    cohort.sessions[1].chapters = [1]
    cohort.sessions[1].chapter_titles = []
    result = check(cohort, EXAMPLE, book_path=book_dir)
    assert not result.ok
    assert any("An Old Title" in e and "The Real Title" in e for e in result.errors)


def test_book_path_accepts_a_matching_chapter_title(tmp_path):
    book_dir = _fake_book(tmp_path, "The Real Title")
    cohort = load(EXAMPLE)
    cohort.sessions[0].chapters = [1]
    cohort.sessions[0].chapter_titles = ["the real  title"]
    cohort.sessions[1].chapters = [1]
    cohort.sessions[1].chapter_titles = []
    result = check(cohort, EXAMPLE, book_path=book_dir)
    assert result.ok


def _rubric(tmp_path, rubric: dict):
    """The example cohort with rubric.yaml replaced."""
    import shutil

    import yaml

    d = tmp_path / "cohort"
    shutil.copytree(EXAMPLE, d)
    (d / "rubric.yaml").write_text(yaml.dump(rubric), encoding="utf-8")
    return d


def test_a_scored_rubric_must_describe_every_cell(tmp_path):
    """A grid with holes is worse than no grid: the holes are exactly where two
    assessors disagree."""
    d = _rubric(
        tmp_path,
        {
            "scale": {"levels": ["No", "Yes"], "pass_level": "Yes"},
            "dimensions": [{"name": "Specificity", "description": "d", "levels": {"Yes": "y"}}],
        },
    )
    result = check(load(d), d)
    assert any("describes no No" in e for e in result.errors)


def test_a_pass_level_has_to_be_on_the_scale(tmp_path):
    d = _rubric(
        tmp_path,
        {
            "scale": {"levels": ["No", "Yes"], "pass_level": "Excellent"},
            "dimensions": [
                {"name": "S", "description": "d", "levels": {"No": "n", "Yes": "y"}}
            ],
        },
    )
    result = check(load(d), d)
    assert any("not one of its levels" in e for e in result.errors)


def test_levels_without_a_scale_are_an_error_not_a_silent_drop(tmp_path):
    d = _rubric(
        tmp_path,
        {"dimensions": [{"name": "S", "description": "d", "levels": {"Yes": "y"}}]},
    )
    result = check(load(d), d)
    assert any("declares no scale" in e for e in result.errors)


def test_a_pass_level_at_the_bottom_of_the_scale_is_a_warning(tmp_path):
    d = _rubric(
        tmp_path,
        {
            "scale": {"levels": ["No", "Yes"], "pass_level": "No"},
            "dimensions": [
                {"name": "S", "description": "d", "levels": {"No": "n", "Yes": "y"}}
            ],
        },
    )
    result = check(load(d), d)
    assert any("every capstone passes by definition" in w for w in result.warnings)
