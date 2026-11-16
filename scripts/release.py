"""Validate a tag, assemble release notes, and publish only complete draft assets."""

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app_version import __version__  # noqa: E402

TARGETS = {"windows-x64": "exe", "macos-arm64": "zip", "linux-x64": "deb"}
SEMVER = r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-(rc|beta)\.([1-9]\d*))?"


def run(*args):
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def notes():
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    match = re.search(
        rf"^## \[{re.escape(__version__)}\] - \d{{4}}-\d{{2}}-\d{{2}}\n(.*?)(?=^## |\Z)",
        changelog,
        re.M | re.S,
    )
    if not match or "## [Unreleased]" not in changelog:
        raise RuntimeError("Versioned changelog and fresh Unreleased section are required")
    return (
        match.group(1).strip()
        + "\n\nUnsigned builds; no code signing or macOS notarization is configured.\n"
    )


def validate_tag(tag):
    if not re.fullmatch(SEMVER, __version__) or tag != f"v{__version__}":
        raise RuntimeError("Tag must exactly match the application SemVer")
    if run("git", "cat-file", "-t", tag) != "tag":
        raise RuntimeError("Release tag must be annotated")
    commit = run("git", "rev-parse", f"{tag}^{{commit}}")
    if commit != run("git", "rev-parse", "HEAD"):
        raise RuntimeError("Checkout does not match the release tag")
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", commit, "origin/main"], cwd=ROOT, check=True
    )
    notes()
    return commit


def publish(tag):
    commit = validate_tag(tag)
    output = ROOT / "release-assets"
    expected: set[str] = set()
    for target, extension in TARGETS.items():
        stem = f"Acadence-{__version__}-{target}"
        artifact = output / f"{stem}.{extension}"
        metadata_path = output / f"{stem}.json"
        metadata = json.loads(metadata_path.read_text())
        if (
            metadata["commit"] != commit
            or metadata["version"] != __version__
            or metadata["artifact"] != artifact.name
            or metadata["sha256"] != digest(artifact)
            or metadata["lock_sha256"] != digest(ROOT / "requirements.lock")
        ):
            raise RuntimeError(f"Artifact provenance mismatch: {target}")
        expected.update((artifact.name, metadata_path.name))
    if {p.name for p in output.iterdir()} != expected:
        raise RuntimeError("Unexpected or missing release assets")
    checksums = output / "SHA256SUMS"
    checksums.write_text("".join(f"{digest(output / name)}  {name}\n" for name in sorted(expected)))
    expected.add(checksums.name)
    notes_path = ROOT / "build" / "release-notes.md"
    notes_path.parent.mkdir(exist_ok=True)
    notes_path.write_text(notes())
    existing = subprocess.run(
        ["gh", "release", "view", tag, "--json", "isDraft"], capture_output=True, text=True
    )
    if existing.returncode == 0:
        if not json.loads(existing.stdout)["isDraft"]:
            raise RuntimeError("Never overwrite a published release")
        # A failed attempt remains draft. Refuse ambiguous partial uploads.
        raise RuntimeError("Draft already exists; inspect its assets before resuming manually")
    command = [
        "gh",
        "release",
        "create",
        tag,
        "--verify-tag",
        "--draft",
        "--title",
        tag,
        "--notes-file",
        str(notes_path),
    ]
    if "-" in __version__:
        command += ["--prerelease"]
    subprocess.run(command, check=True)
    subprocess.run(
        ["gh", "release", "upload", tag, *[str(output / name) for name in sorted(expected)]],
        check=True,
    )
    with tempfile.TemporaryDirectory() as directory:
        subprocess.run(["gh", "release", "download", tag, "--dir", directory], check=True)
        downloaded = Path(directory)
        if {p.name for p in downloaded.iterdir()} != expected:
            raise RuntimeError("Remote draft is incomplete; leaving it unpublished")
        for name in expected:
            if digest(downloaded / name) != digest(output / name):
                raise RuntimeError(f"Remote checksum mismatch: {name}")
    # Pushing this tag is allowed only after the owner's release-plan approval.
    latest = "false" if "-" in __version__ else "true"
    subprocess.run(
        ["gh", "release", "edit", tag, "--draft=false", f"--latest={latest}"], check=True
    )
    print(run("gh", "release", "view", tag, "--json", "url", "--jq", ".url"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["validate", "publish"])
    parser.add_argument("tag")
    args = parser.parse_args()
    if args.command == "validate":
        validate_tag(args.tag)
    else:
        publish(args.tag)
