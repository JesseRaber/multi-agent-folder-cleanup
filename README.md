# Multi-Agent Folder Cleanup

Canonical source for the `multi-agent-folder-cleanup` Agent Skill.

Goal: a shared project folder where any agent opening it cold can answer, in under a minute, what is true now, what is proposed, and what is dead — without picking between two copies of the same document.

## Layout

```
skills/multi-agent-folder-cleanup/
  SKILL.md                       canonical skill
  scripts/
    audit_folder.py              cross-platform read-only inventory
    audit_folder.ps1             Windows / OneDrive inventory
    verify_move.py               hash baseline / preflight / verify (never moves)
  references/
    workflow.md                  full Audit / Plan / Execute protocol
    navigation-templates.md      entrypoint / index templates
adapters/claude/plugin.json      Claude plugin wrapper only
```

The skill folder is the authority. Platform packaging lives under `adapters/`.

## Version

`1.0.0` — see `CHANGELOG.md`.

Report as: **Loaded Multi-Agent Folder Cleanup v1.0.0**.

## Install

Copy or upload `skills/multi-agent-folder-cleanup/` (the folder that contains `SKILL.md`, `scripts/`, and `references/`).

- **Claude:** use that folder, plus `adapters/claude/plugin.json` if the host wants a plugin wrapper.
- **ChatGPT / Codex / other Agent Skills hosts:** upload the skill folder only. Do not include `.claude-plugin/` or `adapters/`.
- **Grok / local models:** point the host at `skills/multi-agent-folder-cleanup/`.

Do not install from a mixed ZIP that also contains a nested ZIP or loose root copies of the scripts.

## What the scripts do

All three scripts are read-only against the target folder. `verify_move.py` never moves files.

```bash
python skills/multi-agent-folder-cleanup/scripts/audit_folder.py \
  --root <folder> --index-path INDEX.md --hash-files

python skills/multi-agent-folder-cleanup/scripts/verify_move.py baseline \
  --map moves.csv --out /tmp/baseline.json
python skills/multi-agent-folder-cleanup/scripts/verify_move.py preflight \
  --map moves.csv --path-threshold 240
python skills/multi-agent-folder-cleanup/scripts/verify_move.py verify \
  --baseline /tmp/baseline.json
```

On Windows / OneDrive, prefer `audit_folder.ps1`. On POSIX, including remote agent sandboxes, use `audit_folder.py` and record OneDrive hydration as unverified unless checked on Windows.

## Authority rule

If two copies of this skill disagree, this repository is current. A downloaded ZIP, a chat upload, or a host-local skill cache is not.
