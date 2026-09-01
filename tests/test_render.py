from __future__ import annotations

from pathlib import Path

from cohortkit.loader import load
from cohortkit.render import build

EXAMPLE = Path(__file__).parent.parent / "examples" / "minimal"


def test_build_writes_both_artifacts(tmp_path):
    cohort = load(EXAMPLE)
    handout_path, guide_path = build(cohort, tmp_path)
    assert handout_path.exists()
    assert guide_path.exists()


def test_facilitator_notes_appear_only_in_the_guide(tmp_path):
    cohort = load(EXAMPLE)
    handout_path, guide_path = build(cohort, tmp_path)
    note = "Runs long the first time"
    assert note not in handout_path.read_text(encoding="utf-8")
    assert note in guide_path.read_text(encoding="utf-8")


def test_rubric_appears_in_both_the_handout_and_the_guide(tmp_path):
    cohort = load(EXAMPLE)
    handout_path, guide_path = build(cohort, tmp_path)
    for path in (handout_path, guide_path):
        text = path.read_text(encoding="utf-8")
        assert "Capstone rubric" in text
        assert "Specificity" in text


def test_output_is_well_formed_enough_to_have_matching_tags(tmp_path):
    cohort = load(EXAMPLE)
    handout_path, _ = build(cohort, tmp_path)
    text = handout_path.read_text(encoding="utf-8")
    assert text.count("<div") == text.count("</div>")
    assert text.startswith("<!doctype html>")


def test_feedback_note_textarea_appears_only_in_the_handout(tmp_path):
    cohort = load(EXAMPLE)
    handout_path, guide_path = build(cohort, tmp_path)
    assert 'data-session-note="1"' in handout_path.read_text(encoding="utf-8")
    assert 'data-session-note="1"' not in guide_path.read_text(encoding="utf-8")


def test_script_block_cannot_be_closed_by_a_title(tmp_path):
    cohort = load(EXAMPLE)
    cohort.config.title = "Evil </script><script>alert(1)</script>"
    handout_path, _ = build(cohort, tmp_path)
    text = handout_path.read_text(encoding="utf-8")
    assert "Evil </script>" not in text
    assert "Evil <\\/script>" in text
