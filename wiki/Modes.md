# Modes

**Work.** Use for any ordinary task that creates, saves, or updates files in a shared project folder. Agent loads `references/work-mode.md` (and `references/work-mode-baseline.md` unless the root instruction file is Project Rules 4.0.0 or later). Routine authorized edits proceed without re-asking; this mode never moves, renames, or deletes existing files. See [Safety rules](Safety-rules).

**Audit.** Use for “What is here?”, “Why are agents confused?”, or “Who has been in this folder?”. Agent loads `references/preconditions.md`, `references/cleanup-principles.md`, and `references/audit-mode.md`. Read-only inventory and evidence report; no approval required because nothing is changed.

**Plan.** Use for “How should this be organized?”. Agent loads `references/preconditions.md`, `references/cleanup-principles.md`, and `references/plan-mode.md`. Read-only inspection plus an exact proposal with mutation lists labeled **PROPOSED**. Approval of a specific list is required before Execute.

**Execute.** Use only after explicit approval of a specific mutation list. Agent loads `references/preconditions.md`, `references/cleanup-principles.md`, `references/execute-principles.md`, then `references/execute-moves.md` or `references/execute-records.md`. Only the approved moves, factual patches, or additive intake files; discovery does not expand the list. See [Safety rules](Safety-rules).
