---
name: multi-agent-folder-cleanup
description: Audit, plan, and safely reorganize a shared project folder so multiple AI agents (Grok, Claude, Copilot, Codex, ChatGPT, Manus, local models) can find current authority, tell evidence apart from backlog and history, and continue work without duplicate or ambiguous trees. Use this skill whenever the user mentions a messy or sprawling project folder, an AI handoff folder, a OneDrive/SharePoint/NAS work area that "agents keep getting confused by", duplicate or superseded docs, stale indexes, archive/ZIP piles, a companion or mirror root that disagrees with the main one, or wants a folder audited, restructured, staged, or moved with verification — even if they never say "cleanup". Applies whether the folder is a local path or reachable only through a cloud connector. Do not use for ordinary source-code refactors or plain cloud-storage housekeeping with no agent-context problem.
license: MIT
metadata:
  version: "1.0.0"
  repository: https://github.com/JesseRaber/multi-agent-folder-cleanup
---

# Multi-Agent Folder Cleanup

Goal: a workspace where any agent opening the folder cold can answer, in under a minute, "what is true now, what is proposed, and what is dead" — without ever having to pick between two copies of the same document.

Cleanup fails in predictable ways: promoting a stale doc to authority, leaving a copy-only dual tree, breaking an index, bulk-extracting archives, or moving OneDrive files that were never hydrated. The protocol below exists to prevent exactly those.

## 1. Pick the operating mode first

Never assume execution. Match the request:

| Mode | Trigger phrasing | What is allowed |
|---|---|---|
| **Audit** | "what's in here", "why do the agents get confused", "status" | Read-only inspection + evidence report. No new files, no moves. |
| **Plan** | "how should this be organized", "propose a structure" | Read-only + an exact proposed tree and a literal source→target move map, clearly labeled **PROPOSED**. |
| **Execute** | explicit approval of a specific move map or record-correction list | The approved moves or factual record corrections only. |

State the mode back to the user in the first line of the response. If the request is ambiguous, default to Audit and say so — an unwanted audit costs nothing, an unwanted move costs trust.

**Out of scope unless separately authorized**, even in Execute mode: git operations, deployments, database changes, credential rotation, scheduled tasks, sync-client settings, sharing permissions. Folder organization only.

**Deletion is never in scope by default.** Execute mode moves files; it does not delete them. The only removals allowed under a standard approval are verified staging copies and source folders confirmed empty — and even those go to the recycle bin / trash where the platform supports it, never a hard delete. Removing an actual document, archive, or duplicate requires its own explicit approval naming the files. When in doubt, move it to `history/` and say so.

**On approving the whole map up front:** this skill deliberately front-loads consent onto the complete move map rather than asking per file, because a move that stops halfway leaves the folder in the dual-copy state the whole protocol exists to prevent. That is why §6 forbids a mid-move pause — the approval already covered every listed path. It is not a licence to act without approval, and it does not extend to anything outside the approved map.

**The approved map is the mutation boundary, whichever agent is executing.** Nothing outside it is authorized, and nothing becomes authorized by being discovered mid-run: not Git operations, not connector or repository writes, not permission changes, not a path that "obviously" belongs with the others. And the boundary is a ceiling, not a floor — a safety failure, collision, concurrent write, changed source, missing file, or unapproved target is still a stop condition. Prior approval says what you *may* touch; it never overrides a check that failed.

## 2. Obey the folder's own instructions before acting

Discover `AGENTS.md`, `CLAUDE.md`, `.github/copilot-instructions.md`, `README.md`, `README_FIRST.md`, or equivalents at the root and in subtrees. A nested instruction file normally scopes only its own subtree. When two files conflict, record the conflict in the report and ask — do not silently pick a winner.

**Instruction files are protected by default, not permanently frozen.** Do not include them in an ordinary move map or rewrite behavioral rules during cleanup. If verified state makes a factual path, count, status, or caution inside an instruction entrypoint demonstrably stale, propose the exact minimal patch separately. Apply it only after the owner explicitly approves that instruction-file correction. Do not change permissions, authority, scope, behavioral rules, or read order unless the owner names that change too. List every intentionally changed instruction file in the final verification block.

