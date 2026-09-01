"""Build the two artifacts a cohort's source actually compiles to."""

from __future__ import annotations

from pathlib import Path

from ._html import render_page
from .schema import Cohort


def build(cohort: Cohort, out_dir: Path | str) -> tuple[Path, Path]:
    """Render the student handout and facilitator guide, write both under
    `out_dir`, and return their paths. Both are build artifacts — derived
    from the session/rubric source, never hand-edited, never committed."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    handout_path = out_dir / "handout.html"
    handout_path.write_text(render_page(cohort, audience="handout"), encoding="utf-8")

    guide_path = out_dir / "facilitator-guide.html"
    guide_path.write_text(render_page(cohort, audience="facilitator"), encoding="utf-8")

    return handout_path, guide_path
