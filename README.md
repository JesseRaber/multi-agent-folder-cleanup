# Multi-Agent Folder Cleanup

Canonical source for the `multi-agent-folder-cleanup` Agent Skill and its OpenAI and Claude plugin packages.

The goal is a shared project folder where an agent arriving cold can quickly tell what is true now, what is proposed, and what is historical without choosing between plausible copies.

Wiki: https://github.com/JesseRaber/multi-agent-folder-cleanup/wiki

## Version

`1.3.0` — see `CHANGELOG.md`.

Report as: **Loaded Multi-Agent Folder Cleanup v1.3.0**.

## Install

Prebuilt packages are attached to each [release](https://github.com/JesseRaber/multi-agent-folder-cleanup/releases):

- `…-openai.zip` — native skills-only plugin for ChatGPT and Codex, with `.codex-plugin/plugin.json`
- `…-portable.zip` — standalone Agent Skill (with INSTALL.md and LICENSE) for ChatGPT desktop, Codex CLI/IDE, Grok, and compatible local hosts
- `…-claude.zip` — Claude Code / Claude Desktop plugin layout
- `…-skill.zip` — the skill folder only, for Claude.ai skill upload and other skill uploaders

Every archive except `-skill.zip` includes its own `INSTALL.md`. Keep the extracted package structure intact.

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
  references/connector-audit.md   connector evidence and safe cloud-edit boundaries
  references/portfolio-audit-template.md  multi-project audit matrix
  references/navigation-templates.md
  references/project-rules/       optional separately adopted rules template
packaging/                       per-host install docs and release notes
tests/                           package, regression, and Python/PowerShell parity tests
.github/workflows/ci.yml         pull-request and main validation
.github/workflows/release.yml    tagged package build and publication
```

The skill folder contains the maintained workflow. Plugin manifests and release files package it without duplicating instructions. It does not override host instructions or adopted project policies; the bundled rules proposal requires separate adoption.

## What v1.3.0 adds

- Generated move reviews with map/resolved-path digests, approval-receipt guards and baseline source checks before execution.
- Complete upfront navigation, staging and removal scope; separated unresolved owner choices.
- Recovery that preserves newer contributions rather than automatically restoring staged copies.
- Evidenced instruction adoption and actual per-project continuity requirements.
- An optional [Project Rules 3.0.0 package](skills/multi-agent-folder-cleanup/references/project-rules/ADOPTION.md), included in every install archive. Skill use does not adopt it.

These address preventable failure modes observed in one model/project and inspected workflow wording. They are not proof of model-wide failure or universal safe execution.

## Retained v1.2.0 capabilities

- Portfolio-root audits with count-scope and entrypoint matrices.
- Strict full-path validation for connector and enterprise-search results.
- Documentary-state versus operationally verified state.
- Pointer, identical-duplicate, divergent-control, and claim-family distinctions.
- Separate move, record-only, and additive-intake execution boundaries.
- Connector-safe exact-context edits with virtualized-editor and concurrent-writer guards.
- Privacy-minimized incoming packages and post-upload manifest verification.
- New audit-helper options for journal thresholds, expected entrypoints, portfolio matrices, pointer candidates, and expected upload manifests.


## What the scripts do

All three scripts are read-only against the target folder. `verify_move.py` never moves files.

```bash
python skills/multi-agent-folder-cleanup/scripts/audit_folder.py \
  --root <folder> --index-path INDEX.md --hash-files

# Optional advisory checks
python skills/multi-agent-folder-cleanup/scripts/audit_folder.py \
  --root <portfolio> --portfolio \
  --entrypoint AGENTS.md --entrypoint AI_CONTEXT/README_FIRST.md \
  --journal-threshold-kb 100 --detect-pointers \
  --expected-upload-manifest expected-files.csv

python skills/multi-agent-folder-cleanup/scripts/verify_move.py review \
  --map moves.csv --approval-out proposal.json > review.md
# After owner approval of that exact review and the complete non-move package:
python skills/multi-agent-folder-cleanup/scripts/verify_move.py preflight \
  --map moves.csv --approval proposal.json --path-threshold 240
python skills/multi-agent-folder-cleanup/scripts/verify_move.py baseline \
  --map moves.csv --approval proposal.json --out /safe/audit/baseline.json
# Recheck with preflight --approval proposal.json --baseline /safe/audit/baseline.json before moving.
python skills/multi-agent-folder-cleanup/scripts/verify_move.py verify \
  --baseline /safe/audit/baseline.json
```

Python 3.8+, standard library only. On Windows or OneDrive, prefer `audit_folder.ps1` (PowerShell 5.1 or 7+) because it can inspect placeholder attributes. On other platforms, record hydration as unverified until checked on Windows.

## Validation and releases

Every pull request runs the pinned OpenAI skill and plugin validators, package/version checks, Python compilation, PowerShell parsing, all regression tests, and a line-by-line Python/PowerShell report comparison on Ubuntu, plus the full suite on Windows (PowerShell 7 and a Windows PowerShell 5.1 junction smoke test). Tagged releases repeat runtime smoke tests, build all four install archives, extract them, run the packaged code, and publish SHA-256 checksums.

To publish after the release commit is merged:

```bash
git tag -a vX.Y.Z -m "Multi-Agent Folder Cleanup vX.Y.Z"
git push origin vX.Y.Z
```

The tag must match the versions in `SKILL.md`, `.codex-plugin/plugin.json`, and `.claude-plugin/plugin.json`. Use **Actions → Release → Run workflow** to build artifacts without publishing.

## Authority rule

If two copies disagree, this repository is current. A release archive, chat upload, or host-local cache is not.
