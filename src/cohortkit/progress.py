"""Aggregate students' exported progress files into a summary an instructor
can actually read — no server, no accounts: the students each send a file,
this reads a folder of them.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import BaseModel, ValidationError

from .schema import Cohort, ProgressExport


class SessionStat(BaseModel):
    number: int
    title: str
    students_complete: int
    students_total: int

    @property
    def rate(self) -> float:
        return self.students_complete / self.students_total if self.students_total else 0.0


class StudentSummary(BaseModel):
    student_name: str
    sessions_complete: int
    sessions_total: int
    exported_at: str


class SessionNote(BaseModel):
    """One student's free-text note on one session — the honest-signal
    channel a single checkbox can't carry."""

    number: int
    title: str
    student_name: str
    note: str


class AggregateReport(BaseModel):
    cohort_title: str
    students: list[StudentSummary]
    session_stats: list[SessionStat]
    notes: list[SessionNote] = []


@dataclass
class LoadResult:
    exports: list[ProgressExport] = field(default_factory=list)
    skipped: list[tuple[Path, str]] = field(default_factory=list)
    """(file, reason) for anything that wasn't valid JSON or didn't match
    the ProgressExport shape — reported, not silently dropped."""


def load_exports(directory: Path | str) -> LoadResult:
    directory = Path(directory)
    result = LoadResult()
    for path in sorted(directory.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            result.exports.append(ProgressExport.model_validate(data))
        except (json.JSONDecodeError, ValidationError) as e:
            result.skipped.append((path, str(e)))
    return result


def _dedupe_latest_per_student(exports: list[ProgressExport]) -> list[ProgressExport]:
    """A student may export more than once as they progress — keep only
    their most recent submission, so a stale early export doesn't undercount
    someone who sent an updated one later."""
    latest: dict[str, ProgressExport] = {}
    for exp in exports:
        key = exp.student_name.strip().lower() or f"(unnamed {id(exp)})"
        if key not in latest or exp.exported_at > latest[key].exported_at:
            latest[key] = exp
    return list(latest.values())


def aggregate(exports: list[ProgressExport], cohort: Cohort | None = None) -> AggregateReport:
    """Build the summary. If `cohort` is given, session titles/order come
    from the curriculum's own source rather than whatever the oldest export
    happened to record — protects against a stale export file describing a
    session that's since been retitled."""
    deduped = _dedupe_latest_per_student(exports)

    cohort_title = cohort.config.title if cohort else (exports[0].cohort_title if exports else "")

    if cohort is not None:
        session_order = [(s.number, s.title) for s in cohort.sessions]
    else:
        seen: dict[int, str] = {}
        for exp in deduped:
            for s in exp.sessions:
                seen.setdefault(s.number, s.title)
        session_order = sorted(seen.items())

    students = [
        StudentSummary(
            student_name=exp.student_name or "(no name given)",
            sessions_complete=sum(1 for s in exp.sessions if s.complete),
            sessions_total=len(exp.sessions),
            exported_at=exp.exported_at.isoformat(),
        )
        for exp in deduped
    ]

    session_stats = []
    for number, title in session_order:
        complete_count = sum(
            1 for exp in deduped for s in exp.sessions if s.number == number and s.complete
        )
        session_stats.append(
            SessionStat(
                number=number,
                title=title,
                students_complete=complete_count,
                students_total=len(deduped),
            )
        )

    notes = sorted(
        (
            SessionNote(
                number=s.number,
                title=s.title,
                student_name=exp.student_name or "(no name given)",
                note=s.note.strip(),
            )
            for exp in deduped
            for s in exp.sessions
            if s.note and s.note.strip()
        ),
        key=lambda n: (n.number, n.student_name),
    )

    return AggregateReport(
        cohort_title=cohort_title, students=students, session_stats=session_stats, notes=notes
    )


def format_table(report: AggregateReport) -> str:
    """A plain-text table for the terminal — no dependency on a table
    library for something this small."""
    lines = [f"{report.cohort_title} — {len(report.students)} student(s)", ""]

    lines.append("By student:")
    for s in sorted(report.students, key=lambda x: -x.sessions_complete):
        lines.append(f"  {s.student_name:<30} {s.sessions_complete}/{s.sessions_total}")

    lines.append("")
    lines.append("By session:")
    for stat in report.session_stats:
        pct = round(stat.rate * 100)
        lines.append(
            f"  {stat.number:>2}. {stat.title:<40} "
            f"{stat.students_complete}/{stat.students_total} ({pct}%)"
        )

    if report.notes:
        lines.append("")
        lines.append("Feedback:")
        current_number = None
        for n in report.notes:
            if n.number != current_number:
                lines.append(f"  {n.number:>2}. {n.title}")
                current_number = n.number
            lines.append(f"      {n.student_name}: {n.note}")

    return "\n".join(lines)