**Instructions often live outside the folder.** Project instructions configured in the owner's app or IDE govern the folder just as much as a file in it, and are usually the only place a journaling or logging requirement is written down. Read them, and check both directions: which files they require an agent to read, and whether those files exist. Finding none on disk is itself a finding — it means every agent's guidance is invisible to the next one.

**A folder's own logging requirement governs, in every mode.** If the owner directs that substantive work be appended to an activity journal, do it — Audit's "creates nothing" rule is about cleanup artifacts (indexes, status files, staging), not about the folder's required log. Record only what was measured, and say in the report that the journal was the only write.

**Append only if the write path can actually append.** Many access routes — Graph/SharePoint connectors, most cloud file APIs, several agent tool surfaces — offer no append: writing means replacing the whole file. On a folder with concurrent writers that is not a log entry, it is the whole-file rewrite this skill calls the acute risk. When you cannot append, and cannot re-read the file immediately beforehand to write from, do not write: report plainly that the entry is owed, why it was not made, and what it would have said. An unwritten entry the owner knows about beats a lost journal.

**Journals that only grow eventually stop being readable.** Instructions commonly say "read the tail," but a growing single file has no cheap tail through most read paths — an agent either skips it or spends a large share of its context on it. Past roughly 100 KB, flag it and propose a rotation convention (a dated `…_JOURNAL_<YYYY-MM>.md` per period plus one short current-tail file that navigation points at). Proposing it is Audit-safe; changing it is a separate owner decision.

## 3. Inventory against artifacts, not claims

Read `references/workflow.md` for the full protocol before an Audit, Plan, or Execute run. Key discipline: a file named `FINAL_v3.md` proves nothing, and a completion report proves nothing. Verify by opening artifacts, comparing dates and hashes, and checking whether described outputs actually exist.

Inventory must cover: substantive documents, archives (`.zip`, `.7z`), handoff files, transcripts, data files, scripts, generated outputs, read-only mirrors/checkouts, and duplicate groups.

**When the folder is only reachable through a connector, say so and downgrade explicitly.** Both audit scripts need a mounted filesystem path. A OneDrive/SharePoint folder reached through Graph, a Drive or Dropbox connector, or a web share is not one, and no local sync path is guaranteed to exist or be readable. Do not silently skip the script and present the result as a normal audit. State the access route in the report's first lines, and record what the route can and cannot establish:

| Still measurable through a connector | Not measurable — mark unverified |
|---|---|
| Tree structure, folder and file names, sizes, modified times | SHA-256 hashes, therefore all identical-content duplicate groups |
| Existence of every required entrypoint | Same-name-different-content divergence (name collisions are still visible; *which* copy differs is not) |
| Index checked in both directions against the listing | Path length as the owner's OS will see it |
| Full text of any file you open, and contradictions between them | Hydration / placeholder state |
| Counts the owner's records claim, checked against the listing | Anything requiring byte comparison |

A connector audit is a real audit of structure and claims — it is often the only way to see the cloud-side view at all (see the reparse-point item below). It is not a substitute for the hashing passes, and an Execute run must not be attempted from it: `verify_move.py` baseline and preflight require the filesystem. Say that in the limitations rather than leaving it implied.

**Generated machine state will drown the report.** Browser profiles, caches, `__pycache__`, `node_modules`, `.git` internals and build output routinely outnumber real documents 3:1. In one audited folder, 1,090 of 1,409 files (77%) were a dead Chrome/Edge profile dump, and the duplicate-name section returned 122 copies of `LOCK` before reaching a single document. Run `--suggest-excludes` to see the clusters, confirm them, then re-run with `--exclude`. Excluded files stay in the totals and are reported per pattern; say in the report how many were excluded and that they were not classified. Noise is never a deletion target — it goes to `history/` or stays put unless the owner separately approves removal naming the paths.

**A junction excluded from the local count may still be fully synced to the cloud.** Reparse-aware inventory is correct arithmetic: a symlink or junction pointing at an external runtime is not project content, and its descendants should stay out of the project-local totals. But the exclusion is a property of the *local* view. OneDrive and SharePoint routinely materialize the target as real files in the cloud tree, and that cloud copy is what every Graph-indexed agent — Copilot, connector-based assistants, org-wide search — actually sees. In one audited folder, a `node_modules` junction correctly excluded from a 386-file project-local count appeared through the connector as roughly 318 MB across fifty-plus packages, about ninety percent of the folder's cloud footprint. Check both sides, report the local and cloud figures separately, and never let "not project contents" stand as an unqualified claim when the tree is synced.

