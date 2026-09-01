---
name: multi-agent-folder-cleanup
description: Audit, plan, or safely reorganize shared project folders when AI agents are confused by duplicate, stale, conflicting, or poorly indexed documents. Use for agent handoff workspaces, OneDrive, SharePoint, NAS project roots, archive piles, companion roots, or verified folder moves. Do not use for source-code refactors or ordinary storage cleanup without an agent-context problem.
license: MIT
metadata:
  version: "1.1.0"
  repository: https://github.com/JesseRaber/multi-agent-folder-cleanup
---

# Multi-Agent Folder Cleanup

Create a workspace where an agent arriving cold can quickly tell what is true now, what is proposed, and what is historical without choosing between plausible copies.

## Choose the operating mode

State the mode in the first line of the response. Default to **Audit** when execution is not explicitly authorized.

| Mode | Typical request | Allowed work |
|---|---|---|
| **Audit** | “What is here?” “Why are agents confused?” | Read-only inspection and an evidence report. |
| **Plan** | “How should this be organized?” | Read-only inspection, a proposed tree, and a literal source-to-target map labeled **PROPOSED**. |
| **Execute** | Explicit approval of a specific map or record-correction list | Only the approved moves or exact factual patches. |

Read [references/workflow.md](references/workflow.md) before any Audit, Plan, or Execute run. Read [references/audit-tools.md](references/audit-tools.md) when a filesystem is mounted and the bundled helpers can run. Read [references/navigation-templates.md](references/navigation-templates.md) only when creating or reviewing navigation files.

## Keep authorization narrow

- The approved map is the mutation boundary. Discovery never expands it.
- Git operations, deployments, databases, credentials, sync settings, sharing permissions, and external service writes remain out of scope unless separately authorized.
- Deletion is never implied. Moving a named path is not approval to delete documents, archives, duplicates, or nearby folders.
- Remove only verified staging copies and confirmed-empty source folders when the approved protocol names that cleanup and the platform offers recoverable trash semantics.
- Protect instruction files by default. Propose a demonstrably stale factual correction separately and apply it only after explicit approval; never rewrite behavioral rules as housekeeping.
- A failed safety check overrides prior approval. Stop on a collision, changed source, missing file, placeholder, concurrent write, path-length failure, or unapproved target.

## Audit evidence, not filenames

Discover root and nested instruction files such as `AGENTS.md`, `CLAUDE.md`, `.github/copilot-instructions.md`, `README.md`, and `README_FIRST.md`. Include instructions configured outside the folder when the host exposes them. Record conflicts rather than silently choosing a winner. Follow the folder’s own required logging policy, but do not replace a concurrently written journal when the access route cannot append safely.

Confirm one exact root, the storage substrate, the access route, and any companion or predecessor roots. A mounted filesystem can support hashes and Execute mode. A connector or web listing can support a real but degraded Audit only; identify unverified hash, hydration, OS path-length, and byte-comparison claims. Never Execute through a connector-only view.

Inventory substantive documents, archives, handoffs, transcripts, data, scripts, outputs, mirrors, generated state, and duplicate groups. Verify every required entrypoint exists. Check indexes in both directions: broken references and live folders omitted from authoritative-looking indexes.

Treat a filename such as `FINAL_v3.md`, `STATUS.md`, or `AUTHORITY.md` as a reading cue, not proof. Open the supporting artifacts and label material claims **verified**, **contradicted**, or **unverifiable**. Never upgrade “unverifiable” to current.

Prioritize these confusion sources:

1. Divergent control documents, especially across separate roots.
2. Missing required entrypoints or no visible agent instructions.
3. One filename resolving to different content.
4. Stale indexes, manifests, status files, or authority maps.
5. Identical copies with no canonical marker.
6. Generated machine state overwhelming search and inventory.

Flag credential-bearing filenames but never open, stage, copy, quote, or index their contents. Keep archives closed unless central-directory inspection is explicitly useful; never bulk-extract them to make them searchable.

On large trees, keep structural checks exhaustive but read selectively: all instructions, authority or state claims, handoffs, and representative files from duplicate groups. Mark other judgments **classified-by-metadata** and report exclusions. An exclusion limits this review; it does not make files invisible to another agent or cloud index.

For OneDrive or SharePoint, distinguish the local and provider views. A junction skipped locally may be materialized as searchable cloud files. Before Execute, verify hydration and quiet sync on Windows. A successful local move does not verify cloud retention, version history, sharing links, conflict copies, or provider-side synchronization.

## Classify each substantive file once

Use exactly one bucket:

1. Owner direction and verified current state
2. Documentary authority
3. Current analysis and provenance
4. Active backlog
5. Historical or superseded evidence
6. Raw or unreviewed incoming material
7. Read-only mirrors and external checkouts
8. Generated machine state

Roadmaps remain backlog until implementation is independently verified. Source snapshots remain history unless tied to a reproducible commit. Generated caches, browser profiles, build output, and runtime dependencies are bucket 8, not documentary history and not automatic deletion targets.

## Design for fast navigation

Prefer a short root with an entrypoint, instructions, status, authority map, index, and one current handoff. Adapt names to the project’s vocabulary; do not impose a universal numbered tree. Keep one authority per topic and clearly separate current material, backlog, history, incoming material, and read-only mirrors.

## Execute with measured verification

Follow the staged sequence in `references/workflow.md` exactly:

1. Freeze the approved literal move map and write a SHA-256 baseline outside the source and target trees.
2. Preflight missing sources, collisions, target roots, hydration, and a conservative 240-character Windows path limit.
3. Copy to a clearly labeled staging tree that mirrors final relative paths.
4. Verify every staged hash.
5. Move the exact approved map in one controlled pass. Do not pause for a second approval already covered by the map.
6. Verify final hashes, intended source absence, and instruction/index integrity.
7. Remove only verified staging and approved confirmed-empty source folders using recoverable semantics.

Use one filesystem environment end to end and literal paths throughout. Do not construct move or deletion commands from globs, unresolved environment variables, or a second shell. If the map empties a parent, name that parent in advance or report the resulting empty folder as follow-up; never silently broaden the cleanup.

For approved navigation-only or factual record corrections, use the record-only Execute protocol in `references/workflow.md`: pre-write hashes, immediate re-read on mismatch, exact-context patches, and post-write checks for both the new facts and stale claims that should be gone.

## Finish with proof

Cleanup is incomplete while staging remains, an index describes proposed paths, a current record retains a superseded claim, or verification has unresolved gaps. Report:

- exact scope and mode;
- inspected, inferred, excluded, and inaccessible material;
- verified findings separated from owner decisions;
- every moved or intentionally changed path;
- hash, collision, hydration, index, and instruction-file checks;
- remaining limitations and separately optional follow-ups.

Do not call the work complete merely because the files look tidy.
