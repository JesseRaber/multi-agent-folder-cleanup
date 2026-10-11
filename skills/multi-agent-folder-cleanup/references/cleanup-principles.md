# Cleanup principles — Audit, Plan and Execute

Read this in every Audit, Plan or Execute run, after [preconditions.md](preconditions.md) and before the mode file. Work mode does not need it. Audit also reads the inventory method in [audit-mode.md](audit-mode.md#inventory-against-artifacts-not-names); Execute also reads [execute-principles.md](execute-principles.md).

## Split mixed-scope requests

When a request combines cleanup with research, data intake, software work, or another domain task, declare separate tracks:

- **Cleanup track** — structure, authority, navigation, duplicates, history, generated state.
- **Domain-work track** — governed by the project’s own evidence, privacy, production, and approval rules.

Cleanup permission is not permission to change domain authority, production data, or accepted evidence. New domain material belongs in the project’s approved incoming/quarantine area until its own review gates pass.

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
2. Build the matrix in [portfolio-audit-template.md](portfolio-audit-template.md).
3. Record entrypoints, authority, documentary state, operational state, count scope, archives, generated state, companion roots, and blockers per project.
4. Inspect portfolio-level indexes, manifests, status decks, numbered copies, and `.orig` variants separately from project files.
5. Do not substitute an old portfolio review for the live child-folder listing.
6. Report a per-project health row: governance/entrypoints, current-state route, session-index drift, unresolved pending updates, generated-state/noise share and primary blocker. Classify an empty placeholder separately from an unmanaged root that contains work but has no discoverable adopted guidance. Do not treat either as permission to install rules.

## Distinguish pointers, duplicates, controls, and claim families

Classify same-name records as:

1. **Identical duplicate** — byte-identical content; canonical ownership still needs evidence or owner direction.
2. **Intentional pointer** — short file naming one canonical target and containing no independent guidance. Verify the target and all authority references.
3. **Divergent competing control** — substantive copies differ. Treat as a blocking owner decision.
4. **Related claim family** — email, attachment, forwarded copy, revision, invoice, benchmark, or summary tied to one underlying event. Do not count these as independent evidence until proven independent.

A divergent control artifact—authority map, exclusion register, schema, allowlist, validation rule, or status entrypoint—outranks ordinary duplicate cleanup. Companion-root disagreement outranks in-tree duplication because search may surface the stale shared copy first.

Canonical status is an authority/navigation fact, not a file-property inference. Do not choose among roots or control artifacts by preferred-looking name, newest modified time, search order, size or matching hash. When same-name roots remain ambiguous, preserve their paths and stable identifiers and stop the affected root-dependent action.

## Protect secrets without erasing private context

Treat passwords, private keys, access or refresh tokens, session cookies, authorization headers, recovery codes and secret-bearing connection strings as secrets. Private links, local or cloud paths, names and ordinary business details may be sensitive or private, but they are not secrets merely because they are non-public.

Unless an applicable governing rule already requires the exact privacy-driven redaction, ask the owner before masking, rewriting, deleting or otherwise redacting content for privacy. Report the affected files, proposed transformation and why it is needed. Preserve a recoverable pre-change copy for authorized privacy edits; actual credential or secret values are the exception and must not be duplicated into recovery material. A cleanup request alone does not authorize privacy rewriting.

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

## Design for fast navigation

Prefer a short root containing an entrypoint, instructions, status, authority map, index, and one current handoff. Adapt to the project’s vocabulary; do not impose a universal numbered tree. Preserve approved files and history. Read [navigation-templates.md](navigation-templates.md) before proposing navigation changes.

## Reconcile competing trackers

With several tracker-like files, establish the canonical one from owner direction, adopted instructions and navigation, never filename, date or completeness, and do not silently merge, rename or delete them. Before treating another as merged or retired, map every actionable item to its canonical tracker ID and record that mapping, keeping each item's status and source identity; search current state and history for completion or supersession before calling an item missing. Unmapped or unverifiable items stay open; a source-level "merged" label is not item-level evidence. Then classify the old file as evidence or History and point it to the canonical tracker; moving or deleting it is cleanup needing approval.
