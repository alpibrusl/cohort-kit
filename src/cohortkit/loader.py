"""Load a cohort's three source files from a directory into a `Cohort`."""

from __future__ import annotations

from pathlib import Path

import yaml
from content_kit_core._errors import NotFoundError
from pydantic import ValidationError

from .schema import Cohort, CohortConfig, RubricDimension, RubricScale, Session


def _read_yaml(path: Path) -> dict:
    if not path.exists():
        raise NotFoundError(
            f"{path.name} not found in {path.parent}",
            hint=f"A cohort directory needs {path.name} — see examples/minimal for the shape.",
        )
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data or {}


def load(cohort_dir: Path | str) -> Cohort:
    """Load ``cohort.yaml``, the sessions file it names, and the rubric file
    it names, from ``cohort_dir``. Raises ``content_kit_core`` errors (not
    bare exceptions) so the CLI can report a hint, not just a traceback."""
    cohort_dir = Path(cohort_dir)

    config_data = _read_yaml(cohort_dir / "cohort.yaml")
    try:
        config = CohortConfig.model_validate(config_data)
    except ValidationError as e:
        raise NotFoundError(
            f"cohort.yaml is malformed: {e}",
            hint="Check it against the CohortConfig fields in schema.py.",
        ) from e

    sessions_data = _read_yaml(cohort_dir / config.sessions_file)
    raw_sessions = sessions_data.get("sessions", [])
    try:
        sessions = [Session.model_validate(s) for s in raw_sessions]
    except ValidationError as e:
        raise NotFoundError(f"{config.sessions_file} is malformed: {e}") from e

    rubric_data = _read_yaml(cohort_dir / config.rubric_file)
    raw_rubric = rubric_data.get("dimensions", [])
    try:
        rubric = [RubricDimension.model_validate(d) for d in raw_rubric]
    except ValidationError as e:
        raise NotFoundError(f"{config.rubric_file} is malformed: {e}") from e

    # `scale` is optional: without it the rubric is descriptive, which is the
    # right shape for a capstone that produces an audit rather than a grade.
    raw_scale = rubric_data.get("scale")
    try:
        scale = RubricScale.model_validate(raw_scale) if raw_scale else None
    except ValidationError as e:
        raise NotFoundError(
            f"{config.rubric_file} has a malformed scale: {e}",
            hint="A scale needs `levels` (two or more, worst first) and a "
            "`pass_level` naming one of them.",
        ) from e

    return Cohort(
        config=config,
        sessions=sessions,
        rubric=rubric,
        scale=scale,
        source_dir=cohort_dir,
    )
