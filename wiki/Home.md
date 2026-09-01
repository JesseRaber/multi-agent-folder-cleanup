# Multi-Agent Folder Cleanup

Canonical skill: [`skills/multi-agent-folder-cleanup/`](https://github.com/JesseRaber/multi-agent-folder-cleanup/tree/main/skills/multi-agent-folder-cleanup)

Version **1.0.0**. Report as: Loaded Multi-Agent Folder Cleanup v1.0.0.

Goal: any agent opening a shared folder cold can answer, in under a minute, what is true now, what is proposed, and what is dead — without picking between two copies of the same document.

This repository is the authority. A downloaded ZIP, a chat upload, or a host-local cache is not.

## Install

Upload or point the host at `skills/multi-agent-folder-cleanup/` (`SKILL.md` + `scripts/` + `references/`).

- **Claude:** that folder, plus `adapters/claude/plugin.json` if the host wants a plugin wrapper.
- **ChatGPT / Codex / other Agent Skills hosts:** skill folder only. Do not include `adapters/` or `.claude-plugin/`.
- **Grok / local models:** point at `skills/multi-agent-folder-cleanup/`.

Do not install from a mixed ZIP that also contains a nested ZIP or loose root copies of the scripts.

## Modes

State the mode in line one. Ambiguous request → Audit.

| Mode | Trigger | Allowed |
|---|---|---|
| Audit | what's in here, why agents get confused, status | Read-only report. No moves. |
| Plan | how should this be organized | Proposed tree + literal source→target map, labeled PROPOSED. |
| Execute | explicit approval of a specific map | Only the approved moves or record corrections. |

Deletion is never in scope by default. Execute moves; it does not delete documents.

## Scripts

All three are read-only against the target. `verify_move.py` never moves files.

```bash
python skills/multi-agent-folder-cleanup/scripts/audit_folder.py \
  --root <folder> --index-path INDEX.md --hash-files

python skills/multi-agent-folder-cleanup/scripts/verify_move.py preflight --map moves.csv --path-threshold 240
python skills/multi-agent-folder-cleanup/scripts/verify_move.py baseline --map moves.csv --out /tmp/baseline.json
python skills/multi-agent-folder-cleanup/scripts/verify_move.py verify --baseline /tmp/baseline.json
```

Windows / OneDrive: prefer `audit_folder.ps1`. POSIX or a remote sandbox: `audit_folder.py`, and record hydration as unverified unless checked on Windows.

Connector-only access is an audit of structure and claims, not an Execute path. Hashing and `verify_move.py` need a mounted filesystem.

## Layout

```
skills/multi-agent-folder-cleanup/
  SKILL.md
  scripts/audit_folder.py
  scripts/audit_folder.ps1
  scripts/verify_move.py
  references/workflow.md
  references/navigation-templates.md
adapters/claude/plugin.json
```

Full protocol: [references/workflow.md](../skills/multi-agent-folder-cleanup/references/workflow.md)
