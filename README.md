# cohort-kit

CLI for turning a book's chapters into a live, facilitated cohort curriculum.

Sessions and a rubric are the source, same discipline as [content-kit](https://github.com/alpibrusl/content-kit)'s
`bookkit`: plain data, checked in CI, with the two things a real cohort
actually needs — a student handout and a facilitator guide — as build
artifacts, never hand-edited and never committed.

## What this is not

Not a place for any book's actual curriculum content. A cohort for a
specific book (its sessions, its fixture, its rubric) lives inside that
book's own repository — e.g. `prompt-to-production/cohort/` — the same way
that book's `verify-*` skill lives in `prompt-to-production/skills/`, not
here. This repository is the mechanism, not the material.

## The shape of a cohort's source

Three files:

**`cohort.yaml`** — identity and format. Which book this cohort is derived
from, how many sessions, cohort size, prerequisite.

**`sessions.yaml`** — the sequence. Each session names the chapters it
draws on, what happens live (`in_session`), and either an `exercise`
(every session but the last) or a `deliverable` (the capstone only).
A session can carry `facilitator_notes` — pacing, common pitfalls — shown
in the facilitator guide and nowhere else.

**`rubric.yaml`** — a small number of dimensions the capstone is actually
judged on. Shown to students up front, in the handout, not held back as a
surprise — a rubric nobody sees in advance isn't a rubric.

See [`examples/minimal`](examples/minimal) for a complete, tiny worked
example — also what this package's own tests run against.

## Install

```bash
pip install "content-kit-core @ git+https://github.com/alpibrusl/content-kit@main#subdirectory=packages/core"
pip install "cohortkit @ git+https://github.com/alpibrusl/cohort-kit@main"
```

## Use

```bash
cohortkit check path/to/cohort              # validate the source
cohortkit check path/to/cohort --book-path path/to/the/book  # + cross-check chapter refs
cohortkit build path/to/cohort --out build  # → build/handout.html, build/facilitator-guide.html
cohortkit build path/to/cohort --out build --self-paced  # → build/self-paced-handbook.html
cohortkit build path/to/cohort --out build --book-path path/to/the/book  # + embed chapter text
cohortkit progress path/to/exports          # summarize students' exported progress files
```

`check` catches the things a facilitator would otherwise find live, in
front of a cohort: session numbers with a gap or a repeat, a capstone
that isn't the last session or has no deliverable, a non-capstone session
with no exercise, an exercise pointing at a fixture file that doesn't
exist, a rubric with nothing in it (or so many dimensions it stops being
usable live), and — given `--book-path` — a chapter reference that doesn't
exist in the source book's own `book.yaml`, or a book chapter no session
ever mentions.

## Reading along, without a separate PDF or EPUB

`--book-path` (on `build`, same flag `check` already uses) embeds each
session's actual chapter text — read straight from the book's own Markdown
source — collapsed under that session in both the handout and the guide.
A student needs nothing but the one HTML file to read along; nothing is
fetched, and nothing needs the book's PDF or EPUB to exist first. Omit the
flag and sessions just list their chapter numbers, as before — this is
additive, not a required step.

## Tracking progress, without a server

The handout is interactive: a student ticks off each session's checkpoint
as they clear it, and a progress bar tracks it — state lives in the
browser's own `localStorage`, keyed to the cohort, so it survives a reload
as long as the handout is reopened at the same URL. No account, no backend.

When a student clicks **Export progress**, the browser downloads a small
JSON file — the only channel this tool uses between a student and an
instructor. The student sends that file however they already would (email,
Slack, an LMS upload); the instructor collects a folder of them and runs:

```bash
cohortkit progress path/to/exports-folder --out report.html
```

This prints a plain-text summary (who's done what, which session the group
is behind on) and, with `--out`, also writes an HTML report in the same
visual style as the handout. Pass `--cohort-dir` to order sessions by the
curriculum's own source rather than whatever an export file happened to
record — protects against a stale export describing a retitled session. A
student who exports more than once is only counted once, by their most
recent submission.

Next to each checkbox is an optional textarea — "what got in the way,"
not another checkbox. The rubric already rewards an honest "not done" over
a false "done"; a free-text note is where that honesty goes when a
checkbox can't carry it. Notes ride in the same export file and show up in
`cohortkit progress`'s output grouped by session, so an instructor sees
which session actually confused people, in the students' own words.

## Three rooms, one curriculum

The same source renders for three ways of running the course, because the
difference between them is who is in the room rather than what is taught.

**A facilitated cohort** — an academy running an open course, or a company
running one internally — gets the handout and the facilitator guide below.

**A reader working alone** gets `--self-paced`: one handbook, no guide, and no
live segment. That last part is the point. Most `in_session` blocks say "as a
group", "live walk", "tabletop" — handing those to someone reading alone hands
them instructions for a room they are not in. A session can carry a `solo`
field saying what that reader does instead; where it has none, the segment is
omitted rather than faked. Progress tracking stays, for the audience with
nobody else keeping count.

**A company** runs the facilitated build, and the differences that matter to it
live in the curriculum rather than the renderer: where the capstone points, who
attends, what may leave the room. See a book's own `cohort/README.md`.

## Why a handout and a guide, not just one page

They come from the exact same source and differ in exactly one way:
`facilitator_notes` render in the guide, never in the handout. Everything
else — sessions, exercises, checkpoints, the rubric — is identical, on
purpose: material judged worth hiding from students belongs to a different
document, not a redacted version of theirs.

## Visual identity

Rendered pages share the cream/ink palette and EB Garamond + IBM Plex Mono
pairing of the *Prompt to...* book series, so a cohort page reads as the
same product as the book it's derived from, not a different one. See
[`src/cohortkit/_html.py`](src/cohortkit/_html.py).

## Development

```bash
pip install -e /path/to/content-kit/packages/core
pip install -e ".[dev]" --no-deps  # avoids re-resolving the git dependency above
pip install typer pyyaml pydantic markdown

ruff check .
ruff format --check .
pytest
```

## Licence

[EUPL-1.2](LICENSE), matching content-kit and the book series this tool
serves.
