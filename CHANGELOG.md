# Changelog

All notable changes are documented here using Keep a Changelog and Semantic
Versioning. Dates use Asia/Manila. Earlier development had no release tags;
branch names and the former UI version label are not published releases.

## [Unreleased]

## [0.1.0] - 2026-11-16

### Added
- Track subjects, deadlines, priorities, completion history, and notifications.
- Create tasks with voice input and review AI-generated guidance before saving.
- Automated checks, native desktop packaging, checksums, and draft-first releases.
- Contributor guidelines and a single application version source.

### Changed
- Store packaged application data in the user's application-data directory.
  Existing portable installations require a backup and manual data migration.
- Use hash-locked release dependencies and separate stable/beta download catalogs.

### Fixed
- Preserve saved settings and task guidance when writes or regeneration fail.
- Validate account recovery codes and keep recovery verification tied to the account.
- Stop microphone and notification workers when their windows or sessions close.
- Show pending tasks beyond the previous query limit and improve spoken deadline parsing.

### Security
- Exclude deployment secrets from builds and prevent remembered administrator logins.
- Update release dependencies; the recorded OSV scan reports no known vulnerabilities.
- Document remaining local-session, encryption, and database migration limitations.
