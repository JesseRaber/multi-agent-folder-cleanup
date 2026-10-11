# Work mode baseline — only for projects without Project Rules 4.0.0 or later

Read this together with [work-mode.md](work-mode.md) when the root instruction file is not Project Rules 4.0.0 or later (no `## 0. Minimum rules` section and no `## 13. Project scope` section). Projects on those rules already carry everything below in their own `AGENTS.md` sections 0–12; reading it twice wastes context.

## B1. Arrive

1. Read the root instruction file (`AGENTS.md`, `CLAUDE.md` or the host's equivalent).
2. Read `AI_CONTEXT/PROJECT_QUICK_CONTEXT.md`, then `PROJECT_INDEX.md` as far as the task needs. Read a large tracker by section or item ID and a journal by its tail; do not read either whole at arrival.
3. When resuming, read the relevant session log's last entries; if the index is stale, list the sessions folder. Required authority and evidence override the budget.

`--orient` lists possibly active sessions, files changed since the latest session started, and changed files the index never names. A close entry, a session-index status other than `in progress`, or the owner saying that agent has finished (which the helper cannot see) closes a session. Without scripts, list and read recent logs; with partial or connector-only access, state the coverage limit and never infer that no writer exists.

## B2. Claim your own space

- New chat or uncertain writer handoff: create your own log with a generated UUID, `AI_CONTEXT/SESSIONS/YYYY-MM-DD_HHMMSS_<tool>_<short-topic>_<uuid>.md`. Within the same established session and writer, append to it; do not create one per request. Resume after a restart only with established writer continuity or an evidenced transfer; otherwise start a linked continuation. Keep source-session links separate.
- Create your session-index row when you create the log, status `in progress` (W6); refresh it at significant outcomes and close.
- `<tool>` is your runtime's established lowercase slug, from the project's `Tool slugs in use:` line or existing log names (`claude`, `codex`, `antigravity`, `gemini`, `copilot`, `manus`, `opal`, `grok`, `muse`, …). One slug per runtime: a different runtime never shares one, even with the same model (`grok` for the xAI app, `cursor-grokbot` for a Cursor agent); model, connector and machine go in the `Tool/runtime` header. A new runtime picks a short unused name (`<runtime>-<agent>` when needed). An unlisted tool still keeps a log.
- Use the project's established log format. Header: session ID, start time with timezone when known, writer instance, source chat or `unavailable`, coverage start. Each request/outcome gets a stable turn ID; write each entry's time from the system clock, never an estimate. Verify prior content is preserved and the entry appears once.
- If another writer looks active, do your independent work and take extra care with shared files (W5).

## B3. Add-only agents

If you can only add files (browser upload, connector without edit or append):

1. Upload into `Incoming/YYYY-MM-DD_<tool>_<topic>/` or the established inbox; no new top-level folder.
2. Include `_PROVENANCE.md`: tool and session (or "browser upload"), time with timezone, each file and purpose, status (unreviewed or ready), and the exact index, tracker and session-index rows you propose, each marked **PENDING**.
3. If you can add files to `AI_CONTEXT/SESSIONS/`, add your own new session log there; creating a new file is allowed even when editing existing ones is not.
4. Tell the owner that shared records are still pending.

The next qualifying agent applies those PENDING rows under W5 in [work-mode.md](work-mode.md). An upload with no session log and no provenance file is incomplete work.

## B5. Edit shared records

Before editing, establish a supported conditional update, a cooperating lock covering all relevant writers/devices (a local lock does not exclude cloud writers), or a designated single writer. Rereads and hashes verify integrity, not exclusivity. Without coordination, stage the exact edit in your scratch folder (W5 format), mark it PENDING in your log, and continue independent work.

Edit shared files in place; never save a second same-name file or leave a sync conflict copy. Before a full-file replacement, keep one byte-for-byte pre-edit copy of that file per session in your project session scratch folder (a tool-private temp folder is not durable) and record its SHA-256 (non-loading name for instruction files, e.g. `AGENTS.md.before-<sha8>`; never copy a credential-bearing file). A pure append or a bounded in-place edit needs no copy; read-back is still mandatory. Preserve encoding, line endings and structure; keep Markdown table rows inside the table, with no blank lines, in the established sort order.

1. Re-read the file immediately before writing.
2. Make the smallest exact edit (bounded replace or true append); never rebuild a shared file from an older or truncated copy.
3. Re-read after saving: the edit is there exactly once, the rest is unchanged (diff against the pre-edit copy if any), encoding, line endings and tables intact.
4. If the file changed since you read it, merge onto the new version; if that is unsafe, stage the edit as PENDING and move on.

Claim "verified", "zero loss" or "aligned" only when the read-back, diff and structure checks above passed. When `verify_records.py` is available, run it on every shared record you changed and cite its output line; a record entry without that output or an equivalent stated check says "not verified". If a credential-bearing file prevented a pre-edit copy, report that limit.

## B6. Index, tracker, quick context, session index

- Maintain exactly one authoritative project-wide tracker for proposed changes, future, deferred and open work: the one named by adopted instructions or navigation, else `PROJECT_ROADMAP_STATUS.md`, linked from the index and quick context. An entry is a proposal or status, not approval.
- Before adding work, search the tracker for the same outcome, scope or dependency; update that item, or assign the next stable ID with title, status, source, material dependencies or acceptance evidence, and links. Never let a suggestion live only in a log, review, report, handoff, transcript or quick context.
- Create no other roadmap, backlog, TODO, proposed-change or next-steps list. A scoped plan may exist when the task needs one, citing the tracker's item IDs; newly discovered future work goes into the canonical tracker, not the plan.
- The tracker is a shared record (B5, W5). If you cannot update it safely, stage one exact pending insertion, link it from your log, and do not create a substitute roadmap; reconcile it before claiming handoff complete. Delegated helpers return proposed rows to the coordinating writer unless a single tracker writer is explicitly designated.
- Give important deliverables and authority files individual index rows, even inside a covered folder, in the established index or its linked topic index: path, purpose, classification (Authority, Current, Deliverable, Evidence, Reference, Backlog, Incoming, History, Scratch), coverage and existence. Folder coverage suffices for routine files and scratch; add a folder row only when navigation does not cover it, and no row per generated file. When superseding a file, mark the old row History and point it at the new one.
- Update quick context only when direction, verified state, decisions or next steps change. Keep one current-state section, replacing stale lines rather than prepending dated paragraphs; move chronology to session/history records; aim for about 12 KB without dropping active decisions, boundaries or evidence links (`--orient` flags size and out-of-order header updates; flags are advisory). While a build or release candidate is in flight, quick context lists the item IDs it already contains.
- Keep one session-index row per session, created with the log. `--session-index` (`-SessionIndex`) lists missing rows and dead links and proposes rows; paste only checked rows, under W5.

## B7. If you cannot save

Read-only limits task files, not your session log, unless the owner expressly prohibits all project writes. If you cannot save to the project, give the session entry as a copyable checkpoint (session/turn, request, outcome, changed files, reason). A sandbox copy does not prove delivery.
