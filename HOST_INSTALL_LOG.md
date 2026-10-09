# Host install log — multi-agent-folder-cleanup

Append-only. One row per attempt. Never edit an old row; add a `superseded` row instead.
Evidence: `observed` (agent saw it), `user-reported`, or a path to a screenshot / error text.
Earlier install history lives in the owner's project records; rows here start with v1.6.1.

| Date (TZ) | Version | Asset (sha256 first 12) | Host / account | Action | Result | Displayed | Evidence | By |
|---|---|---|---|---|---|---|---|---|
| reported 2026-10-08 (install date unknown) | 1.6.1 | gemini-apps-only (asset unknown; published asset is 3ee4a67333ef) | Gemini Apps | upload | accepted | — | user-reported | owner |
| 2026-10-05 | (pre-1.6.1) | UNIVERSAL-skill | Grok | upload | rejected (`.ps1`) | — | owner upload test, documented in project records | owner |
| 2026-10-05 | (pre-1.6.1) | microsoft-copilot-agent-only | Grok | upload | accepted | — | owner upload test, documented in project records | owner |
| 2026-10-08 12:43 -04:00 | 1.6.3 | UNIVERSAL-skill (60c4eacf9c5d) | Codex standalone `%USERPROFILE%\.codex\skills` | replace 1.6.1 (backup `_backups\…pre-v1.6.3-20261008-124259`) | installed; 21/21 files match ZIP | Loaded Multi-Agent Folder Cleanup v1.6.3 (…\.codex\skills\multi-agent-folder-cleanup\SKILL.md; helpers 1.6.3) | observed (Claude 818c3a98 install; Codex check: PS 5.1 + pwsh 7 + py `--version` 1.6.3) | Claude |
| 2026-10-08 13:10 -04:00 | 1.6.3 | (plugin cache) | Codex Personal Plugin cache | check | 1.6.3 present | — | reported by Codex install check | Codex |
| 2026-10-08 12:43 -04:00 | 1.6.3 | UNIVERSAL-skill (60c4eacf9c5d) | Antigravity `~/.gemini/config/skills` | replace 1.6.1 (backup `skills_backups/…pre-v1.6.3-20261008-124259`) | installed; 21/21 files match ZIP | Loaded Multi-Agent Folder Cleanup v1.6.3 (…\.gemini\config\skills\multi-agent-folder-cleanup\SKILL.md; helpers 1.6.3) | observed (Claude install; Antigravity check: PS + py `--version` 1.6.3) | Claude |
| 2026-10-08 13:22 -04:00 | 1.6.3 | UNIVERSAL-skill (60c4eacf9c5d) | Claude app skill upload (synced) | upload | accepted | — | observed: synced SKILL.md `version: "1.6.3"` in a Claude session | owner |
| 2026-10-08 13:32 -04:00 | 1.6.3 | codex-chatgpt-plugin (ba0d36716406) | ChatGPT web app | upload | accepted | Loaded … v1.6.3 (skill://flora-skills/…; helpers 1.6.3) | host-reported: `audit_folder.py 1.6.3` run in sandbox; first "helpers 1.6.3" was assumed, not observed | owner |
| 2026-10-08 13:26 -04:00 | 1.6.3 | opal-only (fe89138c2842) | Microsoft Opal | import | accepted; 11 references, no scripts (by design) | Loaded … v1.6.3 (skills://multi-agent-folder-cleanup/skill.md; helpers unavailable) | Opal event log; frontmatter not exposed, so `version:` unreadable | owner |
| 2026-10-08 13:26 -04:00 | 1.6.3 | microsoft-copilot-agent-only (2427579009f6) | Grok | upload | accepted | Loaded … v1.6.3 (/root/.grok/server-skills/…; helpers 1.6.3) | host-reported: `version: "1.6.3"`, `audit_folder.py 1.6.3` | owner |
| 2026-10-08 13:32 -04:00 | 1.6.3 | microsoft-copilot-agent-only (2427579009f6) | Microsoft 365 Copilot | upload (first install) | accepted | Loaded … v1.6.3 (/home/oai/skills/appCatalog/…; helpers 1.6.3) | host-reported: `audit_folder.py 1.6.3`; frontmatter `version:` not exposed | owner |
| 2026-10-08 13:46 -04:00 | 1.6.3 | gemini-apps-only (3aae9cff4bf8) | Gemini Spark (agent) | upload | accepted; 11 references, no `audit_folder.py` (by design) | Loaded … v1.6.3 | host-reported: `version: "1.6.3"` | owner |
| 2026-10-08 13:47 -04:00 | 1.6.3 | gemini-apps-only (3aae9cff4bf8) | Gemini chat (regular) | load | rejected: "Custom skills containing executable code or scripts are not supported" | SKILL NOT LOADED | user-reported; owner decision: use Gemini Spark only | owner |
| 2026-10-09 00:24 -04:00 | 1.7.0 candidate (a305c6b, then ea43de7) | UNIVERSAL-skill (ea43de7 build dc58b48d0001 = published asset) | Antigravity `~/.gemini/config/skills` | replace 1.6.3 for the one-host trial (backup `skills_backups/…pre-v1.7.0-candidate-20261009-0016`) | installed; 21/21 files match ZIP | Loaded Multi-Agent Folder Cleanup v1.7.0 (…\.gemini\config\skills\multi-agent-folder-cleanup\SKILL.md; helpers 1.7.0) | observed (Claude 99022649 install; arrival line in Antigravity trial report 9b3ad1d2); final build byte-identical to the v1.7.0 release asset | Claude |
| 2026-10-09 12:57 -04:00 | 1.7.0 | UNIVERSAL-skill (dc58b48d0001) | Codex standalone `%USERPROFILE%\.codex\skills` | replace 1.6.3 (backup `_backups\…pre-v1.7.0-20261009-1256`) | installed; 21/21 files match ZIP; py helpers and ps1 report 1.7.0 | not yet observed in a Codex session | observed (Claude 99022649 T017) | Claude |
| reported 2026-10-09 14:22 -04:00 | 1.7.0 | UNIVERSAL-skill (dc58b48d0001) | Claude app skill upload (synced) | upload | accepted; synced copy 21/21 files byte-identical to the asset | — | observed: synced copy compared in Claude session 99022649 T018 | owner |
| reported 2026-10-09 14:22 -04:00 | 1.7.0 | (plugin cache) | Codex Personal Plugin cache | update | 1.7.0 | — | user-reported | owner |
| reported 2026-10-09 14:22 -04:00 | 1.7.0 | codex-chatgpt-plugin (ffd88ebcb076) | ChatGPT web app | upload | accepted | — | user-reported | owner |
| reported 2026-10-09 14:22 -04:00 | 1.7.0 | microsoft-copilot-agent-only (5d58d782054a) | Microsoft 365 Copilot | upload | accepted | — | user-reported | owner |
| reported 2026-10-09 14:22 -04:00 | 1.7.0 | microsoft-copilot-agent-only (5d58d782054a) | Grok | upload | accepted | — | user-reported | owner |
| reported 2026-10-09 14:22 -04:00 | 1.7.0 | gemini-apps-only (46b446635d1c) | Gemini Spark (agent) | upload | accepted | — | user-reported | owner |
| reported 2026-10-09 14:22 -04:00 | 1.7.0 | opal-only (00ac88c3f6c0) | Microsoft Opal | import | accepted | — | user-reported | owner |
