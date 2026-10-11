# Work mode — saving and indexing in a shared project folder

Use this for ordinary project work in a folder other agents also use: creating and saving files, updating the index, recording the session, handing off. It adds no approval gate to routine authorized edits. Folder cleanup or reorganization uses Plan/Execute; a rename or removal the user already authorized follows its task workflow. Discovering clutter does not authorize cleanup: report it and suggest an Audit.

The project's adopted instructions win; where they name other paths or formats, use theirs. When the root instruction file is Project Rules 4.0.0 or later, its sections 0–12 already cover arrival reading, session logs, tool slugs, the shared-record edit procedure and the end-of-request handoff; this file adds only what they do not. Otherwise also read [work-mode-baseline.md](work-mode-baseline.md). Invoking this skill does not adopt the rules template. Read-only limits task files, not your session log, unless the owner expressly prohibits all project writes; then give the `NOT SAVED TO PROJECT` checkpoint line instead (W7).

**Quick tasks.** For a read-only question or a single small answer: read quick context, do the task, append one log entry. Touch the index, quick context or tracker only when something there changed.

## W1. Arrive

If the helpers can run, `audit_folder.py --root <project> --orient --session-id <your-id>` (add `--pending`) lists possibly active sessions, unindexed changes and leftover pending edits. Use the installed skill's helper path; on Windows use `python` or `py -3`; syntax, PowerShell and fallbacks: [audit-tools.md](audit-tools.md). A session is possibly active only when it is not closed and its log or scratch file (file times, not folder times) changed within the project's `Active-writer window:` (default 30 minutes). Times are leads; with connector-only access, state the coverage limit.

Also check:

