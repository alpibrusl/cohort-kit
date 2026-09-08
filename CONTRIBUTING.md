# Contributing

cohort-kit is a renderer that turns a cohort curriculum into teaching documents, licensed under the EUPL-1.2. Contributions are welcome, and
this page is the short version of what makes one easy to merge.

## Setting up

```bash
git clone https://github.com/alpibrusl/cohort-kit
cd cohort-kit
python -m pip install -e .
python -m pip install ruff pytest
```

## What CI will check

Run these before you push and there will be no surprises:

```bash
ruff check src tests
pytest
```

### What belongs here and what does not

cohort-kit is the mechanism, not the material. A curriculum lives in the book
repository it teaches, as `cohort/cohort.yaml`, `sessions.yaml` and
`rubric.yaml`; this project only knows how to render one.

So a change that improves *a course* belongs in that book's repository. A
change that lets every course express something it could not express before —
the `solo` field, say — belongs here.

## Opening a pull request

**Say what broke, not just what changed.** The commit messages in this
repository lead with the problem and the evidence for it — a measurement, a
failing case, a number. A reviewer should be able to tell from the message
alone whether the change is worth making.

**One change per pull request.** A bug fix and a refactor in the same diff
means neither can be reviewed properly, and the fix cannot be reverted without
losing the refactor.

**Tests that would have caught it.** A fix without a test that fails before it
is a fix that comes back.

## Reporting a bug

Open an issue with the smallest input that reproduces it, the command you ran,
and what you expected instead. A version number helps; so does the output of
`pip show cohortkit`.

## Licensing of contributions

By opening a pull request you agree that your contribution is licensed under
the **EUPL-1.2**, the same licence as the rest of this repository. There is no
separate contributor agreement to sign.
