# Multi-Agent Folder Cleanup v1.0.0

An Agent Skill for auditing, planning, and safely reorganizing a shared project
folder so that any AI agent opening it cold can tell what is true now, what is
proposed, and what is dead - without picking between two copies of the same
document.

Works with Claude, ChatGPT, Grok, Copilot, Codex, Manus, and local models.

## Downloads

| File | For | Contains |
|---|---|---|
| `multi-agent-folder-cleanup-1.0.0-claude.zip` | Claude Code / Claude Desktop plugin, or Claude.ai skill upload | Plugin layout with `.claude-plugin/plugin.json` + the skill under `skills/` |
| `multi-agent-folder-cleanup-1.0.0-portable.zip` | ChatGPT, Grok, Codex, local models, Claude.ai skill upload | The bare skill folder + `INSTALL.md` |
| `SHA256SUMS.txt` | Everyone | Checksums for both ZIPs |

Each ZIP has its own `INSTALL.md` with per-host steps.

## What's in it

- `SKILL.md` - the protocol: Audit / Plan / Execute modes, eight-bucket
  classification, the safety rules that stop a half-finished move
- `references/workflow.md` - full staged-move protocol (D0-D7), record-only
  Execute (D8), report formats, failure recovery
- `references/navigation-templates.md` - README / STATUS / AUTHORITY / INDEX /
  HANDOFF templates
- `scripts/audit_folder.py` - cross-platform read-only inventory
- `scripts/audit_folder.ps1` - Windows/OneDrive inventory, incl. the cloud
  placeholder check Python cannot do
- `scripts/verify_move.py` - hash baseline / preflight / verify; never moves
  anything

## Design commitments

- Every script is **read-only** against the target folder.
- Deletion is never in scope by default.
- Execution requires an explicitly approved literal move map - no globs, no
  "and the rest of that folder".
- `verify` exits nonzero on any mismatch, and a nonzero exit is a stop
  condition, not a warning.

## Requirements

- Python 3.8+, standard library only. No dependencies.
- PowerShell 5.1 or 7+ for the `.ps1` script (Windows only; optional elsewhere).

## Verified in this release

Both audit scripts were run against the same test tree and produce matching
findings. `verify_move.py` was exercised across all three subcommands.
`audit_folder.ps1` parses clean under PowerShell 7.4. All documented edge-case
behaviors (comma-argument rejection, missing-index reporting, exclusion coverage
accounting) were confirmed to behave as written.

## Authority

If a downloaded copy disagrees with this repository, the repository is current.
A ZIP, a chat upload, or a host-local skill cache is not.

MIT licensed.
