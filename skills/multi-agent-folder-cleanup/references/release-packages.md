# Release and candidate packages

Read this only when you build, stage, back up or install a skill or plugin package.

- Candidates go in a named staging area, releases in the release area, superseded packages in History or `_superseded/`. Never keep a same-version candidate beside a release without an unmistakable status label and canonical pointer.
- Keep staged and backup packages as ZIP plus `SHA256SUMS`; an extracted copy gets non-loading `SKILL.md`/`AGENTS.md` names.
- When installing into a host, keep the backup of the previous version outside every folder the host scans for skills (hosts such as Codex load `SKILL.md` recursively, so a backup there becomes a second same-name skill). After install, require exactly one `SKILL.md` with that `name:` under the host's skill roots.
- Files matching the ZIP are not proof the host loads them: confirm the version the host reports in a new session.