**Exclusion from review is not exclusion from indexing.** `--exclude`, a `DEEP_SCAN_EXCLUSIONS.txt`, and an owner's scan-exclusion register all govern *your* analysis scope. None of them makes a byte invisible to another agent's search. If generated state is the problem, the fix is on the sync side — selective sync, moving the runtime outside the synced root, a provider-level exclusion — which is out of this skill's scope and belongs in the report as an owner action, not as something the cleanup quietly handles. State the two scopes separately whenever an exclusion register exists, or the owner will reasonably read a passing review as a clean folder.

**Check that required entrypoints exist.** For every file the instructions tell an agent to read first, verify it is on disk. A folder whose instructions open with "read `README_FIRST.md`, `PROJECT_ROADMAP_STATUS.md` and `CHAT_INDEX.md`" when none of the three exists sends every agent into a guess on its first move. This outranks most duplicate problems: a duplicate makes an agent pick wrong; a missing entrypoint makes it pick blind.

**Verify indexes in both directions.** A stale index is not only one pointing at missing paths — check whether it omits folders that exist. A 1,282-row root manifest with an authoritative name and zero rows for the four most recent working folders will convince an agent that the current work is not part of the project. Record that as contradicted by filesystem state, naming the missing folders.

**A divergent control document outranks every other duplicate.** The same-name-different-content check finds two kinds of hit, and they are not equally serious. Two drafts of a report under one name confuse a reader. Two versions of a *control artifact* — an exclusion register, a no-rescan list, an allowlist, a schema, a validation rule set — corrupt the next piece of work, because an agent follows the copy it finds and acts on it. Look for the shorter copy: in one audited project, `Fourth Wide Scan Exclusion List.md` was 56 lines in two folders and 42 in a third, missing ten already-excluded sources, and the truncated copy sat in the folder whose name matched the scan an agent would be looking for. Rank these at the top of the report, name which copies differ and by how much, and treat "which one governs" as an owner decision that blocks new work rather than a tidy-up item.

**The same check runs across roots, and that version is worse.** Projects acquire companion roots — a personal OneDrive copy and a team-site copy, a NAS mirror, an old share nobody retired. Two files named `PROJECT_ROADMAP_STATUS.md` in two roots, each naming a *different* root as the active one, is the divergent-control case with no shared folder to notice it in: neither copy contains anything that reveals the other. Rank it above every in-tree duplicate. When a companion root exists, check three things and report them together: which root each status document declares active; whether the companion carries the required entrypoints at all (a root with no `AGENTS.md`, `CLAUDE.md`, `INDEX.md` or authority declaration hands an arriving agent nothing to correct a stale status file with); and which root a tool-driven search would reach first — a shared team site usually outranks a personal drive in org-wide search, so the stale copy is often the one an agent finds. Whether to merge, retire, or redirect is an owner decision; making the contradiction visible is not.

**Flag credential-bearing files, never open them.** Browser profiles carry `Cookies`, `Login Data`, `Web Data`, `Local State`; account-specific variants such as `Login Data For Account*` also occur. `.env`, `id_rsa`, `credentials.json` and `.npmrc` carry secrets outright. The helpers use conservative exact-name and separator-delimited prefix matching; findings are hints, not proof. Report that they exist and where, tell the owner before the folder is shared with anyone, and never stage, copy, or quote their contents.

**Large folders:** past a few hundred files, do not read everything. Let the script produce the complete structural inventory (counts, empty directories, duplicates, path lengths, broken Markdown links, and unresolved backticked path references — these stay exhaustive and cheap), then read in full only: instruction files, anything claiming current state or authority, all handoffs, and one representative file per duplicate group. Everything else is classified from name, location, and date, and marked **classified-by-metadata** in the report so the owner knows which calls are shallow. Never silently downgrade coverage — say what you read and what you inferred.

## 4. Classify into eight buckets

Every file lands in exactly one:

