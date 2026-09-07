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
import json
import re

from .book_content import ChapterContent
from .progress import AggregateReport
from .schema import Cohort, Session


def _js(value: object) -> str:
    """JSON for embedding inside a <script> block. json.dumps alone is not
    enough: a title containing "</script>" would close the block early, so
    the two sequences that can end a script element are escaped as well."""
    return json.dumps(value).replace("</", "<\\/").replace("<!--", "<\\!--")


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
/* A scored rubric is wide by nature -- one column per level. It scrolls in its
   own box rather than making the whole page scroll sideways. */
.rubric-scroll { overflow-x: auto; }
table.rubric.scored { min-width: 34rem; font-size: 0.86rem; }
table.rubric.scored td.dimension { width: 12rem; }
table.rubric.scored .pass-col { background: var(--accent-wash, rgba(0,0,0,0.035)); }
table.rubric.scored th.pass-col { color: var(--accent-strong); }
table.rubric.scored th.pass-col::after {
  content: " — the bar"; text-transform: none; letter-spacing: 0;
}
p.rubric-bar {
  margin-top: 0.7rem; font-size: 0.86rem; color: var(--ink-faint);
}
footer {
  margin-top: 3.5rem; padding-top: 1.2rem;
  border-top: 1px solid var(--rule-strong);
  font-family: "IBM Plex Mono", monospace; font-size: 0.72rem;
  color: var(--ink-faint);
}
.progress-panel {
  margin: 1.4rem 0 2rem; padding: 1rem 1.2rem;
  background: var(--paper-raised); border: 1px solid var(--rule);
  border-radius: 4px;
}
.name-row {
  display: flex; align-items: center; gap: 0.6rem;
  margin-bottom: 0.8rem; font-size: 0.92rem;
}
.name-row label {
  font-family: "IBM Plex Mono", monospace; font-size: 0.66rem;
  letter-spacing: 0.08em; text-transform: uppercase; color: var(--ink-faint);
}
.name-row input {
  font-family: "EB Garamond", Georgia, serif; font-size: 1rem;
  background: var(--paper); color: var(--ink);
  border: 1px solid var(--rule-strong); border-radius: 3px;
  padding: 0.3rem 0.6rem; flex: 1; max-width: 20rem;
}
.progress-row { display: flex; align-items: center; gap: 0.8rem; }
.progress-track {
  flex: 1; height: 8px; background: var(--rule); border-radius: 4px; overflow: hidden;
}
.progress-fill {
  height: 100%; background: var(--accent); width: 0%;
  transition: width 0.2s ease;
}
.progress-label {
  font-family: "IBM Plex Mono", monospace; font-size: 0.78rem;
  color: var(--ink-soft); white-space: nowrap;
}
.export-btn {
  font-family: "IBM Plex Mono", monospace; font-size: 0.76rem;
  background: var(--accent); color: var(--paper); border: none;
  border-radius: 3px; padding: 0.5rem 0.9rem; margin-top: 0.9rem;
  cursor: pointer;
}
.export-btn:hover { background: var(--accent-strong); }
.checkpoint-body { display: flex; flex-direction: column; gap: 0.5rem; }
.session-checkbox {
  display: inline-flex; align-items: center; gap: 0.4rem;
  cursor: pointer; font-family: "IBM Plex Mono", monospace;
  font-size: 0.78rem; color: var(--ink-soft);
}
.session-checkbox input { width: 1rem; height: 1rem; cursor: pointer; accent-color: var(--accent); }
.session-note {
  font-family: "EB Garamond", Georgia, serif; font-size: 0.92rem;
  background: var(--paper); color: var(--ink);
  border: 1px solid var(--rule-strong); border-radius: 3px;
  padding: 0.4rem 0.6rem; resize: vertical; width: 100%;
}
.feedback-group { margin-bottom: 1.1rem; }
.feedback-group h4 {
  font-size: 0.98rem; margin: 0 0 0.4rem;
  font-family: "IBM Plex Mono", monospace; font-weight: 600; color: var(--accent-strong);
}
.feedback-note {
  padding: 0.5rem 0.7rem; margin-bottom: 0.4rem;
  background: var(--paper-raised); border-radius: 3px; font-size: 0.92rem;
}
.feedback-note .student { color: var(--ink-faint); font-size: 0.76rem; margin-right: 0.4rem; }
.stat-row {
  display: flex; align-items: center; gap: 0.8rem;
  padding: 0.5rem 0; border-bottom: 1px solid var(--rule);
}
.stat-row .stat-name { flex: 0 0 14rem; font-size: 0.94rem; }
.stat-row .progress-track { flex: 1; }
.stat-row .stat-count {
  font-family: "IBM Plex Mono", monospace; font-size: 0.78rem;
  color: var(--ink-soft); white-space: nowrap; width: 5.5rem; text-align: right;
}
.chapter-reading { margin-top: 0.9rem; }
.chapter-embed {
  margin-bottom: 0.5rem; border: 1px solid var(--rule);
  border-radius: 3px; background: var(--paper);
}
.chapter-embed summary {
  cursor: pointer; padding: 0.55rem 0.8rem;
  font-family: "IBM Plex Mono", monospace; font-size: 0.78rem;
  color: var(--accent-strong);
}
.chapter-embed summary:hover { color: var(--accent); }
.chapter-prose {
  padding: 0.2rem 1.1rem 1.1rem; border-top: 1px solid var(--rule);
  font-size: 0.96rem;
}
.chapter-prose h2 { font-size: 1.15rem; margin: 1.3rem 0 0.5rem; }
.chapter-prose h3 { font-size: 1.02rem; margin: 1.1rem 0 0.4rem; }
.chapter-prose p { margin: 0 0 0.85rem; }
.chapter-prose blockquote {
  margin: 0 0 0.85rem; padding-left: 0.9rem;
  border-left: 2px solid var(--rule-strong); color: var(--ink-soft); font-style: italic;
}
.chapter-prose ul, .chapter-prose ol { margin: 0 0 0.85rem; padding-left: 1.4rem; }
.chapter-prose li { margin-bottom: 0.3rem; }
.chapter-prose code {
  font-family: "IBM Plex Mono", monospace; font-size: 0.85em;
  background: var(--tag-bg); padding: 0.1em 0.3em; border-radius: 2px;
}
.chapter-prose pre {
  overflow-x: auto; padding: 0.7rem 0.9rem; background: var(--tag-bg); border-radius: 3px;
}
.chapter-prose pre code { background: none; padding: 0; }
"""

_FONTS = (
    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
    "family=EB+Garamond:ital,wght@0,400;0,500;0,600;1,400"
    '&family=IBM+Plex+Mono:wght@400;500;600&display=swap">'
)


def _esc(s: str) -> str:
    return html.escape(s, quote=False)


def _slugify(s: str) -> str:
    """A stable, storage-key-safe identifier for a cohort title — stable
    across rebuilds and across browsers, since it's computed once here
    rather than re-derived by JS in each viewer."""
    slug = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return slug or "cohort"


def _session_html(
    s: Session,
    *,
    include_facilitator_notes: bool,
    interactive: bool,
    book_chapters: dict[int, ChapterContent] | None = None,
    solo: bool = False,
) -> str:
    chapters = ", ".join(str(c) for c in s.chapters)
    classes = "session capstone" if s.capstone else "session"
    label = f"{s.number:02d} &middot; CAPSTONE" if s.capstone else f"{s.number:02d}"

    body = f"""
    <div class="{classes}" data-session-block="{s.number}">
      <div class="session-head">
        <span class="session-num mono">{label}</span>
        <h3 class="session-title">{_esc(s.title)}</h3>
      </div>
      <div class="session-chapters mono">Chapters {chapters}</div>
    """
    if solo:
        # A reader working alone gets the solo restatement, or nothing --
        # never the live segment, which is written for a room.
        if s.solo:
            body += (
                '<div class="field"><span class="label">On your own</span>'
                f"<p>{_esc(s.solo)}</p></div>\n"
            )
    else:
        body += (
            '<div class="field"><span class="label">In session</span>'
            f"<p>{_esc(s.in_session)}</p></div>\n"
        )
    if book_chapters:
        found = [book_chapters[n] for n in s.chapters if n in book_chapters]
        if found:
            entries = "".join(
                f'<details class="chapter-embed">'
                f"<summary>Chapter {c.number} &middot; {_esc(c.title)}</summary>"
                f'<div class="chapter-prose">{c.html}</div>'
                f"</details>"
                for c in found
            )
            body += f'<div class="chapter-reading">{entries}</div>'
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
        '<div class="checkpoint"><span class="label">Checkpoint</span><div class="checkpoint-body">'
    )
    body += f"<p>{_esc(s.checkpoint)}</p>"
    if interactive:
        body += (
            '<label class="session-checkbox">'
            f'<input type="checkbox" data-session-checkbox="{s.number}"> Mark complete'
            "</label>"
            f'<textarea class="session-note" data-session-note="{s.number}" rows="2" '
            'placeholder="What got in the way? (optional, for the instructor)"></textarea>'
        )
    body += "</div></div>"
    if include_facilitator_notes and s.facilitator_notes:
        body += (
            '<div class="facilitator-note"><span class="label">Facilitator notes</span>'
            f"{_esc(s.facilitator_notes)}</div>"
        )
    body += "</div>"
    return body


def _progress_script(cohort: Cohort) -> str:
    """Client-side only: checkbox state persisted in localStorage, keyed to
    this cohort so different cohorts on the same device don't collide, plus
    an export button that downloads a ProgressExport-shaped JSON file — the
    only channel this whole feature needs, since there's no server to send
    it to instead."""
    storage_key = f"cohortkit:progress:{_slugify(cohort.config.title)}"
    sessions_meta = _js([{"number": s.number, "title": s.title} for s in cohort.sessions])
    cohort_title = _js(cohort.config.title)

    return f"""
