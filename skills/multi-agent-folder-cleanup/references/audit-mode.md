# Audit mode

Read-only. Read [preconditions.md](preconditions.md) first. For a fast, low-token pass run the helper with `--brief` or `--out` (see [audit-tools.md](audit-tools.md)) and read the **Findings at a glance** block before opening detail sections.

## B. Audit mode

Read-only. Produce evidence, not opinions.

### B1. Inventory

Run the bundled audit script, or gather equivalently:

- Full file list with size and modified time
- Depth and per-folder file counts
- Empty directories, listed separately as cosmetic findings rather than automatic removal targets
- Archives (`.zip`, `.7z`, `.tar*`, `.rar`) with size and date
- Maximum depth (reported by the audit script); note unusually large files from the inventory when they matter
- Path lengths, flagging anything over 240 characters, measured against the real host path. When the folder is mounted under another prefix (a cloud sandbox, WSL, a device bridge), pass `--host-root` with its Windows/OneDrive path; the mount prefix is not the length OneDrive enforces.
- Duplicate candidates: same name across folders; with `--hash-files`, identical-content groups **and** the inverse — one name resolving to several different documents
- Index/link check: every Markdown link target in each named index that does not resolve, reported as a broken link. Report unresolved backticked filename/path references separately as review items, because examples and historical labels may be intentionally non-live. `--index-path` is repeatable; an index named in navigation but absent on disk is itself a finding.
- **Reparse points.** Every directory symlink or junction under the root, with its target. Their descendants appear in no count. On a synced root, check the provider's view separately before describing them as external — the cloud copy is what other agents index.
- **Case-mismatched references.** An index reference that resolves only through a case-insensitive filesystem, reported apart from resolving links. It breaks for any agent on a case-sensitive platform.
- **Cloud footprint, where the root is synced.** Total bytes as the provider reports them, beside the project-local total. A large gap is a finding in itself.
- **Index coverage.** `--index-coverage INDEX=DIR` lists files directly in a folder that its index never mentions, such as session logs missing from `SESSION_INDEX.md`. Link checks alone cannot see an omission.
- **Startup read set.** The root auto-loaded instruction files plus the declared entrypoints (`--entrypoint`, in the project's read order). Every session pays this before working; the helper flags a total above the budget (default 40 KB) and any `AGENTS.md` over 32 KiB, which Codex truncates silently.
- **Misplaced live-loading names.** `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.cursorrules` and similar inside incoming, history, scratch, backup or skill-copy folders. A host that walks the tree may load them as rules.
- **Embedded skill copies.** Every `SKILL.md` and `.skill` package with its declared name and version. Several versions of one skill in a project mean an agent may read the wrong protocol.
- **Orphaned temporary files.** Info-ZIP `zi??????` temp names, Office `~$` locks, `.tmp`/`.partial`/`.crdownload`, and extensionless files holding archive bytes. They are usually left by an interrupted write.
- **Credential-bearing files.** Browser profiles carry `Cookies`, `Login Data`, `Web Data`, `Local State` and account-specific variants such as `Login Data For Account*` — live session state. `.env`, `id_rsa`, `credentials.json`, `.npmrc` carry secrets outright. The script flags these through conservative exact-name and separator-delimited prefix hints. Report their existence and location; never open, stage, copy, or quote their contents, and flag them to the owner before the folder is shared with anyone.
- **Handoff ambiguity.** Group handoff, next-prompt and final-named files by subject. Flag several files that appear current without an explicit canonical pointer or lifecycle metadata; do not select one by ordinal, modified time or `final` alone.
- **Package-channel ambiguity.** Flag candidate, released and superseded packages with similar names in the same discoverable location. Status labels and indexes are evidence; moving them is a separate Plan/Execute action.
- **Pending-update lifecycle.** Locate pending shared/navigation patches and report Pending, Applied, Superseded, Conflicted or Unverifiable only after comparing their exact intended change with the current target.

**Noise control.** Generated machine state — browser profiles, caches, `__pycache__`, `node_modules`, `.git` internals, build output — routinely outnumbers real documents 3:1 and will drown every detail section. In one audited folder, 1,090 of 1,409 files (77%) were a dead Chrome/Edge profile dump, and the duplicate-name section returned 122 copies of `LOCK` before it reached a single document.

Run `--suggest-excludes` first to see the noise clusters, confirm them, then re-run with `--exclude`. Recurring names collapse to one pattern (`**/__pycache__/**`), and Python environments — `pyvenv.cfg` or three or more `*.dist-info` folders, including `pip --target` installs — are reported as one cluster. On very large roots add `--prune-noise` so high-confidence generated state is listed but not walked, and `--max-seconds` when the shell has a time limit; both are disclosed as coverage gaps. Excluded files are still counted and reported by pattern, and the report must say how many were excluded and that they were not classified. Never silently drop them from the totals.

Noise is **not** a deletion target. Leave it in place or propose an appropriate generated-state location; do not classify it as historical evidence. Moves and removals still need their own approved paths.

### B2. Verify claims against artifacts

For each document that asserts a completed state:

- Does the output it describes actually exist at the stated path?
- Is its modified date consistent with the work it claims?
- Does a later document contradict it?

For any source described as consolidated, merged or retired, map every actionable item to a canonical tracker ID before accepting that claim. Before reporting an apparent missing item, search current-state evidence and relevant history for proof that it was completed or superseded. Record unmapped, completed, superseded and unverifiable items separately so a stale source does not create either lost work or a false gap.

Record each as **verified**, **contradicted**, or **unverifiable**. Never upgrade "unverifiable" to "current".

For each material conclusion, record a compact claim table: `Claim`, `State` (`Documented`, `Observed`, `Inferred` or `Unknown`), `Evidence`, `Scope/date`, and `What would verify it`. `Observed` means directly inspected in the stated scope; it does not mean provider-wide or current beyond the observation time. Repeated documentary claims remain `Documented` until independently checked.

A stale index is not only one that points at missing paths. Check the inverse too: **does the index or manifest omit folders that exist?** A root-level `PROJECT_FOLDER_MANIFEST.csv` with 1,282 rows and an authoritative name that contains zero rows for the four most recent working folders will convince an agent those folders are not part of the project. Record it as **contradicted by filesystem state**, with the specific folder names that are missing.

### B3. Classify

Assign every substantive file to one of the eight buckets in [cleanup-principles.md](cleanup-principles.md#classify-each-substantive-file-once) ("Classify each substantive file once"). Produce a table: path → bucket → evidence for the call. Files you cannot classify go in a short "needs owner decision" list rather than a guess. Files excluded by `--exclude` are reported as bucket 8 by pattern, not classified individually — say so.

### B4. Name the confusion sources

The point of the audit. Typical findings, in rough order of damage:

- Two or more documents that each look authoritative and disagree
- An index pointing at paths that no longer exist
- **Entrypoints the folder's own instructions require, that do not exist.** Read every instruction file — including app-side or tool-side project instructions the owner has configured outside the folder — and check that each file it tells an agent to read is actually on disk. A folder whose instructions open with "first read `README_FIRST.md`, `PROJECT_ROADMAP_STATUS.md` and `CHAT_INDEX.md`" when none of the three exists sends every agent into a guess on its first move. This outranks most duplicate problems: a duplicate makes an agent pick wrong, a missing entrypoint makes it pick blind.
- **No discoverable adopted project guidance.** Distinguish absent files from missing adoption evidence or inaccessible app settings. A README alone does not prove either adoption or lack of rules. Report the available guidance, authority evidence and limitations; do not invent external instructions.
- **One filename, several different documents.** The inverse of a duplicate, and more dangerous: identical copies are at least interchangeable, whereas six different `research_report.md` files mean any citation by filename alone is ambiguous and any grep returns the wrong one. `--hash-files` reports this separately from identical-content groups.
- **A companion root whose status document names a different root as active.** Two roots, one filename, opposite claims, and nothing inside either one that reveals the conflict. Report which root each declares active, whether the companion has any entrypoints at all, and which one org-wide search reaches first.
- **An append-only journal too large to read.** Past roughly 100 KB, "read the tail" stops being executable through most access routes. Report the size and propose rotation; do not restructure it in Audit mode.
- Roadmap language ("we will add X") sitting in a folder named as if it were current state
- Archives whose contents duplicate live files, so both are searchable
- A read-only mirror or vendored checkout that agents keep editing
- Handoff files with no date or ordinal, so "latest" is unknowable
- **An instruction file too large for a host to load.** Codex reads at most 32 KiB of `AGENTS.md` by default and drops the rest without warning, so rules near the end silently disappear for that agent. Report the size; propose a shorter file that links to on-demand detail.
- **A startup read set that costs more than the work.** When the required read order totals tens of kilobytes, every agent and every session pays it. Report the measured total; propose a short router plus detail files, never deletion.
- **A live-loading instruction name in a non-governing folder.** A proposed `AGENTS.md` under `Incoming/` can be loaded as rules by a host that walks the tree. Propose a non-loading name such as `AGENTS.proposed.md`.
- **Stale or mixed skill copies inside the project.** Copies at different versions, or a new `SKILL.md` over older scripts, give agents a protocol the helpers do not implement. Compare each with the canonical release and the helper `--version`.
- **An index that omits files that exist.** A session or file index that never mentions existing records tells the next agent they do not exist.

Stop here in Audit mode. Do not create navigation files. Do not move anything. The one exception is a journal entry the folder's own instructions require (see A5 in [preconditions.md](preconditions.md)) — that is the owner's directive, and the report must state it was the only write.

## G. Audit report format

**Audit report:**

```
# Folder Audit — <root>
## Access
<route used (mounted path | connector | web share), whether the audit script
 ran, and — if it did not — which checks are therefore unavailable>
## Outcome
<2-4 bullets: the actual state, plainly>
## Claim table
<material claim → Documented/Observed/Inferred/Unknown → evidence → scope/date → what would verify it>
## Other roots
<each companion/mirror root, what it claims is active, whether it carries
 entrypoints — or "none found", which is also a result>
## What confuses agents
<ranked findings with file paths as evidence>
## Classification
<table: path → bucket → evidence>
## Coverage disclosure
<what was read in full, what was classified-by-metadata, how many files
 were excluded by pattern and therefore not classified at all>
## Needs owner decision
<short list>
## Limitations
<what could not be verified and why — including service state on OneDrive/
 SharePoint, unopened archives, roots not connected to this session, and
 concurrent writers that make hashes point-in-time only>
```
