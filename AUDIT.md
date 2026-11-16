# Codebase audit

Branch: `audit/codebase-cleanup`. Audit date: 2026-11-16 (Asia/Manila).
Discovery locations refer to baseline commit `4113411`; locations marked **final**
refer to this branch. No production database or session was opened for testing.

## Architecture

`main.py` starts a Windows CustomTkinter desktop application. `AuthScreen` calls a
singleton SQLite `DatabaseManager`; `DashboardScreen` routes and caches subjects,
tasks, history, insights, settings and notification views. Users own subjects;
subjects own tasks. Queries use bound parameters and foreign keys/indexes exist.
Passwords use bcrypt; recovery emails use AES-GCM. The SQLite file is not encrypted.
Session and preference JSON are local. Google receives voice audio; local Whisper
is the network-failure fallback. g4f providers receive transcripts/task descriptions.
Gmail SMTP delivers recovery codes. A daemon scheduler queries SQLite using its own
connection and sends Windows toasts. PyInstaller builds the desktop distribution.

## Baseline

- Working tree clean on `main`; no applicable AGENTS.md or CI files found.
- `python -m unittest discover -v`: **0 tests**, NO TESTS RAN.
- `python -m compileall -q main.py build_exe.py database screens utils`: passed.
- `python -m pip check`: passed (dependency compatibility, not vulnerability safety).
- Ruff, mypy, Black and PyInstaller unavailable; no repository check configuration.
- Original build not executed: it automatically installed tools and packaged `.env`.
- After installing audit tools, isolated core Ruff rules found 104 issues; broader
  inherited machine rules found 301. The repository now defines its own rules.
- First mypy run before annotation fixes: 46 errors; checking untyped bodies exposed
  17 additional errors after those were corrected. These were not baseline passes.

## Directory coverage

- [x] Root: README, requirements, ignore rules, application and build entry points.
- [x] `screens/`: all tracked desktop views/popups; layouts, callbacks, comments,
  navigation, persistence calls, worker interactions and lifecycle reviewed.
- [x] `utils/`: all tracked security, persistence, AI, audio, scheduling, logging,
  theme, animation, notification and font modules; uncertain-use helper retained.
- [x] `database/`: schema, indexes, foreign keys and manager reviewed. Live DB,
  SQLite sidecars, credentials and existing attachments not inspected or changed.
- [x] `assets/`, `assets/fonts/`: tracked image/font inventory and loading paths;
  binary assets preserved, not decoded as source.
- [x] `.git/`: branch/status/history inspection. Pattern scan of 65 reachable commits
  found no credential/private-key/token matches; this is not proof of no secrets.
- [x] `.venv/`: dependency inventory/check/audit; tooling and compatible security
  updates installed. Vendored implementation is outside application cleanup scope.
- [x] `build/`, `dist/`, `__pycache__/`: generated artifact inventory; existing
  distributions preserved. New package artifacts written only under TEMP.
- [x] `.vscode/`: local editor inventory, not runtime application source.
- [x] `backlogs-sprints/`, `design-reference/`, `guidelines-security/`,
  `notes-considerations/`, `scratch/`: ignored local/reference inventory. Spreadsheets,
  PDFs and prototype scripts are not application entry points and were preserved.
- [x] `logs/`: existing private contents not printed or truncated; application
  imports/tests appended normal diagnostic messages through the existing logger.
- [x] `tests/`: added isolated regression/characterization tests; no real SMTP, AI,
  microphone, desktop toast, user database or session used by unit tests.
- [x] `audit/`: dependency advisory snapshots generated from pip-audit results.

## Findings

