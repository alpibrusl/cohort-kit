"""cohortkit — turn a book's chapters into a live, facilitated curriculum.

Sessions and a rubric are the source, same discipline as a bookkit manuscript:
plain data, checked in CI, with the student handout and facilitator guide as
build artifacts, never hand-edited and never committed.
"""

from __future__ import annotations

__version__ = "0.2.0"

from .loader import load
from .render import build
from .schema import Cohort, CohortConfig, Exercise, RubricDimension, Session

VERSION = "0.1.0"

__all__ = [
    "VERSION",
    "Cohort",
    "CohortConfig",
    "Exercise",
    "RubricDimension",
    "Session",
    "build",
    "load",
]
