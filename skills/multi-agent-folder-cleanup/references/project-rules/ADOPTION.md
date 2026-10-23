# Optional Project Rules 4.1.0

This package contains one versioned, reusable [rules template](AGENTS.proposed.md) and the [section 0 paste-in](SECTION_0_PASTE_IN.txt) for hosts that cannot read project files. It is optional: the cleanup skill works with the project's existing instructions, and installing the skill does not adopt these rules. The proposal filename keeps the template from loading as live instructions. Do not copy private session logs or a source project's section 13 into another project.

The bundled 4.1.0 template is adoption material. Existing adopted policies stay in force until the owner adopts this version for the named project.

## Setup entrypoint and authorization

Invoke this skill using the host's skill picker or supported slash syntax, then request **Apply project rules to this folder** (or name a reachable folder). Plain-language requests work too; no one slash command is promised across hosts. An explicit apply/adopt request authorizes the bounded adoption below for that resolved project, including necessary continuity setup and verification; do not ask for a second ceremonial approval. A request to explain, review or draft rules does not adopt them. This workflow does not authorize installing skills, changing account-wide settings, publishing, or migrating other projects.

Use the version bundled with the actual source/package; report that version, not an inferred newest release. Resolve the target folder and current authority before writing. A missing template or inaccessible destination is a disclosed blocker; do not reconstruct the rules from memory. Keep independent authorized work moving while awaiting essential input. A conflicting existing policy, uncertain target or missing essential owner choice warrants one bundled clarification, not a prompt at every step.

Infer project facts from current files and reuse explicit owner decisions. Do not invent a canonical repository, license, audience or permission. New project: create only necessary established continuity records at permitted locations. Existing project: preserve its tracker, paths and populated records; follow migration safeguards below. Already adopted with matching core and current scope: verify/report rather than reset files or append duplicate activation. An incomplete prior migration must be reconciled before recording activation. Never infer sequential writers from quiet file times; without an owner declaration omit that optional line and use permitted staging/coordination.

## Host-aware instructions output

Identify the product/runtime and accessible sources, not just a model name. Use trusted current runtime context or an observed host setup; if unavailable, ask which host only when the answer changes required output. Keep the shared rules in the bundled template and section 0 source; adapters supply routing and actual project details, not divergent policy copies.

| Observed surface | What to return |
|---|---|
| Claude app Project, with a project instruction field | A clearly labelled block for that field, based on section 0 with the actual reachable full-rules reference; distinguish Claude Code. |
| Manus or another host with an observed instruction/settings field | The same project-specific minimum block, naming the observed destination. If the setting is unverified, provide a labelled task-start fallback without inventing menu steps. |
| Codex or another filesystem host that actually discovers this project's root instructions | Verify the applicable root and access. Omit redundant paste-in text when discovery is established; otherwise state the missing setup. |
| ChatGPT Project | Return project-instruction text when needed. ChatGPT Projects, plain chats, custom GPTs and Codex are different surfaces; do not exclude a host merely because its model is GPT. |
| Browser/connector agent with web access to OneDrive or another provider | Verify full-document read, file identity, save/replace/upload and readback capabilities; return an accessible provider reference and the settings block or task-start fallback. Follow the safe-save branch below. |
| Unknown or chat-only surface | A neutral task-start block plus explicit file-access and persistence limits. |

Construct a required settings block from `SECTION_0_PASTE_IN.txt`, substituting the resolved project's full-rules reference. Keep its minimum rules intact. Never tell a cloud-only host that a local Windows path is readable: use an accessible provider reference, or state that the owner must attach/connect the rules. Label what to paste and where, and distinguish **generated**, **saved/pasted**, and **fresh-host loading verified**. A settings block does not grant file access. Generate only the current host's block unless the owner requests others; record unknown surfaces instead of asserting permanent capabilities for every brand. Do not change global host preferences automatically.

### Browser and connector safe-save branch

