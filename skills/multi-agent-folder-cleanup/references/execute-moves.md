# Execute mode — file moves

Use only after approval of the exact package from [plan-mode.md](plan-mode.md). Read [preconditions.md](preconditions.md) first. Record-only and additive work use [execute-records.md](execute-records.md) instead.

## D. Execute mode

Execute has three mutation types. Use **D0–D7** when files move. Use **D8–D9** in [execute-records.md](execute-records.md) for approved record-only work, with D9 applying when the editor is connector- or web-based. Use **D10** for an approved additive incoming package. Do not create an empty move map for record-only or additive work.

### D0–D7. Staged move protocol

Preconditions: an approved literal map, zero collisions, no target over the path threshold.

### D0. Preflight

- Re-scan sources; abort if any source is missing or modified since the map was built.
- **OneDrive/SharePoint:** verify each source file is hydrated. In PowerShell, `Offline`, `RecallOnOpen`, or `RecallOnDataAccess` indicates a placeholder; `ReparsePoint` alone does not, because hydrated OneDrive files commonly retain it. Hydrate or exclude actual placeholders. Confirm the sync client shows idle. If sync is actively running, stop and wait. Run `verify_move.py preflight` under **Windows-native Python** for this step: elsewhere it prints `NOT CHECKED - needs Windows` rather than a count, and an unverified hydration state is not a passed check — a placeholder moves as a stub and the move then verifies against the wrong bytes.
- Confirm free space ≥ 2× the total size being moved (staging holds a second copy).
- Confirm no other agent or job is mid-write.
- Reject junctions/symlinks in source, target and staging path components. The verifier checks existing components; a later path substitution remains possible, so retain writer coordination and recheck immediately before mutation. Its Windows exclusive-read probe is momentary, not a lease. Do not automatically remove Office lock files to make a check pass.

Run `scripts/verify_move.py preflight --map moves.csv --approval <scratch>/proposal.json --root <project>`. `--root` refuses any source or target outside the project; pass the same `--root` to `review`, `baseline` and `verify`. Unguarded calls remain available for compatibility but print a warning that paths are not confined. Execution recipes must use the approved receipt and explicit root. Relative paths in the map resolve against the map file's folder, and an Excel "CSV UTF-8" byte-order mark is accepted. Target collisions are checked case-insensitively, because `Plan.md` and `plan.md` are one file on Windows, OneDrive and SharePoint. It checks collisions, missing sources, existing targets, duplicated sources, path length, and cloud placeholders in one pass and exits nonzero if any fire. A nonzero exit is a stop condition — resolve and re-run, do not proceed on judgement.

### D1. Baseline hashes

Hash every source file (SHA-256): `scripts/verify_move.py baseline --map moves.csv --approval <scratch>/proposal.json --root <project> --out <scratch>/baseline.json`. The new baseline records plan identity and resolved pairs; it never overwrites an existing baseline. Keep the receipt and baseline immutable.

Save the baseline to a scratch location **outside** the target root, e.g. `%TEMP%\cleanup-baseline-<timestamp>.json`. Move-map receipts, reviews and recovery baselines belong outside the source/target trees being reorganized; the baseline command refuses an in-tree destination. Required project session logs retain their adopted destination and are recorded as continuity deltas, not moved as test evidence. Keep the baseline until the session is fully closed out; it is the only way to reconstruct what was where if something goes wrong later.

### D2. Copy to labeled staging

Copy — do not move — into a clearly labeled staging folder, e.g. `_STAGING_<timestamp>/`. Prefer a location on the same volume but **outside** any OneDrive/SharePoint-synced root: staging inside a synced root uploads a complete second copy that other agents and org search will index as a duplicate tree. If staging must live inside the root, say so in the report and remove it as soon as D5 passes. Mirror each target's path relative to the move map's common target root; do not flatten staging to basenames, because same-named files from different folders would collide. The baseline records the common target root used by `verify --stage`. The staging name must make it obvious to any agent that arrives mid-operation that this is transient.

### D3. Verify staging

`scripts/verify_move.py verify --baseline <scratch>/baseline.json --approval <scratch>/proposal.json --root <project> --stage <staging-dir>`

Any mismatch or missing file: stop, report, change nothing further.

### D4. Move — no pause

