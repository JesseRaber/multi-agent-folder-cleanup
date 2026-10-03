# multi-agent-folder-cleanup 1.5.0 (candidate)

Status: candidate, not released.

## Work mode

The skill now covers day-to-day work, not only cleanup. When an agent saves, names or indexes files in a project folder other models also use, it follows `references/work-mode.md`:

- W1 Arrive with a suggested ~40 KB read budget; required authority/evidence takes precedence; optionally run `--orient`.
- W2 Reuse the established session while writer continuity holds; create a new log for a new chat or uncertain handoff, following project paths.
- W3 Save new files where the next agent will look (deliverables, drafts, incoming material, proposals, never secrets).
- W4 Use format-appropriate provenance; a compact header is a default for standalone Markdown, not code or native documents.
- W5 Coordinate shared edits, then re-read, edit minimally and verify; stage exact pending edits with base digest, anchor/patch and reconciliation outcome.
- W6 Link important deliverables and authority individually; use folder coverage for supporting files. Replace stale quick-context lines while retaining active decisions.
- W7 Hand off at the end of every request.

Before expensive work, Work mode now compares recent session topics/outcomes and reuses prior evidence when the request is already covered. It also defines lifecycle handling for handoffs, pending shared updates and package channels; keeps one maintained quick-context current-state section; and keeps live-loading instruction filenames out of synthetic fixtures.

## Helpers

`--orient` / `-Orient` and `--session-index` / `-SessionIndex` in `audit_folder.py` and `audit_folder.ps1`. Both are read-only. Full audits add lifecycle and credential-risk sections; portfolio output distinguishes empty, managed and unmanaged roots and reports continuity/pending-update signals. `-gemini-apps-only` and `-opal-only` packages carry no scripts, so those hosts use the written steps only.

## Size

Current source bytes: SKILL.md 7,464; work-mode.md 10,337; combined 17,801. These are file sizes, not measured token/runtime savings. Mode-specific references remain loaded only when needed.

## Compatibility

Existing audit CLI flags, report sections, receipts and verify_move behavior are unchanged. Section labels A–G are unchanged; Work mode uses W1–W7.


## Hardening and release checks

Work mode preserves ordinary user-authorized task edits, adopted layouts and explicit read-only boundaries. Helpers distinguish inaccessible/incomplete coverage, disclose duplicate session IDs, and retain timezone and modification-time uncertainty. See the behavioral acceptance pack in `tests/WORK_MODE_ACCEPTANCE.md`.

Before release: refresh upstream, run Ubuntu/Windows CI, review the exact candidate, and retain owner publication approval. Scriptless fixtures are not live host-upload validation; Gemini upload acceptance and cross-model-family checks remain separate evidence. No automatic shared-index writer, separate catalog, or broader rules-template slimming is included; proposed rows and lifecycle states remain review inputs.

Windows validator note (R071): run `python -X utf8 <quick_validate.py> skills/multi-agent-folder-cleanup` with PyYAML in the test environment; this prevents Windows default-encoding errors without changing skill content.
