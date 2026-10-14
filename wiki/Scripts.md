# Read-only folder and record scripts

v1.8.1 ships four helpers under `skills/multi-agent-folder-cleanup/scripts/`. None of them move, copy, or delete the target folder. `verify_move.py` never moves files. `verify_records.py` does not modify the records it checks.

| Script | What it checks | Limit |
|---|---|---|
| `audit_folder.py` | Inventory, duplicates, index coverage, entrypoints, `--orient`, `--session-index`, `--pending`, `--portfolio` | Python cannot see OneDrive placeholder attributes |
| `audit_folder.ps1` | Same audit on Windows, including placeholder hydration | Omitted from the Copilot package because that uploader rejects `.ps1` |
| `verify_move.py` | Review, preflight, baseline, and verify for an approved move map | Refuses sources or targets outside `--root`. A warning remains if `--root` is omitted |
| `verify_records.py` | SHA-256, UTF-8, BOM, line endings, mojibake, relative Markdown links, table damage, NUL/UTF-16 damage, `--compare`, `--expect-sha256` | Cite its output before calling a shared-record edit verified |

On Windows or OneDrive, prefer `audit_folder.ps1`. Elsewhere, record hydration as unverified until checked on Windows. Connector-only access is not an Execute path for moves.

```bash
python skills/multi-agent-folder-cleanup/scripts/audit_folder.py --version
python skills/multi-agent-folder-cleanup/scripts/verify_records.py --version
python skills/multi-agent-folder-cleanup/scripts/verify_records.py path/to/record.md
```

v1.8.0 helper fixes: the Generated line carries the UTC offset; session-log start times with a space before the offset are read as recorded times; `--session-index` lists logs with no header block.

Command details stay in the [README](https://github.com/JesseRaber/multi-agent-folder-cleanup/blob/main/README.md#what-the-scripts-do) and [audit-tools.md](https://github.com/JesseRaber/multi-agent-folder-cleanup/blob/main/skills/multi-agent-folder-cleanup/references/audit-tools.md). The Gemini Apps package carries only `verify_move.py` and `verify_records.py` (no audit helper), and the Opal package has no scripts; say a missing helper is unavailable instead of reconstructing it.

v1.8.1 helper changes: `--portfolio` detects Work routing for Project Rules 4.0.0 and later and lists quick-context files over 12 KB; pending counts skip pre-edit copies in `before*`/`backup*` folders; `verify_records.py` names split tables and reads link targets with balanced parentheses; `audit_folder.ps1 -Orient -Out` prints the same header lines as Python; bold session-log labels parse in both helpers.
