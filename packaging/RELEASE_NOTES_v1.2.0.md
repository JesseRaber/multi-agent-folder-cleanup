# Multi-Agent Folder Cleanup v1.2.0

## Summary

v1.2.0 expands the skill from single-root cleanup into a portfolio- and connector-aware workflow while preserving the Audit / Plan / Execute safety model. The same canonical skill folder is packaged for OpenAI/ChatGPT/Codex, Claude, Opal-compatible skill hosts, and portable installations.

## Packages

| Asset | Intended use |
|---|---|
| `multi-agent-folder-cleanup-1.2.0-openai.zip` | ChatGPT and Codex skills-only plugin |
| `multi-agent-folder-cleanup-1.2.0-portable.zip` | Standalone Agent Skill hosts, including Opal-compatible imports |
| `multi-agent-folder-cleanup-1.2.0-claude.zip` | Claude Code / Claude Desktop plugin |
| `multi-agent-folder-cleanup-1.2.0-skill.zip` | Skill folder only, for Claude.ai and other skill uploaders |
| `SHA256SUMS.txt` | Release-asset integrity verification |

## New workflow capabilities

- Portfolio-root inventory and project/entrypoint matrices.
- Full-path validation and explicit cross-project search-contamination reporting.
- Five lookup outcomes: exact match, likely same family, no result returned, verified absent, and inaccessible.
- Documentary-state versus operationally verified-state reporting.
- Root-level, folder-level, recursive, connector-returned, and record-reported count labels.
- Intentional pointer, identical duplicate, divergent control, and related claim-family distinctions.
- Separate move, record-only, and additive-intake execution boundaries.
- Connector-safe record patches with complete-document, concurrency, virtualized-editor, reopen, marker, order, and link checks.
- Privacy-minimized candidate intake and explicit partial-upload recovery.

## Helper enhancements

Both audit helpers now support:

- journal-size threshold reporting;
- repeatable expected-entrypoint checks;
- advisory portfolio-root matrices;
- conservative pointer-stub candidate detection;
- expected-upload manifest verification with optional size and SHA-256 fields.

All findings remain advisory. The helpers never select authority, move files, promote evidence, or authorize deletion.


## Fixed (from the 2026-09-23 deep scan of v1.1.0)

- `--exclude` / `-Exclude` now use one segment-aware, case-insensitive glob in both helpers. Python missed a root-level `logs/` for `**/logs/**`; PowerShell substring-matched it and also excluded `Catalogs/` and `changelogs.md`.
- Unreadable directories are reported under **Directories not readable** and in a closing **Coverage gap** line instead of silently vanishing from every count.
- Only junctions and directory symlinks (name-surrogate reparse points) are skipped. A bare ReparsePoint attribute, which OneDrive Files On-Demand puts on ordinary synced folders, no longer hides a folder's contents.
- The Python audit no longer crashes with `UnicodeEncodeError` on non-ASCII filenames when output is redirected on Windows.
- `verify_move.py`: accepts Excel "CSV UTF-8" maps with a byte-order mark; resolves relative map paths against the map file; detects case-only target collisions; and fails final verify while a source still exists (a copy is not a move). The new `--allow-source-present` flag is for approved copies.
- `audit_folder.ps1` walks the tree explicitly: it is linear instead of quadratic (40,000 files in about 8 s instead of 64 s), does not follow junctions under Windows PowerShell 5.1, resolves UNC/NAS roots via `ProviderPath`, reads indexes as UTF-8 on 5.1, and no longer crashes when an index path is a directory.
- Index link checks now understand `<angle targets>`, `"titles"`, `%20` escapes and any URI scheme, and ignore version strings such as `v1.1.0` in backticks.
- Python/PowerShell output parity: case-insensitive duplicate names, lower-case extensions, same path-length scope and cap, root-level-only instruction conflict warning, deterministic ordering. A new test compares the two full reports line by line.
- More credential-name hints: `*.pem`, `*.key`, `*.pfx`, `*.p12`, `*.kdbx`, `*.ppk`, `*.jks`, `id_ed25519`, `id_ecdsa`, `.netrc`, `.git-credentials`.
- Documentation: removed dead `SKILL.md §3/§4` references; preflight now runs before baseline everywhere; staging is recommended outside synced roots; the Claude.ai upload instructions no longer contradict the package layout; checksum steps include Windows `Get-FileHash`.
- Release and CI: new `-skill.zip` asset (the skill folder only) for Claude.ai and other skill uploaders; a Windows CI job runs the full suite with PowerShell 7 plus a Windows PowerShell 5.1 junction smoke test; actions are pinned by commit SHA; the dispatch version input is passed through the environment and validated as semver.
- `claude plugin validate` was run against `plugin.json` and `marketplace.json` on 2026-09-23 and passed, resolving the v1.1.0 "not verified" note.

## Validation

The release validation matrix covers:

- OpenAI skill and plugin validators;
- Python compilation and PowerShell parsing;
- Python/PowerShell observable parity;
- package/version/link checks;
- portfolio, entrypoint, journal, pointer, credential-name, ZIP and partial six-file upload fixtures;
- move-verification failure and success behavior;
- package build, extraction and runtime smoke tests;
- a line-by-line comparison of the full Python and PowerShell reports;
- a Windows job (PowerShell 7 and Windows PowerShell 5.1) covering junctions and Windows-only code paths.

Not claimed: live OneDrive Files On-Demand behaviour, which CI cannot reproduce. The reparse fix follows Windows' documented name-surrogate tag bit and is exercised against real junctions in CI.

## Compatibility

- Python 3.8+; standard library for bundled runtime scripts.
- PowerShell 5.1 or 7+ for the Windows/OneDrive audit helper.
- Existing v1.1.0 flags and move-map formats remain supported, with three deliberate behavior changes: final `verify` fails while a source still exists (use `--allow-source-present` for an approved copy), relative map paths resolve against the map file, and exclusion globs are segment-aware and case-insensitive.
- One canonical skill body is reused across host packages; host-specific differences are metadata and installation layout only.
