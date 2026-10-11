# Safety rules

No deletion by default. Deletion is never included unless a separate approval names each target. Prefer history or the Recycle Bin / provider trash over permanent deletion.

Approval is bound to the exact approved mutation list. Discovery never expands it. Anything outside the map is unauthorized.

Deletes go only to the Recycle Bin (or provider trash) after the R255 one-file recycle-path test: create a small test file on the same volume, send it with the exact command that will be used, and confirm it appears in the Recycle Bin and is gone from its path. If the test fails, stop. A delete through a remote shell or device bridge without a passing test does not happen. Record the test result in the session log before the first target.

No connector-based moves. Connector listings are not an Execute path for moves.

No publishing, commit, push, release, or synchronize of skill/repository changes without confirmation immediately before that action.
