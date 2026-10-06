# Execute mode — record-only edits and additive intake

Use only for an approved literal list of factual record changes (D8, D9 for connector or web editors) or an approved new incoming package (D10). Read [preconditions.md](preconditions.md) first. File moves use [execute-moves.md](execute-moves.md).

### D8. Record-only Execute

Use this subtype for an approved literal list of factual corrections where no file moves. It covers navigation, status, authority maps, handoffs, and separately approved factual instruction-entrypoint corrections. It does not authorize new behavioral rules, authority changes, permission changes, or any file omitted from the approved list.

Before D8 or D9 edits, establish a supported conditional update, a cooperating lock of adequate scope, or a designated single writer covering the relevant writers/devices. Rereads, timestamps, hashes, ETags and fingerprints are integrity/conflict checks, not proof of exclusivity. If coordination is unavailable, stage the exact edit as pending and defer only the unsafe shared mutation.

1. Record the exact approved files and the intended factual changes. Name any instruction file separately.
2. Immediately before editing, capture SHA-256 and modified time for every approved file plus any authority or instruction files that must remain unchanged.
3. Re-read the live files. If a hash or modified time changed after review, another writer is active: do not force the old text back. Re-stage from the new version, merge only the approved facts, and repeat the guard.
4. Apply minimal exact-context patches. If expected context does not match, treat that as a safe stop rather than using broad replacement or overwrite.
5. Re-hash the changed files and verify the intended facts directly. Search for the specific stale or contradictory claims the correction was meant to remove or label; absence must be measured, not assumed.
6. Verify protected authority and instruction files are byte-identical except for any instruction file explicitly approved in step 1. For an approved instruction edit, verify that only the named factual text changed and that behavioral rules, authority, scope, permissions and read order remain intact.
7. If a required journal write occurs after these checks, guard it independently and verify the appended entry. Do not present the journal hash as proof that earlier shared records remained unchanged.


### D9. Connector-safe record editing

Use D9 only when the user approved exact files and factual changes and the connector or web editor can expose the complete current document. A connector cannot execute moves because hydration, local path length, source hashes and staging are unavailable; that limitation does not prohibit a guarded record-only patch.

1. **Declare the access route.** Name the service, editor, target URL/path, and which local checks remain unavailable.
2. **Capture a service guard.** Prefer ETag, version ID, modified time, content hash, or a full-text fingerprint. Record the expected document title/header and the exact context around every patch.
3. **Re-read immediately before writing.** If the guard changed, another writer is active. Rebase the approved factual patch on the new complete document; never force an older copy back.
4. **Require full document state.** A viewport, preview, search snippet, or virtualized DOM fragment is not the document. If the complete document cannot be obtained, stop and provide the exact patch for manual application.
5. **Patch exact context.** Every expected old fragment must match exactly once. Zero matches or multiple matches is a safe stop. Avoid broad replacement and whole-file regeneration when a narrow patch is possible.
6. **Never use keyboard-only Home/End insertion in a virtualized editor.** It can target the first rendered tile rather than the real document boundary. Use the editor's complete document model, a provider API with concurrency control, or stop.
7. **Save once, then reopen.** Do not treat a save toast or successful click as proof. Reopen the canonical file and verify:
   - expected title/header is first and unchanged;
   - section order is intact;
   - the marker count is exactly one for every new marker;
   - intended stale text is absent or explicitly labeled;
   - neighboring text was not joined, duplicated, deleted or reordered;
   - required links and backticked paths still resolve where measurable;
   - protected authority/instruction records are unchanged outside approval.
8. **Rollback or stop.** If verification fails and provider version history offers a known pre-write version, restore only with authorization appropriate to that system. Otherwise stop, preserve the observed state, and report the exact repair needed. Never improvise a second broad edit.

Record-only connector work is incomplete until the reopened file passes every applicable check.

### D10. Additive intake

Use D10 only after approval of an exact destination and expected-file manifest. The destination must already be classified by the project as incoming, unreviewed, inbox, or quarantine material.

1. Record the exact destination, filenames, expected sizes or hashes when available, and the source-system provenance to preserve.
2. Create a new destination; do not merge into accepted evidence, authority, production data, or an existing package unless that exact merge was separately approved.
3. Label the package non-governing and candidate-only. State its duplicate-control, privacy and review gates.
4. Minimize data. Prefer internal pointers and redacted extracts. Exclude unnecessary customer names, addresses, contact details, signatures, payment links, account data, design identifiers and unrelated plans.
5. Keep unknown values null. Use exact / likely same family / no result / verified absent / inaccessible rather than converting uncertainty into absence or independence.
6. Group email, attachment, revision, invoice, benchmark and summary records into one claim family until independence is proved.
7. Upload the approved manifest once. Multi-file selection may finish partially: wait for completion, reopen the destination, and compare every expected filename, count, size and hash available. Do not retry the whole batch until partial success is ruled out.
8. Update navigation and journals only if approved or required by project instructions, using D8 or D9 independently. An additive package does not authorize edits to controls.

Close additive execution with:

```
ADDITIVE VERIFICATION
- Destination:                    <exact path>
- Expected files:                 N
- Files visibly present:          N/N
- Sizes / hashes verified:        N/N or NOT AVAILABLE
- Duplicate filenames created:    0
- Existing files overwritten:     0
- Non-governing label verified:   yes
- Privacy exclusions verified:    yes
- Accepted / authority changed:   none
- Navigation/journal updates:     <verified list or none>
- Unverified / out of scope:      <list, or "none">
```

Any missing file, unexplained duplicate, overwrite, or unapproved control change makes the additive run incomplete.

## E. Record verification block

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

## G. Execute report format

**Execute report:** outcome first, then the verification block matching the move or record-only subtype, then optional follow-up work in a clearly separate section.
