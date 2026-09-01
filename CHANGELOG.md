# Changelog

## Unreleased

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
