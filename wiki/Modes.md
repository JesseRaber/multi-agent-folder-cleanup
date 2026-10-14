# Work, Audit, Plan, and Execute

Multi-Agent Folder Cleanup uses four modes. State the mode in the first line. The repository files are the protocol; this page only routes to them.

| Mode | Use it when | It may | It may not |
|---|---|---|---|
| Work | Saving, naming, indexing, or handing off ordinary work in a shared folder | Authorized task edits, a session log, and coordinated navigation updates | Reorganize the folder. Discovering clutter does not authorize cleanup |
| Audit | Asking what is here, or why agents are confused | Read-only inspection and an evidence report | Move, rename, or delete |
| Plan | Asking how the folder should be organized | A proposed tree and a literal source-to-target map labeled PROPOSED | Execute that map |
| Execute | The owner approved a specific mutation list | Only the approved moves, factual record patches, or additive intake | Expand the list from later discovery, or delete documents unless each target is named |

A question about the folder itself defaults to Audit unless execution is explicitly authorized. Ordinary project work is Work mode.

## Where to read

- Router: [SKILL.md](https://github.com/JesseRaber/multi-agent-folder-cleanup/blob/main/skills/multi-agent-folder-cleanup/SKILL.md)
- Work: [work-mode.md](https://github.com/JesseRaber/multi-agent-folder-cleanup/blob/main/skills/multi-agent-folder-cleanup/references/work-mode.md); also [work-mode-baseline.md](https://github.com/JesseRaber/multi-agent-folder-cleanup/blob/main/skills/multi-agent-folder-cleanup/references/work-mode-baseline.md) unless the project has adopted Project Rules 4.0.0 or later
- Cleanup start: [preconditions.md](https://github.com/JesseRaber/multi-agent-folder-cleanup/blob/main/skills/multi-agent-folder-cleanup/references/preconditions.md) and [cleanup-principles.md](https://github.com/JesseRaber/multi-agent-folder-cleanup/blob/main/skills/multi-agent-folder-cleanup/references/cleanup-principles.md)
- Audit: [audit-mode.md](https://github.com/JesseRaber/multi-agent-folder-cleanup/blob/main/skills/multi-agent-folder-cleanup/references/audit-mode.md) (rarer checks and confusion sources in [audit-edge-cases.md](https://github.com/JesseRaber/multi-agent-folder-cleanup/blob/main/skills/multi-agent-folder-cleanup/references/audit-edge-cases.md) on demand)
- Plan: [plan-mode.md](https://github.com/JesseRaber/multi-agent-folder-cleanup/blob/main/skills/multi-agent-folder-cleanup/references/plan-mode.md)
- Execute: [execute-principles.md](https://github.com/JesseRaber/multi-agent-folder-cleanup/blob/main/skills/multi-agent-folder-cleanup/references/execute-principles.md), then [execute-moves.md](https://github.com/JesseRaber/multi-agent-folder-cleanup/blob/main/skills/multi-agent-folder-cleanup/references/execute-moves.md) or [execute-records.md](https://github.com/JesseRaber/multi-agent-folder-cleanup/blob/main/skills/multi-agent-folder-cleanup/references/execute-records.md)

`references/workflow.md` was removed in v1.5.2. SKILL.md is the router.

Deletion is never in scope by default. Before any delete in Execute, run the recycle-path test: send one test file to the Recycle Bin (or provider trash) with the exact command that will be used, confirm it reached the bin and is gone from its path, and stop if not. A delete through a remote shell or device bridge without a passing test does not happen. Record the test result in the session log before the first target.

Optional Project Rules are a separate adoption. Installing the skill does not install them.

Current release: [v1.8.1](https://github.com/JesseRaber/multi-agent-folder-cleanup/releases/tag/v1.8.1).
