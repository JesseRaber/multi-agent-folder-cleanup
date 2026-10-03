# Work mode — saving and indexing in a shared project folder

Use this when you are doing ordinary project work in a folder that other agents and models also use: creating files, saving results, updating the index, recording the session, handing off. It keeps the folder usable for whoever arrives next. Work mode supports the authorized task without adding a separate approval gate to routine edits. Use Plan/Execute for folder cleanup or reorganization. A task-specific rename or removal already authorized by the user follows that task workflow; discovering clutter does not authorize cleanup. If unrelated folder confusion remains, report it and suggest an Audit.

The project's adopted instructions win. Where they name other paths or formats, use theirs. The defaults below match the bundled Project Rules (`AI_CONTEXT/...`). Reuse equivalent existing locations; do not create competing logs or indexes merely to match these names. Invoking this skill does not adopt the optional rules template. An explicit read-only request prohibits all project writes, including continuity records: return a copyable checkpoint instead.

## W1. Arrive (suggested read budget ~40 KB)

1. Read the root instruction file (`AGENTS.md`, `CLAUDE.md` or the host's equivalent).
2. Read `AI_CONTEXT/PROJECT_QUICK_CONTEXT.md`, then `PROJECT_INDEX.md` only as far as your task needs.
3. When resuming related work, read the relevant session log's last entries and inspect the sessions folder for newer records if the index is stale. Follow required authority and evidence even when that exceeds the suggested budget.
4. If scripts can run, check for other writers and recent changes:

```
python scripts/audit_folder.py --root <project> --orient --session-id <your-id>
pwsh -File scripts/audit_folder.ps1 -Root <project> -Orient -SessionId <your-id>
```

It lists recently active session logs and scratch folders, files changed since the latest session started, and changed files the index never names. Times are local modified times: leads, not proof. Without scripts, use available listings and read the relevant recent logs. With connector-only or partial access, state the coverage limit; do not claim a writer is absent from missing activity signals. Use the helper path in the installed skill, not a presumed project-relative scripts directory.

Before expensive or portfolio-wide work, compare the request with the topic, latest outcome and open work in recent session logs. If the same task is active, coordinate rather than duplicate it. If it is complete, reuse its evidence and inspect only changes or gaps. Record the current request promptly in your own session log; that log is the in-progress signal, so do not create a separate shared claim file.

Treat summaries as leads. Verify anything your task depends on against the actual file.

## W2. Claim your own space

- For a new chat or uncertain writer handoff, create your own log with a generated UUID: `AI_CONTEXT/SESSIONS/YYYY-MM-DD_HHMMSS_<tool>_<short-topic>_<uuid>.md`. Preserve source-session links separately. Within the same established session and writer, append to that log; do not create one per request. Resume after a restart only with established writer continuity, or follow an evidenced transfer under the project policy. If identity is uncertain, start a linked continuation.
- Use the project's established format. Include session ID, start time with timezone when known, writer instance, source-chat identity or unavailable, and coverage start. Record each request/outcome with a stable turn ID; verify previous content is preserved and the entry appears once.
- Keep drafts and temporary work in `AI_CONTEXT/scratch/<your-session-id>/`. Never write in another session's scratch folder.
- If another writer looks active, do your independent work anyway and be extra careful with shared files (W5).

## W3. Save new files where the next agent will look

| What you made | Where it goes |
|---|---|
| Finished deliverable | The project area the index names for that kind of work. No obvious area: the closest existing folder, and say so in the index row. |
| Draft, test output, intermediate data | `AI_CONTEXT/scratch/<your-session-id>/` |
| Material from another model, chat or person, not yet reviewed | `Incoming/` (or the project's inbox), as a dated folder with a short provenance note |
| A newer version of an existing file | Edit the file in place when you are authorized to change it. Otherwise save beside it as a proposal and say what it would replace. Never create `final_v2_REAL` siblings. |
| A proposed rule or instruction file | A non-loading name such as `AGENTS.proposed.md`, never a live instruction filename |
| Candidate or release package | Keep candidates in a clearly named candidate/staging area, released artifacts in the release area, and superseded packages in History or `_superseded/`. Never place a same-version candidate beside a released package without an unmistakable status label and canonical pointer. |
| Credentials and tokens | Do not copy into task outputs or continuity records |
| Customer-sensitive material needed for the task | Use only the authorized project location and access scope; omit unnecessary private content from logs and indexes |

Naming:

- Follow established naming and native formats. For a new standalone Markdown report without a convention, use `YYYY-MM-DD_<short-topic>.md`. Add the tool name only when several models produce parallel versions of the same thing.
- Use plain words, hyphens or underscores, and no characters that break on Windows, OneDrive or URLs (`: * ? " < > |`, trailing dots or spaces).
- Keep paths short and check the actual host/application limits; do not treat a single character count as a universal limit.

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

1. Re-read the file immediately before writing.
2. Make the smallest exact edit (a bounded replace or a true append). Never rebuild a whole shared file from an older or truncated copy.
3. Re-read after saving and confirm the edit is there exactly once and everything else is unchanged.
4. If the file changed since you read it, merge your change onto the new version. If you can't do that safely, save the exact intended edit in your scratch folder, mark it PENDING in your session log and move on.

A pending edit must be concrete enough for a later writer to apply without guessing:

```text
Status: PENDING
Target: <project-relative path>
Base: <version or SHA-256 of the complete original; unavailable if unsupported>
Edit: <exact old and new text, insertion anchor plus text, or a linked patch>
Reason: <coordination/access/conflict limitation>
Session/turn: <source ID and turn>
Reconcile: <condition required before applying>
```

When coordination becomes available, read the current target, preserve intervening contributions, rebase the proposed edit and verify the save. Append the applied/superseded/conflicted outcome to the source session record. A staged edit is not an applied update, and an old hash never authorizes overwriting newer work.

Reconcile pending edits into exactly one of: **Pending**, **Applied**, **Superseded**, **Conflicted** or **Unverifiable**. Compare the current target with the exact proposed change; filename age and the old base hash are not enough. Retain the source-session link and outcome even after the staged payload is no longer actionable.

## W6. Index what matters, not everything

- Give important deliverables and authority/instruction files individual discoverable links, even inside a covered folder. Use the established index or its linked topic index. One line: path, purpose, classification (Authority, Current, Deliverable, Evidence, Reference, Backlog, Incoming, History, Scratch), coverage and existence.
- Folder coverage is enough for routine supporting files and scratch descendants. Add a folder row only when existing navigation does not cover it. Do not add a row for every generated file.
- Update the row when you supersede a file: mark the old one History/superseded and point it at the new one.
- Update quick context only when direction, verified state, decisions or next steps changed. Maintain one clearly labeled current-state section: replace stale lines there instead of prepending dated paragraphs. Move useful chronology to session/history records. Aim for about 12 KB (`--orient` flags size and repeated/out-of-order header updates), while retaining active decisions, boundaries and evidence links. Size flags are advisory, not permission to discard context.
- Keep one session-index row per session. If scripts can run, `--session-index` (`-SessionIndex`) lists missing rows and links to logs that no longer exist, and prints proposed rows. Paste only the rows you checked, using W5.

## W7. Hand off at the end of every request

Before each final answer, so the work survives if the chat stops here:

- [ ] Session log entry: request, what you did, files changed, what's verified, what's open
- [ ] Deliverables are saved in the authorized place and format with appropriate provenance (W3–W4)
- [ ] Index row added or updated for new deliverables (W6)
- [ ] Quick context updated if the state changed
- [ ] Session-index row created at session creation or refreshed for a significant outcome/close; routine turns need only their log entry
- [ ] Next step written where the next agent will see it

Mark deferred navigation explicitly and link its exact pending edit. If you cannot save to the project, give the owed session entry as a copyable checkpoint, including session/turn, request, outcome, changed files and reason. A local sandbox copy does not prove delivery to the project destination.

## Stop and switch modes when

- the task is folder cleanup/reorganization involving existing files → Plan (then Execute within the approved scope); ordinary authorized task edits stay in their task workflow;
- you find competing copies, conflicting authority or a stale index you can't fix with one small factual edit → report it and suggest an Audit;
- a shared-record conflict can't be merged → leave it PENDING (W5) and tell the user.
