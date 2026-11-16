# Changelog

All notable changes are documented here using Keep a Changelog and Semantic
Versioning. Dates use Asia/Manila. Earlier development had no release tags;
branch names and the former UI version label are not published releases.

## [Unreleased]

### Added
- Automated checks, native desktop packaging, checksums, and draft-first releases.
- Contributor guidelines and a single application version source.

### Fixed
- Preserve saved settings and task guidance when writes or regeneration fail.
- Validate account recovery codes and keep recovery verification tied to the account.
- Stop microphone and notification workers when their windows or sessions close.
- Show pending tasks beyond the previous query limit and improve spoken deadline parsing.

### Security
- Exclude deployment secrets from builds and prevent remembered administrator logins.
- Document outstanding session, encryption, and dependency risks in AUDIT.md.
