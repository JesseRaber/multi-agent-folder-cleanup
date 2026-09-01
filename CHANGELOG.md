# Changelog

## 1.0.0 — 2026-08-31

First GitHub-canonical release. Assembled from the two local packages rather than invented.

Included as-is from the nested Claude package (content hashes recorded at commit):

- `SKILL.md` protocol (connector audit, record-only Execute, dual-root / reparse notes)
- `references/workflow.md` (includes Access and Other roots report sections)
- `scripts/audit_folder.py` (Windows reparse helper, case-exact reference checks)
- `scripts/audit_folder.ps1`
- `scripts/verify_move.py`
- `references/navigation-templates.md`

Repo-only edits in this tag:

- Added Grok to the skill description agent list
- Added `license` and `metadata.version` / `metadata.repository` (Agent Skills spec)
- Added README, LICENSE, this changelog, `.gitignore`
- Moved Claude `plugin.json` to `adapters/claude/` and restored the truncated description

Not claimed in this tag (present in some local copies, not shipped here):

- Grok-sandbox-only §0 rewrite from the installed Grok skill (180-line SKILL.md)
- Older v2 `workflow.md` / audit scripts (smaller, no Access/Other-roots / reparse helpers)
