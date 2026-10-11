# Audit edge cases

Read this when the audit helper flags one of these, or when you inventory by hand. Report each as a finding; Audit mode changes nothing.

## Inventory checks

- **Reparse points.** Every directory symlink or junction under the root, with its target. Their descendants appear in no count. On a synced root, check the provider's view separately before describing them as external — the cloud copy is what other agents index.
- **Case-mismatched references.** An index reference that resolves only through a case-insensitive filesystem, reported apart from resolving links. It breaks for any agent on a case-sensitive platform.
- **Cloud footprint, where the root is synced.** Total bytes as the provider reports them, beside the project-local total. A large gap is a finding in itself.
- **Index coverage.** `--index-coverage INDEX=DIR` lists files directly in a folder that its index never mentions, such as session logs missing from `SESSION_INDEX.md`. Link checks alone cannot see an omission.
- **Startup read set.** The root auto-loaded instruction files plus the read order the project itself declares (README_FIRST or quick-context read lists), or `--entrypoint` in the project's read order. Every session pays this before working; the helper flags a total above the budget (default 40 KB), whole-file reads of large trackers or journals in that order, and `AGENTS.md` size: warning above 16 KB, high above 32 KiB, which Codex truncates silently.
- **Misplaced live-loading names.** `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.cursorrules` and similar inside incoming, history, scratch, backup or skill-copy folders. A host that walks the tree may load them as rules. Literal `AGENTS.md` hits under scratch, backup or before paths are usually W5 pre-edit copies to rename, rather than competing rules.
- **Embedded skill copies.** Every `SKILL.md` and `.skill` package with its declared name and version. Several versions of one skill in a project mean an agent may read the wrong protocol.
- **Orphaned temporary files.** Info-ZIP `zi??????` temp names, Office `~$` locks, `.tmp`/`.partial`/`.crdownload`, and extensionless files holding archive bytes. They are usually left by an interrupted write.
- **Credential-bearing files.** Browser profiles carry `Cookies`, `Login Data`, `Web Data`, `Local State` and account-specific variants such as `Login Data For Account*` — live session state. `.env`, `id_rsa`, `credentials.json`, `.npmrc` carry secrets outright. The script flags these through conservative exact-name and separator-delimited prefix hints. Report their existence and location; never open, stage, copy, or quote their contents, and flag them to the owner before the folder is shared with anyone.
- **Handoff ambiguity.** Group handoff, next-prompt and final-named files by subject. Flag several files that appear current without an explicit canonical pointer or lifecycle metadata; do not select one by ordinal, modified time or `final` alone.
- **Package-channel ambiguity.** Flag candidate, released and superseded packages with similar names in the same discoverable location. Status labels and indexes are evidence; moving them is a separate Plan/Execute action.
- **Pending-update lifecycle.** Locate pending shared/navigation patches (`PENDING_*` and variants such as `pending-*`, any case) and report Pending, Applied, Superseded, Conflicted or Unverifiable only after comparing their exact intended change with the current target. A pending file without a `Status:` first line is a finding.
- **Sync conflict copies.** `name (1).ext`, `name-<COMPUTER>.ext`, case-only name collisions in one folder and, through a connector, same-name siblings with different file ids; also a copy whose original is missing. Report only: never merge, rename or delete them in Audit mode.
- **Unpacked packages and working copies.** Extracted skill or release trees under scratch or backup folders (loadable `SKILL.md`/`AGENTS.md` copies), and repository-shaped folders without `.git` that do not declare the remote and commit or tag they mirror.
- **Continuity folder misuse.** Deliverables, reports and binaries inside `AI_CONTEXT/` (count and size); propose a content folder such as `Research/` or `Proposals/`.

## Confusion sources

- **An append-only journal too large to read.** Past roughly 100 KB, "read the tail" stops being executable through most access routes. Report the size and propose rotation; do not restructure it in Audit mode. A journal already retired (declared legacy or History, under a `History/` path, or superseded by `SESSIONS/` logs under rules 3.0.0 or later) is reported once as "retired legacy journal, N KB", without a new rotation proposal.
- Roadmap language ("we will add X") sitting in a folder named as if it were current state
- Archives whose contents duplicate live files, so both are searchable
- A read-only mirror or vendored checkout that agents keep editing
- Handoff files with no date or ordinal, so "latest" is unknowable
- **An instruction file too large for a host to load.** Codex reads at most 32 KiB of `AGENTS.md` by default and drops the rest without warning, so rules near the end silently disappear for that agent. Flag above 16 KB as a warning (little headroom for project clauses) and above 32 KiB as high. Report the size; propose a shorter file that links to on-demand detail.
- **A startup read set that costs more than the work.** When the required read order totals tens of kilobytes, every agent and every session pays it. Report the measured total; propose a short router plus detail files, never deletion.
- **A live-loading instruction name in a non-governing folder.** A proposed `AGENTS.md` under `Incoming/` can be loaded as rules by a host that walks the tree. Propose a non-loading name such as `AGENTS.proposed.md`.
- **Stale or mixed skill copies inside the project.** Copies at different versions, or a new `SKILL.md` over older scripts, give agents a protocol the helpers do not implement. Compare each with the canonical release and the helper `--version`.
- **An index that omits files that exist.** A session or file index that never mentions existing records tells the next agent they do not exist.

Journal rotation: measure journal size; above the configured threshold (default 100 KB), flag it and propose rotation into dated history plus a short current-tail file. Rotation requires approval and must preserve every entry.
