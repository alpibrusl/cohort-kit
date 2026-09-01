from __future__ import annotations

from pathlib import Path

import pytest
from content_kit_core._errors import NotFoundError

from cohortkit.loader import load

EXAMPLE = Path(__file__).parent.parent / "examples" / "minimal"


def test_loads_the_minimal_example():
    cohort = load(EXAMPLE)
    assert cohort.config.title == "Minimal Example Cohort"
    assert len(cohort.sessions) == 2
    assert len(cohort.rubric) == 2


def test_sessions_keep_their_order_and_fields():
    cohort = load(EXAMPLE)
    first, second = cohort.sessions
    assert first.number == 1
    assert first.exercise is not None
    assert first.exercise.fixture_ref == "fixture/sample.txt"
    assert second.capstone is True
    assert second.deliverable is not None
    assert second.exercise is None


def test_missing_cohort_yaml_raises_with_a_hint(tmp_path):
    with pytest.raises(NotFoundError) as exc_info:
        load(tmp_path)
    assert exc_info.value.hint is not None


def test_malformed_sessions_file_raises(tmp_path):
    (tmp_path / "cohort.yaml").write_text(
        (EXAMPLE / "cohort.yaml").read_text(encoding="utf-8"), encoding="utf-8"
    )
    (tmp_path / "sessions.yaml").write_text("sessions:\n  - title: missing the number field\n")
    (tmp_path / "rubric.yaml").write_text("dimensions: []\n")
    with pytest.raises(NotFoundError):
        load(tmp_path)
