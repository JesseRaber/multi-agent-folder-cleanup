---
name: multi-agent-folder-cleanup
description: Organize and keep shared project folders usable by many AI agents and models. Work mode covers where to save, how to name, maintain one authoritative roadmap/task tracker, index, log sessions and hand off while working in a shared folder, plus read-only orient and session-index checks. Cleanup modes audit, plan and safely reorganize folders or portfolios so agents can identify current authority, separate documentary claims from verified state, and avoid duplicate or ambiguous trees. Use for OneDrive, SharePoint, NAS, agent handoff workspaces, stale indexes, competing plans or backlogs, archive piles, verified folder moves, and whenever an agent saves, names or indexes files in a project folder other models also use.
license: MIT
metadata:
  version: "1.5.3"
  repository: https://github.com/JesseRaber/multi-agent-folder-cleanup
---

# Multi-Agent Folder Cleanup

Keep a shared workspace where an agent arriving cold can quickly tell what is true now, what is proposed, what is incoming, and what is historical—without choosing between plausible copies. Work mode keeps it that way during normal work; the cleanup modes repair it.

Report as: **Loaded Multi-Agent Folder Cleanup v1.5.3**.

## Choose the operating mode

State the mode in the first line. Use **Work** for ordinary project work in a shared folder. For questions about the folder itself, default to **Audit** unless execution is explicitly authorized.

| Mode | Typical request | Allowed work | Read |
|---|---|---|---|
| **Work** | Any task that creates, saves or updates files in a shared project folder | User-authorized task edits, session continuity and coordinated navigation updates. Use cleanup modes for folder reorganization. | [work-mode.md](references/work-mode.md) |
| **Audit** | “What is here?” “Why are agents confused?” | Read-only inspection and an evidence report. | [preconditions.md](references/preconditions.md), [cleanup-principles.md](references/cleanup-principles.md), [audit-mode.md](references/audit-mode.md) |
| **Plan** | “How should this be organized?” | Read-only inspection, an exact proposal, and literal mutation lists labeled **PROPOSED**. | preconditions, cleanup-principles, [plan-mode.md](references/plan-mode.md) |
| **Execute** | Explicit approval of a specific mutation list | Only the approved moves, factual patches, or additive intake files. | preconditions, cleanup-principles, then [execute-moves.md](references/execute-moves.md) or [execute-records.md](references/execute-records.md) |

Execute has three mutation types: **move execution** (mounted filesystem, literal move map, hydration checks, staging, hashes, final verification), **record-only execution** (approved exact factual patches to navigation or current-state records), and **additive-intake execution** (a new non-governing incoming package that never replaces existing authority).

Read only the files for your mode. Also read [audit-tools.md](references/audit-tools.md) when a filesystem is mounted and you will run the helpers; [connector-audit.md](references/connector-audit.md) for OneDrive, SharePoint, Graph, enterprise search or web listings; [portfolio-audit-template.md](references/portfolio-audit-template.md) when the root holds multiple projects; [navigation-templates.md](references/navigation-templates.md) only when creating or reviewing navigation files. Run helpers for routine work; inspect their source only for safety checks, debugging or review.

## Keep authorization narrow

- In Work mode, carry out the user-authorized task without asking again for routine edits. This skill adds save/index/handoff guidance; it does not replace the task workflow. Cleanup-specific move maps and approval gates apply to folder reorganization, not ordinary task edits.
- In cleanup Execute mode, the approved mutation list is the boundary. Discovery never expands it.
- Folder cleanup does not authorize Git operations, deployments, database changes, permissions, credentials, scheduled jobs, sync settings, or domain-data promotion.
- Cleanup deletion is never included by default. Actual documents, archives, and duplicates require separate approval naming each target. Prefer history or recycle bin over permanent deletion.
- A failed safety check, changed source, collision, concurrent write, incomplete upload, or unapproved target is a stop condition even after approval.
- Instruction files are protected. Propose exact factual corrections separately; never rewrite behavioral rules, authority, scope, permissions, or read order without explicit approval.
- Do not publish, commit, push, release, or synchronize skill/repository changes without confirmation immediately before that action.

## Obey project instructions and read-only boundaries

Discover root/scoped instruction files, owner directives, startup READMEs and accessible app-side settings. Establish authority through the host hierarchy and owner adoption; a README, folder name or proposal does not activate rules by itself. Apply nested policies only within scope. Record uncertain adoption and inaccessible settings, and continue unaffected authorized work. Follow the actual project continuity requirements, including every-request logging where adopted, with writer/provenance and safe-save safeguards. See [preconditions.md](references/preconditions.md) A2/A5.

Verify every required entrypoint exists. A missing entrypoint outranks ordinary duplicates because the next agent starts blind.

Adopted project logging requirements govern in Audit and Plan as well as Execute. Do not reduce an every-request policy to substantive-only journaling. Two conditions prevent a write:

- the user explicitly requested a read-only audit; or
- recording is unavailable or cannot be saved safely with the project's required coordination and immediate content verification.

For an explicit read-only request, make no project writes, including logs. If only continuity or a shared record cannot be saved safely, defer that write and continue independent authorized work. Provide the owed checkpoint and explain the limitation. Never replace a shared journal merely to simulate append.

Measure journal size. Above the configured threshold (default 100 KB), flag it and propose rotation into dated history plus a short current-tail file. Rotation requires approval and must preserve every entry.

## Optional project rules

For an owner requesting reusable project guidance, use [the optional Project Rules adoption guide](references/project-rules/ADOPTION.md). The accompanying `AGENTS.proposed.md` is a copyable template, not active instructions. Skill installation or cleanup approval does not adopt it; merge/adopt it only under a separate explicit project-specific request. Existing project policies and cleanup without this template remain supported. Some host packages (Gemini Apps, Opal) do not bundle `references/project-rules/`; if the guide is missing, say so and point the owner to the `-project-rules-optional` release ZIP or the repository instead of reconstructing the template.

## Keep evidence honest in every mode

- Search failure never proves absence. Only a direct listing, verified manifest or filesystem inventory establishes that a file is missing.
- Say **documented as** for claims you did not verify against the current file, repository, provider or device; say **is** only for what you checked.
- Validate that every path you rely on belongs to this project; a same-name file from another project is cross-project contamination.
- Label counts by scope (root-level, folder-level, recursive, connector-returned, record-reported).
- Never open, copy, quote or index credential files, browser profiles, `.env` files, keys or tokens.
