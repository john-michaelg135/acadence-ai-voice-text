# Proposed first tagged release: v0.1.0

No release tags or manifest version existed before setup, so this starts at the requested 0.1.0 fallback. The old UI's 1.2.0 text was not a release manifest. Future versions follow Conventional Commits, with breaking changes using minor bumps below 1.0.

Expected assets:
- Acadence-0.1.0-windows-x64.exe (portable executable)
- Acadence-0.1.0-macos-arm64.zip (application bundle)
- Acadence-0.1.0-linux-x64.deb
- One provenance JSON per platform
- updates-stable.json
- SHA256SUMS

The release includes subject/task tracking, voice-assisted entry, recovery/session/attachment fixes, worker cleanup, and the native release pipeline. Packaged data moves to user-writable application data directories; existing portable data requires manual backup/migration with its original encryption configuration.

All builds are unsigned. Live microphones, SMTP, online AI providers, and offline model inference have not been tested. Existing local-session trust, legacy encryption configuration, and database migration limitations remain documented in AUDIT.md. Dependency inputs are hash-locked; bit-for-bit reproducibility across machines has not been verified.

After explicit approval:
1. Squash-merge chore/release-v0.1.0 through its PR and delete that branch.
2. Fast-forward main and wait for green CI on the exact merge commit.
3. git tag -a v0.1.0 -m "Release v0.1.0"
4. git push origin v0.1.0
5. The tag workflow builds all targets, creates a DRAFT, uploads all assets, downloads and verifies every checksum, then publishes. Stable metadata points to this tag.
6. Verify published downloads, Windows launch, release notes, tag commit, and fresh Unreleased section. There are no existing milestones or linked issues to close.

At preparation time, no tag or release had been created. On 2026-11-16 the owner
authorized proceeding through the required approvals so the final executable
would be published on GitHub Releases. This covers the tag push and the
tag-triggered publication described above, after the required checks pass.

## Preparation evidence

Main commit: `181e38b7da89171c12f36c47db3c8ba17f767a7c`.
All native builds, packaged GUI/SQLite/Torch/Whisper smoke tests, and the required
CI gate passed in [main CI](https://github.com/john-michaelg135/acadence-ai-voice-text/actions/runs/43828774807).
Local checks passed: formatting, lint, mypy (38 files), 35 tests, compile checks,
dependency consistency, and actionlint. The fresh-environment OSV scan reported
no known vulnerabilities. Windows packaging and launch also passed locally.

Candidate checksums from that CI run:

| Artifact | SHA256 |
| --- | --- |
| Acadence-0.1.0-windows-x64.exe | `ee07075ff78b6d21534b3b22bf1c8b07ad2e651ee4a7f5aa93fffb0441dc14ff` |
| Acadence-0.1.0-macos-arm64.zip | `5caa3510e61c02b406a8cbf353eb5ffc4106937cb171c009fd205e0ec0ddca60` |
| Acadence-0.1.0-linux-x64.deb | `7e7950c3e27f316eb3b712d160f149ff40e28259427968a049d0b2851e6d8c44` |

These are preparation artifacts, not published release assets. The approved tag
workflow rebuilds the release merge commit and generates its final `SHA256SUMS`;
those checksums may differ because the source commit and build timestamp change.

## Repository changes completed

- Squash-merged audit PR #2 and release-tooling PR #3.
- Protected main with required PRs/CI, linear history, admin enforcement, and no
  force pushes or branch deletion. Enabled squash-only merges and branch cleanup.
- Removed merged local `feature/admin`, `feature/core-app-setup`,
  `feature/core-functions`, and `feature/uiux` branches and their remote branches;
  also removed merged remote `version/release-1.1.0`.
- Removed the merged audit PR branch and release-tooling branch/worktree.
- Retained unmerged `version/release-1.2.0` (last commit 2026-05-17, over 30 days
  old), and retained the original local audit branch as published ancestry differs
  after squash merging. No unmerged branch was deleted.
- Added the requested documentation, all-rights-reserved license, repository
  templates, ownership, dependency updates, native CI, and release automation.

No signing secrets or tag-signing key are configured. Required future signing
secret names and remaining manual checks are listed in [release operations](releases.md).
Dependabot maintenance PRs remain separate; none was labeled release-blocking
when preparation began.
