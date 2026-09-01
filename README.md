# Multi-Agent Folder Cleanup

Canonical source for the `multi-agent-folder-cleanup` Agent Skill.

Goal: a shared project folder where any agent opening it cold can answer, in under a minute, what is true now, what is proposed, and what is dead — without picking between two copies of the same document.

Wiki: https://github.com/JesseRaber/multi-agent-folder-cleanup/wiki

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
.claude-plugin/
  plugin.json                    Claude plugin manifest
  marketplace.json               marketplace catalog listing this repo as its own plugin
packaging/
  INSTALL-portable.md            install doc packaged with the portable ZIP
  INSTALL-claude.md              install doc packaged with the Claude ZIP
  RELEASE_NOTES_v*.md            release notes, one per version
.github/workflows/release.yml    builds and publishes both ZIPs on a v* tag
```

The skill folder is the authority. Everything else is packaging. Project wiki lives on the GitHub Wiki tab, not in this tree.

## Version

`1.0.0` — see `CHANGELOG.md`.

Report as: **Loaded Multi-Agent Folder Cleanup v1.0.0**.

## Install

Prebuilt packages are attached to each [release](https://github.com/JesseRaber/multi-agent-folder-cleanup/releases), and each one carries its own `INSTALL.md`:

- `…-claude.zip` — Claude Code / Claude Desktop plugin layout, or Claude.ai skill upload
- `…-portable.zip` — ChatGPT, Grok, Codex, and local models

### Claude Code / Claude Desktop

This repository is also its own marketplace catalog. Both commands are needed — the first registers the catalog, the second installs the plugin listed in it:

```
/plugin marketplace add JesseRaber/multi-agent-folder-cleanup
/plugin install multi-agent-folder-cleanup@jesseraber-plugins
```

`jesseraber-plugins` is the marketplace name from `marketplace.json`, not the repo name.

Not yet verified end to end: these commands match the documented schema and the repository layout satisfies it, but no one has run them against a live Claude Code install. Report anything that fails.

### Other hosts

Copy or upload `skills/multi-agent-folder-cleanup/` (the folder that contains `SKILL.md`, `scripts/`, and `references/`).

- **ChatGPT / Codex / other Agent Skills hosts:** upload the skill folder only. Do not include `.claude-plugin/`, `packaging/`, or `.github/`.
- **Grok / local models:** point the host at `skills/multi-agent-folder-cleanup/`.
- **Claude.ai:** zip that folder on its own and upload it under Settings → Capabilities → Skills.

Do not install from a mixed ZIP that also contains a nested ZIP or loose root copies of the scripts.

## Releases

Releases are built in CI, not by hand. Push a version tag and the workflow validates the skill, smoke-tests both audit scripts and `verify_move.py`, builds both ZIPs with a `SHA256SUMS.txt`, extracts and re-runs them, then publishes:

```bash
git tag -a vX.Y.Z -m "Multi-Agent Folder Cleanup vX.Y.Z"
git push origin vX.Y.Z
```

Do not create the release in the GitHub UI. That creates the tag and the release together and the publish step fails.

The tag must match `metadata.version` in `SKILL.md` or the build stops. Use **Actions → Release → Run workflow** to build artifacts without publishing.

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

Python 3.8+, standard library only. On Windows / OneDrive, prefer `audit_folder.ps1` (PowerShell 5.1 or 7+). On POSIX, including remote agent sandboxes, use `audit_folder.py` and record OneDrive hydration as unverified unless checked on Windows.

## Authority rule

If two copies of this skill disagree, this repository is current. A downloaded ZIP, a chat upload, or a host-local skill cache is not.