<script>
(function () {{
  const STORAGE_KEY = {_js(storage_key)};
  const COHORT_TITLE = {cohort_title};
  const SESSIONS = {sessions_meta};

  function loadState() {{
    try {{
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return {{ studentName: "", sessions: {{}} }};
      const parsed = JSON.parse(raw);
      return {{ studentName: parsed.studentName || "", sessions: parsed.sessions || {{}} }};
    }} catch (e) {{
      return {{ studentName: "", sessions: {{}} }};
    }}
  }}

  function saveState(state) {{
    try {{
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    }} catch (e) {{
      /* private-browsing or storage disabled — progress just won't persist */
    }}
  }}

  function updateProgressBar(state) {{
    const done = SESSIONS.filter(function (s) {{
      return state.sessions[s.number] && state.sessions[s.number].complete;
    }}).length;
    const pct = SESSIONS.length ? Math.round((done / SESSIONS.length) * 100) : 0;
    document.getElementById("progress-fill").style.width = pct + "%";
    document.getElementById("progress-label").textContent =
      done + " of " + SESSIONS.length + " sessions complete";
  }}

  function exportProgress(state) {{
    const payload = {{
      cohort_title: COHORT_TITLE,
      student_name: state.studentName || "",
      exported_at: new Date().toISOString(),
      sessions: SESSIONS.map(function (s) {{
        const entry = state.sessions[s.number] || {{}};
        const note = (entry.note || "").trim();
        return {{
          number: s.number,
          title: s.title,
          complete: !!entry.complete,
          completed_at: entry.complete ? (entry.completed_at || null) : null,
          note: note ? note : null
        }};
      }})
    }};
    const blob = new Blob([JSON.stringify(payload, null, 2)], {{ type: "application/json" }});
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    const namePart = (state.studentName || "student")
      .toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "") || "student";
    a.href = url;
    a.download = {_js(_slugify(cohort.config.title))} + "-progress-" + namePart + ".json";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }}

  document.addEventListener("DOMContentLoaded", function () {{
    const state = loadState();

    const nameInput = document.getElementById("student-name");
    nameInput.value = state.studentName;
    nameInput.addEventListener("input", function () {{
      state.studentName = nameInput.value;
      saveState(state);
    }});

    document.querySelectorAll("[data-session-checkbox]").forEach(function (box) {{
      const num = box.getAttribute("data-session-checkbox");
      const entry = state.sessions[num];
      box.checked = !!(entry && entry.complete);
      box.addEventListener("change", function () {{
        const existing = state.sessions[num] || {{}};
        state.sessions[num] = box.checked
          ? {{ complete: true, completed_at: new Date().toISOString(), note: existing.note || "" }}
          : {{ complete: false, completed_at: null, note: existing.note || "" }};
        saveState(state);
        updateProgressBar(state);
      }});
    }});

    document.querySelectorAll("[data-session-note]").forEach(function (ta) {{
      const num = ta.getAttribute("data-session-note");
      const entry = state.sessions[num];
      ta.value = (entry && entry.note) || "";
      ta.addEventListener("input", function () {{
        const existing = state.sessions[num] || {{}};
        state.sessions[num] = {{
          complete: !!existing.complete,
          completed_at: existing.completed_at || null,
          note: ta.value
        }};
        saveState(state);
      }});
    }});

    document.getElementById("export-progress").addEventListener("click", function () {{
      exportProgress(state);
    }});

    updateProgressBar(state);
  }});
}})();
</script>
"""


def _rubric_html(cohort: Cohort) -> str:
    """The capstone rubric, scored or not.

    Without a scale this is the two-column table it has always been. With one
    it becomes a grid -- a column per level, the pass column marked -- because
    that is the shape somebody has to fill in and hand upward.
    """
    if not cohort.rubric:
        return ""

    scale = cohort.scale
    if scale is None:
        rows = "\n".join(
            f"<tr><td>{_esc(d.name)}</td><td>{_esc(d.description)}</td></tr>" for d in cohort.rubric
        )
        return f"""
        <h2 class="block-title">Capstone rubric</h2>
        <table class="rubric">
          <thead><tr><th>Dimension</th><th>What earns it</th></tr></thead>
          <tbody>{rows}</tbody>
        </table>
        """

    def cls(level: str) -> str:
        return ' class="pass-col"' if level == scale.pass_level else ""

    head = "".join(f"<th{cls(lv)}>{_esc(lv)}</th>" for lv in scale.levels)
    rows = "\n".join(
        "<tr>"
        + f'<td class="dimension"><strong>{_esc(d.name)}</strong><br>{_esc(d.description)}</td>'
        + "".join(f"<td{cls(lv)}>{_esc(d.levels.get(lv, ''))}</td>" for lv in scale.levels)
        + "</tr>"
        for d in cohort.rubric
    )
    where = "every dimension" if scale.all_dimensions else "the rubric overall"
    bar = (
        f"Passing means reaching <strong>{_esc(scale.pass_level)}</strong> on {where}. "
        "A strong showing on one dimension does not make up for a missing one."
        if scale.all_dimensions
        else f"Passing means reaching <strong>{_esc(scale.pass_level)}</strong> overall."
    )
    return f"""
        <h2 class="block-title">Capstone rubric</h2>
        <div class="rubric-scroll">
        <table class="rubric scored">
          <thead><tr><th>Dimension</th>{head}</tr></thead>
          <tbody>{rows}</tbody>
        </table>
        </div>
        <p class="rubric-bar">{bar}</p>
        """


def render_page(
    cohort: Cohort,
    *,
    audience: str,
    book_chapters: dict[int, ChapterContent] | None = None,
) -> str:
    """`audience` is 'handout', 'facilitator' or 'self-paced'.

    The three are the same curriculum rendered for three rooms. 'handout' and
    'facilitator' are a facilitated cohort -- an academy running an open
    course, or a company running one internally -- and differ in exactly one
    field, `facilitator_notes`. 'self-paced' is for a reader working alone: it
    drops the live segment, which is written for a group and reads as
    instructions for a room they are not in, and keeps the progress tracking,
    which is the audience that needs it most.

    The handout also gets an
    interactive progress checklist (checkboxes, a progress bar, an export
    button) that the facilitator guide doesn't — tracking your own progress
    is a student concept, not a facilitator one. Everything else, including
    the rubric, is shown to both, on purpose: a rubric nobody sees in
    advance isn't a rubric, it's a surprise.

    `book_chapters`, when given, embeds each session's actual chapter text
    (collapsed by default) right in that session — reading along needs
    nothing but this one file, no separate PDF or EPUB."""
    include_notes = audience == "facilitator"
    solo = audience == "self-paced"
    interactive = audience in ("handout", "self-paced")
    label = {
        "facilitator": "Facilitator Guide",
        "self-paced": "Self-Paced Handbook",
    }.get(audience, "Student Handout")

    sessions_html = "\n".join(
        _session_html(
            s,
            include_facilitator_notes=include_notes,
            interactive=interactive,
            book_chapters=book_chapters,
            solo=solo,
        )
        for s in cohort.sessions
    )

    rubric_html = _rubric_html(cohort)

    progress_panel = ""
    script = ""
    if interactive:
        progress_panel = """
        <div class="progress-panel">
          <div class="name-row">
            <label for="student-name">Name</label>
            <input type="text" id="student-name"
                   placeholder="For the export file — stays in this browser only">
          </div>
          <div class="progress-row">
            <div class="progress-track"><div class="progress-fill" id="progress-fill"></div></div>
            <span class="progress-label mono" id="progress-label">0 of 0 sessions complete</span>
          </div>
          <button class="export-btn" id="export-progress" type="button">Export progress</button>
        </div>
        """
        script = _progress_script(cohort)

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
  {progress_panel}
</header>
<section>
  <h2 class="block-title">Sessions</h2>
  {sessions_html}
  {rubric_html}
</section>
<footer>{_esc(cohort.config.book)} &middot; cohort-kit</footer>
{script}
</body>
</html>
"""