| ID | Severity | Category | Location | Problem and impact | Proposed fix | Status |
|---|---|---|---|---|---|---|
| A01 | Critical | Security/build | build_exe.py:36 | The build embeds `.env`, distributing SMTP/encryption credentials. | Exclude secrets, load operator configuration beside executable, ignore bootstrap credentials. | Fixed. Existing distributed credentials need rotation; old artifacts preserved. |
| A02 | Critical | Authentication | main.py:43 | An editable username restores an account without password verification, including admin. | Reject admin restore; replace normal-user remembered names with protected, revocable sessions. | Deferred / needs decision for session redesign. Admin bypass fixed and tested. |
| A03 | Critical | Encryption | utils/security.py:93 | Missing configuration uses a public deterministic master key. Changing it can strand existing recovery emails. | Provision a managed secret with an explicit re-encryption/recovery plan. | Deferred / needs decision: keys and existing data. |
| A04 | High | Audio correctness | utils/voice_manager.py:126 | Thread objects are used as elapsed time, so absent results never time out; model load failure leaves waiters stuck. | Use a monotonic deadline and detect a stopped worker. | Fixed; timeout and result-consumption tests. |
| A05 | High | Concurrency | utils/notification_scheduler.py:73 | Restart can revive the old loop with another user's state and duplicate notifications. | Signal cancellation and join before resetting state; reject restart if termination fails. | Fixed; restart regression test. Stop may wait up to 35 seconds for an active DB operation. |
| A06 | High | AI contract | utils/ai_parser.py:115 | Required-key checks accept null/array fields, invalid priorities and invalid model dates/times, crashing or mispopulating forms. Connectivity probes leak sockets. | Validate object/field contracts and close probes. | Fixed; malformed responses use offline parsing. |
| A07 | High | Persistence | utils/session_manager.py:17 | Valid non-object JSON crashes startup; interrupted writes destroy previous settings. | Validate shapes and atomically replace UTF-8 JSON. | Fixed; invalid JSON shapes and simulated write failure tested. |
| A08 | High | Data integrity | utils/security.py:149 | Encryption failure returns an empty email while signup reports success. | Propagate failure and report account-creation failure to the user. | Fixed; encryption-failure and randomized round-trip tests. |
| A09 | High | Migrations | database/db_manager.py:105 | Startup attempts ALTER statements and suppresses unexpected OperationalError; even duplicate-column errors are misclassified as warnings. | Explicit versioned migrations with a backup/recovery strategy. | Deferred / needs decision: migrations. Reproduced only on a temporary DB. |
| A10 | Medium | Build/ops | requirements.txt:1 | Unbounded versions and absent tooling/CI make checks and installs inconsistent. | Define check configuration and dev tools; set compatible security bounds; decide lockfile and CI policy. | Deferred for full locking/CI; tooling, commands and security constraints implemented. |
| A11 | Medium | Duplication | database/db_manager.py:165 | Two username lookups duplicate identical SQL and mapping. | Retain both APIs and delegate to one implementation. | Fixed after database characterization tests. |
| A12 | Low | Ownership/docs | README.md:17; utils/ai_parser.py:418 | Placeholder setup, false local-only claims, noisy debug prints, unused imports and hundreds of redundant comments obscure behavior. | Accurate README/walkthrough, consistent formatting, remove redundant comments/debug output and unused bindings. | Fixed. Comment-only cleanup preserved ASTs for 30 source files; meaningful constraints retained. |
| A13 | High | Recovery authorization | screens/auth_screen.py:289 | Password update relies on wizard navigation; no verification state binds the reset to the current account. | Require a verified username, invalidate on mode/account changes and consume after reset. | Fixed; unverified and wrong-account reset tests. |
| A14 | High | Recovery reliability | utils/email_service.py:167 | Configured resend cooldown is unused; resends replace codes/reset attempts. Non-ASCII input raises TypeError in compare_digest; SMTP details leak to users. | Enforce cooldown, compare bytes, discard failed sends, return a generic error. | Fixed; cooldown and Unicode tests. |
| A15 | Critical | Attachment data loss | screens/tasks_view.py:899 | Regeneration deletes existing guidance before success; overwriting a file can truncate it on failure. | Retain the old association until success and atomically replace through one shared writer. | Fixed; existing-content and failed-replacement regressions. |
| A16 | High | UI lifecycle | screens/voice_popup.py:43; screens/dashboard_screen.py:192 | Closing voice window leaves listening active. Dashboard destructor calls Tk after interpreter destruction. | Stop listening once during destroy; clean cached views before Tk teardown; bound recorded phrases/network requests. | Fixed; lifecycle tests and hidden GUI smoke test. |
| A17 | High | Incomplete results | screens/all_pending_tasks_view.py:128; screens/notifications_view.py:79 | Screens labelled all pending/notifications silently omit tasks beyond the manager's default 200-row limit. | Explicitly fetch all rows for those views; retain chunked card rendering. | Fixed; 201-task regression. |
| A18 | High | Preferences | utils/session_manager.py:71 | Invalid value types break themes/scheduling; new users inherit a previous user's session preferences. | Validate settings values; use per-user defaults when no stored preferences exist; log persistence failures. | Fixed; malformed-value and user-isolation regressions. |
| A19 | High | Encryption compatibility | utils/security.py:136 (**final**) | Legacy format detection uses payload length; ordinary older ciphertext can be mistaken for the salted format. Errors return empty strings. | Identify supported legacy KDF/format versions from fixtures, then implement authenticated versioned decoding. | Deferred / needs decision: existing encrypted data and supported formats. No real PII used. |
| A20 | High | Credential lifecycle | database/db_manager.py:79; database/db_manager.py:219 (**final**) | Bootstrap password persists in plaintext; chmod is not a Windows owner-only ACL. Stored system-password expiration is never checked. | Decide bootstrap credential delivery/ACLs and expiry/recovery policy. | Deferred / needs decision: auth and permissions changes. File now ignored by Git. |
| A21 | Medium | Audio resource bounds | utils/voice_manager.py:52; utils/voice_manager.py:211 (**final**) | Inference queue/result map and per-phrase processing threads remain unbounded; late results can outlive timed-out callers. | Bounded inference requests with per-request completion/cancellation and hardware stress tests. | Deferred: requires worker lifecycle characterization beyond mocked timeouts; 30-second phrases and request timeouts now bound individual recordings. |
| A22 | Medium | Uncertain-use helper | utils/db_thread_safe.py:25 (**final**) | Helper advertises cross-thread safety but uses check_same_thread=True; no tracked callers found. | Confirm external/local callers, then remove it or implement a complete connection/cursor ownership contract. | Deferred / needs decision before deleting or changing a possibly external helper. |
| A23 | High | Voice parsing | utils/ai_parser.py:152; utils/ai_parser.py:299 | Spelled compound numbers become separate digits; offline tomorrow is ignored; online relative dates lack a current-date anchor. | Add compound tens/units and basic local-date offsets; give online prompt a local-date anchor. | Fixed for these cases; tested. Local parser remains intentionally limited and forms require review. |
| A24 | High | Dependencies | requirements.txt:1 | OSV reports 97 advisory records across 9 installed packages. pip check does not detect these vulnerabilities. | Apply compatible security fixes; review major Pillow/filelock upgrades separately. | Compatible updates installed and constrained. Remaining major upgrades need decision; see dependency inventory below. |
| A25 | High | Executable reliability | build_exe.py:43 (**final**) | Isolated package build omits Tk under sandbox; external build repeatedly crashes in native PyTorch DLL import and did not finish. | Validate a supported Windows/Python/PyTorch build environment before release. | Deferred: environment/native dependency blocker; no claim of a verified executable. |
| A26 | Medium | Async UI/maintainability | screens/tasks_view.py:729; screens/tasks_view.py:1250 (**final**) | AI worker callbacks query/schedule Tk during teardown, exceptions can be swallowed, and form layouts repeat. Broad extraction lacks interaction characterization. | Add deterministic main-thread dispatch and GUI interaction tests before consolidating form workflows. | Deferred: retain layouts rather than risk behavior changes for style; shared attachment writing extracted and core lifecycle bugs fixed. |
| A27 | Medium | Accessibility | screens/home_view.py:281; screens/insights_view.py:206 (**final**) | Clickable frame/label navigation is mouse-bound, and icon actions lack explicit keyboard alternatives in those cards. | Add focus/keyboard navigation and screen-reader checks on Windows. | Deferred: needs interactive accessibility verification; construction smoke tests do not establish accessibility. |

