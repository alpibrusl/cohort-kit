"""Curriculum-integrity checks — the cohort equivalent of bookkit's term
linter. Same instinct: catch the thing a human proofreader would eventually
find, automatically, before it ships.

Every check here answers one question: does this claim about the curriculum
actually hold, checked against the real files, not just against itself.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .schema import Cohort

_CHAPTER_FILE_RE = re.compile(r"^(\d+)-")
_H1_RE = re.compile(r"^#\s+(.+?)\s*$")
_TITLE_OVERRIDE_RE = re.compile(r"^Chapter\s+\d+\s+[—–-]+\s+(.+)$")


@dataclass
class CheckResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def _book_chapter_numbers(book_path: Path) -> set[int]:
    """Read a book repo's book.yaml and return the chapter numbers it
    actually has, parsed from each chapter file's own leading number —
    the same convention every book in the series already follows."""
    book_yaml = book_path / "book.yaml"
    if not book_yaml.exists():
        raise FileNotFoundError(f"no book.yaml found at {book_path}")
    with book_yaml.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    numbers = set()
    for entry in data.get("chapters", []):
        filename = Path(entry["file"]).name
        m = _CHAPTER_FILE_RE.match(filename)
        if m:
            numbers.add(int(m.group(1)))
    return numbers


def _book_chapter_titles(book_path: Path) -> dict[int, str]:
    """Chapter number -> the title the book itself uses: the chapter file's
    own H1 when the file exists, else the book.yaml title with any
    "Chapter N — " prefix stripped. A chapter whose title can't be resolved
    either way is simply absent, so nothing is compared against a guess."""
    book_yaml = book_path / "book.yaml"
    with book_yaml.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    titles: dict[int, str] = {}
    for entry in data.get("chapters", []):
        filename = Path(entry["file"]).name
        m = _CHAPTER_FILE_RE.match(filename)
        if not m:
            continue
        number = int(m.group(1))
        chapter_path = book_path / entry["file"]
        if chapter_path.exists():
            for line in chapter_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                h1 = _H1_RE.match(line)
                if h1:
                    titles[number] = h1.group(1)
                break
        if number not in titles:
            override = _TITLE_OVERRIDE_RE.match(str(entry.get("title") or ""))
            if override:
                titles[number] = override.group(1).strip()
    return titles


def _norm(title: str) -> str:
    return " ".join(title.split()).casefold()


def check(cohort: Cohort, cohort_dir: Path, book_path: Path | None = None) -> CheckResult:
    result = CheckResult()

    # --- cohort.yaml's own count agrees with the sequence it describes ---
    if cohort.config.session_count != len(cohort.sessions):
        result.errors.append(
            f"cohort.yaml says session_count: {cohort.config.session_count} but "
            f"sessions.yaml has {len(cohort.sessions)} session(s) — one of them is stale"
        )

    # --- session numbering: unique, sequential from 1, no gaps ---
    numbers = [s.number for s in cohort.sessions]
    if sorted(numbers) != list(range(1, len(numbers) + 1)):
        result.errors.append(
            f"session numbers must run 1..{len(numbers)} with no gaps or repeats; "
            f"got {sorted(numbers)}"
        )

    # --- exactly one capstone, and it's the last session ---
    capstones = [s for s in cohort.sessions if s.capstone]
    if len(capstones) == 0:
        result.warnings.append("no session is marked capstone: true — no closing deliverable")
    elif len(capstones) > 1:
        result.errors.append(
            f"{len(capstones)} sessions marked capstone — a curriculum closes once, not twice"
        )
    elif cohort.sessions and capstones[0].number != max(numbers):
        result.errors.append(
            f"the capstone (session {capstones[0].number}) isn't the last session "
            f"(session {max(numbers)}) — a capstone that isn't the ending is a contradiction"
        )

    # --- capstone sets a deliverable; every other session sets an exercise ---
    for s in cohort.sessions:
        if s.capstone and not s.deliverable:
            result.errors.append(f"session {s.number} is a capstone but has no deliverable set")
        if not s.capstone and s.deliverable:
            result.warnings.append(
                f"session {s.number} sets deliverable but isn't marked capstone — "
                "intentional, or should this be an exercise instead?"
            )
        if not s.capstone and not s.exercise:
            result.errors.append(
                f"session {s.number} isn't a capstone and has no exercise — "
                "a session with nothing hands-on is just the reading, live"
            )
        if s.capstone and s.exercise:
            result.warnings.append(
                f"session {s.number} is a capstone and also sets an exercise — "
                "the deliverable is what the rubric assesses; is the exercise meant "
                "to be part of it?"
            )

    # --- fixture references stay inside the cohort and actually exist ---
    cohort_root = cohort_dir.resolve()
    for s in cohort.sessions:
        ref = s.exercise.fixture_ref if s.exercise else None
        if not ref:
            continue
        target = (cohort_dir / ref).resolve()
        if not target.is_relative_to(cohort_root):
            result.errors.append(
                f"session {s.number}'s exercise references fixture '{ref}', "
                f"which resolves outside {cohort_dir} — fixtures live under the cohort directory"
            )
        elif not target.exists():
            result.errors.append(
                f"session {s.number}'s exercise references fixture '{ref}', "
                f"which doesn't exist under {cohort_dir}"
            )

    # --- rubric: present, and small enough to actually use in a session ---
    if not cohort.rubric:
        result.errors.append("rubric.yaml has no dimensions — the capstone has nothing to grade")
    elif len(cohort.rubric) > 6:
        result.warnings.append(
            f"rubric has {len(cohort.rubric)} dimensions — past 5 or 6 it stops being "
            "gradable live in a session and turns into a checklist wearing a rubric's name"
        )

    # --- the scale, if there is one: a grid with holes is worse than no grid ---
    scale = cohort.scale
    if scale is None:
        scored = [d.name for d in cohort.rubric if d.levels]
        if scored:
            result.errors.append(
                f"{len(scored)} dimension(s) describe levels but rubric.yaml declares no "
                f"scale — add one, or the descriptions render nowhere: {', '.join(scored)}"
            )
    else:
        if len(set(scale.levels)) != len(scale.levels):
            result.errors.append(
                f"scale repeats a level name: {scale.levels} — level names are the grid's "
                "column headers and have to be distinct"
            )
        if scale.pass_level not in scale.levels:
            result.errors.append(
                f"scale's pass_level '{scale.pass_level}' is not one of its levels "
                f"({', '.join(scale.levels)})"
            )
        elif scale.pass_level == scale.levels[0]:
            result.warnings.append(
                f"the pass level '{scale.pass_level}' is the lowest on the scale, so every "
                "capstone passes by definition — check that is what was meant"
            )
        for d in cohort.rubric:
            missing = [lv for lv in scale.levels if lv not in d.levels]
            if missing:
                result.errors.append(
                    f"rubric dimension '{d.name}' describes no {', '.join(missing)} — a "
                    "scored rubric needs every cell, because the empty ones are exactly "
                    "where two assessors disagree"
                )
            extra = [lv for lv in d.levels if lv not in scale.levels]
            if extra:
                result.errors.append(
                    f"rubric dimension '{d.name}' describes '{', '.join(extra)}', which the "
                    "scale does not list — it will render nowhere"
                )

    # --- chapter references, cross-checked against the real book if given ---
    if book_path is not None:
        try:
            book_chapters = _book_chapter_numbers(book_path)
        except FileNotFoundError as e:
            result.errors.append(str(e))
            book_chapters = None
        if book_chapters is not None:
            referenced: set[int] = set()
            for s in cohort.sessions:
                for ch in s.chapters:
                    referenced.add(ch)
                    if ch not in book_chapters:
                        result.errors.append(
                            f"session {s.number} references chapter {ch}, which doesn't "
                            f"exist in {book_path.name}'s book.yaml — renumbered or removed?"
                        )
            orphaned = book_chapters - referenced
            if orphaned:
                result.warnings.append(
                    f"chapters {sorted(orphaned)} in {book_path.name} aren't referenced by "
                    "any session — deliberate, or a gap in the curriculum?"
                )

            # --- chapter_titles, if given, are the titles the book actually uses ---
            book_titles = _book_chapter_titles(book_path)
            for s in cohort.sessions:
                if not s.chapter_titles:
                    continue
                if len(s.chapter_titles) != len(s.chapters):
                    result.errors.append(
                        f"session {s.number} lists {len(s.chapter_titles)} chapter_titles for "
                        f"{len(s.chapters)} chapters — they're positional, one per chapter"
                    )
                    continue
                for ch, given in zip(s.chapters, s.chapter_titles, strict=True):
                    actual = book_titles.get(ch)
                    if actual is not None and _norm(actual) != _norm(given):
                        result.errors.append(
                            f"session {s.number} calls chapter {ch} '{given}' but "
                            f"{book_path.name} titles it '{actual}' — retitled in the book?"
                        )

    return result
