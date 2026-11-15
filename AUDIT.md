# Codebase audit

Branch: `audit/codebase-cleanup`. Locations refer to the code at discovery unless marked final.

## Architecture

`main.py` starts a Windows CustomTkinter desktop application. `AuthScreen` authenticates
against a singleton SQLite `DatabaseManager`; `DashboardScreen` routes and caches
subject, task, history, insights, settings, and notification views. SQL uses bound
parameters. Subjects own tasks; users own subjects. Recovery email is encrypted with
AES-GCM; passwords use bcrypt. Session and preference JSON are stored locally.
SpeechRecognition sends audio to Google; offline fallback queues Whisper inference.
g4f sends transcripts and task descriptions to external providers. SMTP sends recovery
codes through Gmail. A daemon scheduler queries SQLite and dispatches Windows toasts.
`build_exe.py` packages the application using PyInstaller.

## Baseline

- Clean `main` working tree; no AGENTS.md found.
- `python -m unittest discover -v`: 0 tests (NO TESTS RAN).
- `python -m compileall -q main.py build_exe.py database screens utils`: passed.
- `python -m pip check`: passed.
- Ruff, mypy, Black and PyInstaller initially unavailable; no configurations or CI.
- Original build was not executed: it installs tooling automatically and bundles `.env`.
- Existing database, sessions, credentials, logs and old distribution are private runtime
  artifacts, not test fixtures. Do not launch the application against them.

## Directory coverage

- [x] Root manifests, README, entry point, build script, ignore rules; no CI present.
- [ ] `screens/`: all desktop views and popups.
- [ ] `utils/`: security, persistence, AI, audio, scheduling, logging, themes, animation.
- [x] `database/`: schema and manager read; runtime DB and attachments not opened.
- [x] `assets/`, `assets/fonts/`: tracked image/font inventory; binary assets preserved.
- [x] `.git/`: status, branch and history metadata; no history rewriting.
- [x] `.venv/`, `build/`, `dist/`, `__pycache__/`: generated/vendor inventories only;
  not treated as application source or reformatted.
- [x] `.vscode/`: local editor settings; not application source.
- [x] `backlogs-sprints/`, `design-reference/`, `guidelines-security/`,
  `notes-considerations/`, `scratch/`: ignored reference/local material; inventory only.
- [x] `logs/`: private runtime logs; not printed or altered.

## Findings

| ID | Severity | Category | Location | Evidence and impact | Proposed fix | Status |
|---|---|---|---|---|---|---|
| A01 | Critical | Security/build | build_exe.py:36 | `.env` is included in distributable assets, exposing SMTP and encryption secrets to recipients. Existing bundles may contain credentials and need rotation. | Exclude secrets; load operator configuration outside bundle. | Open |
| A02 | Critical | Authentication | main.py:43 | Editable session username is sufficient to restore any account, including admin. | Reject admin auto-login as an obvious privilege bug; decide protected session design for normal accounts. | Open / needs decision for session redesign |
| A03 | Critical | Encryption | utils/security.py:93 | Missing master secret uses a public deterministic key; replacing it blindly makes existing recovery emails unreadable. | Require managed secret and plan data re-encryption. | Needs decision: data format/key migration |
| A04 | High | Correctness/audio | utils/voice_manager.py:126 | Timeout compares Thread objects; fallback sets elapsed equal to timeout, so missing results wait forever. Model-load failure leaves callers waiting. | Use monotonic elapsed time; report stopped worker. | Open |
| A05 | High | Concurrency | utils/notification_scheduler.py:73 | stop resets shared running flag without waiting; immediate restart lets old and new loops run with new user's state. | Give each run a cancellation event and join before restart. | Open |
| A06 | High | API validation | utils/ai_parser.py:115 | Only required key presence is checked; lists, null/string types and invalid enum values reach UI operations. | Validate object, field types and enum values; fallback on malformed output. | Open |
| A07 | High | Persistence | utils/session_manager.py:17 | Valid JSON arrays/null cause `.get` failures at startup; writes truncate file before completion. | Validate object shape and replace atomically. | Open |
| A08 | High | Data integrity | utils/security.py:149 | Encryption errors return empty string; account creation can report success with unusable recovery email. | Fail explicitly with UI handling; characterize legacy data first. | Open |
| A09 | High | Data layer | database/db_manager.py:105 | Startup runs ALTER statements, suppressing unexpected operational failures; partially initialized existing DB can be accepted. | Explicit versioned migrations with recovery strategy. | Needs decision: migrations |
| A10 | Medium | Build/ops | requirements.txt:1 | Unbounded dependency versions, no dev tooling, checks or reproducible build instructions. | Add development check configuration; record dependency audit; defer version policy. | Open |
| A11 | Medium | Maintainability | database/db_manager.py:165 | Two user lookup implementations duplicate identical SQL and mapping. | Preserve API and delegate to one implementation after characterization. | Open |
| A12 | Low | Cleanup/docs | README.md:17; utils/ai_parser.py:418 | Placeholder clone URL, misleading offline-model claim, debug prints and explanatory filler throughout. | Correct docs, remove debug prints and redundant comments without changing behavior. | Open |

## Decisions

Do not alter existing database migrations, encryption keys/formats, or production data.
Do not remove uncertain-use files/features or perform major dependency upgrades.
These decisions do not block independent fixes. No secrets are reproduced here.