## Behavior changes

- Secrets excluded from new packages; runtime configuration is external. Missing build
  tools/failing PyInstaller now produce errors instead of installing silently or succeeding.
- Admin remembered-login restoration rejected; reset requires current-account OTP state;
  resend cooldown enforced and malformed Unicode codes fail without crashing.
- Transcription waits expire; model death is reported; speech/network operations bounded.
  Scheduler restart waits for old worker termination. Voice/window teardown releases resources.
- Malformed AI/session/settings inputs fall back safely; account creation aborts on
  encryption failure. Preferences no longer cross accounts. Relative voice dates and
  compound spoken numbers corrected; model output remains subject to form review.
- All-task screens include rows beyond 200. Editing refreshes immediately and retains
  existing AI guidance until an atomic replacement succeeds.
- Bare exception handlers in UI teardown/date rendering narrowed to expected Tk/date
  errors, so unexpected errors and process interrupts are no longer silently absorbed.
- Compatible installed dependency updates applied; no major upgrades, schema changes,
  user-data edits, uncertain file deletion or Git history rewriting performed.

## Dependency inventory

OSV initially reported these installed packages (records can include related advisories;
this is not a count of unique CVEs). Full ID/fix-version snapshots are in
`audit/dependency-advisories.json`.

| Package | Initial version | Initial records | Action |
|---|---|---:|---|
| aiohttp | 3.14.3 | 8 | Updated to 3.14.5 |
| brotli | 1.2.0 | 2 | Updated to 1.2.1 |
| certifi | 2026.7.22 | 2 | Updated to 2026.10.23 |
| msgpack | 1.2.2 | 1 | Updated to 1.2.4 |
| multidict | 6.8.0 | 2 | Updated to 6.9.1 |
| setuptools | 84.0.0 | 1 | Updated to 84.2.1 |
| urllib3 | 2.7.0 | 6 | Updated to 2.8.0 |
| filelock | 3.32.6 | 13 | Needs decision: fixes require 4.x; proposed minimum 4.2.1 |
| Pillow | 12.3.0 | 62 | Needs decision: fixes require 13.0.0 |

