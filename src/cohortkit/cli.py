from __future__ import annotations

from pathlib import Path

import typer
from content_kit_core._errors import ContentKitError
from content_kit_core._exit_codes import ExitCode

from ._html import render_progress_report
from .check import check as run_check
from .loader import load
from .progress import aggregate, format_table, load_exports
from .render import build as run_build

app = typer.Typer(
    name="cohortkit",
    help="CLI for turning a book's chapters into a live, facilitated cohort curriculum.",
    no_args_is_help=True,
)


def _die(message: str, hint: str | None = None, code: ExitCode = ExitCode.GENERAL_ERROR) -> None:
    typer.secho(f"error: {message}", fg=typer.colors.RED, err=True)
    if hint:
        typer.secho(f"  hint: {hint}", fg=typer.colors.YELLOW, err=True)
    raise typer.Exit(code=int(code))


@app.command()
def check(
    cohort_dir: Path = typer.Argument(Path("."), help="Directory containing cohort.yaml"),
    book_path: Path | None = typer.Option(
        None,
        "--book-path",
        help="Path to the source book's repo, to cross-check chapter references",
    ),
) -> None:
    """Validate a cohort's source: session numbering, capstone shape, fixture
    references, rubric size, and — if --book-path is given — that every
    chapter a session references actually exists in the book."""
    try:
        cohort = load(cohort_dir)
    except ContentKitError as e:
        _die(str(e), e.hint, e.code)
        return

    result = run_check(cohort, cohort_dir, book_path=book_path)

    for w in result.warnings:
        typer.secho(f"warning: {w}", fg=typer.colors.YELLOW)
    for e in result.errors:
        typer.secho(f"error: {e}", fg=typer.colors.RED, err=True)

    n_sessions = len(cohort.sessions)
    n_dims = len(cohort.rubric)
    typer.echo(
        f"checked {n_sessions} session(s), {n_dims} rubric dimension(s): "
        f"{len(result.errors)} error(s), {len(result.warnings)} warning(s)"
    )

    if not result.ok:
        raise typer.Exit(code=int(ExitCode.PRECONDITION_FAILED))


@app.command()
def build(
    cohort_dir: Path = typer.Argument(Path("."), help="Directory containing cohort.yaml"),
    out: Path = typer.Option(Path("build"), "--out", help="Output directory"),
    book_path: Path | None = typer.Option(
        None,
        "--book-path",
        help="Embed each session's real chapter text from the book's own repo",
    ),
    self_paced: bool = typer.Option(
        False,
        "--self-paced",
        help="Render one handbook for a reader working alone, instead of a "
        "handout and a facilitator guide.",
    ),
) -> None:
    """Render a cohort's documents from its source. Does not check first — run
    `cohortkit check` in CI, this command just builds what's there."""
    try:
        cohort = load(cohort_dir)
    except ContentKitError as e:
        _die(str(e), e.hint, e.code)
        return

    try:
        handout_path, guide_path = run_build(
            cohort, out, book_path=book_path, self_paced=self_paced
        )
    except ContentKitError as e:
        _die(str(e), e.hint, e.code)
        return
    typer.echo(f"wrote {handout_path}")
    if guide_path != handout_path:
        typer.echo(f"wrote {guide_path}")


@app.command()
def progress(
    exports_dir: Path = typer.Argument(
        ..., help="Directory of students' exported progress JSON files"
    ),
    cohort_dir: Path | None = typer.Option(
        None,
        "--cohort-dir",
        help="Directory containing cohort.yaml, to order sessions by the real curriculum",
    ),
    out: Path | None = typer.Option(
        None, "--out", help="Write an HTML report here in addition to the terminal summary"
    ),
) -> None:
    """Summarize a folder of students' exported progress files: who's done
    what, and which session the group is behind on. No accounts, no server —
    the students each send a file, this reads the folder they landed in."""
    result = load_exports(exports_dir)

    for path, reason in result.skipped:
        typer.secho(f"warning: skipped {path.name}: {reason}", fg=typer.colors.YELLOW)

    if not result.exports:
        _die(
            f"no valid progress export files found in {exports_dir}",
            hint="Each file should be JSON downloaded from a handout's 'Export progress' button.",
        )
        return

    cohort = None
    if cohort_dir is not None:
        try:
            cohort = load(cohort_dir)
        except ContentKitError as e:
            _die(str(e), e.hint, e.code)
            return

    report = aggregate(result.exports, cohort=cohort)
    typer.echo(format_table(report))

    if out is not None:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render_progress_report(report), encoding="utf-8")
        typer.echo(f"\nwrote {out}")


if __name__ == "__main__":
    app()
