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


# --- self-paced: the same curriculum, rendered for a reader with no room ---


def test_self_paced_writes_one_handbook_and_no_guide(tmp_path):
    cohort = load(EXAMPLE)
    a, b = build(cohort, tmp_path, self_paced=True)
    assert a.name == "self-paced-handbook.html"
    assert a == b
    assert not (tmp_path / "facilitator-guide.html").exists()


def test_the_live_segment_is_not_shown_to_a_solo_reader(tmp_path):
    """Most in_session blocks say "as a group" or "live" — handing those to
    someone reading alone is handing them instructions for a room."""
    cohort = load(EXAMPLE)
    live = cohort.sessions[0].in_session
    handbook, _ = build(cohort, tmp_path, self_paced=True)
    assert live not in handbook.read_text(encoding="utf-8")

    handout, _ = build(cohort, tmp_path / "facilitated")
    assert live in handout.read_text(encoding="utf-8")


def test_a_solo_restatement_is_shown_when_the_session_has_one(tmp_path):
    cohort = load(EXAMPLE)
    cohort.sessions[0].solo = "Do this part on your own, like so."
    handbook, _ = build(cohort, tmp_path, self_paced=True)
    text = handbook.read_text(encoding="utf-8")
    assert "Do this part on your own, like so." in text
    assert "On your own" in text


def test_a_session_without_a_solo_restatement_omits_the_segment(tmp_path):
    """Silence beats faking a group activity for one person."""
    cohort = load(EXAMPLE)
    for s in cohort.sessions:
        s.solo = None
    handbook, _ = build(cohort, tmp_path, self_paced=True)
    text = handbook.read_text(encoding="utf-8")
    assert "In session" not in text
    assert "On your own" not in text


def test_a_solo_reader_still_gets_the_exercise_checkpoint_and_rubric(tmp_path):
    cohort = load(EXAMPLE)
    handbook, _ = build(cohort, tmp_path, self_paced=True)
    text = handbook.read_text(encoding="utf-8")
    assert cohort.sessions[0].exercise.description in text
    assert cohort.sessions[0].checkpoint in text
    assert cohort.rubric[0].name in text


def test_a_solo_reader_keeps_progress_tracking(tmp_path):
    """The audience that needs it most: nobody else is keeping count."""
    handbook, _ = build(load(EXAMPLE), tmp_path, self_paced=True)
    assert "Export progress" in handbook.read_text(encoding="utf-8")