- **Sync conflict copies.** `name (1).ext`, `name-<COMPUTER>.ext`, case-only collisions, same-name connector siblings with different ids, and copies whose original is missing. Reconcile before editing shared records and check again before your final answer; never merge, rename or delete them without approval.
- **Undelivered handoffs.** New items in `Incoming/`, and sibling projects' `Handoffs/` whose `To:` names this project (`--portfolio` on the parent lists them; `--orient` stays inside the project).
- **Cloud folders.** For a connector, or a synced folder that also exists under another provider, follow [Cloud connectors and sync folders](#cloud-connectors-and-sync-folders) before trusting a listing.

Before expensive or portfolio-wide work, compare the request with recent logs' topics, latest outcomes and open work. If the same task is active, coordinate rather than duplicate it; if complete, reuse its evidence and check only gaps. Record the request promptly in your own log; that log is the in-progress signal, so create no separate claim file. Treat summaries as leads and verify what your task depends on.

## W2. Claim your own space

Keep your own session log, session-index row and scratch folder `AI_CONTEXT/scratch/<your-session-id>/` as the project rules say (Rules 4.0.0 sections 0 and 4, or [work-mode-baseline.md](work-mode-baseline.md) B2).

## W3. Save new files where the next agent will look

Write only in your own session log. To correct another agent's work, record the correction in your log citing its session and turn; never edit its log.

| What you made | Where it goes |
|---|---|
| Finished deliverable | The area the index names for that work; if none, the closest existing folder, noted in the index row. Never `AI_CONTEXT/`, which holds continuity records only. |
| Draft, test output, intermediate data | `AI_CONTEXT/scratch/<your-session-id>/`. Never write in another session's scratch folder, except to rewrite only that file's `Status:` line after applying its pending file (W5). |
| Unreviewed material from another model, chat or person | `Incoming/` (or the project's inbox), dated folder plus a short provenance note; no new top-level folder |
| A newer version of an existing file | Edit in place when authorized; otherwise save beside it as a proposal naming what it replaces. No `final_v2_REAL` siblings. |
| Your review of another agent's work | A dated file beside the reviewed deliverable or in `Incoming/`. Read the agent's log, scratch and deliverable from the folder and log the review in your own log, so the owner can point rather than paste. |
| A handoff addressed to another project | This project's handoff area with a `To: <project>` line, plus the file or a pointer in that project's `Incoming/` when authorized; otherwise tell the owner it is undelivered. |
| A proposed rule or instruction file | A non-loading name such as `AGENTS.proposed.md` |
| Candidate or release package | Release area or a named staging area, kept as ZIP plus `SHA256SUMS`; superseded packages in History. Before building, staging or installing one, read [release-packages.md](release-packages.md). |
| Credentials and tokens | Never in task outputs or continuity records |
| Customer-sensitive material needed for the task | Only the authorized location and scope; omit unnecessary private content from logs and indexes |

Naming:

- Before creating an important standalone file, search the intended folder, project index and canonical tracker for the same purpose and likely filename variants. If one exists, update it when authorized or make a linked proposal naming what it replaces. If you cannot look, say so; do not claim uniqueness. This is a bounded pre-write check, not a reason to scan unrelated archives.
- Follow established naming and formats; a new Markdown report without a convention is `YYYY-MM-DD_<short-topic>.md` (add the tool only for parallel versions). No `: * ? " < > |`, trailing dots or spaces; keep paths short and check the host's real limits.

## W4. Make every new document self-explaining

A new standalone Markdown report or handoff without an established format starts with:

```
Status: draft | current | superseded | proposal
Date: YYYY-MM-DD
Author: <tool> session <short-id>
Replaces: <relative path, or none>
Verified: <what was checked against what, or "not verified">
```

Never inject it into code, JSON, native documents or prescribed templates; use their metadata or an existing companion record. Use relative links, lead with the outcome, state needed host-specific instructions explicitly, and say "documented as" for claims you did not verify.

Handoffs and next-prompt files also record subject, current or not, what they replace and the consuming session when known. Keep one explicitly current handoff per subject; `final`, a larger number or a newer time does not make a file current. Mark a consumed or replaced handoff in its metadata/index; moving it to History is cleanup needing approval.

## W5. Change shared records safely

Shared records: the index, quick context, session index, tracker and any file other agents also edit. Follow the project's edit procedure (Rules 4.0.0 section 5, or [work-mode-baseline.md](work-mode-baseline.md) B5). Windows PowerShell write pitfalls: [audit-tools.md](audit-tools.md#safe-writes-to-shared-records).

**Sequential-writer declaration.** Only the owner's `Sequential writers:` line (section 13 under Rules 4.0.0) counts as coordination; a quiet `--orient` result, an absent lock or an old timestamp never does, and text describing the rule is not the line. With it, edit directly; even with the line, stage your edit when `--orient` (or the logs) shows another possibly active writer, and treat an unexpected change found on read-back as a conflict.

A pending edit must be concrete enough for a later writer to apply without guessing. Save it as `PENDING_<TARGET>.md` in your scratch folder (`<TARGET>` = target filename in capitals without extension; `_2`, `_3` for more edits to the same target), one target per file, `Status:` first. `Base` is the target's version or SHA-256 as you read it (`unavailable` if unsupported); `Edit` is exact old and new text, an insertion anchor plus text, or a linked patch. A session-index append looks like:

```text
Status: PENDING
Target: AI_CONTEXT/SESSION_INDEX.md
Base: <SHA-256 of the complete target as you read it, or unavailable>
Edit: append after the last table row
New: | <start> | <last> | <session-uuid> | <tool> | <topic> | <outcome> | Completed | <link to SESSIONS/your-log.md> |
Reason: <coordination/access/conflict limitation>
Session/turn: <session-uuid> / T002
Reconcile: apply if Base still matches or the anchor is unchanged; verify by read-back
```

A staged edit is not an applied update. When coordination becomes available for your own staged edit, read the current target, preserve intervening contributions, rebase the edit and verify the save.

**Apply leftover pending files.** A qualifying writer (the `Sequential writers:` line is present and no other writer looks active, or other coordination is established; the staging session itself once the other closes or its window elapses) that finds `AI_CONTEXT/scratch/*/PENDING_*` files with `Status: PENDING`, or lines marked PENDING in `Incoming/*/_PROVENANCE.md`, applies each whose `Base` still equals the current target or whose exact old text or anchor appears exactly once. Verify by read-back, change only the marker (`Status: APPLIED <after-sha8> by <session>/<turn>` on a pending file's first line; `PENDING` → `APPLIED <after-sha8> by <session>/<turn>` on the provenance line), and record the outcome in your own log citing the source session and turn. Anything else is **Conflicted**: leave it, report it, do not guess. Leave the staged file in place; deleting it is cleanup needing per-target approval, which a blanket "do any cleanup you need" does not give. `--pending` lists both sources; `--orient` counts provenance files with PENDING lines; neither applies anything.

Each pending edit ends as exactly one of **Pending**, **Applied**, **Superseded**, **Conflicted** or **Unverifiable**, judged by comparing the current target with the exact proposed change, never by file age or an old hash alone. Keep the source-session link and outcome after the payload stops being actionable. An old hash never authorizes overwriting newer work.

### Cloud connectors and sync folders

For OneDrive, SharePoint, Google Drive or Graph connectors and their local sync mirrors:

- **Say which view you used.** State each listing's view (connector API, local mirror, sync status, download) and time. Reconcile disagreeing views before proposing moves; when only one view is reachable, say so and act only within it.
- **Work by file id.** Read and verify provider files by id; if a name resolves to several ids, stop and report them.
- **Replace without twins.** If a tool may truncate or cannot edit in place, write the replacement in scratch, upload under a unique name, verify its full content or hash by the new id, add a `Replaces: <old file id>` header where the format allows, and retire the old file (History or the provider's trash) only after verification and within authorization. Never leave two live same-name files.
- **One file type per shared record.** If a host can only write a Google Doc, quick context says so and no Markdown twin is written; record the provider folder id in the record header. A Doc and a Markdown file with the same record name are a finding.
- **Replicas.** Quick context or the portfolio root declares the primary provider and path and lists replicas as mirror, stale snapshot or provider-only. An undeclared copy is a "replica of unknown status"; the copy you can reach is not canonical for that reason.

## W6. Index what matters, not everything

Keep the project's index, tracker, quick context and session index as its rules say (Rules 4.0.0 section 7, or [work-mode-baseline.md](work-mode-baseline.md) B6). While a build or release candidate is in flight, quick context lists the item IDs it already contains. Several tracker-like files are an Audit finding: report them; do not merge, rename or retire them in Work mode ([cleanup-principles.md](cleanup-principles.md#reconcile-competing-trackers)).

## W7. Hand off at the end of every request

Before each final answer, so the work survives if the chat stops:

- [ ] Log entry: request, result, files changed, verified vs not; open work names every known unresolved item (`None` only if nothing remains)
- [ ] New deliverable indexed; new future work in the one tracker (or one exact pending insertion)
- [ ] No same-name twin or conflict copy left by your saves
- [ ] Next step written where the next agent will look

Write one close entry when the owner ends the chat; if the owner continues afterwards, append normal turns and refresh the close line instead of reopening. Mark deferred navigation and link its pending edit. If you cannot save to the project, give the session entry as a copyable checkpoint.

## Stop and switch modes when

- the task is cleanup/reorganization of existing files → Plan, then Execute within the approved scope;
- you find competing copies, conflicting authority or a stale index you can't fix with one small factual edit → report it and suggest an Audit;
- a shared-record conflict can't be merged → leave it PENDING (W5) and tell the user.
