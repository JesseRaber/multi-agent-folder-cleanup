# multi-agent-folder-cleanup 1.5.1 (candidate)

Status: local candidate; not committed, published or installed.

## Changes

- Stop root-dependent work when connector/search discovery returns multiple same-name candidate project roots. Preserve their full paths/sites and stable identifiers in a checkpoint.
- Never choose a canonical root from filename, modified time, search rank, size or matching hashes. Require owner direction or applicable adopted authority/navigation.
- Add a compact audit claim table separating Documented, Observed, Inferred and Unknown conclusions.
- Check the intended folder, project index and canonical tracker before creating an important standalone file.
- Maintain exactly one authoritative project-wide tracker for proposed changes, future work, deferred work and open tasks; use exact pending insertions when safe shared writing is unavailable.
- Add a Microsoft Copilot agent package that retains the Python helpers and omits the unsupported `.ps1` file. The universal package remains unchanged for hosts that support PowerShell.

## Compatibility and boundaries

- No cleanup, move, deletion, connector mutation or deployment permission is added.
- The helper command interfaces and receipt schema are unchanged from 1.5.0; helper version strings are 1.5.1 for package consistency.
- Existing projects do not adopt the optional Project Rules merely by installing this skill.

## Verification required before release

- Run the complete repository test suite and official quick validator.
- Build all seven packages and reopen/byte-check their members.
- Verify Python/PowerShell helper versions and syntax.
- Confirm the generated archives remain candidates until an explicitly authorized release step.
