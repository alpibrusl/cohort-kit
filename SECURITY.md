# Security policy

## Reporting a vulnerability

Report privately through GitHub's
[security advisory form](https://github.com/alpibrusl/cohort-kit/security/advisories/new),
or by email to **alfonso@alpibru.com** if you would rather not use GitHub.

Please do not open a public issue for a vulnerability. Expect an
acknowledgement within a week.

## What is in scope

This project renders `cohort.yaml`, `sessions.yaml` and
`rubric.yaml` into HTML documents, and the rendered handout carries JavaScript
for progress tracking.

* Curriculum text that escapes into the rendered page as markup or script.
* Path handling in `--book-path` that reads outside the directory given.

Progress data stays in the reader's own browser and is never transmitted; a
change to that is a vulnerability, not a feature.

## What is not

This is a small project maintained by one person in the open. There is no bug
bounty, no service-level agreement on fixes, and no embargo process beyond a
reasonable delay to prepare a patch. Fixes land on `main` and are described
plainly in the commit that carries them.

## Supported versions

`main` only. There are no maintained release branches.
