# Contributing

Create a short-lived branch from current `main`: `type/short-description`, lowercase,
hyphenated, at most five words; put an issue number first when present. Types:
`feat`, `fix`, `refactor`, `perf`, `docs`, `test`, `chore`, `hotfix`.
Use one concern per branch and a separate Git worktree for parallel work.

Commit subjects use `type(scope): imperative summary`, under 72 characters.
Types are `feat`, `fix`, `perf`, `refactor`, `docs`, `test`, `build`, `ci`, `chore`,
and `revert`. Explain why in the body. Breaking changes need `!` and a
`BREAKING CHANGE:` footer.

Rebase unpublished work onto main before opening a PR. Never rewrite published
history or force-push shared branches; merge current main when a published PR
needs updating. CI must pass. Squash-merge with a Conventional Commit PR title,
then remove the merged branch and worktree. Never push directly to main.

Install Python 3.13, Tcl/Tk, FFmpeg, and platform PortAudio dependencies. Install
the locked dependencies and run `python scripts/check.py`. Native packages are
built with `python build_exe.py`, then `python scripts/package_release.py`.
See [release operations](docs/releases.md) for commands and limitations.

Releases are annotated `vX.Y.Z` tags on main. Release branches are only for
maintaining older series. A release PR updates the version and changelog, passes
all checks, and requires explicit owner approval of the version, notes, artifacts,
and publication commands before merging/tagging. Never move a published tag.

Hotfixes branch from the released tag, include a failing regression test, and use
the same PR and patch-release process. Backport to maintained release branches.
Mark defective releases in their notes and ship a patch; do not erase history.
