"""Shared visual identity for rendered cohort output — the same cream/ink
palette and EB Garamond + IBM Plex Mono pairing as the Prompt to... book
series, so a cohort page reads as the same product as its source book, not a
different one wearing the same words.

This module only assembles HTML from already-validated data (a `Cohort`); it
has no opinions about what belongs in a student handout versus a facilitator
guide — that split is `render.py`'s job.
"""

from __future__ import annotations

import html

from .schema import Cohort, Session

_CSS = """
:root {
  --paper: #f6f1e6; --paper-raised: #efe8d8;
  --ink: #211d18; --ink-soft: #514a3f; --ink-faint: #7c7362;
  --accent: #2f4157; --accent-strong: #24313f;
  --rule: rgba(33,29,24,0.14); --rule-strong: rgba(33,29,24,0.28);
  --tag-bg: rgba(47,65,87,0.08); --good: #3c5f3f;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --paper: #1b1815; --paper-raised: #242019;
    --ink: #ece7da; --ink-soft: #c7c0af; --ink-faint: #948a75;
    --accent: #9db3c9; --accent-strong: #bfd0de;
    --rule: rgba(236,231,218,0.14); --rule-strong: rgba(236,231,218,0.26);
    --tag-bg: rgba(157,179,201,0.12); --good: #7fae82;
  }
}
:root[data-theme="dark"] {
  --paper: #1b1815; --paper-raised: #242019;
  --ink: #ece7da; --ink-soft: #c7c0af; --ink-faint: #948a75;
  --accent: #9db3c9; --accent-strong: #bfd0de;
  --rule: rgba(236,231,218,0.14); --rule-strong: rgba(236,231,218,0.26);
  --tag-bg: rgba(157,179,201,0.12); --good: #7fae82;
}
* { box-sizing: border-box; }
body {
  background: var(--paper); color: var(--ink);
  font-family: "EB Garamond", Georgia, serif;
  font-size: 19px; line-height: 1.6;
  max-width: 46rem; margin: 0 auto; padding: 3.5rem 1.5rem 5rem;
}
.mono { font-family: "IBM Plex Mono", ui-monospace, monospace; }
h1, h2, h3 { text-wrap: balance; font-weight: 600; }
.eyebrow {
  font-family: "IBM Plex Mono", monospace; font-size: 0.72rem;
  letter-spacing: 0.14em; text-transform: uppercase; color: var(--accent);
}
h1.title { font-size: 2.4rem; line-height: 1.1; margin: 0.6rem 0 0.5rem; }
.dek { font-size: 1.1rem; color: var(--ink-soft); font-style: italic; margin: 0 0 1.5rem; }
h2.block-title {
  font-size: 1.4rem; margin: 2.6rem 0 0.9rem; padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--rule-strong);
}
.session {
  padding: 1.4rem 1.6rem 1.5rem; margin-bottom: 1rem;
  background: var(--paper-raised); border: 1px solid var(--rule); border-radius: 4px;
}
.session-head {
  display: flex; align-items: baseline; gap: 0.7rem; margin-bottom: 0.2rem;
}
.session-num {
  font-family: "IBM Plex Mono", monospace; font-size: 0.85rem;
  color: var(--accent); font-weight: 600;
}
.session-title { font-size: 1.15rem; font-weight: 600; margin: 0; }
.session-chapters {
  font-family: "IBM Plex Mono", monospace; font-size: 0.7rem;
  color: var(--ink-faint); margin-bottom: 0.9rem;
}
.field {
  padding-left: 0.85rem; border-left: 2px solid var(--rule-strong);
  margin-bottom: 0.8rem;
}
.field .label {
  font-family: "IBM Plex Mono", monospace; font-size: 0.64rem;
  letter-spacing: 0.1em; text-transform: uppercase; color: var(--accent);
  display: block; margin-bottom: 0.25rem;
}
.field p { margin: 0; font-size: 0.96rem; }
.checkpoint {
  margin-top: 0.9rem; padding-top: 0.8rem;
  border-top: 1px dashed var(--rule-strong); font-size: 0.94rem;
}
.checkpoint .label {
  font-family: "IBM Plex Mono", monospace; font-size: 0.64rem;
  letter-spacing: 0.1em; text-transform: uppercase; color: var(--good);
  display: block; margin-bottom: 0.25rem;
}
.capstone { border-color: var(--accent); background: var(--tag-bg); }
.facilitator-note {
  margin-top: 0.9rem; padding: 0.7rem 0.9rem;
  background: var(--tag-bg); border-radius: 3px; font-size: 0.92rem;
}
.facilitator-note .label {
  font-family: "IBM Plex Mono", monospace; font-size: 0.62rem;
  letter-spacing: 0.1em; text-transform: uppercase;
  color: var(--accent-strong); display: block; margin-bottom: 0.3rem;
}
table.rubric {
  width: 100%; border-collapse: collapse; margin-top: 0.6rem; font-size: 0.92rem;
}
table.rubric th, table.rubric td {
  text-align: left; padding: 0.5rem 0.6rem;
  border-bottom: 1px solid var(--rule); vertical-align: top;
}
table.rubric th {
  font-family: "IBM Plex Mono", monospace; font-size: 0.62rem;
  letter-spacing: 0.08em; text-transform: uppercase; color: var(--ink-faint);
}
footer {
  margin-top: 3.5rem; padding-top: 1.2rem;
  border-top: 1px solid var(--rule-strong);
  font-family: "IBM Plex Mono", monospace; font-size: 0.72rem;
  color: var(--ink-faint);
}
"""

