# Cleanup principles — Audit, Plan and Execute

Read this in every Audit, Plan or Execute run, after [preconditions.md](preconditions.md) and before the mode file. Work mode does not need it.

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

## Inventory against artifacts, not names

With a mounted filesystem, run the deterministic helper described in [audit-tools.md](audit-tools.md). First confirm `--version` equals this skill's version; a mismatch is a mixed install whose documented checks may not exist. Prefer `--brief` or `--out` and read **Findings at a glance** before any detail section. With connector-only access, follow [connector-audit.md](connector-audit.md) and disclose the downgrade.

Inventory substantive documents, archives, handoffs, next-prompt files, candidate/released/superseded packages, transcripts, datasets, scripts, outputs, mirrors, generated state, duplicate groups, required entrypoints, indexes in both directions, pending shared-edit artifacts, reparse points, case-mismatched references, and credential-name hints. Also measure what makes shared folders expensive or misleading for agents: the startup read set (flag `AGENTS.md` over 32 KiB, which Codex truncates), live-loading instruction names inside incoming/history/scratch/test fixtures, embedded skill copies at different versions, orphaned temp files from interrupted writes, and files their index never mentions.

Normally execute the helpers and read their reports; load their implementation only when diagnosing, reviewing or changing the code. Blocked content reads are coverage gaps, never evidence that a file is empty or safe.

For large roots, let the helper produce exhaustive structural results. Read in full only instructions, authority/current-state claims, handoffs, and representative duplicate candidates. Mark all metadata-only classifications explicitly.

Generated state is not evidence. Excluding it from analysis does not remove it from cloud indexing. A local junction excluded from counts may still be materialized in OneDrive or SharePoint; report local and cloud views separately.

Credential-name matches are warnings. Report probable private credentials separately from ambiguous cryptographic material and recognizable public certificate bundles; a `.pem` extension alone does not prove a private key. Keep content-read guards conservative: never open, stage, copy, quote or index browser profiles, cookies, login databases, `.env`, private-key candidates or tokens merely to classify them.

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

Prefer a short root containing an entrypoint, instructions, status, authority map, index, and one current handoff. Adapt to the project’s vocabulary; do not impose a universal numbered tree. Preserve approved files and history. Read [navigation-templates.md](navigation-templates.md) before proposing navigation changes.

## Execute with measured verification

For moves, use [execute-moves.md](execute-moves.md): generate the exact map review and proposal receipt; separately list owner decisions and exact navigation, staging and removal scope; obtain approval of that package; use receipt-bound preflight/baseline; copy and verify staging; recheck the approved plan and baseline source hashes immediately before movement; execute the approved resolved pairs; verify final hashes and source absence; apply approved navigation patches and remove only verified approved staging/empty folders. On target mismatch, preserve evidence and reconcile newer contributions before any recovery overwrite.

For record-only or connector edits:

- guard the complete current document with a hash, version, ETag, modified time, or equivalent;
- re-read immediately before writing;
- apply only an exact-context patch;
- never use keyboard-only Home/End insertion in a virtualized editor;
- stop if complete document state or expected context is unavailable;
- reopen after save and verify the title/header, section order, marker count, stale-text removal, links, and protected-file invariants.

A successful click, upload selection, or save message is not proof. Verify the resulting artifact directly.

## Finish with proof

Close with the matching verification block from [execute-moves.md](execute-moves.md) or [execute-records.md](execute-records.md). Report outcome first, measurements second, limitations third, and optional follow-up separately.

A run is incomplete if any required fact, file, upload, final path, stale-claim removal, protected-file invariant, or concurrent-write conflict remains unverified. Never describe a production system, dataset, or folder as ready solely because cleanup succeeded.
