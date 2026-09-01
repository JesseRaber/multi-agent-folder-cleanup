# Multi-Agent Folder Cleanup

Canonical source for the `multi-agent-folder-cleanup` Agent Skill and its OpenAI and Claude plugin packages.

The goal is a shared project folder where an agent arriving cold can quickly tell what is true now, what is proposed, and what is historical without choosing between plausible copies.

Wiki: https://github.com/JesseRaber/multi-agent-folder-cleanup/wiki

## Version

`1.1.0` — see `CHANGELOG.md`.

Report as: **Loaded Multi-Agent Folder Cleanup v1.1.0**.

## Install

Prebuilt packages are attached to each [release](https://github.com/JesseRaber/multi-agent-folder-cleanup/releases):

- `…-openai.zip` — native skills-only plugin for ChatGPT and Codex, with `.codex-plugin/plugin.json`
- `…-portable.zip` — standalone Agent Skill for ChatGPT desktop, Codex CLI/IDE, Claude.ai skill upload, Grok, and compatible local hosts
- `…-claude.zip` — Claude Code / Claude Desktop plugin layout

Each archive includes its own `INSTALL.md`. Keep the extracted package structure intact.

### ChatGPT and Codex

OpenAI distinguishes authoring from distribution: a standalone skill is useful for personal workflows in ChatGPT desktop and Codex, while a plugin is the installable package used to distribute skills across supported ChatGPT and Codex surfaces.

For local development, extract the `-openai.zip`, add its outer folder to a local marketplace, install it, refresh the app, and test it in a new conversation. Publication to the universal plugin directory is a separate OpenAI review step and is not claimed by this repository.

For a personal installation in ChatGPT desktop, Codex CLI, or the IDE extension, install the inner `skills/multi-agent-folder-cleanup/` directory as a standalone skill. Its optional OpenAI display metadata lives in `agents/openai.yaml`.

### Claude Code / Claude Desktop

This repository is also its own Claude marketplace catalog:

```text
/plugin marketplace add JesseRaber/multi-agent-folder-cleanup
/plugin install multi-agent-folder-cleanup@jesseraber-plugins
```

`jesseraber-plugins` is the marketplace name from `.claude-plugin/marketplace.json`.

### Other hosts

Copy or upload only `skills/multi-agent-folder-cleanup/`, preserving its `SKILL.md`, `agents/`, `scripts/`, and `references/` directories. Do not install from a mixed archive containing nested packages or loose duplicate scripts.

## Repository layout

```text
.codex-plugin/plugin.json        OpenAI plugin manifest
.claude-plugin/                  Claude plugin manifest and marketplace catalog
skills/multi-agent-folder-cleanup/
  SKILL.md                       concise routing and safety contract
  agents/openai.yaml             OpenAI discovery and starter-prompt metadata
  scripts/                       read-only audit and move-verification helpers
  references/workflow.md         full Audit / Plan / Execute protocol
  references/audit-tools.md      deterministic helper usage and limitations
  references/navigation-templates.md
packaging/                       per-host install docs and release notes
tests/                           package and Python/PowerShell parity checks
.github/workflows/ci.yml         pull-request and main validation
.github/workflows/release.yml    tagged package build and publication
```

The skill folder is the workflow authority. Plugin manifests and release files package it without duplicating the instructions.

## What the scripts do

All three scripts are read-only against the target folder. `verify_move.py` never moves files.

```bash
python skills/multi-agent-folder-cleanup/scripts/audit_folder.py \
  --root <folder> --index-path INDEX.md --hash-files

python skills/multi-agent-folder-cleanup/scripts/verify_move.py baseline \
  --map moves.csv --out /safe/audit/baseline.json
python skills/multi-agent-folder-cleanup/scripts/verify_move.py preflight \
  --map moves.csv --path-threshold 240
python skills/multi-agent-folder-cleanup/scripts/verify_move.py verify \
  --baseline /safe/audit/baseline.json
```

Python 3.8+, standard library only. On Windows or OneDrive, prefer `audit_folder.ps1` (PowerShell 5.1 or 7+) because it can inspect placeholder attributes. On other platforms, record hydration as unverified until checked on Windows.

## Validation and releases

Every pull request runs the pinned OpenAI skill validator, package/version checks, Python compilation, PowerShell parsing, and a cross-language parity fixture. Tagged releases repeat runtime smoke tests, build all three install archives, extract them, run the packaged code, and publish SHA-256 checksums.

To publish after the release commit is merged:

```bash
git tag -a vX.Y.Z -m "Multi-Agent Folder Cleanup vX.Y.Z"
git push origin vX.Y.Z
```

The tag must match the versions in `SKILL.md`, `.codex-plugin/plugin.json`, and `.claude-plugin/plugin.json`. Use **Actions → Release → Run workflow** to build artifacts without publishing.

## Authority rule

If two copies disagree, this repository is current. A release archive, chat upload, or host-local cache is not.
