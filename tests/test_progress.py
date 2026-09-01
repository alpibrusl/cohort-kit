from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

from cohortkit._html import render_progress_report
from cohortkit.loader import load
from cohortkit.progress import aggregate, format_table, load_exports
from cohortkit.schema import ProgressExport, SessionProgress

EXAMPLE = Path(__file__).parent.parent / "examples" / "minimal"

NOW = datetime(2026, 3, 1, 12, 0, 0)


def _export(name: str, *, s1: bool, s2: bool, when: datetime = NOW) -> ProgressExport:
    return ProgressExport(
        cohort_title="Minimal Example Cohort",
        student_name=name,
        exported_at=when,
        sessions=[
            SessionProgress(number=1, title="Orientation", complete=s1),
            SessionProgress(number=2, title="Capstone", complete=s2),
        ],
    )


def _write(path: Path, export: ProgressExport) -> None:
    path.write_text(export.model_dump_json(), encoding="utf-8")


def test_load_exports_reads_valid_files(tmp_path):
    _write(tmp_path / "alice.json", _export("Alice", s1=True, s2=False))
    _write(tmp_path / "bob.json", _export("Bob", s1=True, s2=True))

    result = load_exports(tmp_path)

    assert len(result.exports) == 2
    assert result.skipped == []


def test_load_exports_skips_and_reports_invalid_files(tmp_path):
    _write(tmp_path / "alice.json", _export("Alice", s1=True, s2=False))
    (tmp_path / "garbage.json").write_text("not json at all", encoding="utf-8")
    (tmp_path / "wrong_shape.json").write_text(json.dumps({"foo": "bar"}), encoding="utf-8")

    result = load_exports(tmp_path)

    assert len(result.exports) == 1
    assert {p.name for p, _ in result.skipped} == {"garbage.json", "wrong_shape.json"}


def test_aggregate_keeps_only_latest_export_per_student(tmp_path):
    stale = _export("Alice", s1=True, s2=False, when=NOW)
    fresh = _export("Alice", s1=True, s2=True, when=NOW + timedelta(hours=1))

    report = aggregate([stale, fresh])

    assert len(report.students) == 1
    assert report.students[0].sessions_complete == 2


def test_aggregate_computes_session_and_student_stats():
    exports = [
        _export("Alice", s1=True, s2=True),
        _export("Bob", s1=True, s2=False),
    ]

    report = aggregate(exports)

    by_number = {s.number: s for s in report.session_stats}
    assert by_number[1].students_complete == 2
    assert by_number[2].students_complete == 1
    assert by_number[2].students_total == 2
    assert by_number[2].rate == 0.5


def test_aggregate_orders_sessions_by_cohort_when_given():
    cohort = load(EXAMPLE)
    exports = [_export("Alice", s1=True, s2=False)]

    report = aggregate(exports, cohort=cohort)

    assert [s.number for s in report.session_stats] == [1, 2]
    assert report.cohort_title == cohort.config.title


def test_format_table_lists_every_student_and_session():
    exports = [_export("Alice", s1=True, s2=True), _export("Bob", s1=True, s2=False)]
    report = aggregate(exports)

    table = format_table(report)

    assert "Alice" in table
    assert "Bob" in table
    assert "Orientation" in table
    assert "Capstone" in table


def test_render_progress_report_is_well_formed_html():
    exports = [_export("Alice", s1=True, s2=True), _export("Bob", s1=True, s2=False)]
    report = aggregate(exports)

    html = render_progress_report(report)

    assert html.startswith("<!doctype html>")
    assert html.count("<div") == html.count("</div>")
    assert "Alice" in html
    assert "Bob" in html
