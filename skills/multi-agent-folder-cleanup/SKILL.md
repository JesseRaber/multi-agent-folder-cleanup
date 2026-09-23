---
name: multi-agent-folder-cleanup
description: Audit, plan, and safely reorganize shared project folders or multi-project portfolios so AI agents can identify current authority, separate documentary claims from operationally verified state, and avoid duplicate or ambiguous trees. Use for OneDrive, SharePoint, NAS, agent handoff workspaces, stale indexes, companion roots, archive piles, confusing project portfolios, and verified folder moves—even when the user only asks what is current or why agents are confused.
license: MIT
metadata:
  version: "1.2.0"
  repository: https://github.com/JesseRaber/multi-agent-folder-cleanup
---

# Multi-Agent Folder Cleanup

Create a workspace where an agent arriving cold can quickly tell what is true now, what is proposed, what is incoming, and what is historical—without choosing between plausible copies.

Report as: **Loaded Multi-Agent Folder Cleanup v1.2.0**.

## Choose the operating mode and mutation type

State the mode in the first line. Default to **Audit** when execution is not explicitly authorized.

| Mode | Typical request | Allowed work |
|---|---|---|
| **Audit** | “What is here?” “Why are agents confused?” | Read-only inspection and an evidence report. |
| **Plan** | “How should this be organized?” | Read-only inspection, an exact proposal, and literal mutation lists labeled **PROPOSED**. |
| **Execute** | Explicit approval of a specific mutation list | Only the approved moves, factual patches, or additive intake files. |

Execute has three mutation types:

1. **Move execution** — needs a mounted filesystem, literal move map, hydration checks, staging, hashes, and final verification.
2. **Record-only execution** — approved exact factual patches to navigation/current-state records; connector or web editing is allowed only when the complete current document can be guarded, patched, reopened, and verified.
3. **Additive-intake execution** — approved creation of a new non-governing incoming/quarantine package; it never promotes, replaces, moves, or overwrites existing authority.

Read [references/workflow.md](references/workflow.md) before any run. Read [references/audit-tools.md](references/audit-tools.md) when a filesystem is mounted. Read [references/connector-audit.md](references/connector-audit.md) for OneDrive, SharePoint, Graph, enterprise search, or web listings. Read [references/portfolio-audit-template.md](references/portfolio-audit-template.md) when the root contains multiple projects. Read [references/navigation-templates.md](references/navigation-templates.md) only when creating or reviewing navigation files.

## Keep authorization narrow

- The approved mutation list is the boundary. Discovery never expands it.
- Folder cleanup does not authorize Git operations, deployments, database changes, permissions, credentials, scheduled jobs, sync settings, or domain-data promotion.
- Deletion is never included by default. Actual documents, archives, and duplicates require separate approval naming each target. Prefer history or recycle bin over permanent deletion.
- A failed safety check, changed source, collision, concurrent write, incomplete upload, or unapproved target is a stop condition even after approval.
- Instruction files are protected. Propose exact factual corrections separately; never rewrite behavioral rules, authority, scope, permissions, or read order without explicit approval.
- Do not publish, commit, push, release, or synchronize skill/repository changes without confirmation immediately before that action.

## Split mixed-scope requests

When a request combines cleanup with research, data intake, software work, or another domain task, declare separate tracks:

- **Cleanup track** — structure, authority, navigation, duplicates, history, generated state.
- **Domain-work track** — governed by the project’s own evidence, privacy, production, and approval rules.

Cleanup permission is not permission to change domain authority, production data, or accepted evidence. New domain material belongs in the project’s approved incoming/quarantine area until its own review gates pass.

## Obey project instructions and read-only boundaries

Before substantive work, discover root and nested `AGENTS.md`, `CLAUDE.md`, `.github/copilot-instructions.md`, `README.md`, `README_FIRST.md`, owner directives, and app-side project instructions. A nested instruction file normally scopes its subtree. Record conflicts; resolve none by recency alone.

Verify every required entrypoint exists. A missing entrypoint outranks ordinary duplicates because the next agent starts blind.

A project logging requirement normally governs, including in Audit mode. Two exceptions override the write:

- the user explicitly requested a read-only audit; or
- the access route cannot perform a safe append and immediate verification.

In either case, make no write. Provide the exact owed entry and explain why it was not saved. Never replace a shared journal merely to simulate append.

Measure journal size. Above the configured threshold (default 100 KB), flag it and propose rotation into dated history plus a short current-tail file. Rotation requires approval and must preserve every entry.

## Validate every evidence path

Before using retrieved content:

1. Verify the full path belongs to the target project or portfolio root.
2. Reject plausible snippets and same-name files from other projects as **cross-project contamination**.
3. Preserve the supplied identity and path; never infer a missing directory, owner, or canonical location.
4. Classify search outcomes exactly:

| State | Meaning |
|---|---|
| **Exact match** | Exact path, file, identifier, hash, or verified claim fingerprint found. |
| **Likely same family** | Strong relationship, but equivalence or independence is not fully verified. |
| **No result returned** | Search did not locate it; absence is not established. |
| **Verified absent** | An applicable exhaustive listing or inventory supports absence. |
| **Inaccessible** | The item appears to exist but could not be opened or validated. |

Search failure never proves absence. Only a direct listing, verified manifest, or authoritative filesystem inventory can establish a missing file.

