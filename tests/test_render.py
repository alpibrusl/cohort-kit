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


def _scored(tmp_path: Path, **scale) -> Path:
    """A copy of the example cohort whose rubric declares a scale."""
    import shutil

    import yaml

    d = tmp_path / "cohort"
    shutil.copytree(EXAMPLE, d)
    rubric = yaml.safe_load((d / "rubric.yaml").read_text(encoding="utf-8"))
    rubric["scale"] = {
        "levels": ["Not yet", "Approaching", "Meets"],
        "pass_level": "Meets",
        **scale,
    }
    for dim in rubric["dimensions"]:
        dim["levels"] = {
            "Not yet": f"{dim['name']}: not demonstrated.",
            "Approaching": f"{dim['name']}: partly demonstrated.",
            "Meets": f"{dim['name']}: demonstrated.",
        }
    (d / "rubric.yaml").write_text(yaml.dump(rubric), encoding="utf-8")
    return d


def test_a_rubric_with_no_scale_renders_the_two_column_table(tmp_path):
    """The default has to stay the default: a capstone that produces an honest
    audit rather than a grade should not sprout columns because a schema field
    exists."""
    cohort = load(EXAMPLE)
    handout, _ = build(cohort, tmp_path)
    text = handout.read_text(encoding="utf-8")
    assert "<th>What earns it</th>" in text
    assert 'class="rubric scored"' not in text
    # the class, not the phrase -- the stylesheet always carries a rule that
    # mentions "the bar", and matching that would pass whatever the body did
    assert 'class="rubric-bar"' not in text


def test_a_scale_turns_the_rubric_into_a_grid_with_the_bar_marked(tmp_path):
    cohort = load(_scored(tmp_path))
    handout, guide = build(cohort, tmp_path / "out")
    for path in (handout, guide):
        text = path.read_text(encoding="utf-8")
        assert 'class="rubric scored"' in text
        for level in ("Not yet", "Approaching", "Meets"):
            assert f">{level}</th>" in text
        # the pass column is marked in the head and in every body cell of it
        assert '<th class="pass-col">Meets</th>' in text
        assert text.count('<td class="pass-col">') == len(cohort.rubric)
        assert "reaching <strong>Meets</strong> on every dimension" in text


def test_the_solo_reader_is_told_the_bar_too(tmp_path):
    """A reader with no facilitator has more need of the threshold, not less."""
    cohort = load(_scored(tmp_path))
    handbook, _ = build(cohort, tmp_path / "out", self_paced=True)
    text = handbook.read_text(encoding="utf-8")
    assert 'class="rubric scored"' in text
    assert "reaching <strong>Meets</strong>" in text


def test_a_compensatory_scale_says_overall_instead_of_every_dimension(tmp_path):
    cohort = load(_scored(tmp_path, all_dimensions=False))
    handout, _ = build(cohort, tmp_path / "out")
    text = handout.read_text(encoding="utf-8")
    assert "reaching <strong>Meets</strong> overall" in text
    assert "does not make up for" not in text


def test_every_document_records_what_built_it(tmp_path):
    """A printed handout six months old should be rebuildable into that exact
    handout. That needs the curriculum's commit and the renderer's — cohortkit
    installs from @main, so its version number alone names a moving target."""
    cohort = load(EXAMPLE)
    handout, guide = build(cohort, tmp_path)
    handbook, _ = build(cohort, tmp_path / "solo", self_paced=True)
    for path in (handout, guide, handbook):
        footer = path.read_text(encoding="utf-8").split("<footer>")[1].split("</footer>")[0]
        assert "source " in footer
        assert "cohortkit" in footer


def test_the_stamp_describes_the_curriculum_not_the_output_directory(tmp_path):
    """`--out` often points somewhere temporary. Stamping it would record a
    commit that has nothing to do with the material in the document."""
    cohort = load(EXAMPLE)
    handout, _ = build(cohort, tmp_path)
    assert cohort.source_dir == EXAMPLE
    footer = handout.read_text(encoding="utf-8").split("<footer>")[1].split("</footer>")[0]
    # EXAMPLE lives in this repository, so its commit is this repository's
    assert "no recorded commit" not in footer