1. **Owner direction + verified current state** — what the owner said, and what is provably true today
2. **Documentary authority** — specs, standards, formulas, conventions that other work must conform to
3. **Current analysis and provenance** — how the current state was reached
4. **Active backlog** — proposed, planned, not yet real
5. **Historical / superseded evidence** — was true, is not now; kept for audit
6. **Raw or unreviewed incoming** — dropped in, not yet triaged
7. **Read-only mirrors and external checkouts** — not ours to reorganize
8. **Generated machine state** — browser profiles, caches, `__pycache__`, build output, scratch dumps; produced by a tool, read by nobody, and evidence of nothing

Three rules that catch most misclassification:
- **Roadmaps are backlog** until implementation is independently verified.
- **Source snapshots are historical evidence** unless tied to a known commit and shown reproducible.
- **Generated state is bucket 8, not bucket 5.** It is tempting to call a stale scratch folder "historical evidence" and keep it in the audit trail. It is not evidence — nobody will ever read a LevelDB lock file to reconstruct a decision. Separating it is what stops noise from being preserved with the ceremony owed to documents.

## 5. Design the smallest structure that works

Prefer a short root: an entrypoint, instructions, status, authority map, index, and one current master handoff. Adapt folder names to the project's own vocabulary. Do not impose a universal numbered tree — an inherited `01_/02_/03_` scheme that nobody's language matches makes navigation worse.

When creating or reviewing navigation files, read `references/navigation-templates.md`.

## 6. Move safely — never leave a dual tree

The single most damaging outcome is two plausible copies of the same document. The staged move sequence (preflight → copy to labeled staging → hash-verify staged → move the exact approved list with **no approval pause mid-move** → verify final hashes → remove only verified staging and confirmed-empty source folders) is specified step by step in `references/workflow.md`. Follow it literally.

Non-obvious safeguards:

- **OneDrive/SharePoint:** confirm files are hydrated (not cloud-only placeholders) and sync appears idle before moving. A successful local move proves nothing about conflict copies, sharing links, retention, or version history — those are service state, report them as unverified.
- **Path length:** precompute every final path; stop at 240 characters as a conservative Windows/OneDrive default.
- **Literal paths only.** No wildcards, no globs, no "and the rest of that folder" in an execution map.
- **Emptying a folder's last child orphans its parent.** Removing only what the map names is correct — but a parent left holding nothing, sitting beside a live folder with a near-identical name (`output/` next to `outputs/`), is a fresh ambiguity created by the cleanup itself. Either include the parent in the map when the move empties it, or list every orphaned parent by name in the verification block as a follow-up. Do not remove it unnamed on the grounds that it is obviously implied.
- **Use one filesystem environment end to end.** On Windows, do not discover paths in one shell and pass constructed strings to another shell for moving or removal. Resolve and verify every absolute target within the approved root before recursive operations.
- **Archives stay closed.** Keep originals byte-identical unless the user explicitly asks for a rewrite. If content is needed, extract selectively with no-overwrite into a scratch area — never bulk-extract just to make things searchable.
- **Secrets stay out.** Do not stage credential-bearing material into project-local folders without explicit owner classification, and never copy secret values into an index, journal, or report.

When approved cleanup changes only navigation, status, authority maps, handoffs, or separately authorized factual instruction text, use the **record-only Execute** protocol in `references/workflow.md` instead of inventing an empty move map. Guard every shared record with a pre-write hash, re-read on any mismatch, apply only exact-context patches, and verify both the intended new facts and the removal or labeling of stale claims afterward.

## 7. Finish with proof, not assertion

Cleanup is not complete while the index still describes proposed paths, staging still exists, or current navigation retains a claim the approved correction superseded. Close with the matching move or record-only verification block from `references/workflow.md`, covering unintended instruction-file changes, broken required Markdown links, unresolved backticked path references, and any limitation you could not verify.

Lead the handoff with the outcome, then the evidence, then optional follow-up work kept clearly separate from what was done.

## Deterministic audit helper

`scripts/audit_folder.ps1` (Windows/PowerShell) and `scripts/audit_folder.py` (cross-platform) perform the same read-only inventory, with the same flags in each language's convention. Neither writes to the target folder.

