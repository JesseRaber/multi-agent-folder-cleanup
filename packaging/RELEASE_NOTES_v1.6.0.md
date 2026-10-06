# Multi-Agent Folder Cleanup v1.6.0 candidate

This candidate implements register rows R140-R146 from the reviewed handoff in Claude session `9ea792fb-da82-4728-982b-0d544f7c891e`.

## Changes

- Fixed the pre-existing R100 Python/PowerShell ordering mismatch for duplicate session IDs with tied activity timestamps, including Windows PowerShell 5.1 regression coverage and a reproducible PyYAML-gated test runner.
- Item-level tracker mapping and false-gap checks before source consolidation claims.
- Recoverable non-credential pre-edit copies, hashes, diffs and structure preservation for shared-record edits.
- Idempotent edit/move scripts, archived-original protection and inspect-before-rerun safeguards.
- Session-log ownership and complete open-work reporting.
- Narrow secret definitions, owner approval for other privacy redactions and recoverable non-secret originals; optional Project Rules 3.2.0.
- Opal review follow-ups: own-log pending-edit outcomes, Work mode in the universal install fallback, clearer helper hydration requirements, archive-and-stub excluded from the move protocol.

## Candidate status

Local candidate only. Git push, pull request, tag, release and host installation require separate owner authorization.
