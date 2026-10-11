# Execute principles

Read this in every Execute run, after [cleanup-principles.md](cleanup-principles.md) and before [execute-moves.md](execute-moves.md) or [execute-records.md](execute-records.md).

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