Immediately before movement, run `scripts/verify_move.py preflight --map moves.csv --approval <scratch>/proposal.json --baseline <scratch>/baseline.json --root <project>` and recheck the separately approved patches/staging/removal package under adequate writer coordination. This compares plan identity and current source hashes to the baseline. A successful check is point-in-time evidence, not an atomic lock or proof of idle cloud sync. All helpers remain non-mutating against the target; the agent performs the separately authorized moves from the approved baseline's resolved pairs, not a freshly invented or retyped list.

Execute the exact approved list in one uninterrupted pass. **Do not add a discretionary approval pause between already approved paths.** A partially executed move is the dual-tree failure the whole protocol exists to prevent. However, a failed safety check, changed source, missing file, collision, hash mismatch, or newly required action outside the map is a stop condition: preserve staging, stop at the safest recoverable boundary, and report the exact partial state.

An agent-written move script must invoke `verify_move.py` with the approved receipt/root/baseline as applicable, or implement the same current-source, existing-target, already-moved, identity and hash checks. It must be safe to run twice and must never overwrite an archived original or any existing target. If a run produces unexpected behavior, inspect and reconcile the complete current source/target/staging state before any rerun; do not assume the first run failed cleanly. Archive-and-stub (moving a file and leaving a pointer stub in its place) is not part of this protocol; it needs its own owner-approved scope, map and acceptance checks.

This is consistent with normal consent practice rather than an exception to it: approval was obtained for the entire map in C3, so every path touched here is already authorized. Anything *outside* the map is not, and does not become authorized by being discovered mid-run.

### D5. Verify final

`scripts/verify_move.py verify --baseline <scratch>/baseline.json --approval <scratch>/proposal.json --root <project>`

Final verify also fails when a source file still exists: a verified target plus a surviving source is a copy, which is the dual-tree state this protocol prevents. Use `--allow-source-present` only when the approved plan was explicitly a copy.

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
- Refuse ordinary cleanup through a junction or symlink, including linked ancestors; do not use recursive removal to detach links. Leave the path in place and request a separately reviewed link-specific operation. A successful verifier result never authorizes removal by itself.

### D7. Update navigation

Apply the exact navigation/current-state patches approved in C2 ([plan-mode.md](plan-mode.md)) to the verified final paths. Re-read and coordinate shared writes; preserve warnings and unrelated contributions. If the live context differs, stop the affected patch and reconcile rather than inventing a broader rewrite. Use verified facts only. Cleanup remains incomplete while required post-move navigation is unresolved. Instruction files remain untouched unless the owner separately approved an exact factual correction under A2; list any such intended edit explicitly in the verification block.

## E. Move verification block

Close every move Execute run with this exact block, filled from measurements rather than expectation:

```
VERIFICATION
- Approved map SHA-256:        <digest>
- Resolved-pairs SHA-256:      <digest>
- Pre-move source check:       passed / failed / NOT CHECKED
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

---

## F. Failure recovery

- **Hash mismatch at staging:** source is being written concurrently, or the copy failed. Do not proceed. Report the specific file.
- **Hash mismatch at target:** stop dependent writes and staging cleanup. Preserve the current target and staged recovery evidence within authorized, non-secret scope. Record source/target/staging hashes and partial state, then reconcile intervening contributions with the responsible writer. Never automatically overwrite the target from staging: staging may predate newer work. Restore, merge or reverse only the exact reconciled recovery action within existing authorization; request narrowly scoped approval when recovery would exceed it.
- **Move interrupted:** preserve staging and reconcile every approved pair against the baseline and any newer contributions. List whether each file is at source, target or both. Resume or reverse only a reconciled authorized remainder; never infer that a rollback may overwrite later edits.
- **Placeholder discovered mid-move:** a placeholder here means D0's hydration precondition was false, so the environment is not the one the approval assumed. Skip that file and immediately re-check hydration across the *remaining* sources before touching them. If it is isolated, finish the approved remainder and report the one file as unmoved — a completed map minus one known file is a smaller dual state than a map abandoned halfway. If others are also dehydrated, the sync client is actively reclaiming files underneath you and every subsequent hash is untrustworthy: stop at the safest recoverable boundary, preserve staging, and report the exact source/target/staging state of every mapped file. Reconcile before resuming or reversing the approved remainder.

## G. Execute report format

**Execute report:** outcome first, then the verification block matching the move or record-only subtype, then optional follow-up work in a clearly separate section.
