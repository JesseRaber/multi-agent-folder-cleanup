# multi-agent-folder-cleanup 1.7.0

Status: released 2026-10-09.

A stable release meant to stay installed. It folds the unreleased 1.6.4 candidate (R187–R191) together with the items approved on 2026-10-08 (R030, R195, R197–R199, R201, R203–R209, R211–R215) and the Batch B items R155, R161, R165/R166, R168, R169 and the declaration part of R156.

## For agents working in a shared folder (Work mode)

- **Sequential writers.** When the owner opts a project in with a `Sequential writers:` line (asked once at adoption; off by default), the active agent edits shared records directly with read-back verification instead of staging PENDING files. Multi-operator projects keep staging.
- **Leftover pending files.** One name (`PENDING_<TARGET>.md`, `Status:` first line). The next qualifying writer applies those whose base still matches, verifies them and marks them APPLIED; mismatches are reported as Conflicted.
- **Sync conflict copies.** Shared files are edited in place; no second same-name file in one folder; `(1)` and `-COMPUTER` copies and missing originals are checked at arrival and before the final answer.
- **Cloud connectors.** Every listing states its view and time; files are handled by id; replacements are staged in scratch and carry `Replaces: <old id>`; one file type per shared record; replicas under other providers are declared.
- Add-only agents upload into a dated `Incoming/` folder with `_PROVENANCE.md`; `muse` joins the tool slugs; Audit mode B5 attributes activity (from the 1.6.4 candidate).

## For audits

New report-only guidance for conflict copies, unpacked packages, repository working copies without `.git`, deliverables in `AI_CONTEXT/`, retired journals, the project's declared startup read order and a lower `AGENTS.md` size warning (16 KB). The portfolio template gains a rules matrix.

## Helpers

Both `audit_folder.py` and `audit_folder.ps1`, same output, read-only:

- `--pending` lists leftover pending files and says whether each can still be applied, is already applied, conflicts or cannot be checked.
- `--orient` adds the sequential-writer declaration, the declared read order, changed files no log names, identical-timestamp clusters and sync conflict copies.
- The full audit adds a section for conflict copies, unpacked skill trees, working copies without `.git` and `AI_CONTEXT/` misuse; retired journals are no longer proposed for rotation; `AGENTS.md` over 16 KB is a warning.
- `--portfolio` adds rules version, Work routing, core match and declaration columns, likely replicas and cross-project handoffs.

## Optional Project Rules 3.3.0

Additive lines in sections 3, 4, 5 and 7, including the opt-in `Sequential writers:` rule (off unless the owner adds the line). Gemini Apps and Opal packages do not include `references/project-rules/`.

## Not included

R200 (exact direct-write test, on hold), the mutating `apply_record_patch.py` helper, R196/R210/R216 (actions in other projects). No host installation is included.
