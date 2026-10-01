# Multi-Agent Folder Cleanup v1.4.0

A read-only scan of an 18-project shared portfolio showed that agents spend more on getting oriented than on cleanup. Typical sessions read 30–120 KB before any work. Earlier helpers also missed several multi-agent problems: an `AGENTS.md` over Codex's 32 KiB load limit, a proposed `AGENTS.md` sitting in `Incoming/`, session logs missing from a session index, stale skill copies, an orphaned Info-ZIP temp file, and a 1.3 GB Python install inside OneDrive. This release targets those.

## Changes

- Protocol split by mode: `preconditions.md` plus one of `audit-mode.md`, `plan-mode.md`, `execute-moves.md` or `execute-records.md`. `workflow.md` remains as a router, and section labels are unchanged.
- Audit helpers: `--brief`, `--out`, a closing **Findings at a glance** block, a startup read budget with a 32 KiB `AGENTS.md` flag, `--index-coverage`, live-loading names in non-governing folders, embedded skill copies with versions, orphaned temp files, collapsed noise suggestions with Python-environment detection, `--prune-noise`, `--max-seconds`, `--host-root`, and `--version` on every helper.
- Python/PowerShell report parity extended to every new section and option.
- Two new release assets: `-gemini-apps.zip` and `-project-rules.zip`.

## Upgrade

Install one complete package and confirm `audit_folder.py --version` (or `audit_folder.ps1 -Version`) prints `1.4.0`. Report text changed: relative paths, a `Measured against:` line, a split instruction-file section and new sections. Update anything that parses the old text. The move protocol, approval receipts and helper exit codes are unchanged.

## Validation scope

CI runs package, version and link checks; helper regression tests; v1.4 feature and parity tests; and the Windows and Ubuntu suites. Release builds extract and run every package. The new checks were exercised against real folders read-only. This is not a certification of live OneDrive sync state, every host's loading behavior, or universal model behavior. The 32 KiB figure is Codex's documented default and can be configured.
