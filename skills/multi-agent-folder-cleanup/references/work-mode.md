# Work mode — saving and indexing in a shared project folder

Use this for ordinary project work in a folder other agents also use: creating and saving files, updating the index, recording the session, handing off. It adds no approval gate to routine authorized edits. Folder cleanup or reorganization uses Plan/Execute; a rename or removal the user already authorized follows its task workflow. Discovering clutter does not authorize cleanup: report it and suggest an Audit.

The project's adopted instructions win; where they name other paths or formats, use theirs. Defaults below match the bundled Project Rules (`AI_CONTEXT/...`); reuse equivalent existing locations rather than creating competing logs or indexes. Invoking this skill does not adopt the rules template. Read-only limits task files, not your session log, unless the owner expressly prohibits all project writes; then give the `NOT SAVED TO PROJECT` checkpoint line instead (W7).

## W1. Arrive (suggested read budget ~40 KB)

1. Read the root instruction file (`AGENTS.md`, `CLAUDE.md` or the host's equivalent).
2. Read `AI_CONTEXT/PROJECT_QUICK_CONTEXT.md`, then `PROJECT_INDEX.md` as far as the task needs. Read a large tracker by section or item ID and a journal by its tail; do not read either whole at arrival.
3. When resuming, read the relevant session log's last entries; if the index is stale, list the sessions folder. Required authority and evidence override the budget.
4. If scripts can run (use the installed skill's helper path, not a project-relative `scripts/`):

```
python3 scripts/audit_folder.py --root <project> --orient --session-id <your-id>
pwsh -File scripts/audit_folder.ps1 -Root <project> -Orient -SessionId <your-id>
```

Add `--pending` (`-Pending`) to list leftover pending files and whether each still applies (W5). On Windows use `python`/`py -3`, or `powershell.exe -NoProfile -ExecutionPolicy Bypass -File` without `pwsh`; the Copilot/Grok package has no `.ps1`. Fallbacks: [audit-tools.md](audit-tools.md).

`--orient` lists possibly active sessions, files changed since the latest session started, and changed files the index never names. A session is possibly active only when it is not closed and its log or a scratch file changed within the active-writer window (the project's `Active-writer window:` line, else 30 minutes; file times, not folder times). A close entry, a session-index status other than `in progress`, or the owner saying that agent has finished (which the helper cannot see) closes it. Times are leads, not proof. Without scripts, list and read recent logs; with partial or connector-only access, state the coverage limit and never infer that no writer exists.

Also check:

- **Sync conflict copies.** `name (1).ext`, `name-<COMPUTER>.ext`, case-only collisions, same-name connector siblings with different ids, and copies whose original is missing. Reconcile before editing shared records and check again before your final answer; never merge, rename or delete them without approval.
- **Undelivered handoffs.** New items in `Incoming/`, and sibling projects' `Handoffs/` whose `To:` names this project (`--portfolio` on the parent lists them; `--orient` stays inside the project).
- **Cloud folders.** For a connector, or a synced folder that also exists under another provider, follow [Cloud connectors and sync folders](#cloud-connectors-and-sync-folders) before trusting a listing.

Before expensive or portfolio-wide work, compare the request with recent logs' topics, latest outcomes and open work. If the same task is active, coordinate rather than duplicate it; if complete, reuse its evidence and check only gaps. Record the request promptly in your own log; that log is the in-progress signal, so create no separate claim file. Treat summaries as leads and verify what your task depends on.

## W2. Claim your own space

- New chat or uncertain writer handoff: create your own log with a generated UUID, `AI_CONTEXT/SESSIONS/YYYY-MM-DD_HHMMSS_<tool>_<short-topic>_<uuid>.md`. Within the same established session and writer, append to it; do not create one per request. Resume after a restart only with established writer continuity or an evidenced transfer; otherwise start a linked continuation. Keep source-session links separate.
- Create your session-index row when you create the log, status `in progress` (W6); refresh it at significant outcomes and close.
- `<tool>` is your runtime's established lowercase slug, from the project's `Tool slugs in use:` line or existing log names (`claude`, `codex`, `antigravity`, `gemini`, `copilot`, `manus`, `opal`, `grok`, `muse`, …). One slug per runtime: a different runtime never shares one, even with the same model (`grok` for the xAI app, `cursor-grokbot` for a Cursor agent); model, connector and machine go in the `Tool/runtime` header. A new runtime picks a short unused name (`<runtime>-<agent>` when needed). An unlisted tool still keeps a log.
- Use the project's established log format. Header: session ID, start time with timezone when known, writer instance, source chat or `unavailable`, coverage start. Each request/outcome gets a stable turn ID; verify prior content is preserved and the entry appears once.
- Drafts and temporary work go in `AI_CONTEXT/scratch/<your-session-id>/`. Never write in another session's scratch folder, except to rewrite only that file's `Status:` line after applying its pending file (W5).
- If another writer looks active, do your independent work and take extra care with shared files (W5).

## W3. Save new files where the next agent will look

Write only in your own session log. To correct another agent's work, record the correction in your log citing its session and turn; never edit its log.

| What you made | Where it goes |
|---|---|
| Finished deliverable | The area the index names for that work; if none, the closest existing folder, noted in the index row. Never `AI_CONTEXT/`, which holds continuity records only. |
| Draft, test output, intermediate data | `AI_CONTEXT/scratch/<your-session-id>/` |
| Unreviewed material from another model, chat or person | `Incoming/` (or the project's inbox), dated folder plus a short provenance note; no new top-level folder |
| A newer version of an existing file | Edit in place when authorized; otherwise save beside it as a proposal naming what it replaces. No `final_v2_REAL` siblings. |
| Your review of another agent's work | A dated file beside the reviewed deliverable or in `Incoming/`. Read the agent's log, scratch and deliverable from the folder and log the review in your own log, so the owner can point rather than paste. |
| A handoff addressed to another project | This project's handoff area with a `To: <project>` line, plus the file or a pointer in that project's `Incoming/` when authorized; otherwise tell the owner it is undelivered. |
| A proposed rule or instruction file | A non-loading name such as `AGENTS.proposed.md` |
| Candidate or release package | Candidates in a named staging area, releases in the release area, superseded packages in History or `_superseded/`; never a same-version candidate beside a release without an unmistakable status label and canonical pointer. Keep staged and backup packages as ZIP plus `SHA256SUMS`; an extracted copy gets non-loading `SKILL.md`/`AGENTS.md` names. When installing into a host, keep the backup of the previous version outside every folder the host scans for skills (hosts such as Codex load `SKILL.md` recursively, so a backup there becomes a second same-name skill); after install, require exactly one `SKILL.md` with that `name:` under the host's skill roots. Files matching the ZIP are not proof the host loads them: confirm the version the host reports in a new session. |
| Credentials and tokens | Never in task outputs or continuity records |
| Customer-sensitive material needed for the task | Only the authorized location and scope; omit unnecessary private content from logs and indexes |

Naming:

- Before creating an important standalone file, search the intended folder, project index and canonical tracker for the same purpose and likely filename variants. If one exists, update it when authorized or make a linked proposal naming what it replaces. If you cannot look, say so; do not claim uniqueness. This is a bounded pre-write check, not a reason to scan unrelated archives.
- Follow established naming and formats; a new Markdown report without a convention is `YYYY-MM-DD_<short-topic>.md` (add the tool only for parallel versions). No `: * ? " < > |`, trailing dots or spaces; keep paths short and check the host's real limits.

### Add-only agents

If you can only add files (browser upload, connector without edit or append):

1. Upload into `Incoming/YYYY-MM-DD_<tool>_<topic>/` or the established inbox; no new top-level folder.
2. Include `_PROVENANCE.md`: tool and session (or "browser upload"), time with timezone, each file and purpose, status (unreviewed or ready), and the exact index, tracker and session-index rows you propose, each marked **PENDING**.
3. If you can add files to `AI_CONTEXT/SESSIONS/`, add your own new session log there; creating a new file is allowed even when editing existing ones is not.
4. Tell the owner that shared records are still pending.

The next qualifying agent applies those PENDING rows under W5. An upload with no session log and no provenance file is incomplete work.

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

Shared records: the index, quick context, session index, tracker and any file other agents also edit.

Before editing, establish a supported conditional update, a cooperating lock covering all relevant writers/devices (a local lock does not exclude cloud writers), or a designated single writer. Rereads and hashes verify integrity, not exclusivity. Without coordination, stage the exact edit in your scratch folder, mark it PENDING in your log, and continue independent work.

**Sequential-writer declaration.** A line beginning `Sequential writers:` in the adopted rules (under Rules 4.0.0 only in section 13; projects still on 3.3.0 may carry it in quick context as their rules allow) is the owner's designated-writer coordination: the active agent edits shared records directly under steps 1–4. Only the owner's line counts; a quiet `--orient` result, an absent lock or an old timestamp never does, and text describing the rule is not the line. Even with the line, stage your edit when `--orient` (or the logs) shows another possibly active writer, and treat an unexpected change found on read-back as a conflict (step 4).

Edit shared files in place; never save a second same-name file or leave a sync conflict copy. Before a full-file replacement, keep one byte-for-byte pre-edit copy of that file per session in your project session scratch folder (a tool-private temp folder is not durable) and record its SHA-256 (non-loading name for instruction files, e.g. `AGENTS.md.before-<sha8>`; never copy a credential-bearing file). A pure append or a bounded in-place edit needs no copy; read-back is still mandatory. Preserve encoding, line endings and structure; keep Markdown table rows inside the table, with no blank lines, in the established sort order.

1. Re-read the file immediately before writing.
2. Make the smallest exact edit (bounded replace or true append); never rebuild a shared file from an older or truncated copy.
3. Re-read after saving: the edit is there exactly once, the rest is unchanged (diff against the pre-edit copy if any), encoding, line endings and tables intact.
4. If the file changed since you read it, merge onto the new version; if that is unsafe, stage the edit as PENDING and move on.

**Write mechanics (Windows especially).** Shared records are UTF-8. Windows PowerShell 5.1 `>>`, `Out-File` and `Set-Content` without `-Encoding utf8` write UTF-16LE or ANSI. Never use `>>` on a shared record; append with ``[IO.File]::AppendAllText($path, $line + "`n", [Text.UTF8Encoding]::new($false))`` (``"`r`n"`` for CRLF files) or Python. Never pipe `Get-Content | Set-Content` over a shared file, and never regex-replace across a shared file: change only the one line that carries your own session ID or the exact anchor you read.

Claim "verified", "zero loss" or "aligned" only when the read-back, diff and structure checks above passed. When `verify_records.py` is available, run it on every shared record you changed and cite its output line; a record entry without that output or an equivalent stated check says "not verified". If a credential-bearing file prevented a pre-edit copy, report that limit.

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

- Maintain exactly one authoritative project-wide tracker for proposed changes, future, deferred and open work: the one named by adopted instructions or navigation, else `PROJECT_ROADMAP_STATUS.md`, linked from the index and quick context. An entry is a proposal or status, not approval.
- Before adding work, search the tracker for the same outcome, scope or dependency; update that item, or assign the next stable ID with title, status, source, material dependencies or acceptance evidence, and links. Never let a suggestion live only in a log, review, report, handoff, transcript or quick context.
- Create no other roadmap, backlog, TODO, proposed-change or next-steps list. A scoped plan may exist when the task needs one, citing the tracker's item IDs; newly discovered future work goes into the canonical tracker, not the plan.
- With several tracker-like files, establish the canonical one from owner direction, adopted instructions and navigation, never filename, date or completeness, and do not silently merge, rename or delete them. Before treating another as merged or retired, map every actionable item to its canonical tracker ID and record that mapping, keeping each item's status and source identity; search current state and history for completion or supersession before calling an item missing. Unmapped or unverifiable items stay open; a source-level "merged" label is not item-level evidence. Then classify the old file as evidence or History and point it to the canonical tracker; moving or deleting it is cleanup needing approval.
- The tracker is a shared record (W5). If you cannot update it safely, stage one exact pending insertion, link it from your log, and do not create a substitute roadmap; reconcile it before claiming handoff complete. Delegated helpers return proposed rows to the coordinating writer unless a single tracker writer is explicitly designated.
- Give important deliverables and authority files individual index rows, even inside a covered folder, in the established index or its linked topic index: path, purpose, classification (Authority, Current, Deliverable, Evidence, Reference, Backlog, Incoming, History, Scratch), coverage and existence. Folder coverage suffices for routine files and scratch; add a folder row only when navigation does not cover it, and no row per generated file. When superseding a file, mark the old row History and point it at the new one.
- Update quick context only when direction, verified state, decisions or next steps change. Keep one current-state section, replacing stale lines rather than prepending dated paragraphs; move chronology to session/history records; aim for about 12 KB without dropping active decisions, boundaries or evidence links (`--orient` flags size and out-of-order header updates; flags are advisory). While a build or release candidate is in flight, quick context lists the item IDs it already contains.
- Keep one session-index row per session, created with the log. `--session-index` (`-SessionIndex`) lists missing rows and dead links and proposes rows; paste only checked rows, under W5.

## W7. Hand off at the end of every request

Before each final answer, so the work survives if the chat stops:

- [ ] Session log entry: request, what you did, files changed, what's verified, what's open
- [ ] `Limits/open work` names every known unresolved item, including owner decisions this turn created; `None` only when nothing remains. A correction restates the complete open-work list.
- [ ] Deliverables saved in the authorized place and format with provenance (W3–W4); uploads have a log or `_PROVENANCE.md`
- [ ] Index row for new deliverables (W6); quick context updated if state changed
- [ ] Every new future task is in the one canonical tracker (or one exact pending insertion); no competing list
- [ ] Session-index row created at session start or refreshed for a significant outcome/close; routine turns need only their log entry
- [ ] No sync conflict copy or same-name twin left by your saves (W1, W5)
- [ ] Next step written where the next agent will see it

Mark deferred navigation and link its pending edit. If you cannot save to the project, give the session entry as a copyable checkpoint (session/turn, request, outcome, changed files, reason). A sandbox copy does not prove delivery.

## Stop and switch modes when

- the task is cleanup/reorganization of existing files → Plan, then Execute within the approved scope;
- you find competing copies, conflicting authority or a stale index you can't fix with one small factual edit → report it and suggest an Audit;
- a shared-record conflict can't be merged → leave it PENDING (W5) and tell the user.
