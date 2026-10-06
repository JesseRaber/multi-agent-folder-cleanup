# multi-agent-folder-cleanup 1.6.1

Released 2026-10-06.

This release implements register rows R150 and R154 (PR #14), the first item in the v1.6.1 scope confirmed by the Codex and Manus audits of 2026-10-06.

## Changes

- New read-only `scripts/verify_records.py`: per-file SHA-256, UTF-8 validity, BOM, CRLF/LF/lone-CR counts, mojibake markers outside code, unresolved Markdown relative links and table damage, plus `--compare` (exact / newline-normalized / whitespace-only / differ) and `--expect-sha256`. Output is UTF-8 when redirected, including Windows cp1252 consoles.
- Work mode W5: when the helper is available, cite its output before calling a shared-record edit verified; otherwise say "not verified".
- Packaged `--version` smoke checks, install guides and audit-tools reference cover the new helper.

## Deferred

- Remaining v1.6.1-scope rows (R148/R149, R133/R132, R151/R152, R131, R136, R125, R127) are tracked in the project register for a later release.

## Publication boundary

Installed host copies are updated separately; this release does not change any host by itself.