Which to run: neither, if the folder is only reachable through a connector or a web share — both need a mounted path, and there is no partial mode. Fall back to the connector inventory described in §3 and label the report accordingly. On Windows, prefer the PowerShell version — the OneDrive placeholder check needs Windows file attributes and is the one finding the Python version cannot produce. Everywhere else, or when reaching a Windows folder through a POSIX mount or device bridge, run the Python version and record hydration status as **unverified** in the report's limitations. A POSIX view of a OneDrive folder cannot reliably see `Offline` / recall-on-access attributes, so hydration must be re-checked on Windows before any Execute run.

> The PowerShell version has been exercised on Windows against hydrated OneDrive files and compared with the Python report. A OneDrive file may retain the `ReparsePoint` attribute while fully readable; the helper correctly treats only `Offline`, `RecallOnOpen`, or `RecallOnDataAccess` as placeholder signals.

```powershell
pwsh -File scripts/audit_folder.ps1 -Root <folder> -IndexPath INDEX.md
```

```bash
python scripts/audit_folder.py --root <folder> --index-path INDEX.md
```

Add `-HashFiles` / `--hash-files` for duplicate groups, a pre-move baseline, and the same-name-different-content check. Add `-InspectZip` / `--inspect-zip` only when archive-directory inspection is authorized (it reads the ZIP central directory only — it never extracts).

Two passes on any folder that might hold generated noise:

```bash
# 1. see what the noise is; nothing is excluded
python scripts/audit_folder.py --root <folder> --suggest-excludes

# 2. re-run with the confirmed clusters out of the detail sections
python scripts/audit_folder.py --root <folder> --hash-files \
    --exclude 'tmp/**' --exclude '**/__pycache__/**' \
    --index-path INDEX.md --index-path AI_CONTEXT/CHAT_INDEX.md
```

The same two passes in PowerShell (arrays instead of repeated flags):

```powershell
pwsh -File scripts/audit_folder.ps1 -Root <folder> -SuggestExcludes

pwsh -File scripts/audit_folder.ps1 -Root <folder> -HashFiles `
    -Exclude 'tmp/**','**/__pycache__/**' `
    -IndexPath 'INDEX.md','AI_CONTEXT/CHAT_INDEX.md'
```

`pwsh -File` does not parse PowerShell argument syntax — it hands the script a single string — so the PowerShell script accepts comma-separated values for these parameters and splits them internally. `-Exclude 'a/**','b/**'` and `-Exclude 'a/**,b/**'` are therefore equivalent, and the `-File` form above works as written. A literal comma inside a path or pattern is not supported.

The Python script deliberately does **not** mirror that. `-File` forces the comma form on PowerShell; Python has no such constraint, so repeating the flag always works and inventing a comma syntax would only break paths that legitimately contain one. Passing a comma to `--exclude` or `--index-path` therefore **exits 1 with an explanation** rather than failing quietly — the comma form used to match nothing and print an empty exclusion table, and on `--index-path` it was worse: a present `INDEX.md` was reported absent and flagged as a top-tier finding. The asymmetry between the two scripts is intentional, and each refuses in its own language's convention.

`--exclude` (repeatable glob, `/` separators, relative to the root) keeps paths out of the detail sections while still counting them; the report prints the excluded count per pattern and a closing coverage line. `--index-path` is repeatable, and a named index that does not exist is reported as a finding rather than passed over. Each named index gets two results: actual Markdown link targets that fail to resolve are **broken links**; backticked filename/path references that do not resolve are **review items**, because examples and historical labels may be intentionally non-live. The helpers also report empty directories explicitly and print, unconditionally, the files whose names *claim* current state or authority (`*authority*`, `*status*`, `*manifest*`, `*final*`, `*_v[0-9]*`, …) — that list is the reading queue for §3, not a set of conclusions.

Two further sections are always printed:

- **Reparse points not descended.** Every directory symlink or junction found under the root, with its target where readable. Their descendants are in no count in the report. That is the correct local arithmetic and an incomplete picture of a synced folder — pair it with the cloud-side check in §3 before writing "not project contents" anywhere.
- **Case-mismatched references.** An index reference that resolves only because the filesystem is case-insensitive is reported separately from a resolving one. `tools\build_x.ps1` against an on-disk `Build_x.ps1` works on Windows and breaks on any Linux or macOS agent reading the same index — and multi-agent almost always means multi-platform. These are review items, not broken links.

