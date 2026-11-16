# Acadence

A Windows desktop academic tracker built with CustomTkinter and SQLite. It manages
subjects, task deadlines, priorities, completion history, and desktop notifications.

## Run from source

Use Python 3.10 or newer with Tcl/Tk installed, FFmpeg on PATH, and a microphone
for voice input. PyAudio may require Windows build tools if no wheel is available.

From the repository directory in PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

The first launch creates `database/acadence.db` and a random initial administrator
password in `database/.admin_credentials`. Protect that file and the database;
the database file itself is not encrypted. See [AUDIT.md](AUDIT.md) for remaining
security decisions before distributing or relying on this application.

## Configuration and data

Configure `SMTP_EMAIL` and `SMTP_PASSWORD` in an untracked `.env` beside `main.py`
for Gmail recovery emails. Use an app password. `ENCRYPTION_MASTER_SECRET` controls
recovery-email encryption. Set a strong secret before creating a new database and
retain it securely; changing it on an existing installation requires a migration.
The legacy fallback key remains for compatibility and is not safe for deployment.

Optional recovery settings are `OTP_TTL_SECONDS` (300), `OTP_MAX_ATTEMPTS` (5),
and `RESEND_COOLDOWN` (60). Values are in seconds except the attempt count.

Back up the database, its SQLite sidecar files when active, attachment directory,
and encryption configuration consistently. `session.json` stores the remembered
username and local preferences. Normal-user remembered sessions are not protected
authentication tokens; anyone who can edit the file can impersonate local users.

## Voice and AI

Audio is sent to Google Speech Recognition first. On network request failure,
Whisper `small.en` provides a local fallback. Download its weights before using
offline transcription:

```powershell
python -c "import whisper; whisper.load_model('small.en')"
```

Online text mapping and task guidance use g4f providers and send transcripts or
task descriptions externally. Offline text mapping uses local rules. Generated
research citations are suggestions and are not independently verified.

Open a subject, choose **Voice AI**, speak, then select **Done Speaking** and
**Process**. Review the populated subject or task form before saving it.

## Development checks

```powershell
python -m pip install -r requirements-dev.txt
python -m ruff format --check main.py build_exe.py database screens utils tests
python -m ruff check main.py build_exe.py database screens utils tests
python -m mypy
python -m unittest discover -v
python -m compileall -q main.py build_exe.py database screens utils tests
python -m pip check
python -m pip_audit --vulnerability-service osv
```

Unit tests use temporary files, in-memory databases, and mocked external services.
They do not test real microphones, delivery of emails/toasts, or live AI providers.
Typechecking includes untyped function bodies; third-party modules without type
information are ignored. Security constraints cover compatible dependency updates;
the remaining major upgrades are listed in the audit.

## Build for Windows

Install the development requirements, then run:

```powershell
python build_exe.py
```

The script uses the active Python interpreter and writes `dist/Acadence/Acadence.exe`.
It does not install tooling automatically or bundle `.env`. Configure any packaged
installation with environment variables or an operator-owned `.env` beside the
executable. Never include live SMTP credentials or encryption keys in a release.
Existing executables made with the old script may contain secrets; rotate those
credentials if distributed.

Packaging includes PyTorch and can take several minutes. A completed build still
needs a Windows launch and microphone/offline-model smoke test; see the audit for
the results and limitations of the current environment.
