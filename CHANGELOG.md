# Changelog

## Unreleased

- Nothing yet.

## 1.2.0 - 2026-09-23

- Added portfolio-root auditing, strict retrieved-path validation, count-scope labels, documentary-versus-operational state, and intentional-pointer versus divergent-control classification.
- Added connector-safe record-only and additive-intake protocols, including complete-document guards, virtualized-editor prohibitions, concurrent-writer checks, partial-upload recovery, privacy minimization, and reopen-after-save verification.
- Added `references/connector-audit.md` and `references/portfolio-audit-template.md`.
- Added five explicit lookup outcomes: exact match, likely same family, no result returned, verified absent, and inaccessible.
- Added journal-size threshold reporting, repeatable expected-entrypoint checks, advisory portfolio matrices, conservative pointer-stub candidates, and expected-upload manifest verification to both audit helpers.
- Expanded Python/PowerShell parity and regression tests, including a partial six-file upload fixture and move-verification failure/success checks.
- Updated OpenAI, Claude, marketplace, portable, install, README, release-note, and version metadata for one shared canonical skill body.
- Preserved the v1.1 move protocol, reparse-point handling, case-mismatched reference checks, credential-name warnings, ZIP no-extract inspection, and package/release safeguards.
- Included the post-v1.1 release-workflow and installation corrections that had remained under `Unreleased`.

### Fixed (from the 2026-09-23 deep scan of v1.1.0)

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

### Behavior changes to review when upgrading

- `verify_move.py verify` (without `--stage`) now exits nonzero while any source file still exists. Pass `--allow-source-present` for an approved copy.
- Relative paths in a move map resolve against the map file's folder instead of the current directory.
- `--exclude` / `-Exclude` matching is case-insensitive, and `*` no longer crosses `/`. A pattern with no `/` (for example `*.log`) still matches at any depth.

## 1.1.0 - 2026-09-01

- Added a native OpenAI skills-only plugin manifest at
  `.codex-plugin/plugin.json` and skill presentation metadata at
  `skills/multi-agent-folder-cleanup/agents/openai.yaml`.
- Refactored the 30 KB `SKILL.md` into a concise routing and safety contract;
  detailed helper usage now lives in `references/audit-tools.md`, while the
  complete operational protocol remains in `references/workflow.md`.
- Fixed Python/PowerShell parity for versioned claim filenames, claim byte-size
  reporting, and dotfile extension classification.
- Added pull-request CI with OpenAI's pinned validators, package consistency
  checks, PowerShell parsing, and a shared-fixture cross-language parity test.
- Added a separate `-openai.zip` release package, OpenAI install guide, and
  v1.1.0 release notes. Synchronized both plugin manifests and skill metadata.

- Added `.claude-plugin/marketplace.json`. `/plugin marketplace add` reads a
  marketplace catalog from that path; `plugin.json` alone is a plugin manifest
  and is not a catalog, so the GitHub install command shipped in the v1.0.0
  `-claude.zip` could not have worked. The repository is now both the catalog
  and the plugin it lists (`"source": "./"`).
- Corrected `packaging/INSTALL-claude.md`, which told users to run
  `/plugin marketplace add` against a repository with no catalog, and omitted
  the required `/plugin install <plugin>@<marketplace>` second step.
- Corrected the "Verified in this release" section of
  `packaging/RELEASE_NOTES_v1.0.0.md`. It claimed a verification of
  `audit_folder.ps1` that had not actually been performed.

Not verified: `claude plugin validate` has not been run against the new
marketplace catalog. The file was checked against the documented schema by hand.

## 1.0.0 - 2026-08-31

First GitHub-canonical release. Assembled from the two local packages rather than invented.

Included from the nested Claude package, unchanged except where noted below:

- `SKILL.md` protocol (connector audit, record-only Execute, dual-root / reparse notes)
- `references/workflow.md` (includes Access and Other roots report sections)
- `scripts/audit_folder.py` (Windows reparse helper, case-exact reference checks)
- `scripts/audit_folder.ps1` - **modified before the tag was cut, see below**
- `scripts/verify_move.py`
- `references/navigation-templates.md`

Fixed before the tag was cut:

- `scripts/audit_folder.ps1`: `Test-CaseExact` called
  `Split-Path -LiteralPath $cur -Parent`. `-LiteralPath` and `-Parent` belong to
  different parameter sets, so that call threw
  "Parameter set cannot be resolved" on every platform, Windows included. The
  function only runs once an index reference resolves, so the script worked on a
  folder with broken links and aborted as soon as one was good - which is why it
  went unnoticed. The case-mismatch check had therefore never worked in the
  PowerShell script. Replaced with `[System.IO.Path]::GetDirectoryName` and
  `GetFileName`, which keep the literal, non-globbing semantics `-LiteralPath`
  was there for. `audit_folder.py` implements the same check correctly and was
  never affected.

Repo-only edits in this tag:

- Added Grok to the skill description agent list
- Added `license` and `metadata.version` / `metadata.repository` (Agent Skills spec)
- Added README, LICENSE, this changelog, `.gitignore`
- Added `.claude-plugin/plugin.json` with version, author, homepage, repository,
  license and keywords. Removed `adapters/claude/plugin.json`: plugin loaders read
  `.claude-plugin/plugin.json`, so the `adapters/` copy was inert, and two
  manifests with different contents were an ambiguity this skill exists to prevent
- Added `packaging/` (install docs and release notes consumed by the build) and
  `.github/workflows/release.yml`, which validates, smoke-tests, builds and
  publishes both ZIPs on a `v*` tag

Not claimed in this tag (present in some local copies, not shipped here):

- Grok-sandbox-only section 0 rewrite from the installed Grok skill (180-line SKILL.md)
- Older v2 `workflow.md` / audit scripts (smaller, no Access/Other-roots / reparse helpers)
