# multi-agent-folder-cleanup 1.5.2

Status: released as tag `v1.5.2` after owner approval 2026-10-04.

## Changes

- **Move safety (`verify_move.py`)**
  - `--root <project>` on `preflight`, `baseline` and `verify`: any source or target outside the project is refused as OUTSIDE ROOT, and a baseline inside the project is refused. Optional; omitting it keeps 1.5.1 behavior.
  - Maps whose sources or targets span top-level folders (common root `/` or a drive) no longer refuse every baseline location; each pair's folder is guarded instead.
  - Case-only renames (`readme.md` to `README.md`) on case-insensitive volumes are no longer reported as TARGET EXISTS, and final verify does not report them as STILL AT SOURCE.
  - macOS path comparisons fold case (Python's `normcase` does not on macOS). Linux stays case-sensitive.
  - The Windows exclusive-read probe uses the `\\?\` extended-length form for paths of 240+ characters.
- **Docs**: `-ExecutionPolicy Bypass`, `powershell.exe` and `python3` examples; guidance when a host package omits a helper or the project-rules folder; legacy `references/workflow.md` router removed.
- **Housekeeping**: pyflakes cleanup in `audit_folder.py` (no behavior change); author link to https://jesseraber.net in plugin metadata and a README credit line.

## Compatibility and boundaries

- No new move, deletion, connector or deployment permission. Receipt and baseline schemas are unchanged.
- `audit_folder.py` / `audit_folder.ps1` behavior is unchanged; their version strings are 1.5.2 for package consistency.
- The long-path probe change and Windows case-rename behavior are covered by unit tests on Linux and by the Windows CI job; they were not run on a live OneDrive folder.