## Separate documentary from operational state

Classify each implementation claim as:

- **Documentary state** — stated in a roadmap, handoff, journal, report, transcript, or snapshot.
- **Operationally verified state** — confirmed against the current repository, provider, deployment, database, runtime, or device.

When only documentary evidence exists, say **documented as**, not **is**. List the operational checks still required. Roadmaps remain backlog until implementation is independently verified.

Label every count as **root-level**, **folder-level**, **recursive**, **connector-returned**, or **record-reported**. Never present a cloud list-view item count as a recursive total.

## Audit portfolio roots explicitly

When a root contains multiple projects:

1. Enumerate immediate child projects from the live listing.
2. Build the matrix in [references/portfolio-audit-template.md](references/portfolio-audit-template.md).
3. Record entrypoints, authority, documentary state, operational state, count scope, archives, generated state, companion roots, and blockers per project.
4. Inspect portfolio-level indexes, manifests, status decks, numbered copies, and `.orig` variants separately from project files.
5. Do not substitute an old portfolio review for the live child-folder listing.

## Distinguish pointers, duplicates, controls, and claim families

Classify same-name records as:

1. **Identical duplicate** — byte-identical content; canonical ownership still needs evidence or owner direction.
2. **Intentional pointer** — short file naming one canonical target and containing no independent guidance. Verify the target and all authority references.
3. **Divergent competing control** — substantive copies differ. Treat as a blocking owner decision.
4. **Related claim family** — email, attachment, forwarded copy, revision, invoice, benchmark, or summary tied to one underlying event. Do not count these as independent evidence until proven independent.

A divergent control artifact—authority map, exclusion register, schema, allowlist, validation rule, or status entrypoint—outranks ordinary duplicate cleanup. Companion-root disagreement outranks in-tree duplication because search may surface the stale shared copy first.

## Inventory against artifacts, not names

With a mounted filesystem, run the deterministic helper described in [references/audit-tools.md](references/audit-tools.md). With connector-only access, follow [references/connector-audit.md](references/connector-audit.md) and disclose the downgrade.

Inventory substantive documents, archives, handoffs, transcripts, datasets, scripts, outputs, mirrors, generated state, duplicate groups, required entrypoints, indexes in both directions, reparse points, case-mismatched references, and credential-name hints.

For large roots, let the helper produce exhaustive structural results. Read in full only instructions, authority/current-state claims, handoffs, and representative duplicate candidates. Mark all metadata-only classifications explicitly.

Generated state is not evidence. Excluding it from analysis does not remove it from cloud indexing. A local junction excluded from counts may still be materialized in OneDrive or SharePoint; report local and cloud views separately.

Credential-name matches are warnings. Never open, stage, copy, quote, or index browser profiles, cookies, login databases, `.env`, private keys, tokens, or credential files.

## Classify each substantive file once

Use exactly one bucket:

1. Owner direction and verified current state
2. Documentary authority
3. Current analysis and provenance
4. Active backlog
5. Historical or superseded evidence
6. Raw or unreviewed incoming
7. Read-only mirrors and external checkouts
8. Generated machine state

Unknown files go to an owner-decision list, not a guess. Source snapshots are historical unless tied to a known reproducible commit. Generated state belongs in bucket 8, not history.

## Create additive intake safely

After explicit approval, a connector may create a new package only under an existing incoming, unreviewed, inbox, or quarantine area:

- Label the package non-governing and candidate-only.
- Preserve source-system provenance and date.
- Prefer internal pointers and redacted extracts over raw customer records.
- Exclude unnecessary names, addresses, contact details, signatures, payment links, account data, design IDs, and unrelated plans.
- Keep unknown numeric values null.
- Record duplicate and claim-family status using the evidence states above.
- Do not edit accepted evidence, production data, authority, or exclusion controls.
- After a multi-file upload, wait for completion, reopen the destination, and compare every filename and count with the approved manifest. Partial success is not permission to retry the whole batch blindly.

## Design for fast navigation

Prefer a short root containing an entrypoint, instructions, status, authority map, index, and one current handoff. Adapt to the project’s vocabulary; do not impose a universal numbered tree. Preserve approved files and history. Read [references/navigation-templates.md](references/navigation-templates.md) before proposing navigation changes.

## Execute with measured verification

For moves, use the staged protocol in [references/workflow.md](references/workflow.md): preflight, baseline, copy to labeled staging, verify staging, execute the complete approved map without a discretionary pause, verify final hashes and that every source is gone (a copy is not a move), then remove only verified staging and confirmed-empty source folders.

For record-only or connector edits:

- guard the complete current document with a hash, version, ETag, modified time, or equivalent;
- re-read immediately before writing;
- apply only an exact-context patch;
- never use keyboard-only Home/End insertion in a virtualized editor;
- stop if complete document state or expected context is unavailable;
- reopen after save and verify the title/header, section order, marker count, stale-text removal, links, and protected-file invariants.

A successful click, upload selection, or save message is not proof. Verify the resulting artifact directly.

## Finish with proof

Close with the matching verification block from [references/workflow.md](references/workflow.md). Report outcome first, measurements second, limitations third, and optional follow-up separately.

A run is incomplete if any required fact, file, upload, final path, stale-claim removal, protected-file invariant, or concurrent-write conflict remains unverified. Never describe a production system, dataset, or folder as ready solely because cleanup succeeded.
