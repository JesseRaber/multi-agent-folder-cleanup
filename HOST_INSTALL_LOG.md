# Host install log — multi-agent-folder-cleanup

Append-only. One row per attempt. Never edit an old row; add a `superseded` row instead.
Evidence: `observed` (agent saw it), `user-reported`, or a path to a screenshot / error text.
Earlier install history lives in the owner's project records; rows here start with v1.6.1.

| Date (TZ) | Version | Asset (sha256 first 12) | Host / account | Action | Result | Displayed | Evidence | By |
|---|---|---|---|---|---|---|---|---|
| reported 2026-10-08 (install date unknown) | 1.6.1 | gemini-apps-only (asset unknown; published asset is 3ee4a67333ef) | Gemini Apps | upload | accepted | — | user-reported | owner |
| 2026-10-05 | (pre-1.6.1) | UNIVERSAL-skill | Grok | upload | rejected (`.ps1`) | — | owner upload test, documented in project records | owner |
| 2026-10-05 | (pre-1.6.1) | microsoft-copilot-agent-only | Grok | upload | accepted | — | owner upload test, documented in project records | owner |
