# multi-agent-folder-cleanup 1.8.1

Patch release: the bundled Project Rules template moves to 4.0.1, the helpers fix the false positives and parsing gaps found in the October 2026 audits, and the install guides route Work-mode reads correctly. No mode, protocol or helper interface changes; all packages keep their layout.

## Project Rules 4.0.1 (bundled template)

Eight wording changes to the reusable core, each from a failure observed in use across a 21-project portfolio; sections 0-3, 6 and 8-11 are unchanged, so the section 0 paste-in for hosts that cannot read project files is unchanged too.

- Section 4: header fields may be plain or bold label lines; a read-only pass across several projects logs once, in the project it was requested from; after an append, confirm the entry appears once, and on hosts without a true append (browser, Graph, whole-file writes) confirm the prior content survived.
- Section 5: `SUPERSEDED (<session>/<turn>: <reason>)` is a permitted staging marker beside `APPLIED`; applied and superseded staging files stay in place and are never counted as pending again.
- Section 7: one session-index column set (`Start | Last activity | Session ID | Tool | Topic | Latest outcome | Status | Link`) and three Status values (`in progress`, `closed`, `unknown`), adopted by each project at its next index edit; recording times come from the system clock, never estimates.
- Section 12: apply or hand off your own pending edits at close.
- Section 13 template: one slug per runtime with legacy names declared; an optional `Change policy:` line for a stability period.

Projects on 4.0.0 migrate by replacing sections 0-12 and editing section 13 under section 11; nothing is renamed. `ADOPTION.md` lists the changes.

## Helpers (Python and PowerShell, same output; read-only)

- `--portfolio` reports `Work routing: yes` for Project Rules 4.0.0 and later (it matched 3.x text only); versions compare numerically so 10.x sorts after 4.x.
- Pending-update counts skip pre-edit copies in `before*` and `backup*` folders and report them on one line.
- `--portfolio` lists quick-context files over 12 KB.
- `verify_records.py` names a split table (`table split: rows continue the table that ended at line N`) and reads link targets with balanced or escaped parentheses, so `doc%20(1).md` and sync-conflict copies no longer produce false broken-link findings.
- `audit_folder.ps1 -Orient -Out` prints the check, `Helper:` and `Generated` lines before the glance section, as Python does.
- Session-log header and outcome labels written in bold (`- **Session ID:** ...`) parse in both helpers.
- Pending `.json` files: keys are matched case-insensitively in Python, as PowerShell already did.
- `--out` root confinement compares case-folded paths on Windows and macOS.

## Install guides, README and manifests

- `INSTALL-universal.md` paste-in: Work mode reads `work-mode.md` (plus `work-mode-baseline.md` below Rules 4.0.0); cleanup modes read `preconditions.md` and `cleanup-principles.md` first. The Custom GPT upload list includes both files.
- All four install guides show the full arrival line `Loaded Multi-Agent Folder Cleanup v1.8.1 (SKILL.md at <path>; helpers <version>)`.
- README names Project Rules 4.0.1, notes that the Gemini Apps and Opal packages omit the rules folder, links the Safety-rules wiki page, summarizes v1.6.2-v1.8.1 and shows the `--orient`, `--session-index` and `--pending` commands.
- Codex and Claude plugin manifests describe Work mode alongside Audit, Plan and Execute.

## Release hygiene

- `packaging/version_files.json` tracks `wiki/Home.md` and `wiki/Changelog-summary.md`; CI checks for stale mentions of the previous version and installs the pinned test dependency.
- Executable bits cleared on two text files; stray comment removed from `.gitattributes`.
- Wiki install table lists the optional rules package; the wiki changelog summary is complete from 1.0.0.

## Packages

Seven archives as in 1.8.0: UNIVERSAL-skill, claude-code-plugin, codex-chatgpt-plugin, microsoft-copilot-agent-only (also for Grok), gemini-apps-only, opal-only, project-rules-optional. `SHA256SUMS.txt` and `BUILD_EVIDENCE.json` are attached.

## Upgrade notes

- Hosts: replace the 1.8.0 install with the matching 1.8.1 archive; keep any backup outside every folder the host scans for skills, and confirm the arrival line reports 1.8.1 in a new conversation.
- Projects: adopting Rules 4.0.1 is a separate owner decision per project; installing the skill adopts nothing.
