"""Package native builds and record their source and dependency provenance."""

import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app_version import __version__  # noqa: E402


def sha256(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def package():
    os.chdir(ROOT)
    system = {"win32": "windows", "darwin": "macos", "linux": "linux"}[sys.platform]
    architecture = {"AMD64": "x64", "x86_64": "x64", "arm64": "arm64", "aarch64": "arm64"}[
        platform.machine()
    ]
    stem = f"Acadence-{__version__}-{system}-{architecture}"
    output = ROOT / "release-assets"
    output.mkdir(exist_ok=True)
    if sys.platform == "win32":
        artifact = output / f"{stem}.exe"
        shutil.copy2(ROOT / "dist" / "Acadence.exe", artifact)
    elif sys.platform == "darwin":
        artifact = output / f"{stem}.zip"
        subprocess.run(
            [
                "ditto",
                "-c",
                "-k",
                "--sequesterRsrc",
                "--keepParent",
                "dist/Acadence.app",
                str(artifact),
            ],
            check=True,
        )
    else:
        stage = ROOT / "build" / "deb"
        if stage.exists():
            raise RuntimeError("build/deb already exists; use a fresh build directory")
        target = stage / "opt" / "acadence"
        shutil.copytree(ROOT / "dist" / "Acadence", target)
        control = stage / "DEBIAN"
        control.mkdir()
        deb_version = __version__.replace("-", "~")
        deb_arch = {"x64": "amd64", "arm64": "arm64"}[architecture]
        (control / "control").write_text(
            f"Package: acadence\nVersion: {deb_version}\nArchitecture: {deb_arch}\n"
            "Maintainer: Acadence contributors\nDepends: libportaudio2, ffmpeg, libx11-6, libxext6, libxrender1\n"
            "Description: Acadence academic tracker\n",
            encoding="utf-8",
        )
        launcher = stage / "usr" / "bin"
        launcher.mkdir(parents=True)
        (launcher / "acadence").symlink_to("/opt/acadence/Acadence")
        artifact = output / f"{stem}.deb"
        subprocess.run(
            ["dpkg-deb", "--root-owner-group", "--build", str(stage), str(artifact)], check=True
        )
    if not artifact.is_file() or artifact.stat().st_size == 0:
        raise RuntimeError("Missing native package")
    if artifact.stat().st_size >= 2_000_000_000:
        raise RuntimeError("Package exceeds GitHub's per-asset size limit")
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    metadata = {
        "version": __version__,
        "commit": revision,
        "os": system,
        "arch": architecture,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "lock_sha256": sha256(ROOT / "requirements.lock"),
        "artifact": artifact.name,
        "sha256": sha256(artifact),
        "signed": False,
        "source_date_epoch": os.environ.get("SOURCE_DATE_EPOCH"),
    }
    (output / f"{stem}.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(f"{metadata['sha256']}  {artifact.name}")


if __name__ == "__main__":
    package()
