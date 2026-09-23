# Connector and Web Audit Protocol

Use this when the target is reachable only through OneDrive, SharePoint, Graph, enterprise search, or a browser listing. This is a real structural and documentary audit, but it is not a filesystem audit.

## Access and limits

Record the provider, root URL, access route, and whether a mounted path exists. Mark hashes, hydration, OS path length, reparse points, and byte comparison unverified when the route cannot measure them.

Connector access supports Audit and may support approved record-only or additive-intake execution. It never supports verified move execution because hydration, Windows path length, source hashes, and staging are unavailable.

## Enumerate from the live listing

- Record immediate child names.
- Label displayed counts as root-level or folder-level, never recursive.
- Inspect every project root and its context/navigation subtree.
- Scroll the full listing before concluding that an item is absent.
- Search failure does not prove absence.

## Validate retrieved paths

For every enterprise-search or connector result:

1. Compare the full returned path with the target project root.
2. Reject results from another project, companion root, or unrelated site.
3. Record rejected results as cross-project contamination.
4. Do not use a mismatched result to establish presence, absence, authority, or current state.
5. Treat quoted hashes or byte comparisons as record-reported evidence, not independently recomputed evidence.

## Build an entrypoint matrix

Derive expected files from owner instructions. Typical candidates are `AGENTS.md`, `CLAUDE.md`, `README_FIRST.md`, `PROJECT_ROADMAP_STATUS.md`, `AUTHORITY_MAP.md`, `INDEX.md`, `AI_CONTEXT/PROJECT_QUICK_CONTEXT.md`, `AI_CONTEXT/PROJECT_ACTIVITY_JOURNAL.md`, and `AI_CONTEXT/CHAT_INDEX.md`.

Classify each as opened, directly listed, path-validated search result, missing by direct exhaustive listing, alternate name, or unverified.

## Evidence-state labels

| Label | Required basis |
|---|---|
| Exact match | Exact path, item identifier, file, hash, or verified claim fingerprint. |
| Likely same family | Related email, attachment, revision, invoice, benchmark, or summary; equivalence not yet proved. |
| No result returned | Search did not locate the item. This is not absence. |
| Verified absent | A direct exhaustive listing or verified inventory supports absence. |
| Inaccessible | Existence is indicated, but content or metadata could not be validated. |

## Separate state types

A handoff, roadmap, journal, or report establishes documentary state. Operational state requires current repository, provider, deployment, database, runtime, device, or test evidence. Use **documented as** when operational verification is unavailable.

## Same-name controls

Classify each pair as identical duplicate, intentional pointer, divergent competing control, likely same claim family, or unverified. A pointer must name one canonical relative path and contain no independent behavioral guidance.

## Connector-safe execution

For record-only changes, use `workflow.md` D9. Do not edit from a search snippet or virtualized viewport. Require complete current document state, a service version/fingerprint, exact-context matching, and reopen-after-save verification.

For additive intake, use `workflow.md` D10. Upload only the approved manifest to an incoming/quarantine location. Wait for completion and reopen the folder: multi-file uploads may succeed partially. Compare filenames and counts before any retry.

## Privacy and claim-family handling

Prefer authorized internal pointers and redacted extracts over customer emails, exact addresses, signatures, payment links, account data, design identifiers, or unrelated plans. Treat an email, its attachment, forwarded copies, revisions, invoices, benchmarks, and summaries as one claim family until independence is proven.

## Connector audit output

Report access route and limitations; root and count type; projects inspected; entrypoint matrix; documentary and operational findings; rejected cross-project results; duplicate/pointer/claim-family findings; archives left unopened; generated state; owner decisions; and exact checks that remain unverified.
