# Multi-Agent Folder Cleanup v1.4.1

Focused corrections to v1.4.0. No default-brief switch, catalog helper, deadline supervisor, incremental checkpoint format, domain-specific move rules, or receipt-schema migration.

- Both audit helpers block content reads for credential-hinted paths, links and detected cloud placeholders. Metadata inventory remains available; blocked reads do not count as verified hashes.
- Balanced/escaped parentheses in inline Markdown destinations work; root-only fallback matches are disclosed. Case checking normalizes relative segments and stops at the audit root.
- Previously uncapped brief detail lists now respect the ten-item limit without changing aggregate counts.
- Move verification refuses junction/symlink traversal, including linked ancestors, and refuses to hash detected cloud placeholders. Windows preflight checks momentary exclusive-read access and reports sharing failures.
- Link checks stop at the audited root (audit helpers) or the plan's common folder (move verifier). A project under a symlinked or junctioned parent folder, such as macOS `/tmp` or a redirected Windows profile, stays readable; links inside the root or plan are still refused. Cloud-placeholder refusal applies to the file itself, not its OneDrive parent folders.
- New regressions cover those failures using synthetic fixtures. Existing approved-map/receipt/source-change/newer-target tests remain in place.

## Limits

Checks are point-in-time, not locks or transactions. Windows attribute fixtures are not proof of live OneDrive hydration or cloud synchronization. No claim of stub-hash corruption was reproduced. No helper moves or deletes files. Host/volume-bound receipts, whole-process deadlines and interruption-resumable report output are deferred. `--max-seconds` remains a traversal budget, and `--out` remains a completed-report output, not a recovery baseline.

Validation: 68 tests on Linux (3 Windows-only skips); Ubuntu and Windows CI. The candidate also ran 64 tests on Windows with PowerShell 7 and 5.1 before the link-scope fix. Independent cross-model behavioral validation and live OneDrive Files On-Demand tests remain open.
