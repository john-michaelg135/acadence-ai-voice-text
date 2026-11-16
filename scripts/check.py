"""Run the same quality checks locally and in CI; fail on the first failure."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = [
    "main.py",
    "app_version.py",
    "build_exe.py",
    "database",
    "screens",
    "utils",
    "tests",
    "scripts",
]


def main():
    commands = [
        ["ruff", "format", "--check", *SOURCES],
        ["ruff", "check", *SOURCES],
        ["mypy", "--no-incremental"],
        ["unittest", "discover", "-v"],
        ["compileall", "-q", *SOURCES],
        ["pip", "check"],
    ]
    for command in commands:
        subprocess.run([sys.executable, "-m", *command], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
