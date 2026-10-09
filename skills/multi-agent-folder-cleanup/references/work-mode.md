# Work mode — saving and indexing in a shared project folder

Use this when you are doing ordinary project work in a folder that other agents and models also use: creating files, saving results, updating the index, recording the session, handing off. It keeps the folder usable for whoever arrives next. Work mode supports the authorized task without adding a separate approval gate to routine edits. Use Plan/Execute for folder cleanup or reorganization. A task-specific rename or removal already authorized by the user follows that task workflow; discovering clutter does not authorize cleanup. If unrelated folder confusion remains, report it and suggest an Audit.

The project's adopted instructions win. Where they name other paths or formats, use theirs. The defaults below match the bundled Project Rules (`AI_CONTEXT/...`). Reuse equivalent existing locations; do not create competing logs or indexes merely to match these names. Invoking this skill does not adopt the optional rules template. Read-only limits task files, not your session log, unless the owner expressly prohibits all project writes; then give the `NOT SAVED TO PROJECT` checkpoint line instead (W7).

## W1. Arrive (suggested read budget ~40 KB)

1. Read the root instruction file (`AGENTS.md`, `CLAUDE.md` or the host's equivalent).
2. Read `AI_CONTEXT/PROJECT_QUICK_CONTEXT.md`, then `PROJECT_INDEX.md` only as far as your task needs. Read a large tracker by section or item ID and a journal by its tail; do not read either whole at arrival.
3. When resuming related work, read the relevant session log's last entries and inspect the sessions folder for newer records if the index is stale. Follow required authority and evidence even when that exceeds the suggested budget.
4. If scripts can run, check for other writers and recent changes:

```
python3 scripts/audit_folder.py --root <project> --orient --session-id <your-id>
pwsh -File scripts/audit_folder.ps1 -Root <project> -Orient -SessionId <your-id>
```

Add `--pending` (`-Pending`) to list leftover pending files and whether each can still be applied (W5).

On Windows, `python` or `py -3` may replace `python3`; use `powershell.exe -NoProfile -ExecutionPolicy Bypass -File` when `pwsh` is absent. The Microsoft Copilot/Grok package intentionally omits `audit_folder.ps1`, so use its Python helper. See [audit-tools.md](audit-tools.md) for the complete fallbacks.

It lists possibly active sessions, files changed since the latest session started, and changed files the index never names. A session is possibly active only when it is not closed and its log or a file in its scratch folder changed within the active-writer window (the project's `Active-writer window:` line, else 30 minutes; file times, not folder times). A close entry in the log or a session-index status other than `in progress` closes a session, and so does the owner's handoff message saying that agent has finished, which the helper cannot see: the owner's statement overrides the listing. Times are local modified times: leads, not proof. Without scripts, use available listings and read the relevant recent logs. With connector-only or partial access, state the coverage limit; do not claim a writer is absent from missing activity signals. Use the helper path in the installed skill, not a presumed project-relative scripts directory.

Also check, with the helper or by listing:

- **Sync conflict copies.** `name (1).ext`, `name-<COMPUTER>.ext`, case-only name collisions and, through a connector, same-name siblings with different file ids; also a copy whose original is missing. Reconcile them before editing shared records, and check again before your final answer. Never merge, rename or delete them without the applicable approval.
- **Undelivered handoffs.** New items in `Incoming/`, and handoffs in sibling projects' `Handoffs/` whose `To:` names this project (`--portfolio` on the parent folder lists them; `--orient` never reads outside the project).
- **Cloud folders.** For a connector or a synced folder that also exists under another provider, follow [Cloud connectors and sync folders](#cloud-connectors-and-sync-folders) before trusting any listing.

Before expensive or portfolio-wide work, compare the request with the topic, latest outcome and open work in recent session logs. If the same task is active, coordinate rather than duplicate it. If it is complete, reuse its evidence and inspect only changes or gaps. Record the current request promptly in your own session log; that log is the in-progress signal, so do not create a separate shared claim file.

Treat summaries as leads. Verify anything your task depends on against the actual file.

## W2. Claim your own space

- For a new chat or uncertain writer handoff, create your own log with a generated UUID: `AI_CONTEXT/SESSIONS/YYYY-MM-DD_HHMMSS_<tool>_<short-topic>_<uuid>.md`. Preserve source-session links separately. Within the same established session and writer, append to that log; do not create one per request. Resume after a restart only with established writer continuity, or follow an evidenced transfer under the project policy. If identity is uncertain, start a linked continuation.
- Create your session-index row when you create the log, with status `in progress` (W6); refresh it at significant outcomes and close.
- Use your runtime's established lowercase slug in that filename and the `Tool/runtime` header: the one every session of that runtime uses, as listed in the project's `Tool slugs in use:` line or existing log names (`claude`, `codex`, `antigravity`, `gemini`, `copilot`, `manus`, `opal`, `grok`, `muse`, …). One slug per runtime: a different runtime never shares one, even with the same model (`grok` for the xAI app, `cursor-grokbot` for a Cursor agent); model, connector and machine go in the header. A new runtime picks a short unused name, `<runtime>-<agent>` when needed. Never skip the session log because your tool is unlisted. Use a canonical UUID for the ID segment.
- Use the project's established format. Include session ID, start time with timezone when known, writer instance, source-chat identity or unavailable, and coverage start. Record each request/outcome with a stable turn ID; verify previous content is preserved and the entry appears once.
- Keep drafts and temporary work in `AI_CONTEXT/scratch/<your-session-id>/`. Never write in another session's scratch folder. The one exception: after applying another session's pending file under W5, rewrite only that file's `Status:` line.
- If another writer looks active, do your independent work anyway and be extra careful with shared files (W5).

## W3. Save new files where the next agent will look

Write only in your own session log. If another agent's work needs correction, record the correction as a turn in your log and cite that agent's session and turn; never append to or rewrite the other agent's log.

| What you made | Where it goes |
|---|---|
| Finished deliverable | The project area the index names for that kind of work. No obvious area: the closest existing folder, and say so in the index row. Never `AI_CONTEXT/`, which holds continuity records only. |
| Draft, test output, intermediate data | `AI_CONTEXT/scratch/<your-session-id>/` |
| Material from another model, chat or person, not yet reviewed | `Incoming/` (or the project's inbox), as a dated folder with a short provenance note. Do not create a new top-level folder for it. |
| A newer version of an existing file | Edit the file in place when you are authorized to change it. Otherwise save beside it as a proposal and say what it would replace. Never create `final_v2_REAL` siblings. |
| Your review of another agent's work | A dated file where that agent and the owner will look: beside the reviewed deliverable or in `Incoming/`. Read the other agent's log, scratch and deliverable from the folder, and log the review as a turn in your own log, so the owner can point rather than paste. |
| A handoff addressed to another project | This project's handoff area with a `To: <project>` line. Also place it, or a pointer, in that project's `Incoming/` when you are authorized to write there; otherwise tell the owner it is undelivered. |
| A proposed rule or instruction file | A non-loading name such as `AGENTS.proposed.md`, never a live instruction filename |
| Candidate or release package | Keep candidates in a clearly named candidate/staging area, released artifacts in the release area, and superseded packages in History or `_superseded/`. Never place a same-version candidate beside a released package without an unmistakable status label and canonical pointer. Keep staged and backup packages as ZIP plus `SHA256SUMS`, not extracted trees; if you must extract one, rename its `SKILL.md`, `AGENTS.md` and similar files to non-loading names. |
| Credentials and tokens | Do not copy into task outputs or continuity records |
| Customer-sensitive material needed for the task | Use only the authorized project location and access scope; omit unnecessary private content from logs and indexes |

Naming:

- Before creating an important standalone file, search the intended folder, project index and canonical tracker for the same purpose, subject and likely filename variants. If an established artifact already serves the purpose, update it in place when authorized or create a clearly linked proposal that says what it would replace. If the lookup is unavailable, disclose that limitation; do not claim the file is unique. This is a bounded pre-write check, not a reason to scan unrelated archives.
- Follow established naming and native formats. For a new standalone Markdown report without a convention, use `YYYY-MM-DD_<short-topic>.md`. Add the tool name only when several models produce parallel versions of the same thing.
- Use plain words, hyphens or underscores, and no characters that break on Windows, OneDrive or URLs (`: * ? " < > |`, trailing dots or spaces).
- Keep paths short and check the actual host/application limits; do not treat a single character count as a universal limit.

### Add-only agents

If you can only add files (a browser upload, or a connector without edit or append) and cannot append to a log or edit shared records:

1. Do not create a new top-level folder. Upload into `Incoming/YYYY-MM-DD_<tool>_<topic>/` or the project's established inbox.
2. Upload a `_PROVENANCE.md` with the files. It lists:
   - tool and session (or "browser upload")
   - time with timezone
   - each file with its purpose
   - status (unreviewed or ready)
   - the exact index row, tracker row and session-index row you propose, each marked **PENDING**
3. If you can add files to `AI_CONTEXT/SESSIONS/`, also add your own new session log there. Creating a new file is allowed even when editing existing ones is not.
4. Tell the owner in your reply that shared records are still pending.

The next qualifying agent that finds PENDING rows in a `_PROVENANCE.md` applies them under W5 ("Apply leftover pending files"), then changes each marker to `APPLIED <after-sha8> by <session>/<turn>`.

An upload with no session log and no provenance file is incomplete work.

## W4. Make every new document self-explaining

For a new standalone Markdown report or handoff without an established format, use a short header block so a cold reader knows what it is without reading the session log:

```
Status: draft | current | superseded | proposal
Date: YYYY-MM-DD
Author: <tool> session <short-id>
Replaces: <relative path, or none>
Verified: <what was checked against what, or "not verified">
```

Keep code, JSON, native documents and prescribed templates in their required formats; never inject this header into syntax that cannot accept it. Put provenance in supported metadata or an existing companion record when needed. For Markdown, prefer relative links and lead with the outcome. Include necessary host-specific instructions explicitly, without relying on private chat memory. Say "documented as" for claims you did not verify yourself.

For handoffs and next-prompt files, also record the subject, whether the file is current, what it replaces, and the consuming session when known. Keep one explicitly current handoff per subject. Do not infer that `final`, a larger ordinal or a newer modified time makes a file current. Mark a consumed or replaced handoff in its metadata/index; moving it to History is cleanup and still needs the applicable approval.

## W5. Change shared records safely

Shared records are the index, quick context, session index and any file other agents also edit.

Before editing, establish a supported conditional update, a cooperating lock covering the relevant writers/devices, or a designated single writer. A local lock does not exclude remote cloud writers. Rereading and hash checks verify integrity; they do not establish exclusive ownership. If coordination is unavailable, save the exact intended edit in your session scratch folder, mark it PENDING in your log, and continue independent work.

**Sequential-writer declaration.** When the adopted rules or quick context contain a line beginning `Sequential writers:` (the owner's opt-in that agents work one after another; the project's adopted rules say how it applies), that line is the designated-writer coordination: the active agent edits shared records directly under steps 1–4 below. Only the owner's line establishes this; a quiet `--orient` result, an absent lock or an old timestamp never does, and text describing the rule is not the line. Even with the line, stage your edit when `--orient` (or the session logs) shows another possibly active writer (W1: not closed, file activity inside the window), and treat a change you did not make, found on read-back, as a conflict (step 4).

Edit shared files in place. Never write a replacement as a second file with the same name in the same folder, and never leave a sync conflict copy (`name (1).ext`) as the result of your save.

Before a full-file replacement, keep one byte-for-byte pre-edit copy of that file per session in your project session scratch area (a tool-private temporary folder is not a durable recovery location) and record its SHA-256. A pure append or a bounded in-place edit needs no copy; read-back is still mandatory. Use a non-loading filename for an instruction-file copy, such as `AGENTS.md.before-<sha8>` or `AGENTS.before.md`, never a literal `AGENTS.md` under scratch. Never copy a credential-bearing file. Preserve the target's encoding, line endings and structure while editing. For Markdown tables, keep each row inside the table, with no blank lines, and retain the table's established sort order.

1. Re-read the file immediately before writing.
2. Make the smallest exact edit (a bounded replace or a true append). Never rebuild a whole shared file from an older or truncated copy.
3. Re-read after saving. Confirm the edit is there exactly once, everything else is unchanged (diff against the pre-edit copy when you made one), and encoding, line endings and structured regions such as Markdown tables remain intact.
4. If the file changed since you read it, merge your change onto the new version. If you can't do that safely, save the exact intended edit in your scratch folder, mark it PENDING in your session log and move on.

**Write mechanics (Windows especially).** Shared records are UTF-8. Windows PowerShell 5.1 `>>`, `Out-File` and `Set-Content` without `-Encoding utf8` write UTF-16LE or ANSI into them (one `>>` append made a session index unreadable). Never use `>>` on a shared record; append with `[IO.File]::AppendAllText($path, $line + "`n", [Text.UTF8Encoding]::new($false))` (use "`r`n" if the file is CRLF), or use Python. Never rewrite a whole shared file through `Get-Content | Set-Content` (it changes line endings), and never regex-replace across a shared file: change only the one line that carries your own session ID or the exact anchor you read. After saving, run `verify_records.py` on it; it flags NUL bytes, UTF-16 segments and mixed line endings.

Do not claim a shared edit is **verified**, **zero loss** or **aligned** unless the applicable read-back, diff and structure checks above passed. When `scripts/verify_records.py` is available, run it on every shared record you changed and cite its output line for each file; an ACTIVATED or "verified" record entry without that output, or an equivalent stated check, must say "not verified". When a full replacement could not keep a pre-edit copy because the file contains credentials, report that recovery and diff coverage limit instead.

A pending edit must be concrete enough for a later writer to apply without guessing. Save it in your scratch folder as `PENDING_<TARGET>.md`, where `<TARGET>` is the target filename in capitals without its extension (`PENDING_SESSION_INDEX.md`; add `_2`, `_3` for further edits to the same target), with `Status:` as its first line:

```text
Status: PENDING
Target: <project-relative path>
Base: <version or SHA-256 of the complete original; unavailable if unsupported>
Edit: <exact old and new text, insertion anchor plus text, or a linked patch>
Reason: <coordination/access/conflict limitation>
Session/turn: <source ID and turn>
Reconcile: <condition required before applying>
```

One target per file, `Status:` on the first line, and the real SHA-256 of the target as you read it. For example, `AI_CONTEXT/scratch/<your-session-id>/PENDING_SESSION_INDEX.md`:

```text
Status: PENDING
Target: AI_CONTEXT/SESSION_INDEX.md
Base: 3f0ac80650cf8f20e44c4f61790a554d085d4f7b9dd9c00eb7df15e87710e891
Edit: append after the last table row
New: | 2026-10-09T00:23-04:00 | 2026-10-09T00:35-04:00 | <session-uuid> | Antigravity | <topic> | <outcome> | Completed | <link to SESSIONS/your-log.md> |
Reason: no sequential-writer declaration in this project
Session/turn: <session-uuid> / T002
Reconcile: apply if Base still matches or the last row is unchanged; verify by read-back
```

When coordination becomes available, read the current target, preserve intervening contributions, rebase the proposed edit and verify the save. Record the Applied/superseded/conflicted outcome in your own session log, citing the source session and turn; only the source session's writer appends to that session's log (W3). Leave the staged file in place after applying another session's edit. Removing it is cleanup requiring per-target approval; a blanket "do any cleanup you need" does not approve that deletion. A staged edit is not an applied update, and an old hash never authorizes overwriting newer work.

**Apply leftover pending files.** A qualifying writer (the `Sequential writers:` line is present and no other writer looks active, or other coordination is established) that finds `AI_CONTEXT/scratch/*/PENDING_*` files with `Status: PENDING`, or lines marked PENDING in `Incoming/*/_PROVENANCE.md` (rows proposed by hosts that read only section 0), applies each one whose `Base` hash still equals the current target, or whose exact old text or anchor still appears exactly once. The staging session itself qualifies once the other session closes or its window elapses. Verify by read-back as in step 3, change only the marker (`Status: APPLIED <after-sha8> by <session>/<turn>` on a pending file's first line; `PENDING` → `APPLIED <after-sha8> by <session>/<turn>` on the provenance line), and record the outcome in your own log. Anything else is **Conflicted**: leave it, report it, and do not guess. `--pending` (`-Pending`) lists both sources and their state when scripts can run, and `--orient` counts provenance files with PENDING lines; neither ever applies.

Reconcile pending edits into exactly one of: **Pending**, **Applied**, **Superseded**, **Conflicted** or **Unverifiable**. Compare the current target with the exact proposed change; filename age and the old base hash are not enough. Retain the source-session link and outcome even after the staged payload is no longer actionable.

### Cloud connectors and sync folders

Use this with OneDrive, SharePoint, Google Drive or Graph connectors, and with local sync mirrors of those providers.

- **Say which view you used.** Every listing or folder finding states its view (connector API, local sync mirror, sync client status, download) and the time. When two views disagree, such as local `(1)` names against same-name Drive files, reconcile before proposing moves. When only one view is reachable, say so and act only within what it shows.
- **Work by file id.** Read, re-download and verify a provider file by its id, never by name. If a name resolves to more than one id, stop and report the ids instead of picking one.
- **Replace without twins.** When a tool may truncate or cannot edit in place, write the replacement in your own scratch folder, upload it under a unique name, verify its full content or hash by the new id, and give it a `Replaces: <old file id>` header line where the format allows. Retire the old file (History or the provider's trash) only after that verification and within the task's authorization. Never leave two live files with the same name.
- **One file type per shared record.** If a host can only write a Google Doc, quick context says so and no Markdown twin is written. Record the provider folder id in the record header. A Doc and a Markdown file with the same record name are a finding.
- **Replicas.** A project may also exist under another provider or parent (for example a Drive snapshot of a OneDrive project). Quick context, or the portfolio root, declares the primary provider and path and lists known replicas with status: mirror, stale snapshot or provider-only. An undeclared copy is a "replica of unknown status": never treat the copy you can reach as canonical because it is the one you can reach.

## W6. Index what matters, not everything

- Maintain exactly one authoritative project-wide tracker for proposed changes, future work, deferred work and open tasks. Use the tracker named by adopted project instructions or current navigation; if none exists, default to `PROJECT_ROADMAP_STATUS.md`. Put the canonical path in the project index and quick context/startup navigation. A roadmap entry is a proposal or status record, not approval to execute it.
- Before recording new future work, search the canonical tracker for the same outcome, scope or dependency. Update the existing item when it is the same work; otherwise assign the next stable ID and record a concise title, status, source/provenance, dependencies or acceptance evidence when material, and links to supporting detail. Never let a suggestion live only in a session log, review, report, handoff, chat transcript or quick-context paragraph.
- Do not create another roadmap, backlog, TODO list, proposed-change list, next-steps list or independent future-task file. A scoped design, migration, validation or execution plan may exist when the task needs one, but it must identify the canonical tracker and its related item IDs; any newly discovered future work goes into the canonical tracker rather than becoming a second backlog inside the supporting plan.
- When multiple tracker-like files already exist, do not choose by filename, modified time or apparent completeness and do not silently merge, rename or delete them. Establish the canonical tracker from owner direction, adopted instructions and current navigation. Inventory unresolved actionable items from the others with provenance, reconcile them into the canonical tracker without losing status or source identity, then classify the older files as supporting evidence or History and point them to the canonical tracker. Physical moves or deletions remain cleanup work and need their applicable authorization.
- Before treating a source roadmap, backlog, review, handoff or task list as merged or retired, map every actionable item to its canonical tracker ID and record that mapping. For each apparent gap, search current-state evidence and relevant history for proof that the item was completed or superseded before reporting it missing. Unmapped or unverifiable items remain open; source-level labels such as "merged" are not item-level evidence.
- Treat the canonical tracker as a shared record under W5. If it cannot be updated safely, save one exact pending tracker insertion in your session scratch area and link it from the session log; do not create a substitute roadmap. Reconcile the pending insertion before claiming the task handoff is complete. Delegated helpers return proposed tracker rows to the coordinating writer unless a single writer for the tracker is explicitly designated.
- Give important deliverables and authority/instruction files individual discoverable links, even inside a covered folder. Use the established index or its linked topic index. One line: path, purpose, classification (Authority, Current, Deliverable, Evidence, Reference, Backlog, Incoming, History, Scratch), coverage and existence.
- Folder coverage is enough for routine supporting files and scratch descendants. Add a folder row only when existing navigation does not cover it. Do not add a row for every generated file.
- Update the row when you supersede a file: mark the old one History/superseded and point it at the new one.
- Update quick context only when direction, verified state, decisions or next steps changed. Maintain one clearly labeled current-state section: replace stale lines there instead of prepending dated paragraphs. Move useful chronology to session/history records. Aim for about 12 KB (`--orient` flags size and repeated/out-of-order header updates), while retaining active decisions, boundaries and evidence links. Size flags are advisory, not permission to discard context. While a build or release candidate is in flight, quick context lists the item IDs it already contains, so reviewers do not propose finished work.
- Keep one session-index row per session, created with the session log (status `in progress`), not at close. If scripts can run, `--session-index` (`-SessionIndex`) lists missing rows and links to logs that no longer exist, and prints proposed rows. Paste only the rows you checked, using W5.

## W7. Hand off at the end of every request

Before each final answer, so the work survives if the chat stops here:

- [ ] Session log entry: request, what you did, files changed, what's verified, what's open
- [ ] `Limits/open work` names every known unresolved item, including owner decisions created by this turn; write `None` only when nothing remains. A correction to an earlier turn restates the complete current open-work list.
- [ ] Deliverables are saved in the authorized place and format with appropriate provenance (W3–W4)
- [ ] New uploads have a log or a `_PROVENANCE.md` (Add-only agents)
- [ ] Index row added or updated for new deliverables (W6)
- [ ] Quick context updated if the state changed
- [ ] Every newly proposed, deferred or discovered future task is added to the one canonical tracker (or one exact pending insertion is recorded); no competing task list was created
- [ ] Session-index row created at session creation or refreshed for a significant outcome/close; routine turns need only their log entry
- [ ] No new sync conflict copy or same-name twin left by your saves (W1, W5)
- [ ] Next step written where the next agent will see it

Mark deferred navigation explicitly and link its exact pending edit. If you cannot save to the project, give the owed session entry as a copyable checkpoint, including session/turn, request, outcome, changed files and reason. A local sandbox copy does not prove delivery to the project destination.

## Stop and switch modes when

- the task is folder cleanup/reorganization involving existing files → Plan (then Execute within the approved scope); ordinary authorized task edits stay in their task workflow;
- you find competing copies, conflicting authority or a stale index you can't fix with one small factual edit → report it and suggest an Audit;
- a shared-record conflict can't be merged → leave it PENDING (W5) and tell the user.