_FONTS = (
    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
    "family=EB+Garamond:ital,wght@0,400;0,500;0,600;1,400"
    '&family=IBM+Plex+Mono:wght@400;500;600&display=swap">'
)


def _esc(s: str) -> str:
    return html.escape(s, quote=False)


def _session_html(s: Session, *, include_facilitator_notes: bool) -> str:
    chapters = ", ".join(str(c) for c in s.chapters)
    classes = "session capstone" if s.capstone else "session"
    label = f"{s.number:02d} &middot; CAPSTONE" if s.capstone else f"{s.number:02d}"

    body = f"""
    <div class="{classes}">
      <div class="session-head">
        <span class="session-num mono">{label}</span>
        <h3 class="session-title">{_esc(s.title)}</h3>
      </div>
      <div class="session-chapters mono">Chapters {chapters}</div>
      <div class="field"><span class="label">In session</span><p>{_esc(s.in_session)}</p></div>
    """
    if s.capstone and s.deliverable:
        body += (
            '<div class="field"><span class="label">Deliverable</span>'
            f"<p>{_esc(s.deliverable)}</p></div>"
        )
    elif s.exercise:
        body += (
            f'<div class="field"><span class="label">Exercise: {_esc(s.exercise.name)}</span>'
            f"<p>{_esc(s.exercise.description)}</p></div>"
        )
    body += (
        f'<div class="checkpoint"><span class="label">Checkpoint</span>{_esc(s.checkpoint)}</div>'
    )
    if include_facilitator_notes and s.facilitator_notes:
        body += (
            '<div class="facilitator-note"><span class="label">Facilitator notes</span>'
            f"{_esc(s.facilitator_notes)}</div>"
        )
    body += "</div>"
    return body


def render_page(cohort: Cohort, *, audience: str) -> str:
    """`audience` is 'handout' or 'facilitator'. The two differ only in
    whether facilitator_notes render — everything else, including the
    rubric, is shown to both, on purpose: a rubric nobody sees in advance
    isn't a rubric, it's a surprise."""
    include_notes = audience == "facilitator"
    label = "Facilitator Guide" if include_notes else "Student Handout"

    sessions_html = "\n".join(
        _session_html(s, include_facilitator_notes=include_notes) for s in cohort.sessions
    )

    rubric_html = ""
    if cohort.rubric:
        rows = "\n".join(
            f"<tr><td>{_esc(d.name)}</td><td>{_esc(d.description)}</td></tr>" for d in cohort.rubric
        )
        rubric_html = f"""
        <h2 class="block-title">Capstone rubric</h2>
        <table class="rubric">
          <thead><tr><th>Dimension</th><th>What earns it</th></tr></thead>
          <tbody>{rows}</tbody>
        </table>
        """

    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_esc(cohort.config.title)} — {label}</title>
{_FONTS}
<style>{_CSS}</style>
</head>
<body>
<header>
  <div class="eyebrow">{label} &middot; based on {_esc(cohort.config.book_title)}</div>
  <h1 class="title">{_esc(cohort.config.title)}</h1>
  <p class="dek">{_esc(cohort.config.subtitle)}</p>
</header>
<section>
  <h2 class="block-title">Sessions</h2>
  {sessions_html}
  {rubric_html}
</section>
<footer>{_esc(cohort.config.book)} &middot; cohort-kit</footer>
</body>
</html>
"""