def render_progress_report(report: AggregateReport) -> str:
    """The instructor-facing side of the export button: one page built from
    whatever exported JSON files landed in a folder, showing the same two
    views a facilitator actually wants — who's behind, and which session
    the group is behind on."""
    student_rows = "\n".join(
        f"""
        <div class="stat-row">
          <span class="stat-name">{_esc(s.student_name)}</span>
          <div class="progress-track">
            <div class="progress-fill" style="width:{
            round(100 * s.sessions_complete / s.sessions_total) if s.sessions_total else 0
        }%"></div>
          </div>
          <span class="stat-count mono">{s.sessions_complete}/{s.sessions_total}</span>
        </div>
        """
        for s in sorted(report.students, key=lambda x: -x.sessions_complete)
    )

    session_rows = "\n".join(
        f"""
        <div class="stat-row">
          <span class="stat-name">{stat.number:02d}. {_esc(stat.title)}</span>
          <div class="progress-track">
            <div class="progress-fill" style="width:{round(stat.rate * 100)}%"></div>
          </div>
          <span class="stat-count mono">{stat.students_complete}/{stat.students_total}</span>
        </div>
        """
        for stat in report.session_stats
    )

    feedback_html = ""
    if report.notes:
        groups: dict[int, list] = {}
        titles: dict[int, str] = {}
        for n in report.notes:
            groups.setdefault(n.number, []).append(n)
            titles[n.number] = n.title
        feedback_html = "\n".join(
            f"""
            <div class="feedback-group">
              <h4>{number:02d}. {_esc(titles[number])}</h4>
              {
                "".join(
                    f'<div class="feedback-note">'
                    f'<span class="student mono">{_esc(n.student_name)}</span>{_esc(n.note)}'
                    f"</div>"
                    for n in notes
                )
            }
            </div>
            """
            for number, notes in groups.items()
        )
        feedback_html = f'<h2 class="block-title">Feedback</h2>\n{feedback_html}'

    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_esc(report.cohort_title)} — Progress Report</title>
{_FONTS}
<style>{_CSS}</style>
</head>
<body>
<header>
  <div class="eyebrow">Instructor report &middot; from exported student files</div>
  <h1 class="title">{_esc(report.cohort_title)}</h1>
  <p class="dek">{len(report.students)} student(s) reporting in.</p>
</header>
<section>
  <h2 class="block-title">By student</h2>
  {student_rows or "<p>No exports yet.</p>"}

  <h2 class="block-title">By session</h2>
  {session_rows or "<p>No exports yet.</p>"}

  {feedback_html}
</section>
<footer>cohort-kit &middot; generated from exported progress files, not stored anywhere</footer>
</body>
</html>
"""
