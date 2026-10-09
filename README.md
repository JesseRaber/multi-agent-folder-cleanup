# Multi-Agent Folder Cleanup

Agent skill for a shared project folder used by more than one AI model. It keeps Claude, ChatGPT, Codex, Microsoft Copilot, Gemini, Grok, Opal, and local models from treating a stale copy, an incoming draft, or a second roadmap as current.

Canonical source for the skill and its OpenAI and Claude plugin packages. This branch holds **v1.7.0**; published releases are listed on GitHub.

An agent opening the folder cold should be able to tell what is true now, what is proposed, what is incoming, and what is historical without choosing between plausible copies.

Documentation: [wiki](https://github.com/JesseRaber/multi-agent-folder-cleanup/wiki) · [install](https://github.com/JesseRaber/multi-agent-folder-cleanup/wiki/Install) · [modes](https://github.com/JesseRaber/multi-agent-folder-cleanup/wiki/Modes) · [scripts](https://github.com/JesseRaber/multi-agent-folder-cleanup/wiki/Scripts) · [FAQ](https://github.com/JesseRaber/multi-agent-folder-cleanup/wiki/FAQ) · [changelog](CHANGELOG.md)

## Version

`1.7.0`; see `CHANGELOG.md`.

Report as: **Loaded Multi-Agent Folder Cleanup v1.7.0 (SKILL.md at <path>; helpers <version>)**.

## Install

Prebuilt packages are attached to each [release](https://github.com/JesseRaber/multi-agent-folder-cleanup/releases). **Which ZIP do I use?**

| Your AI app | Download |
|---|---|
| **Almost everything**: Claude app skill upload, ChatGPT/Codex standalone skills, local models, any skills folder | `…-UNIVERSAL-skill.zip` |
| Claude Code `/plugin install` (not the Claude app uploader) | `…-claude-code-plugin.zip` |
| Codex / ChatGPT plugin marketplace | `…-codex-chatgpt-plugin.zip` |
| Microsoft Copilot agent skill upload, **Grok** | `…-microsoft-copilot-agent-only.zip` |
| Gemini Apps skill upload | `…-gemini-apps-only.zip` |
| Opal skill import | `…-opal-only.zip` |
| Optional Project Rules template only | `…-project-rules-optional.zip` |

Coding agents that install from GitHub (Antigravity, Claude Code, Codex CLI) can use the repository directly.

Host-specific packages leave out what that host rejects:

- `-microsoft-copilot-agent-only`: no `.ps1`; Microsoft Copilot's custom-skill sandbox supports Python and selected web/POSIX script types but rejects PowerShell skill scripts. Grok also needs this package: it rejected the Universal ZIP for `.ps1` (owner upload test, 2026-10-05).
- `-gemini-apps-only`: no `audit_folder.py`, `audit_folder.ps1`, `agents/openai.yaml` or project rules. Google's upload security scan rejects the audit script's credential-guard code; the package omits it rather than disguising it.
- `-opal-only`: `SKILL.md` (name and description only in the header) plus `references/*.md`. Opal imports Markdown only, so no scripts.

The universal and plugin packages include an `INSTALL.md`. Keep the extracted structure intact. Releases before v1.5.0 used older names (`-skill`, `-portable`, `-claude`, `-openai`, `-gemini-apps`, `-project-rules`).

### ChatGPT and Codex

OpenAI distinguishes authoring from distribution: a standalone skill is useful for personal workflows in ChatGPT desktop and Codex, while a plugin is the installable package used to distribute skills across supported ChatGPT and Codex surfaces.

For local development, extract the `-codex-chatgpt-plugin.zip`, add its outer folder to a local marketplace, install it, refresh the app, and test it in a new conversation. Publication to the universal plugin directory is a separate OpenAI review step and is not claimed by this repository.

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
  scripts/                       read-only audit, move- and record-verification helpers
  references/preconditions.md    every-mode preconditions (read first)
  references/audit-mode.md       Audit protocol and report format
  references/plan-mode.md        Plan protocol and approval package
  references/execute-moves.md    staged move protocol, verification, recovery
  references/execute-records.md  record-only, connector and additive execution
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

## Release safety and host routing

- Grok now points to the `-microsoft-copilot-agent-only` package in the README and install guide (Grok rejects `.ps1`).
- Releases are created as **drafts**; the workflow refuses to touch an existing release and never replaces published assets. Assets are verified against a local candidate before publishing.
- `packaging/check_versions.py` and `packaging/verify_release.py` (from the github-release skill) gate versions and verify published assets; `HOST_INSTALL_LOG.md` records per-host installs.
- The packager pins ZIP metadata so Windows and Linux builds give identical archives; `.gitattributes` keeps text LF.

## What v1.6.1 adds

- `scripts/verify_records.py`: a read-only checker for shared records (UTF-8, BOM, line endings, mojibake, dead relative links, broken Markdown tables, `--compare` and `--expect-sha256`). Work mode asks agents to cite its output before calling a shared-record edit verified.

## What v1.5.3 fixes

- Move-verification recipes consistently pass `--root`; unguarded calls remain compatible but emit a clear confinement warning.
- ZIP member safety, credential-guard hash reporting, session-header parsing and distinct-writer counting now agree across Python and PowerShell.
- Work/Plan command fallbacks, audit and record-edit routing, optional-rules package wording, and canonical-tracker guidance are corrected.

## What v1.5.2 fixes

- `verify_move.py --root <project>` refuses any source or target outside the project, and any baseline written inside it.
- Case-only renames (`readme.md` to `README.md`) are no longer blocked as TARGET EXISTS; maps spanning top-level folders no longer refuse every baseline location; macOS paths compare case-insensitively; Windows probes handle long paths.
- Helper examples now cover `-ExecutionPolicy Bypass`, `powershell.exe` without PowerShell 7, and `python3` on Linux/macOS. The legacy `references/workflow.md` router is removed (SKILL.md already routes by mode). Guidance for host packages that omit a helper or the project-rules folder.

## What v1.5.1 adds

- Stops root-dependent work when connector discovery returns ambiguous same-name project roots and preserves every path/site and stable identifier in the checkpoint.
- Forbids canonical-root selection from filename, modified time, search rank, size or matching hashes; authority/navigation evidence is required.
- Adds a claim-state table to audits, a bounded pre-write duplicate lookup, and one canonical roadmap/task tracker for shared projects.

## What v1.5.0 adds

- **Work mode** for agents doing ordinary work in a shared folder: where to save, how to name, one authoritative roadmap/task tracker, a short header for new documents, safe edits to shared records, what to index, and an end-of-request handoff checklist (`references/work-mode.md`).
- **`--orient` and `--session-index`** in both audit helpers: read-only arrival checks (possibly active writers, files changed since the latest session, changed files the index never names) and a session-index gap check with proposed rows.
- **Smaller always-loaded file**: SKILL.md is now a 7 KB router; cleanup-only guidance moved to `references/cleanup-principles.md`. A Work-mode run reads about 13 KB.
- Optional Project Rules 3.1.0 adds a short pointer to Work mode (3.2.0 in v1.6.0 narrows the section 9 secret definition).

## What v1.4.1 fixes

Blocks credential-hinted, linked and cloud-only content reads; fixes balanced-parenthesis Markdown links and root-fallback reporting; caps previously uncapped brief lists; rejects linked move paths and baselining placeholders; adds a Windows point-in-time exclusive-read probe. CLI defaults and receipt schema are unchanged. Link checks stop at the audited root, so projects under a linked parent folder still work. See the release notes for verification limits.

## What v1.4.0 adds

Measured on a real 18-project shared portfolio, v1.4.0 cuts what agents must read and catches multi-agent problems the earlier helpers missed:

- **Mode-split protocol.** An Audit run reads `preconditions.md` and `audit-mode.md` (about 15 KB) instead of the whole 35 KB workflow.
- **Smaller reports.** `--brief`, `--out FILE` (full report to a file, summary to the agent) and a closing **Findings at a glance** block.
- **Startup read budget.** Totals the root instruction files plus the declared read order and flags an `AGENTS.md` over 32 KiB, which Codex silently truncates.
- **Index coverage.** `--index-coverage INDEX=DIR` lists files an index never mentions, such as session logs missing from a session index.
- **Live-loading names in the wrong place.** Flags `AGENTS.md`/`CLAUDE.md`/`GEMINI.md` inside incoming, history, scratch or skill-copy folders.
- **Embedded skill copies and version self-check.** Lists every `SKILL.md`/`.skill` with its version; all helpers report `--version`.
- **Orphaned temp files.** Info-ZIP `zi??????` temp names, Office locks, partial downloads and extensionless archives.
- **Large roots.** Collapsed noise suggestions, Python-environment detection, `--prune-noise`, `--max-seconds`, and `--host-root` for correct path lengths on mounted copies.

## Retained v1.3.0 capabilities

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

All four scripts are read-only against the target folder. `verify_move.py` never moves files. `verify_records.py` (v1.6.1) checks shared records and does not modify them.

```bash
python skills/multi-agent-folder-cleanup/scripts/audit_folder.py \
  --root <folder> --index-path INDEX.md --hash-files

# Low-token pass: summary to stdout, full report to a file outside the root
python skills/multi-agent-folder-cleanup/scripts/audit_folder.py \
  --root <folder> --hash-files --out /safe/outside/report.txt \
  --entrypoint AGENTS.md --entrypoint AI_CONTEXT/PROJECT_QUICK_CONTEXT.md \
  --index-coverage AI_CONTEXT/SESSION_INDEX.md=AI_CONTEXT/SESSIONS

# Optional advisory checks
python skills/multi-agent-folder-cleanup/scripts/audit_folder.py \
  --root <portfolio> --portfolio \
  --entrypoint AGENTS.md --entrypoint AI_CONTEXT/README_FIRST.md \
  --journal-threshold-kb 100 --detect-pointers \
  --expected-upload-manifest expected-files.csv

python skills/multi-agent-folder-cleanup/scripts/verify_move.py review \
  --map moves.csv --root <project> --approval-out proposal.json > review.md
# After owner approval of that exact review and the complete non-move package:
python skills/multi-agent-folder-cleanup/scripts/verify_move.py preflight \
  --map moves.csv --approval proposal.json --root <project> --path-threshold 240
python skills/multi-agent-folder-cleanup/scripts/verify_move.py baseline \
  --map moves.csv --approval proposal.json --root <project> --out /safe/audit/baseline.json
# Recheck with preflight --approval proposal.json --baseline /safe/audit/baseline.json --root <project> before moving.
python skills/multi-agent-folder-cleanup/scripts/verify_move.py verify \
  --baseline /safe/audit/baseline.json --root <project>

python skills/multi-agent-folder-cleanup/scripts/verify_records.py \
  path/to/INDEX.md path/to/PROJECT_QUICK_CONTEXT.md
```

Python 3.8+, standard library only. On Windows or OneDrive, prefer `audit_folder.ps1` (PowerShell 5.1 or 7+) because it can inspect placeholder attributes. On other platforms, record hydration as unverified until checked on Windows.

## Validation and releases

Every pull request runs the pinned OpenAI skill and plugin validators, package/version checks, Python compilation, PowerShell parsing, all regression tests, and a line-by-line Python/PowerShell report comparison on Ubuntu, plus the full suite on Windows (PowerShell 7 and a Windows PowerShell 5.1 junction smoke test). Tagged releases repeat runtime smoke tests, build the install archives, extract them, run the packaged code, and publish SHA-256 checksums.

To publish after the release commit is merged:

```bash
git tag -a vX.Y.Z -m "Multi-Agent Folder Cleanup vX.Y.Z"
git push origin vX.Y.Z
```

The tag must match the versions in `SKILL.md`, `.codex-plugin/plugin.json`, and `.claude-plugin/plugin.json`. Use **Actions → Release → Run workflow** to build artifacts without publishing.

## FAQ

### Which ZIP do I install?

Use `…-UNIVERSAL-skill.zip` for Claude app skill upload, ChatGPT or Codex standalone skills, Grok, local models, and a normal skills folder. Claude Code, the Codex/ChatGPT plugin marketplace, Microsoft Copilot, Gemini Apps, and Opal each need the matching package in the install table. Releases before v1.5.0 used older asset names.

### Does this skill move or delete files?

No. Audit is read-only. Plan only proposes a map. Execute follows an approved mutation list. Deletion is never included unless a separate approval names each target. The scripts do not move files.

### What is Work mode?

The mode for ordinary saving, naming, indexing, and handoff in a folder other agents also use. It is not a folder reorganization. Questions about the folder itself default to Audit.

### What did v1.6.1 add?

Read-only `scripts/verify_records.py` for SHA-256, encoding, line endings, mojibake, relative Markdown links, and table damage. Work mode asks agents to cite that output before calling a shared-record edit verified.

### Does install adopt the Project Rules?

No. The optional template is 3.3.0. Adoption is a separate owner decision.

## Authority rule

If two copies disagree, this repository is current. A release archive, chat upload, or host-local cache is not.

---

Created by Jesse Raber — [jesseraber.net](https://jesseraber.net)