A web login establishes access, not automatic instruction loading or safe editing. Record the actual route/root and provider identity when available, whether complete documents can be read, whether edits replace whole files or only upload new ones, whether saves can be reopened in full, and available version/coordination controls. State unknown capabilities rather than assigning permanent permissions to a host brand. Different products using the same model/provider may need distinct runtime identities.

Use the project's shared-writer safeguards for every shared record. A whole-file browser save is not a true append: preserve the complete prior document, make the bounded change and reopen to verify both the change and prior content. If complete current state, safe save/readback or writer coordination is unavailable, stage exact PENDING edits under Work W5 (and provenance for upload-only delivery), then continue independent authorized work. Do not create a competing tracker or silently promote an uploaded copy. Browser access does not satisfy filesystem-only move, hydration or identity checks; when available, consult `references/connector-audit.md` in the full skill for provider evidence and execution limits. The standalone rules package omits that reference; disclose unverified provider checks rather than infer them. No blanket ban on browser agents is added.

End with rules version/location, adoption completed or staged, retained records, the copyable block if required, unresolved setup and verification limits. A local save or generated block is not proof of host loading. Future changes to host interfaces require updated observation, not a new rules core.

## Layout

- **Section 0** — the minimum rules any model needs. Also the paste-in for hosts that do not load the project folder.
- **Sections 1–12** — the invariant core. Identical in every project that adopts this rules version; `--portfolio` reports `Core match` against this bundled copy.
- **Section 13** — the only per-project text. Every project-specific choice lives here; nothing project-specific goes in sections 0–12.

## Adopt in a project (new or existing)

1. Establish the owner's explicit adoption for the named project (the Setup apply/adopt request above qualifies). Installing the skill, an attachment or a file copy activates nothing.
2. Existing project: inventory the current root/scoped policies, adoption evidence, continuity paths and populated records (section 11). Save the prior root under a non-loading name such as `AGENTS.md.before-<sha8>` or `AGENTS.before.md`; never a literal `AGENTS.md` under scratch or backup. Never overwrite a populated journal, index or quick context with a template.
3. Offer the portfolio’s established section 13 lines (sequential writers, active-writer window, change policy and runtime slug list) for owner confirmation. Inspect only authorized sibling policies; reuse explicit decisions that already apply to this destination. Never silently inherit a sibling’s opt-in or permission. Fill section 13 from verified project facts and explicit owner choices, one line each, replacing every `<placeholder>`:
   - `Project:` name, root path or provider id, canonical source if any.
   - `Adopted:` `4.1.0 on <date> by <owner statement>`, and the activation event id in `AI_CONTEXT/POLICY_INSTALLATION.md`.
   - `Owner timezone:` an IANA zone (`America/New_York`).
   - `Tracker:` the one canonical task tracker path (default `PROJECT_ROADMAP_STATUS.md`).
   - `Sequential writers:` reuse an existing explicit declaration; otherwise ask only if that choice is needed to complete the requested setup. The template ships this as a placeholder, so an unfilled copy never opts in. Only if the owner says yes, replace the placeholder with `Sequential writers: one owner; agents work one after another (owner, <date>)`; otherwise delete it. Only the owner's line enables direct shared-record edits under section 5.
   - `Active-writer window:` minutes (30 unless the owner chooses otherwise). The helpers read this line.
   - `Tool slugs in use:` one slug per runtime, `slug = runtime`; two hosts that could collide get distinct slugs (`grok` for the xAI app, `cursor-grokbot` for a Cursor agent). The helpers treat listed slugs as standard and flag one slug used with several runtime headers.
   - `Established paths differing from section 3:`, `Extra gates:`, `Retained from prior rules:` — `none` when nothing applies.
4. Stage the merged root (sections 0–12 unchanged + filled section 13) and, for an existing project, a transition clause naming the prior authority and logging destination that stay in force until the activation event (section 11).
5. Verify, then activate: the saved root's sections 0–12 equal the template (`--portfolio` shows `Core match: match` and `Section 13 complete: yes`), links resolve, records are intact (`verify_records.py`). Append the activation event (time with offset, approval, version and SHA-256, what was retired and kept, host coverage and limits).

