# multi-agent-folder-cleanup 1.6.4

Status: candidate, not released.

This release covers register rows R187–R191. Agents that can only add files (browser uploads, connectors without edit or append) now have a defined minimum: upload into a dated `Incoming/` folder, never a new top-level folder, with a `_PROVENANCE.md` that lists pending index, tracker and session-index rows for the next agent with edit access. `muse` joins the tool slugs, and unlisted tools use their own lowercase name instead of skipping the log. Audit mode adds B5 "Attribute activity": a missing name is not proof of absence, unaccounted changes are findings, and timestamps are converted to the owner's local timezone.

Optional Project Rules move to 3.3.0 with three additive lines (sections 3, 4 and 7). The Gemini Apps and Opal packages do not include `references/project-rules/`, so those hosts get the Work-mode and Audit-mode changes but not the template update; use the `-project-rules-optional` package or the repository for it.

Not included: an `--orient` helper check for unattributed changes (deferred; needs Python and PowerShell parity). R190 overlaps R158/R179; this release adds only the audit guidance, not helper timestamp changes. No host installation is included.
