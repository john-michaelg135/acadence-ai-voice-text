# Release operations

## Policy and supported targets

Main requires PRs, passing `checks`, up-to-date branches, resolved conversations,
and linear history. Admins are included. Force pushes and deletion are disabled.
The sole contributor can merge their own passing PR; no second reviewer is required.
Only squash merge is enabled. Do not rewrite published branches or tags.

The initial version is **0.1.0**: no tags or manifest version existed. The old
`Version 1.2.0` UI label was untagged development text, not a release manifest.
After the first tag, breaking changes bump major (minor below 1.0), features bump
minor, and fixes/performance/tooling bump patch. A major bump requires owner approval.
Prereleases use `-rc.N` or `-beta.N`; they never become GitHub's latest stable release.

CI targets Windows x64, macOS arm64, and Ubuntu x64. Windows arm64 and macOS Intel
are not supported by this matrix. Linux `.deb` packages require an apt-compatible
system. Native packages are unsigned. The release publishes `updates-stable.json`
or `updates-beta.json` with versioned download URLs and hashes. Prereleases never
write stable metadata. There is no in-app updater yet; this is a documented download
catalog, not a claim that the app installs updates. The stable catalog is available
at the repository's `releases/latest/download/updates-stable.json` endpoint.

## Repeat the build

Use a fresh checkout at the release tag, Python 3.13.7, and the runner OS identified
in each artifact's JSON provenance. Install Tcl/Tk and FFmpeg; Linux also needs
`portaudio19-dev`, `python3-tk`, and `xvfb`; macOS needs Homebrew PortAudio.

```text
python -m pip install --require-hashes -r requirements.lock
python scripts/check.py
python build_exe.py --onefile       # Windows
python build_exe.py                 # macOS / Linux
python scripts/package_release.py
```

Set `PYTHONHASHSEED=0` and `SOURCE_DATE_EPOCH` to `git log -1 --format=%ct` before
building. CI sets both. Packages include the source commit, Python/OS versions,
lock hash, and artifact hash in adjacent JSON files. The lock pins all resolved
Python dependencies with hashes and uses CPU PyTorch. Update it intentionally:

```text
uv pip compile requirements-dev.txt --python-version 3.13 --universal --torch-backend cpu --extra-index-url https://download.pytorch.org/whl/cpu --index-strategy unsafe-best-match --generate-hashes --emit-index-url --output-file requirements.lock
```

Runner images, OS packages, native compilers, and source-distribution build tools
can still affect bytes. Bit-for-bit reproducibility across machines is not yet
verified. Preserve the released packages and provenance; do not rebuild and replace
published assets. PyInstaller's reproducibility controls are documented at
https://pyinstaller.org/en/stable/advanced-topics.html#creating-a-reproducible-build.

## Prepare and approve

1. Fetch origin and tags. Require a clean tree on main exactly matching origin/main,
   green CI for that exact commit, and no open release-blocking PRs. Review AUDIT.md;
   unresolved deployment decisions remain release blockers until reviewed.
2. Run `python scripts/prepare_release.py` to list grouped commits and the version.
   Run with `--write` to create the release branch and dated changelog section.
   Run all checks, build, and smoke-test; commit with
   `chore(release): prepare vX.Y.Z`, then push and open a PR. Wait for native CI.
3. Show the owner the version rationale, notes, expected native assets, hashes,
   missing signing, test results, and commands below. **Wait for approval.**
4. After approval, squash-merge the release PR. Fetch and fast-forward main.
   Confirm CI is green on the resulting main commit and its version matches.
   Check `git config tag.gpgSign` / `user.signingKey`; sign the annotated tag when
   configured (`git tag -s`), otherwise annotate (`git tag -a`). Never reuse a tag.

```text
gh pr merge RELEASE_PR --squash --delete-branch
git switch main
git pull --ff-only origin main
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push origin vX.Y.Z
```

The tag workflow verifies the annotated tag belongs to main and matches the version
and changelog. It reruns checks and native builds, then creates a draft, uploads all
three packages, three provenance files, channel metadata and `SHA256SUMS`, downloads and hashes every
asset, and only then publishes. The tag approval therefore also authorizes this
workflow's publication. Failures leave either no release or an unpublished draft.
Existing drafts require manual inspection before retry; published releases cannot
be overwritten by the script.

Verify published downloads against `SHA256SUMS`, launch the Windows executable,
inspect release notes and the tag commit, and close only the milestone and linked
issues actually shipped. Confirm the fresh Unreleased section remains. Do not close
unrelated issues. The verification job downloads every published asset, checks all
checksums, and repeats the packaged Windows launch test.

## Smoke tests and limitations

`python scripts/smoke.py PATH_TO_EXECUTABLE` starts the actual packaged application
with isolated user data, builds the login GUI, queries SQLite, executes a Torch
tensor operation, imports Whisper, and requires a success report. On Linux, use
`xvfb-run -a` before the command. On macOS use the executable inside the `.app`.
This does not verify microphone access, toast delivery, SMTP, live AI providers,
model download/inference, screen-reader behavior, or end-user installation prompts.

## Signing and credentials

No Actions secrets were configured during setup. Current builds are explicitly
unsigned; no signing or notarization implementation is implied. A future signing
integration would need `WINDOWS_CERTIFICATE_BASE64`, `WINDOWS_CERTIFICATE_PASSWORD`,
`MACOS_CERTIFICATE_BASE64`, `MACOS_CERTIFICATE_PASSWORD`, `APPLE_ID`,
`APPLE_APP_SPECIFIC_PASSWORD`, and `APPLE_TEAM_ID` as CI secrets, plus reviewed
signing/notarization steps. Setting the names alone does not enable signing.
SMTP credentials and deployment encryption keys are per-installation runtime
configuration and must never enter the repository or packages.

## Rollback

### Recover a stopped release workflow

Actions checkout can replace a runner-local annotated tag ref with its peeled
commit (see [actions/checkout issue 882](https://github.com/actions/checkout/issues/882)).
Release jobs explicitly fetch the original annotation back into the disposable
runner checkout. This force **fetch** does not push, move, or delete the remote tag.
CI exercises rejection of a peeled local ref and successful restoration.

If a tag workflow stopped before creating a release, dispatch the repaired workflow
from main with the existing tag. Optionally supply a successful main CI run whose
commit exactly matches the tag; its previously built and smoke-tested native assets
can be reused. The workflow validates the run's commit, workflow, event, and result,
then verifies each artifact's provenance and checksums before draft publication.

```text
gh workflow run release.yml --ref main -f tag=vX.Y.Z -f artifact_run_id=RUN_ID
```

Omit `artifact_run_id` to rebuild the tagged source. Existing drafts still require
inspection before resuming; published assets are never overwritten.

To repeat verification of an already-published release without building, uploading,
or editing it, use:

```text
gh workflow run release.yml --ref main -f tag=vX.Y.Z -f verify_only=true
```

The verification job uses an explicit condition so skipped recovery/build jobs
cannot silently skip the final downloads, checksum checks, and Windows launch.

Never remove a published release or move its tag. Mark a broken release in its
notes and ship a fixed patch. Ask the owner before changing even an unused tag
pushed by mistake. Keep unmerged stale branches until explicitly approved for deletion.