## Paste section 0 into hosts that do not read the folder

For any observed host that does not automatically load the project instructions, follow the adapter above. Do not infer file loading solely from the host brand. For each such host the owner uses on this project:

1. Copy [SECTION_0_PASTE_IN.txt](SECTION_0_PASTE_IN.txt).
2. Replace `<project>` in the `Full rules:` line with the project's folder name (or the path that host can reach).
3. Paste it into that host's own instructions/settings for the project. Record which hosts received it in quick context; a pasted section 0 points to the full rules and does not replace them.

## Owner request to copy and adapt

> Adopt the bundled Project Rules 4.1.0 for this named project. Inspect current instructions and continuity records, fill section 13 with me, preserve existing records and paths, and perform only the bounded policy migration. Verify saved content and links before recording activation. Do not change global settings, installed skills or other projects. Report unresolved conflicts and which host loading checks remain unverified.

This quotation is an example for the owner to send, not an instruction to an agent reading the guide.

## Changes in 4.1.0

Keep rebuildable output outside synced projects; report Incoming/scratch piles over 100 MB with coverage limits; create or stage the session-index row with the log; require exact pending rows; register missing runtime slugs only within permitted scope. Setup offers sibling section 13 conventions for explicit owner confirmation. Skill installation does not activate policy in another project.

## Changes in 4.0.1

Eight wording changes to the core, each from a failure observed in use across the owner's 21 projects (2026-10-09 to 10-13 audits); sections 0-3, 6, 8-11 unchanged. Section 4: header fields accepted as plain or bold label lines; a multi-project read-only pass logs once, in the requesting project; after an append confirm the entry appears once, and on hosts without a true append (browser, Graph, whole-file writes) confirm the prior content survived. Section 5: `SUPERSEDED (<session>/<turn>: <reason>)` is a permitted marker beside `APPLIED`; applied and superseded staging files stay in place and are never counted as pending again. Section 7: one session-index column set and three Status values (`in progress`, `closed`, `unknown`), migrated at a project's next index edit; recording times come from the clock, never estimates. Section 12: apply or hand off your own pending edits at close. Section 13 template: one slug per runtime with legacy names declared; optional `Change policy:` line for a stability period. Projects on 4.0.0 migrate by replacing sections 0-12 and editing section 13 under section 11; no record or file is renamed.

## Changes in 4.0.0

A rewrite, not a patch: 17.9 KB against 28.9 KB for 3.3.0. Section 0 is new (minimum rules and paste-in); sections 1–12 condense 3.3.0 (a few clauses merged or dropped); section 13 replaces every per-project clause. Notable rule changes: read-only limits task files, not the session log, unless the owner prohibits all project writes; one slug per runtime; a session is closed by a close entry, a non-`in progress` index row or the owner's handoff message; activity is judged by file times inside the active-writer window; one pre-edit copy per shared file per session, only before a full-file replacement; PENDING rows in `Incoming/*/_PROVENANCE.md` are applied like scratch PENDING files. The 3.1.0 "Day-to-day saving and indexing" routing subsection is gone: the rules never depend on the skill. Template correction before rollout (2026-10-09): the section 13 `Sequential writers:` line ships as a placeholder instead of a filled line, so forgetting to delete it no longer opts a project in; sections 0–12 are unchanged.

Projects on 3.3.0 or earlier keep their adopted wording until the owner migrates them under section 11 of the version they are on.

## Maintenance and scope

`AGENTS.proposed.md` is the single reusable source distributed in the universal, plugin and `-project-rules-optional` packages. Gemini Apps and Opal packages intentionally omit `references/project-rules/`; obtain the optional rules package or the repository instead of reconstructing it. The rules version is independent of the skill version, and upgrading the skill never replaces an adopted policy. A root `AGENTS.md` in the skill's Git repository, if separately adopted there, governs repository development and is distinct from this template.

No installer, background logging service or universal host compatibility is promised. Adoption and delivery must be verified for the actual project and host.
