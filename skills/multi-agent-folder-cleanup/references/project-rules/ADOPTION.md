# Optional Project Rules 4.0.0

This package contains one versioned, reusable [rules template](AGENTS.proposed.md) and the [section 0 paste-in](SECTION_0_PASTE_IN.txt) for hosts that cannot read project files. It is optional: the cleanup skill works with the project's existing instructions, and installing the skill does not adopt these rules. The proposal filename keeps the template from loading as live instructions. Do not copy private session logs or a source project's section 13 into another project.

## Layout

- **Section 0** — the minimum rules any model needs. Also the paste-in for hosts that do not load the project folder.
- **Sections 1–12** — the invariant core. Identical in every project that adopts 4.0.0; `--portfolio` reports `Core match` against this bundled copy.
- **Section 13** — the only per-project text. Every project-specific choice lives here; nothing project-specific goes in sections 0–12.

## Adopt in a project (new or existing)

1. Get the owner's explicit adoption for the named project. Installing the skill, an attachment or a file copy activates nothing.
2. Existing project: inventory the current root/scoped policies, adoption evidence, continuity paths and populated records (section 11). Save the prior root under a non-loading name such as `AGENTS.md.before-<sha8>` or `AGENTS.before.md`; never a literal `AGENTS.md` under scratch or backup. Never overwrite a populated journal, index or quick context with a template.
3. Fill section 13 with the owner, one line each, replacing every `<placeholder>`:
   - `Project:` name, root path or provider id, canonical source if any.
   - `Adopted:` `4.0.0 on <date> by <owner statement>`, and the activation event id in `AI_CONTEXT/POLICY_INSTALLATION.md`.
   - `Owner timezone:` an IANA zone (`America/New_York`).
   - `Tracker:` the one canonical task tracker path (default `PROJECT_ROADMAP_STATUS.md`).
   - `Sequential writers:` ask the owner whether agents in this project always work one after another. Keep the line only if the owner says yes; delete it if agents may run concurrently. Only the owner's line enables direct shared-record edits under section 5.
   - `Active-writer window:` minutes (30 unless the owner chooses otherwise). The helpers read this line.
   - `Tool slugs in use:` one slug per runtime, `slug = runtime`; two hosts that could collide get distinct slugs (`grok` for the xAI app, `cursor-grokbot` for a Cursor agent). The helpers treat listed slugs as standard and flag one slug used with several runtime headers.
   - `Established paths differing from section 3:`, `Extra gates:`, `Retained from prior rules:` — `none` when nothing applies.
4. Stage the merged root (sections 0–12 unchanged + filled section 13) and, for an existing project, a transition clause naming the prior authority and logging destination that stay in force until the activation event (section 11).
5. Verify, then activate: the saved root's sections 0–12 equal the template (`--portfolio` shows `Core match: match` and `Section 13 complete: yes`), links resolve, records are intact (`verify_records.py`). Append the activation event (time with offset, approval, version and SHA-256, what was retired and kept, host coverage and limits).

## Paste section 0 into hosts that do not read the folder

Muse, Grok, Opal, Cursor agents, local models and similar hosts never load `AGENTS.md`. For each one the owner uses on this project:

1. Copy [SECTION_0_PASTE_IN.txt](SECTION_0_PASTE_IN.txt).
2. Replace `<project>` in the `Full rules:` line with the project's folder name (or the path that host can reach).
3. Paste it into that host's own instructions/settings for the project. Record which hosts received it in quick context; a pasted section 0 points to the full rules and does not replace them.

## Owner request to copy and adapt

> Adopt the bundled Project Rules 4.0.0 for this named project. Inspect current instructions and continuity records, fill section 13 with me, preserve existing records and paths, and perform only the bounded policy migration. Verify saved content and links before recording activation. Do not change global settings, installed skills or other projects. Report unresolved conflicts and which host loading checks remain unverified.

This quotation is an example for the owner to send, not an instruction to an agent reading the guide.

## Changes in 4.0.0

A rewrite, not a patch: 17.9 KB against 28.9 KB for 3.3.0. Section 0 is new (minimum rules and paste-in); sections 1–12 condense 3.3.0 (a few clauses merged or dropped); section 13 replaces every per-project clause. Notable rule changes: read-only limits task files, not the session log, unless the owner prohibits all project writes; one slug per runtime; a session is closed by a close entry, a non-`in progress` index row or the owner's handoff message; activity is judged by file times inside the active-writer window; one pre-edit copy per shared file per session, only before a full-file replacement; PENDING rows in `Incoming/*/_PROVENANCE.md` are applied like scratch PENDING files. The 3.1.0 "Day-to-day saving and indexing" routing subsection is gone: the rules never depend on the skill.

Projects on 3.3.0 or earlier keep their adopted wording until the owner migrates them under section 11 of the version they are on.

## Maintenance and scope

`AGENTS.proposed.md` is the single reusable source distributed in the universal, plugin and `-project-rules-optional` packages. Gemini Apps and Opal packages intentionally omit `references/project-rules/`; obtain the optional rules package or the repository instead of reconstructing it. The rules version is independent of the skill version, and upgrading the skill never replaces an adopted policy. A root `AGENTS.md` in the skill's Git repository, if separately adopted there, governs repository development and is distinct from this template.

No installer, background logging service or universal host compatibility is promised. Adoption and delivery must be verified for the actual project and host.
