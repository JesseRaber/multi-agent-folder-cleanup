# multi-agent-folder-cleanup 1.7.1

Status: released 2026-10-09.

Aligns the skill with Project Rules 4.0.0 (register R227–R233, R235; R234 skill-size audit not included). Independently reviewed by Antigravity before release; its seven findings are fixed here.

## Optional Project Rules 4.0.0

The bundled template is now Project Rules 4.0.0: section 0 (the minimum rules any model needs), the invariant core in sections 1–12 and a per-project section 13. `SECTION_0_PASTE_IN.txt` is the text the owner pastes into hosts that never read the project folder. `ADOPTION.md` walks through filling section 13. Projects on 3.3.0 or earlier keep their wording until the owner migrates them.

## Work mode

- Read-only limits task files, not your session log, unless the owner prohibits all project writes.
- One tool slug per runtime; a different runtime never shares one.
- One pre-edit copy per shared file per session, only before a full-file replacement; read-back after every shared edit.
- Leftover PENDING rows in `Incoming/*/_PROVENANCE.md` are applied like scratch pending files.
- Windows PowerShell 5.1: never `>>` or `Set-Content`/`Out-File` without UTF-8 on a shared record; change only your own line.

## Helpers

- `--orient`: closed sessions are never listed as possibly active; activity uses file times; the window used is printed (from the `Active-writer window:` line when present); provenance PENDING count; slug/runtime collisions; PowerShell 5.1 warning.
- `--session-index`: slugs declared in `Tool slugs in use:` are standard; one slug with several runtime headers is listed.
- `--pending`: lists provenance PENDING lines.
- `--portfolio`: core match over sections 0–12; `Section 13 complete` column.
- `verify_records.py`: flags NUL bytes, UTF-16 segments and mis-decoded UTF-16 line breaks.
- `audit_folder.ps1` no longer depends on `Get-FileHash`, which fails when Windows PowerShell 5.1 is started from PowerShell 7.
- A session that was closed and then resumed is treated as open; only its latest turn decides.

The bundled section 13 template ships the `Sequential writers:` line as a placeholder, so an unfilled copy never opts a project in.