The aiohttp update also upgraded its existing dependency yarl to 1.25.1. No new
runtime package was introduced. Constraints preserve existing major versions.

## Verification

27 findings: 4 Critical, 16 High, 6 Medium, 1 Low. 15 fixed; 12 deferred or awaiting
decisions, including partially mitigated session/dependency issues.

Final commands, using `.venv/Scripts/python.exe`:

| Command | Observed result |
|---|---|
| `-m ruff format --check main.py build_exe.py database screens utils tests` | 43 files already formatted |
| `-m ruff check main.py build_exe.py database screens utils tests` | All checks passed |
| `-m mypy --no-incremental` | Success, 31 application source files; untyped bodies checked |
| `-m unittest discover -q` | 27 tests passed |
| `-m compileall -q main.py build_exe.py database screens utils tests` | Exit 0 |
| `-m pip check` | No broken requirements found |
| `-m pip_audit --vulnerability-service osv --timeout 30 --format json` | Exit 1: 75 advisory records remain in Pillow/filelock, down from 97 across 9 packages |
| `git diff --check` | Exit 0 |

Regression tests were observed failing before the fixes for timeout, malformed/session
write handling, model fields, cooldown/Unicode, reset verification, task truncation,
attachment loss, teardown, preference isolation and spoken date/number parsing.
The encryption test intentionally logs an injected failure; the suite still passes.
The build unit test mocks PyInstaller and is not evidence of executable success.

The hidden-window smoke test constructs Home, Subjects, Insights, History, AllPending,
AllCompleted, Notifications, Settings and Tasks against a temporary SQLite database
and session. It passes after teardown fixes. It does not exercise real microphone,
Whisper inference, SMTP, live AI providers, toast delivery, or screen readers.

The first PyInstaller run exited 0 and generated a temporary executable, but reported
Tk excluded because Tcl initialization was blocked by sandbox access. It is not a
valid release artifact. Tcl initialization succeeds outside sandbox. The external
retry encountered repeated native torch/functorch access violations and was stopped;
its exit code is 1. Existing distribution was not overwritten. Build diagnostic log:
`%TEMP%/acadence-build-verified.log`. A working executable is not verified.

Packaging used `python -m PyInstaller --noconfirm --onedir --windowed --name
AcadenceAudit`, the CustomTkinter directory/schema/assets data entries, and isolated
`--distpath`, `--workpath`, `--specpath` under `%TEMP%/acadence-audit-build`.
No private `.env` was present in the first generated package. This remains a failed
release check, not a passing build. The external retry was stopped after repeated
native access violations; it was not rerun against the final source/dependency snapshot.

The final source diff was inspected against baseline at the AST/function level to
separate formatting/comment removal from changed behavior. Files with uncertain
usage, existing distributions and encrypted user data were retained.

## Release-tooling follow-up (2026-11-16)

The isolated release environment upgrades Pillow to 13.0.0 and filelock to
4.2.10; the expanded regression suite passes. OSV reported no known vulnerabilities
for that environment; its machine-readable report is in
`audit/release-dependency-check.json`. This supersedes the dependency snapshot
above for the new release environment only. Native packaging and platform smoke
results must still pass before release; the original environment's torch 2.14
build again produced access violations. Session, encryption, migration, and live
service limitations below remain unresolved by release tooling.

## Needs decision before release

1. Protected/revocable normal-user sessions and credential expiry/bootstrap policy.
2. Managed encryption key plus supported legacy formats and a reviewed data migration.
3. Review/test major Pillow 13 and filelock 4 upgrades; do not ship with known advisories.
4. Versioned database migration strategy; confirm external callers before helper removal.
5. Supported Windows/Python/PyTorch packaging environment and end-to-end release checks.

Existing credentials embedded in previously distributed bundles need rotating. Their
locations are identified above; no secret values are included in this report.
