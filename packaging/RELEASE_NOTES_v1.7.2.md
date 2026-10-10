# multi-agent-folder-cleanup 1.7.2

Status: candidate, not released.

Patch release: install guidance for host backups (R237) and a smaller Work-mode reference (R234). No helper behavior changes; helpers report 1.7.2.

## Install guidance (R237)

Observed 2026-10-09: Codex loads every `SKILL.md` under `.codex/skills` recursively, so a pre-install backup kept in `.codex/skills/_backups` loaded as a second skill with the same name and shadowed the new version.

- The install guides now have an **Updating an existing install** section: keep the previous version's backup outside every folder the host scans for skills, or rename the backup's `SKILL.md` to a non-loading name such as `SKILL.backup-not-loaded.md`.
- After install, require exactly one `SKILL.md` named `multi-agent-folder-cleanup` under the host's skill roots.
- Files matching the ZIP are not proof the host loads them: restart or refresh the host and confirm the reported version in a new session.
- The Work-mode release-package row carries the same rule; the Copilot guide asks for exactly one listed skill after re-upload.

## Work mode (R234)

`references/work-mode.md` is 22.3 KB instead of 28.6 KB, read by every agent each session. Repetition and explanation that changed no decision were removed; every W1–W7 rule, section and anchor is kept. An independent old-versus-new comparison found 13 rules weakened by the first pass and 5 unintended additions; all were restored or removed before this candidate. The 16 KB target was not pursued further because it would move rules into a second file agents might not open.
