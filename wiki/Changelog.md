# Changelog

Source documentation: repository source is 2.1.0; as of 2026-10-29 the latest published release is 2.0.0. Source installs and published downloads may report different versions.

Current release: **[v2.0.0](https://github.com/JesseRaber/multi-agent-folder-cleanup/releases/tag/v2.0.0)**. The full history is [CHANGELOG.md](https://github.com/JesseRaber/multi-agent-folder-cleanup/blob/main/CHANGELOG.md). This page does not replace it.

## 2.0.0 — Project setup and scoped workflows

Setup, host-aware instructions, browser-safe saves, scoped approval and append-only closeout. Project Rules remain4.0.1.

## v1.9.0 — pending targets and index discovery

- Contained absolute pending targets; unresolved-first reporting; declared/conventional index discovery with ambiguity reporting.
- Windows/Ubuntu package checksum comparison; Project Rules remain 4.0.1.

## v1.8.1 — Project Rules 4.0.1 and helper accuracy

- Bundled Project Rules template 4.0.1: eight core wording changes (sections 4, 5, 7, 12) from the 2026-10-12/13 portfolio and rules-behavior audits; section 0 unchanged. Projects on 4.0.0 migrate by replacing sections 0-12 and editing section 13.
- Helpers: Work routing detected for Rules 4.0.0+ (numeric version compare); pre-edit copies in `before*`/`backup*` not counted as pending; split-table and oversized-quick-context findings; link targets with balanced or escaped parentheses; `-Orient -Out` header parity; bold log labels; case-insensitive pending JSON keys; case-folded `--out` confinement.
- Install guides route Work-mode reads correctly and show the full arrival line; README names Rules 4.0.1; plugin manifests describe Work mode; CI checks stale previous-version mentions and installs pinned dependencies.
- Release notes: [v1.8.1](https://github.com/JesseRaber/multi-agent-folder-cleanup/releases/tag/v1.8.1).

## v1.8.0 — smaller read sets, recycle-path test

- Per-mode read sets reduced (Work on Project Rules 4.0.0+ from 6,706 to 4,757 tokens; Audit 8,185 to 6,676; Plan 6,055 to 5,292). Content moved to on-demand files: work-mode-baseline.md, audit-edge-cases.md, execute-principles.md, release-packages.md.
- R255: Execute runs a recycle-path test before any delete and stops if the test file does not reach the Recycle Bin; no delete through a remote shell or bridge without a passing test.
- Helper fixes: Generated line carries the UTC offset; space-before-offset session start times are parsed; `--session-index` lists logs without a header block.
- README FAQ: Grok uses the microsoft-copilot-agent-only ZIP, not UNIVERSAL.
- Release notes: [v1.8.0](https://github.com/JesseRaber/multi-agent-folder-cleanup/releases/tag/v1.8.0).

## v1.7.2 — install backups and Work-mode trim

- Work mode trimmed (references/work-mode.md reduced by removing repetition while preserving rules and anchors).
- Install guides: keep the previous version's backup outside every folder the host scans for skills; afterward exactly one SKILL.md with name multi-agent-folder-cleanup under the host skill roots. Files matching the ZIP are not proof of loading.
- Release notes: [v1.7.2](https://github.com/JesseRaber/multi-agent-folder-cleanup/releases/tag/v1.7.2).

## v1.7.1 — align with Project Rules 4.0.0

- Bundled optional rules are now Project Rules 4.0.0: section 0 (minimum rules), invariant sections 1–12, and a per-project section 13 template. `SECTION_0_PASTE_IN.txt` for hosts that never read the folder.
- Work mode: read-only limits task files (not the session log unless all writes are prohibited); one tool slug per runtime; one pre-edit copy per shared file per session only before a full-file replacement; apply leftover PENDING rows from `Incoming/*/_PROVENANCE.md`; Windows PowerShell 5.1 write rules (no `>>` or unencoded `Set-Content`/`Out-File` on shared records).
- Helpers: `--orient` treats closed sessions as closed (never possibly active), uses file times for activity, prints the window used, counts provenance PENDING, lists slug/runtime collisions, and warns under PowerShell 5.1. `--session-index` treats declared slugs as standard. `--pending` lists provenance PENDING lines. `--portfolio` gains core-match and Section 13 complete columns. `verify_records.py` flags NUL bytes and UTF-16 damage.
- Independent review fixes included. Optional rules section 13 ships with a placeholder so an unfilled copy never opts in sequential writers.
- Release notes: [v1.7.1](https://github.com/JesseRaber/multi-agent-folder-cleanup/releases/tag/v1.7.1).

## v1.7.0 — add-only agents, sequential writers, sync-copy and pending-file checks

- Add-only agents upload into a dated `Incoming/` folder with `_PROVENANCE.md` (never a new top-level folder).
- Opt-in sequential writers: owner adds a `Sequential writers:` line; active agent edits shared records directly with read-back when no other writer looks active.
- Leftover pending files (`PENDING_<TARGET>.md`) are applied by the next qualifying writer when the base still matches.
- Sync conflict copies and same-name files are reported, never merged or deleted by the skill.
- Cloud connector guidance: work by file id, state view and time, stage replacements.
- Expanded audit sections and helpers (`--pending`, enhanced `--orient` and `--portfolio`). Optional Project Rules 3.3.0.
- Release notes: [v1.7.0](https://github.com/JesseRaber/multi-agent-folder-cleanup/releases/tag/v1.7.0).

## v1.6.3 — portfolio audit corrections

- Filename-derived session times, nonstandard session filenames, brief portfolio matrix shows every child, running helper path/version, non-loading instruction backup names, pending-edit retention, device helper access route.
- Release notes: [v1.6.3](https://github.com/JesseRaber/multi-agent-folder-cleanup/releases/tag/v1.6.3).

## v1.6.2 — release safety

- Grok routed to the `-microsoft-copilot-agent-only` package (Grok rejects the Universal ZIP's `.ps1`; owner upload test 2026-10-05).
- Draft-first release workflow: refuses an existing release, requires the notes file, never replaces published assets.
- `packaging/check_versions.py`, `packaging/verify_release.py` and `HOST_INSTALL_LOG.md` added; Windows and Linux builds give identical archives.
- No change to the skill's modes or rules.
- Release notes: [packaging/RELEASE_NOTES_v1.6.2.md](https://github.com/JesseRaber/multi-agent-folder-cleanup/blob/main/packaging/RELEASE_NOTES_v1.6.2.md).

## v1.6.1 — record verification

- Added read-only `scripts/verify_records.py`: SHA-256, UTF-8, BOM, line endings, mojibake markers, unresolved Markdown relative links, table damage, `--compare`, and `--expect-sha256`.
- Work mode asks agents to cite that output before calling a shared-record edit verified.
- Release notes: [packaging/RELEASE_NOTES_v1.6.1.md](https://github.com/JesseRaber/multi-agent-folder-cleanup/blob/main/packaging/RELEASE_NOTES_v1.6.1.md).

## v1.6.0 — shared-record, rerun, and privacy safeguards

- Recoverable non-credential copies, before/after hashes, and exact diffs before a shared-record edit is called verified.
- Idempotent reruns, session-log ownership, and a narrower secret definition.
- Optional Project Rules template 3.2.0. Installing the skill does not adopt it.
- Release: [v1.6.0](https://github.com/JesseRaber/multi-agent-folder-cleanup/releases/tag/v1.6.0).

## Earlier releases still on the current line

- [v1.5.3](https://github.com/JesseRaber/multi-agent-folder-cleanup/releases/tag/v1.5.3) — audit parity and documentation corrections.
- [v1.5.2](https://github.com/JesseRaber/multi-agent-folder-cleanup/releases/tag/v1.5.2) — `verify_move.py --root`; `workflow.md` removed.
- [v1.5.1](https://github.com/JesseRaber/multi-agent-folder-cleanup/releases/tag/v1.5.1) — root identity, one canonical tracker, Copilot package.
