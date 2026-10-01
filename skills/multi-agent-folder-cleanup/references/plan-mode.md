# Plan mode

Read-only plus a written proposal. Read [preconditions.md](preconditions.md) and the audit evidence first. Execution follows [execute-moves.md](execute-moves.md) or [execute-records.md](execute-records.md) only after approval of the exact package built here.

## C. Plan mode

Read-only, plus a written proposal.

### C1. Proposed tree

Render the exact target tree as a code block, labeled `PROPOSED — not yet applied`. Keep the root short. A workable default, renamed to the project's vocabulary:

```
<root>/
  README.md              entrypoint: what this is, where to start
  AGENTS.md              instructions for agents (existing file — do not rewrite)
  STATUS.md              verified current state, dated
  AUTHORITY.md           which documents govern what
  INDEX.md               map of the tree
  HANDOFF.md             current master handoff
  authority/             specs, standards, conventions
  current/               active analysis and provenance
  backlog/               proposals, roadmaps, not-yet-real
  history/               superseded evidence, dated subfolders
  inbox/                 raw, untriaged incoming
  mirrors/               read-only external checkouts (untouched)
  scratch/               generated machine state (bucket 8) - excluded from
                         search and evidence review, deleted by nobody
```

Bucket 8 needs a named home or it leaks back into `history/` and gets preserved with the ceremony owed to documents. If the noise already sits in a folder the owner recognizes (`tmp/`, `.cache/`), leaving it where it is and naming it in the README beats moving 1,090 files to prove a point — moving noise costs the same verification effort as moving evidence and buys nothing.

Justify each departure from the user's existing names. If their tree already works, propose fewer changes rather than a prettier scheme.

### C2. Exact plan and complete approval package

Resolve owner choices before building executable rows. Put uncertain disposition, canonical ownership and unsupported historical/redundant labels in a separate decision list; excluded rows are not approved moves. Do not nest an installable archive inside its unpacked skill tree merely for tidiness. Preserve packaging usability and the project's existing vocabulary.

For moves, enumerate files in a CSV (`source,target`, optional later columns) or JSON map; expand proposed folders to their actual files. No wildcards. Generate the approval view from the exact map using the same parser as preflight:

```bash
python scripts/verify_move.py review --map /safe/plan/moves.csv \
  --approval-out /safe/plan/proposal.json > /safe/plan/review.md
python scripts/verify_move.py preflight --map /safe/plan/moves.csv
```

Use new session-owned output paths. The generated view contains ordinal row IDs, resolved absolute paths, raw map SHA-256, resolved-pairs SHA-256 and row count. Present that view directly; do not hand-retype a second table. Reasons/classification may be supplied separately keyed to those IDs. A receipt identifies a proposal; creating it is not human approval. Paths containing Markdown delimiters are escaped by the renderer.

Include the following in the separately versioned **PROPOSED** approval package before asking:

- Generated move view and exact map/receipt paths, digests and count; collision, existing-target, missing-source, path-length and hydration results with their measured scope.
- Untouched files, unmapped files and unresolved decisions; decisions affecting any retained row block execution of that row or the whole plan when dependent.
- Exact factual patches to navigation/status/handoffs, including warning preservation and full reconciliation of affected current-state claims. Name protected instruction-file patches separately. A promised future rewrite is not an approval package.
- Exact baseline, staging and evidence locations, staging copy/removal scope, and any source-folder removals. List potentially empty parents by path; an empty folder is not automatically approved for deletion. Disclose any staging inside a synced root.
- Required continuity writes and their policy source, kept distinct from cleanup approval. Preserve the original test baseline; do not refresh it silently after a run.

### C3. Bind owner approval to the presented package

Record the owner's authorization and its scope in the session record, identifying the generated review's map path, both digests and row count, plus the version/digest of the non-move patch/staging/removal package. Clear approval of the presented package is sufficient; do not demand magic wording or repeat established permission. If scope is ambiguous, ask narrowly before the dependent action.

Use the corresponding proposal receipt as `--approval` after that authorization. The helper checks plan identity, not whether a human actually approved it. Recheck immediately before execution. A changed map, relocated relative map, changed resolved paths or changed non-move patches require a revised review and approval of the changed scope. Approval does not excuse failed safety checks.

## G. Plan report format

**Plan report:** proposed tree, generated map review with both digests/count and complete C2 patch/staging/removal package, separated owner decisions, measured checks and an approval request tied to that version.
