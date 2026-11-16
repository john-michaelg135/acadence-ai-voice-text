"""Launch a packaged app against isolated user data and require its success report."""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app_version import __version__  # noqa: E402


def smoke(executable):
    with tempfile.TemporaryDirectory(prefix="acadence-smoke-") as temporary:
        root = Path(temporary)
        env = os.environ.copy()
        for name in ("HOME", "USERPROFILE", "LOCALAPPDATA", "APPDATA", "XDG_DATA_HOME"):
            env[name] = temporary
        env["ENCRYPTION_MASTER_SECRET"] = "isolated-smoke-test-not-a-deployment-secret"
        env.pop("SMTP_EMAIL", None)
        env.pop("SMTP_PASSWORD", None)
        report = root / "smoke.json"
        startup = None
        if sys.platform == "win32":
            startup = subprocess.STARTUPINFO()
            startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startup.wShowWindow = 0
        subprocess.run(
            [str(Path(executable).resolve()), "--smoke-test", str(report)],
            cwd=root,
            env=env,
            check=True,
            timeout=180,
            startupinfo=startup,
        )
        result = json.loads(report.read_text())
        if result != {"version": __version__, "status": "ok"}:
            raise RuntimeError(f"Unexpected smoke report: {result}")
        print(f"Packaged GUI, SQLite, Torch and Whisper imports passed: {__version__}")


if __name__ == "__main__":
    smoke(sys.argv[1])
