# Full Cleanup Protocol

Contents:
- [A. Preconditions](#a-preconditions)
- [B. Audit mode](#b-audit-mode)
- [C. Plan mode](#c-plan-mode)
- [D. Execute mode](#d-execute-mode)
- [E. Verification block](#e-verification-block)
- [F. Failure recovery](#f-failure-recovery)
- [G. Report formats](#g-report-formats)

---

## A. Preconditions

Before any mode:

1. **Confirm the root.** One absolute path. If the user names a folder loosely ("the project folder"), echo the resolved path and continue only once it matches.
2. **Read instruction files.** Root and nested `AGENTS.md` / `CLAUDE.md` / `copilot-instructions.md` / `README.md` / `README_FIRST.md`. Summarize what they require. Log conflicts; resolve none unilaterally. Instructions configured in the owner's app or IDE govern the folder just as much as a file in it — read those too, and note when they are the *only* place guidance lives. Instruction files are protected by default. A demonstrably stale factual path, count, status, or caution may be corrected only through a separately proposed and explicitly approved minimal patch; never fold behavioral-rule changes into cleanup.
3. **Note the storage substrate and the access route separately.** Substrate: local disk, OneDrive/SharePoint-synced, NAS/SMB share, or a mix — this drives the hydration and path-length checks later. Route: a mounted filesystem path, or a connector/API/web share. They are independent, and only the first can run the audit scripts or any Execute step. If the root is synced, expect a local view and a cloud view that do not agree about reparse points; note which one you have. If the only route is a connector, say so in the report's opening lines and use the degraded inventory in SKILL.md §3.
3a. **Enumerate the other roots.** Ask whether a companion, mirror, or predecessor root exists — a team site beside a personal drive, a NAS copy, an old share. If one does, record for each root: whether it carries the required entrypoints, what its status document claims is active, and which root a tool-driven search reaches first. Cross-root contradictions outrank in-tree duplicates and are invisible from inside either root.
4. **Note who else writes here.** Other agents, sync clients, scheduled jobs. Concurrent writers make hash verification unreliable — say so if present.
5. **Check for a logging or journaling requirement.** Some folders carry an owner directive to append an entry to an activity journal after substantive work. That directive is the owner's and it governs — including in Audit mode, whose "creates nothing" rule is about cleanup artifacts (indexes, status files, staging), not about the folder's own required log. Append the entry, keep it to what was measured, and state in the report that the journal was the only write. If a folder's logging policy and this skill's mode rules appear to conflict beyond that, record the conflict and ask.
6. **Check repository state without changing it.** If the root is in a Git worktree, record tracked, modified, and untracked paths that overlap the proposed map. Git operations remain out of scope unless separately authorized; never clean or reset a dirty tree as part of folder organization.

---

## B. Audit mode

Read-only. Produce evidence, not opinions.

### B1. Inventory

Run the bundled audit script, or gather equivalently:

- Full file list with size and modified time
- Depth and per-folder file counts
- Empty directories, listed separately as cosmetic findings rather than automatic removal targets
- Archives (`.zip`, `.7z`, `.tar*`, `.rar`) with size and date
- Files over ~1 MB and files at depth > 5
- Path lengths, flagging anything over 240 characters
- Duplicate candidates: same name across folders; with `--hash-files`, identical-content groups **and** the inverse — one name resolving to several different documents
- Index/link check: every Markdown link target in each named index that does not resolve, reported as a broken link. Report unresolved backticked filename/path references separately as review items, because examples and historical labels may be intentionally non-live. `--index-path` is repeatable; an index named in navigation but absent on disk is itself a finding.
- **Reparse points.** Every directory symlink or junction under the root, with its target. Their descendants appear in no count. On a synced root, check the provider's view separately before describing them as external — the cloud copy is what other agents index.
- **Case-mismatched references.** An index reference that resolves only through a case-insensitive filesystem, reported apart from resolving links. It breaks for any agent on a case-sensitive platform.
- **Cloud footprint, where the root is synced.** Total bytes as the provider reports them, beside the project-local total. A large gap is a finding in itself.
- **Credential-bearing files.** Browser profiles carry `Cookies`, `Login Data`, `Web Data`, `Local State` and account-specific variants such as `Login Data For Account*` — live session state. `.env`, `id_rsa`, `credentials.json`, `.npmrc` carry secrets outright. The script flags these through conservative exact-name and separator-delimited prefix hints. Report their existence and location; never open, stage, copy, or quote their contents, and flag them to the owner before the folder is shared with anyone.

**Noise control.** Generated machine state — browser profiles, caches, `__pycache__`, `node_modules`, `.git` internals, build output — routinely outnumbers real documents 3:1 and will drown every detail section. In one audited folder, 1,090 of 1,409 files (77%) were a dead Chrome/Edge profile dump, and the duplicate-name section returned 122 copies of `LOCK` before it reached a single document.

Run `--suggest-excludes` first to see the noise clusters, confirm them, then re-run with `--exclude`. Excluded files are still counted and reported by pattern, and the report must say how many were excluded and that they were not classified. Never silently drop them from the totals.

Noise is **not** a deletion target. It goes to `history/` or stays where it is unless the owner separately approves removal naming the paths.

### B2. Verify claims against artifacts

For each document that asserts a completed state:

- Does the output it describes actually exist at the stated path?
- Is its modified date consistent with the work it claims?
- Does a later document contradict it?

Record each as **verified**, **contradicted**, or **unverifiable**. Never upgrade "unverifiable" to "current".

A stale index is not only one that points at missing paths. Check the inverse too: **does the index or manifest omit folders that exist?** A root-level `PROJECT_FOLDER_MANIFEST.csv` with 1,282 rows and an authoritative name that contains zero rows for the four most recent working folders will convince an agent those folders are not part of the project. Record it as **contradicted by filesystem state**, with the specific folder names that are missing.

### B3. Classify

Assign every substantive file to one of the eight buckets in SKILL.md §4. Produce a table: path → bucket → evidence for the call. Files you cannot classify go in a short "needs owner decision" list rather than a guess. Files excluded by `--exclude` are reported as bucket 8 by pattern, not classified individually — say so.

### B4. Name the confusion sources

The point of the audit. Typical findings, in rough order of damage:

- Two or more documents that each look authoritative and disagree
- An index pointing at paths that no longer exist
- **Entrypoints the folder's own instructions require, that do not exist.** Read every instruction file — including app-side or tool-side project instructions the owner has configured outside the folder — and check that each file it tells an agent to read is actually on disk. A folder whose instructions open with "first read `README_FIRST.md`, `PROJECT_ROADMAP_STATUS.md` and `CHAT_INDEX.md`" when none of the three exists sends every agent into a guess on its first move. This outranks most duplicate problems: a duplicate makes an agent pick wrong, a missing entrypoint makes it pick blind.
- **Zero instruction files anywhere in the tree.** If no `AGENTS.md`, `CLAUDE.md`, `README.md` or equivalent exists, all agent guidance lives outside the folder in per-tool settings — invisible to the next agent and unversioned. Report it as a finding even though nothing on disk is wrong.
- **One filename, several different documents.** The inverse of a duplicate, and more dangerous: identical copies are at least interchangeable, whereas six different `research_report.md` files mean any citation by filename alone is ambiguous and any grep returns the wrong one. `--hash-files` reports this separately from identical-content groups.
- **A companion root whose status document names a different root as active.** Two roots, one filename, opposite claims, and nothing inside either one that reveals the conflict. Report which root each declares active, whether the companion has any entrypoints at all, and which one org-wide search reaches first.
- **An append-only journal too large to read.** Past roughly 100 KB, "read the tail" stops being executable through most access routes. Report the size and propose rotation; do not restructure it in Audit mode.
- Roadmap language ("we will add X") sitting in a folder named as if it were current state
- Archives whose contents duplicate live files, so both are searchable
- A read-only mirror or vendored checkout that agents keep editing
- Handoff files with no date or ordinal, so "latest" is unknowable

Stop here in Audit mode. Do not create navigation files. Do not move anything. The one exception is a journal entry the folder's own instructions require (see A5) — that is the owner's directive, and the report must state it was the only write.

---

## C. Plan mode

Read-only, plus a written proposal.

### C1. Proposed tree

Render the exact target tree as a code block, labeled `PROPOSED — not yet applied`. Keep the root short. A workable default, renamed to the project's vocabulary:

```
<root>/
  README.md              entrypoint: what this is, where to start
  AGENTS.md              instructions for agents (existing file — do not rewrite)
  STATUS.md              verified current state, dated
  AUTHORITY.md           which documents govern what
  INDEX.md               map of the tree
  HANDOFF.md             current master handoff
  authority/             specs, standards, conventions
  current/               active analysis and provenance
  backlog/               proposals, roadmaps, not-yet-real
  history/               superseded evidence, dated subfolders
  inbox/                 raw, untriaged incoming
  mirrors/               read-only external checkouts (untouched)
  scratch/               generated machine state (bucket 8) - excluded from
                         search and evidence review, deleted by nobody
```

Bucket 8 needs a named home or it leaks back into `history/` and gets preserved with the ceremony owed to documents. If the noise already sits in a folder the owner recognizes (`tmp/`, `.cache/`), leaving it where it is and naming it in the README beats moving 1,090 files to prove a point — moving noise costs the same verification effort as moving evidence and buys nothing.

Justify each departure from the user's existing names. If their tree already works, propose fewer changes rather than a prettier scheme.

### C2. Literal move map

A table with one row per file or per explicitly enumerated folder. No wildcards.

| # | Source (absolute) | Target (absolute) | Bucket | Reason |
|---|---|---|---|---|

Then compute and report:

- **Collisions:** any two sources mapping to one target — must be zero before approval
- **Path length:** longest resulting path, and every target over 240 characters
- **Unmapped files:** anything in the root not appearing in the map, listed explicitly
- **Untouched by design:** mirrors, archives, instruction files

### C3. Ask for approval on the map itself

Approval must reference the specific map, not the idea. "Yes, run the map as written" is approval. "Sounds good" is not — ask again, naming what you would do first.

---

## D. Execute mode

Execute has two subtypes. Use **D0–D7** when files move. Use **D8** when the approved work changes only navigation/current-state records or separately authorized factual instruction text. Do not create an empty move map for record-only work.

### D0–D7. Staged move protocol

Preconditions: an approved literal map, zero collisions, no target over the path threshold.

### D0. Preflight

- Re-scan sources; abort if any source is missing or modified since the map was built.
- **OneDrive/SharePoint:** verify each source file is hydrated. In PowerShell, `Offline`, `RecallOnOpen`, or `RecallOnDataAccess` indicates a placeholder; `ReparsePoint` alone does not, because hydrated OneDrive files commonly retain it. Hydrate or exclude actual placeholders. Confirm the sync client shows idle. If sync is actively running, stop and wait. Run `verify_move.py preflight` under **Windows-native Python** for this step: elsewhere it prints `NOT CHECKED - needs Windows` rather than a count, and an unverified hydration state is not a passed check — a placeholder moves as a stub and the move then verifies against the wrong bytes.
- Confirm free space ≥ 2× the total size being moved (staging holds a second copy).
- Confirm no other agent or job is mid-write.

Run `scripts/verify_move.py preflight --map moves.csv`. It checks collisions, missing sources, existing targets, duplicated sources, path length, and cloud placeholders in one pass and exits nonzero if any fire. A nonzero exit is a stop condition — resolve and re-run, do not proceed on judgement.

### D1. Baseline hashes

Hash every source file (SHA-256): `scripts/verify_move.py baseline --map moves.csv --out <scratch>/baseline.json`.

Save the baseline to a scratch location **outside** the target root, e.g. `%TEMP%\cleanup-baseline-<timestamp>.json`. Nothing about the audit trail should live inside the folder being reorganized — the script refuses to write it there. Keep the baseline until the session is fully closed out; it is the only way to reconstruct what was where if something goes wrong later.

### D2. Copy to labeled staging

Copy — do not move — into a clearly labeled staging folder, e.g. `<root>/_STAGING_<timestamp>/`. Mirror each target's path relative to the move map's common target root; do not flatten staging to basenames, because same-named files from different folders would collide. The baseline records the common target root used by `verify --stage`. The staging name must make it obvious to any agent that arrives mid-operation that this is transient.

### D3. Verify staging

`scripts/verify_move.py verify --baseline <scratch>/baseline.json --stage <staging-dir>`

Any mismatch or missing file: stop, report, change nothing further.

### D4. Move — no pause

Execute the exact approved list in one uninterrupted pass. **Do not add a discretionary approval pause between already approved paths.** A partially executed move is the dual-tree failure the whole protocol exists to prevent. However, a failed safety check, changed source, missing file, collision, hash mismatch, or newly required action outside the map is a stop condition: preserve staging, stop at the safest recoverable boundary, and report the exact partial state.

This is consistent with normal consent practice rather than an exception to it: approval was obtained for the entire map in C3, so every path touched here is already authorized. Anything *outside* the map is not, and does not become authorized by being discovered mid-run.

### D5. Verify final

`scripts/verify_move.py verify --baseline <scratch>/baseline.json`

Report count moved, count verified, any mismatch. Nonzero exit means the run is incomplete — say so plainly rather than reporting success with a caveat.

### D6. Clean up — the only removals allowed

Nothing here deletes user content. If a step seems to require deleting a document, archive, or duplicate, stop and ask for approval naming that file.

- Remove staging copies **only** for files verified at their final path.
- Remove source folders **only** when confirmed empty (`os.listdir()` returns nothing — not "looks empty in the report").
- Remove the staging folder itself only once empty. Never remove staging while any verification is outstanding — staging is the recovery path for D5 failures.
- Prefer recycle bin / trash over permanent deletion wherever the platform supports it. On Windows, `Remove-Item` is permanent; use the shell's recycle API or leave the empty folders in place and note them as follow-up.
- Empty source folders left behind are a cosmetic problem. A deleted file is not. When the two trade off, leave the folder.
- A parent left empty because the move took its last child is not always cosmetic. If its name is confusable with a live folder (`output/` beside `outputs/`), it is a new ambiguity the cleanup created. Name every such parent in the verification block. Remove it only if the approved map named it.
- On Windows, keep path resolution and any recursive move or cleanup in one PowerShell process. Verify each resolved absolute path remains within the approved root; do not enumerate in PowerShell and hand string-built paths to another shell.

### D7. Update navigation

Rewrite `INDEX.md` and any path-bearing navigation to the final paths — never to proposed paths. Update `STATUS.md` and the master handoff with verified facts only. Instruction files remain untouched unless the owner separately approved an exact factual correction under A2; list any such intended edit explicitly in the verification block.

### D8. Record-only Execute

Use this subtype for an approved literal list of factual corrections where no file moves. It covers navigation, status, authority maps, handoffs, and separately approved factual instruction-entrypoint corrections. It does not authorize new behavioral rules, authority changes, permission changes, or any file omitted from the approved list.

1. Record the exact approved files and the intended factual changes. Name any instruction file separately.
2. Immediately before editing, capture SHA-256 and modified time for every approved file plus any authority or instruction files that must remain unchanged.
3. Re-read the live files. If a hash or modified time changed after review, another writer is active: do not force the old text back. Re-stage from the new version, merge only the approved facts, and repeat the guard.
4. Apply minimal exact-context patches. If expected context does not match, treat that as a safe stop rather than using broad replacement or overwrite.
5. Re-hash the changed files and verify the intended facts directly. Search for the specific stale or contradictory claims the correction was meant to remove or label; absence must be measured, not assumed.
6. Verify protected authority and instruction files are byte-identical except for any instruction file explicitly approved in step 1. For an approved instruction edit, verify that only the named factual text changed and that behavioral rules, authority, scope, permissions and read order remain intact.
7. If a required journal write occurs after these checks, guard it independently and verify the appended entry. Do not present the journal hash as proof that earlier shared records remained unchanged.

---

## E. Verification block

Close every move Execute run with this exact block, filled from measurements rather than expectation:

```
VERIFICATION
- Files in approved map:        N
- Files moved:                  N
- Hash-verified at target:      N
- Target collisions:            0
- Missing / unaccounted files:  0
- Longest final path:           NNN chars (threshold 240)
- Staging remaining:            none
- Source folders removed:       N (all confirmed empty)
- Orphaned empty parents:       <none, or named exactly>
- Index paths resolving:        N/N
- Instruction files changed:    <none, or approved file(s) named exactly>
- Hydration checked on:         Windows | NOT CHECKED (state which)
- Unverified / out of scope:    <list, or "none">
```

Any nonzero in the "must be zero" rows means the run is reported as incomplete, not complete.

Close every record-only Execute run with this block:

```
RECORD VERIFICATION
- Files in approved list:        N
- Files changed:                 N
- Pre-write guards checked:      N/N
- Intended facts verified:       N/N
- Stale claims remaining:        0
- Concurrent-write conflicts:    0 unresolved
- Protected authority changed:   none
- Instruction files changed:     <none, or approved file(s) named exactly>
- Required Markdown links:       N/N resolving
- Backticked references:         N unresolved review items
- Journal entry verified:        yes / not required
- Unverified / out of scope:     <list, or "none">
```

A record-only run is incomplete if any intended fact is unverified, any stale target claim remains unlabeled, any concurrent-write conflict is unresolved, or a protected file changed outside the approval.

---

## F. Failure recovery

- **Hash mismatch at staging:** source is being written concurrently, or the copy failed. Do not proceed. Report the specific file.
- **Hash mismatch at target:** restore that file from staging (staging is still intact at this point — this is why D6 comes last). Report.
- **Move interrupted:** the folder is now in a dual state. Do not start a new plan. Reconcile first: list every mapped file, determine whether it sits at source, target, or both, and finish or reverse the exact remainder.
- **Placeholder discovered mid-move:** a placeholder here means D0's hydration precondition was false, so the environment is not the one the approval assumed. Skip that file and immediately re-check hydration across the *remaining* sources before touching them. If it is isolated, finish the approved remainder and report the one file as unmoved — a completed map minus one known file is a smaller dual state than a map abandoned halfway. If others are also dehydrated, the sync client is actively reclaiming files underneath you and every subsequent hash is untrustworthy: stop at the safest recoverable boundary, preserve staging, and report the exact source/target/staging state of every mapped file. Reconcile before resuming or reversing the approved remainder.

---

## G. Report formats

**Audit report:**

```
# Folder Audit — <root>
## Access
<route used (mounted path | connector | web share), whether the audit script
 ran, and — if it did not — which checks are therefore unavailable>
## Outcome
<2-4 bullets: the actual state, plainly>
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

**Plan report:** proposed tree, literal move map, collision/path-length/unmapped counts, explicit approval request.

**Execute report:** outcome first, then the verification block matching the move or record-only subtype, then optional follow-up work in a clearly separate section.
