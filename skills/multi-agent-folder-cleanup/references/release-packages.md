# Release and candidate packages

Read this only when you build, stage, back up or install a skill or plugin package.

- Candidates go in a named staging area, releases in the release area, superseded packages in History or `_superseded/`. Never keep a same-version candidate beside a release without an unmistakable status label and canonical pointer.
- For human-friendly navigation, keep a short `Release Packages/README.md` pointing to the current published version. After publication, copy the exact published assets and `SHA256SUMS.txt` into one `Release Packages/vX.Y.Z/` folder, verify the copies against the published release before labeling them released, and link the folder from the project index. If copying is unavailable, record the exact release link and reason. Preserve older releases and their evidence; keep drafts and local candidates unmistakably separate, including historically labeled candidates.
- Keep staged and backup packages as ZIP plus `SHA256SUMS`; an extracted copy gets non-loading `SKILL.md`/`AGENTS.md` names.
- When installing into a host, keep the backup of the previous version outside every folder the host scans for skills (hosts such as Codex load `SKILL.md` recursively, so a backup there becomes a second same-name skill). After install, require exactly one `SKILL.md` with that `name:` under the host's skill roots.
- A saved ZIP is not proof of installation; matching files are not proof the host loads them. Confirm the version the host reports in a new session.
