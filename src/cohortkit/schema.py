"""The shape of a cohort curriculum: a config, a sequence of sessions, and a rubric.

Three files make up a cohort's source, same spirit as a book's ``book.yaml`` +
``glossary.yaml``: ``cohort.yaml`` (title, format, which book this is derived
from), ``sessions.yaml`` (the sequence), and ``rubric.yaml`` (how the capstone
is assessed). Everything here is data — no rendering logic lives in this file.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field


class Exercise(BaseModel):
    """The hands-on activity for one session — the thing that makes it a
    taught session rather than an assigned reading."""

    name: str
    description: str
    fixture_ref: str | None = None
    """Path (relative to the cohort's own repo) to shared fixture material
    this exercise uses, if any — e.g. a seeded sample repo reused across
    several sessions. Checked for existence by ``check.py``, never guessed at
    by the renderer if missing."""


class Session(BaseModel):
    """One taught session: what it covers, what happens in the room, what a
    student actually does, and how anyone — student or facilitator — knows
    it landed."""

    number: int = Field(gt=0)
    title: str
    chapters: list[int] = Field(default_factory=list)
    """Chapter numbers in the source book this session draws on. Checked
    against the book's own book.yaml when ``--book-path`` is given to
    ``cohortkit check``, so a chapter renumber in the book can't silently
    strand a session's reference."""
    chapter_titles: list[str] = Field(default_factory=list)
    in_session: str
    """What actually happens live — discussion, demo, walkthrough. Distinct
    from the exercise: this is facilitator-led, the exercise is student-led."""
    solo: str | None = None
    """What a reader working alone does instead of the live segment.

    Most `in_session` blocks assume a room — "as a group", "live walk",
    "tabletop" — and rendering them to someone reading on their own hands them
    instructions for a room they are not in. Where a session's live segment
    teaches something a solo reader still needs, restate it here as something
    they can do alone; where it is purely a group activity, leave this unset
    and the self-paced handout omits the segment rather than faking it."""
    exercise: Exercise | None = None
    """Required on a non-capstone session, absent on a capstone one — a
    capstone sets `deliverable` instead. `check.py` enforces the split;
    the schema only enforces the shape of whichever one is present."""
    checkpoint: str
    """What tells you the session landed — a concrete, checkable thing a
    student produces, not a feeling that the material was covered."""
    facilitator_notes: str | None = None
    """Pacing, common pitfalls, how to run an exercise that needs a specific
    setup — shown in the facilitator guide only, never the student handout.
    Optional on purpose: a straightforward session doesn't need one."""
    capstone: bool = False
    deliverable: str | None = None
    """Set instead of (not alongside) an exercise on a capstone session —
    the thing being assessed against the rubric, rather than practiced."""


class RubricScale(BaseModel):
    """The columns of a scored rubric, declared once for the whole grid.

    Optional. Without it the rubric renders as it always has -- dimensions and
    what earns them -- which is the right shape for a cohort whose capstone
    produces an honest audit rather than a grade.

    With it the rubric becomes gradable, which is what a company's L&D function
    needs in order to report completion to somebody who was not in the room.
    Level names live here rather than on each dimension so the rendered rubric
    is a grid with consistent columns; dimensions that each invented their own
    scale would not be a rubric at all.
    """

    levels: list[str] = Field(min_length=2)
    """Ordered worst to best. The last is not automatically the pass mark."""

    pass_level: str
    """Which level is the bar, by name. Must be one of ``levels``."""

    all_dimensions: bool = True
    """Whether the bar must be met on every dimension.

    True by default, and deliberately: this material does not let a strong
    showing on one axis compensate for a missing one. A capstone that names no
    owner is not rescued by checking presence honestly.
    """


class RubricDimension(BaseModel):
    """One axis the capstone is actually judged on. Kept small on purpose —
    a rubric with more than a handful of dimensions stops being usable as a
    rubric and starts being a checklist pretending to be one."""

    name: str
    description: str

    levels: dict[str, str] = {}
    """What each level looks like on this dimension, keyed by level name.

    Empty unless the rubric declares a scale. When one is declared, every
    dimension has to describe every level -- a grid with holes in it is worse
    than no grid, because the holes are exactly where two assessors disagree.
    """


class CohortConfig(BaseModel):
    """The top-level ``cohort.yaml`` — identity and format, not content."""

    title: str
    subtitle: str
    book: str
    """The book's own repo slug this cohort is derived from, e.g.
    'prompt-to-production' — not a display name."""
    book_title: str
    session_count: int = Field(gt=0)
    session_length_hours: float = Field(gt=0)
    cohort_size_min: int = Field(gt=0)
    cohort_size_max: int = Field(gt=0)
    format: str
    prerequisite: str
    sessions_file: str = "sessions.yaml"
    rubric_file: str = "rubric.yaml"


class Cohort(BaseModel):
    """A fully loaded cohort — config, sessions, rubric — ready to check or
    render. What ``loader.load()`` returns."""

    config: CohortConfig
    sessions: list[Session]
    rubric: list[RubricDimension]
    source_dir: Path | None = None
    """Where this cohort was loaded from. The build stamp describes this, not
    the output directory -- `--out` often points somewhere temporary."""

    scale: RubricScale | None = None
    """Present only when rubric.yaml declares one. None means the rubric is
    descriptive rather than scored, and renders exactly as it always did."""


class SessionProgress(BaseModel):
    """One session's checkbox state, as the handout's own JS tracks it —
    nothing more than whether the checkpoint was marked done, and when."""

    number: int = Field(gt=0)
    title: str
    complete: bool
    completed_at: datetime | None = None
    """None when `complete` is False — a session can't have been completed
    at no particular time."""
    note: str | None = None
    """Free-text, optional: what got in the way, or anything else the
    student wants the instructor to see about this session specifically.
    Deliberately not another checkbox — the rubric already rewards an
    honest "not done" over a false "done"; a note is where the honesty
    goes when a checkbox can't carry it."""


class ProgressExport(BaseModel):
    """What the handout's "Export progress" button actually downloads, and
    what `cohortkit progress` reads back in. The whole point of this shape
    is that it's the only channel between a student's browser and an
    instructor — no account, no server, just a file someone sends."""

    cohort_title: str
    student_name: str
    exported_at: datetime
    sessions: list[SessionProgress]
