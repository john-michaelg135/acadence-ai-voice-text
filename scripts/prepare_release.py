"""Plan a SemVer release; optionally prepare files after verifying main and CI."""

import argparse
import collections
import datetime
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app_version import __version__  # noqa: E402


def run(*args):
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()


def plan():
    tags = run("git", "tag", "--merged", "HEAD", "--sort=-version:refname").splitlines()
    stable = next((tag for tag in tags if re.fullmatch(r"v\d+\.\d+\.\d+", tag)), None)
    revision = f"{stable}..HEAD" if stable else "HEAD"
    commits = run("git", "log", "--format=%s", revision).splitlines()
    grouped = collections.defaultdict(list)
    for subject in commits:
        match = re.match(r"([a-z]+)(?:\([^)]*\))?!?:", subject)
        grouped[match.group(1) if match else "other"].append(subject)
    if not stable:
        version, reason = __version__, "No release tags: use the initial manifest version (0.1.0)."
    else:
        major, minor, patch = map(int, stable[1:].split("."))
        bodies = run("git", "log", "--format=%B", revision)
        breaking = any(re.match(r"[a-z]+(?:\([^)]*\))?!:", s) for s in commits)
        breaking = breaking or bool(re.search(r"^BREAKING[ -]CHANGE:", bodies, re.M))
        if breaking:
            version = f"{major + 1}.0.0" if major else f"0.{minor + 1}.0"
            reason = "Breaking change: major bump; below 1.0 use a minor bump."
        elif "feat" in grouped:
            version, reason = f"{major}.{minor + 1}.0", "Feature commits require a minor bump."
        else:
            version, reason = (
                f"{major}.{minor}.{patch + 1}",
                "Fixes and maintenance require a patch bump.",
            )
    return version, reason, grouped


def prepare(version, allow_major):
    if run("git", "status", "--porcelain"):
        raise RuntimeError("Working tree is not clean")
    if run("git", "branch", "--show-current") != "main":
        raise RuntimeError("Release preparation requires main")
    subprocess.run(["git", "fetch", "origin", "--tags"], cwd=ROOT, check=True)
    commit = run("git", "rev-parse", "HEAD")
    if commit != run("git", "rev-parse", "origin/main"):
        raise RuntimeError("main must exactly match origin/main")
    if plan()[0] != version:
        raise RuntimeError("Remote tags changed the release plan; review the new plan")
    if int(version.split(".")[0]) > int(__version__.split(".")[0]) and not allow_major:
        raise RuntimeError("Stop: obtain owner approval before a major bump")
    checks = json.loads(
        run(
            "gh",
            "run",
            "list",
            "--workflow",
            "ci.yml",
            "--branch",
            "main",
            "--commit",
            commit,
            "--limit",
            "1",
            "--json",
            "conclusion,status",
        )
    )
    if not checks or checks[0] != {"conclusion": "success", "status": "completed"}:
        raise RuntimeError("CI is not green for this exact main commit")
    blocking = json.loads(
        run(
            "gh",
            "pr",
            "list",
            "--state",
            "open",
            "--label",
            "release-blocker",
            "--json",
            "number,title",
        )
    )
    if blocking:
        raise RuntimeError(f"Open release-blocking PRs: {blocking}")
    if run("git", "tag", "--list", f"v{version}"):
        raise RuntimeError("Release tag already exists")
    changelog_path = ROOT / "CHANGELOG.md"
    changelog = changelog_path.read_text()
    if changelog.count("## [Unreleased]") != 1:
        raise RuntimeError("Expected exactly one Unreleased section")
    date = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).date()
    subprocess.run(["git", "switch", "-c", f"chore/release-v{version}"], cwd=ROOT, check=True)
    version_path = ROOT / "app_version.py"
    version_path.write_text(
        re.sub(r'__version__ = "[^"]+"', f'__version__ = "{version}"', version_path.read_text())
    )
    changelog_path.write_text(
        changelog.replace("## [Unreleased]", f"## [Unreleased]\n\n## [{version}] - {date}")
    )
    print(
        "Prepared files. Run checks/build, commit, push, open the PR, and wait for owner approval."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument(
        "--allow-major", action="store_true", help="Only after explicit owner approval"
    )
    args = parser.parse_args()
    version, reason, grouped = plan()
    print(f"Proposed version: {version}\n{reason}")
    for category, subjects in sorted(grouped.items()):
        print(f"\n{category}:")
        for subject in subjects:
            print(f"  {subject}")
    if args.write:
        prepare(version, args.allow_major)