## What the scripts do not decide

Both audit scripts are deliberately dumb about meaning. They find structure; you supply judgment.

- **The suggested exclusions are a proposal, not a verdict.** Segment matching is exact (plus `chrome-profile*`-style prefixes) precisely so a `Catalogs/` or `rebuild-notes/` folder is never proposed as junk — but a project can still name a real folder `build/` or `logs/`. Confirm every pattern with the owner before the second pass, and never exclude a folder you have not looked inside.
- **The claims list is a reading queue.** A file matching `*status*` is a file to open, not a file that is current. Half the entries will be historical.
- **The credential list is name-matching only.** It cannot find a secret pasted into a `.md` file, and it will flag a document innocently named `credentials.json`. Absence of hits is not proof the folder is clean.
- **Identical hashes prove identical bytes, not which copy is canonical.** That is an owner decision, always.
- **A reparse point is skipped, not assessed.** The scripts name it and stop. Whether its target is an external runtime, a second copy of the project, or something the cloud has quietly materialized is yours to determine.
- **Nothing here judges whether a document is true.** A perfectly-structured folder full of wrong specs passes every check in both scripts.

## Move verification helper

`scripts/verify_move.py` handles the hashing arithmetic in Execute mode, so verification is measured rather than eyeballed. It reads a move map (CSV or JSON: `source,target`) and never moves anything itself.

```bash
# before the move — writes the baseline OUTSIDE the target root
python scripts/verify_move.py baseline --map moves.csv --out /tmp/baseline.json

# checks collisions, path length, missing sources, cloud placeholders
python scripts/verify_move.py preflight --map moves.csv --path-threshold 240

# after staging (mirrored relative to the common target root), and again after the move
python scripts/verify_move.py verify --baseline /tmp/baseline.json --stage <staging-dir>
python scripts/verify_move.py verify --baseline /tmp/baseline.json
```

`verify` exits nonzero on any mismatch. Treat a nonzero exit as a stop condition, not a warning.

Run it with **Windows-native Python** when the folder is OneDrive-synced. `preflight`'s placeholder check reads Windows file attributes, so anywhere else it prints `NOT CHECKED - needs Windows` and says so again in its closing line rather than reporting a zero you could mistake for a verified one. Everything else — collisions, missing sources, path length, hashes — is platform-independent and trustworthy anywhere. A clean preflight on POSIX means clean *except hydration*, and a cloud placeholder moves as a stub.

`baseline` records the common target root and refuses to write itself inside either the source or the target tree, and `verify --stage` mirrors the target tree under staging rather than flattening to filenames. That last point is not cosmetic: two files named `notes.md` from different source folders used to land on the same staged path, so the second one silently verified against the first one's bytes — a corruption inside the step meant to detect corruption. If your move map's targets share no common parent, `preflight` fails rather than guessing; split it into one map per target root.

## Worked example

> **User:** "The SharePoint project folder is a mess — Copilot keeps citing the old spec. Can you sort it out?"

Wrong response: proposing a tree and starting to move things. "Sort it out" is not approval of anything specific, and nothing is known yet about which spec is old.

Right shape:

1. **Mode: Audit** — stated in line one, because no plan exists to approve.
2. Run the audit script. It finds `spec.md` in two folders with identical hashes, plus `spec-v2.md` dated later with different content, and an `INDEX.md` pointing at a third path that no longer exists.
3. Report the finding as evidence: three candidates for "the spec", one index that resolves to none of them, so any agent picks arbitrarily. That is the actual answer to "why does Copilot cite the old one."
4. Offer Plan mode next. Do not create `AUTHORITY.md` yet — that is a cleanup artifact, and Audit creates none. (A journal entry the folder's own instructions require is the one exception, per §2.)
5. On approval of a specific map, run Execute: baseline → stage → verify → move in one pass → verify → clean staging → rewrite the index to final paths → verification block.

The failure this sequence prevents: designating `spec-v2.md` as authority in step 2 because it is newest, when the audit would have shown the owner reverted to v1 deliberately.
