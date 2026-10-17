# Multi-Agent Folder Cleanup

Agent skill for a shared project folder used by more than one AI model. It is for Claude, ChatGPT, Codex, Microsoft Copilot, Gemini, Grok, Opal, and local models that keep saving into the same OneDrive, SharePoint, NAS, or handoff workspace.

Canonical skill: [`skills/multi-agent-folder-cleanup/`](https://github.com/JesseRaber/multi-agent-folder-cleanup/tree/main/skills/multi-agent-folder-cleanup)

Version **1.9.0**. Report as: **Loaded Multi-Agent Folder Cleanup v1.9.0 (SKILL.md at <path>; helpers <version>)**, taking the helper version from an actual `--version` run or saying `helpers not run`. Current release: [v1.9.0](https://github.com/JesseRaber/multi-agent-folder-cleanup/releases/tag/v1.9.0).

This page is a short pointer. The repository is the authority. A release archive, chat upload, or host-local cache is not. Protocol lives in the skill folder, not here, so this page does not drift into a second copy.

Goal: an agent opening a shared folder cold can tell what is true now, what is proposed, what is incoming, and what is historical — without choosing between plausible copies.

## Documentation

- [Install](Install) — which ZIP for Claude, ChatGPT, Codex, Copilot, Gemini, Opal, and Grok
- [Modes](Modes) — Work, Audit, Plan, and Execute
- [Scripts](Scripts) — read-only audit, move, and record checks
- [FAQ](FAQ) — common install and safety questions
- [Changelog](Changelog) — what changed through v1.9.0 (v1.9.0 released 2026-10-14)
- [README](https://github.com/JesseRaber/multi-agent-folder-cleanup/blob/main/README.md) — repository landing page

## Install

Prebuilt packages are on each [release](https://github.com/JesseRaber/multi-agent-folder-cleanup/releases). Host notes: [Install](Install) and the [README](https://github.com/JesseRaber/multi-agent-folder-cleanup/blob/main/README.md).

| Your AI app | Download |
|---|---|
| Almost everything: Claude app skill upload, ChatGPT/Codex standalone skills, local models, any skills folder | `…-UNIVERSAL-skill.zip` |
| Claude Code `/plugin install` (not the Claude app uploader) | `…-claude-code-plugin.zip` |
| Codex / ChatGPT plugin marketplace | `…-codex-chatgpt-plugin.zip` |
| Microsoft Copilot agent skill upload, **Grok** | `…-microsoft-copilot-agent-only.zip` |
| Gemini Apps skill upload | `…-gemini-apps-only.zip` |
| Opal skill import | `…-opal-only.zip` |
| Optional Project Rules template only | `…-project-rules-optional.zip` |

Coding agents that install from GitHub can use the repository directly. Keep the extracted structure intact. Do not install from a mixed archive with nested packages or loose duplicate scripts. Releases before v1.5.0 used older asset names (`-skill`, `-portable`, `-claude`, `-openai`, `-gemini-apps`, `-project-rules`). There is no `adapters/` tree.

Host packages leave out what that host rejects. The Copilot package has no `.ps1`; Grok needs it too, because Grok rejects the Universal ZIP's `.ps1`. The Gemini Apps package omits the audit helpers (`audit_folder.py`, `audit_folder.ps1`), `agents/openai.yaml`, and project rules; it keeps `verify_move.py` and `verify_records.py`. Opal imports Markdown only. If a host package has no `references/project-rules/` folder, use the optional ZIP or the repository; do not reconstruct the template.

When updating an existing install, keep the previous version's copy outside every folder the host scans for skills. Afterward there must be exactly one `SKILL.md` whose `name:` is `multi-agent-folder-cleanup` under the host skill roots. Files matching the ZIP are not proof the host loaded them; restart and check the reported version.

## Modes

State the mode in the first line. A question about the folder itself defaults to Audit unless execution is explicitly authorized. Ordinary save, name, and index work is Work mode.

| Mode | Typical request | Allowed |
|---|---|---|
| Work | Ordinary save, name, or index work in a shared folder | Authorized task edits, session continuity, and coordinated navigation updates |
| Audit | What is here? Why are agents confused? | Read-only report. No moves. |
| Plan | How should this be organized? | Proposed tree and a literal source-to-target map, labeled PROPOSED |
| Execute | Explicit approval of a specific mutation list | Only the approved moves, factual record patches, or additive intake |

Deletion is never in scope by default. Execute does not delete documents unless a separate approval names each target. Before any delete, run the recycle-path test (one test file to the Recycle Bin with the exact command, confirm it arrived, stop if not). A delete through a remote shell or device bridge without a passing test does not happen.

Read order is in [SKILL.md](https://github.com/JesseRaber/multi-agent-folder-cleanup/blob/main/skills/multi-agent-folder-cleanup/SKILL.md). Work mode: [work-mode.md](https://github.com/JesseRaber/multi-agent-folder-cleanup/blob/main/skills/multi-agent-folder-cleanup/references/work-mode.md) (and [work-mode-baseline.md](https://github.com/JesseRaber/multi-agent-folder-cleanup/blob/main/skills/multi-agent-folder-cleanup/references/work-mode-baseline.md) unless the project has adopted Project Rules 4.0.0 or later). Cleanup modes start at [preconditions.md](https://github.com/JesseRaber/multi-agent-folder-cleanup/blob/main/skills/multi-agent-folder-cleanup/references/preconditions.md). SKILL.md is the router. `references/workflow.md` was removed in v1.5.2 and is not on `main`.

## Scripts

`audit_folder.py`, `audit_folder.ps1`, `verify_move.py`, and `verify_records.py` are read-only against the target. `verify_move.py` never moves files. `verify_records.py` checks shared records and does not modify them. On Windows or OneDrive, prefer `audit_folder.ps1`. Elsewhere, record hydration as unverified until checked on Windows. Connector-only access is not an Execute path for moves.

```bash
python skills/multi-agent-folder-cleanup/scripts/audit_folder.py --version
```

See [Scripts](Scripts) for the full list and limits. The Gemini Apps package carries only `verify_move.py` and `verify_records.py` (no audit helper), and the Opal package has no scripts; say a missing helper is unavailable instead of reconstructing it.

The UNIVERSAL skill folder holds 26 files.
