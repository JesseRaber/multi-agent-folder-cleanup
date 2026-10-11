# multi-agent-folder-cleanup 1.8.0

Status: released 2026-10-10 (GitHub release v1.8.0).

Minor release: smaller per-mode read sets (register R252, from the Grok Bot evaluation of 2026-10-10), a recycle-path test before any delete (R255), the README FAQ Grok fix, and small helper fixes.

## Read-set size (tiktoken cl100k_base, same method as the 2026-10-10 evaluation)

| Mode (SKILL.md + required references) | v1.7.2 | v1.8.0 | Change |
|---|---|---|---|
| Work, project on Project Rules 4.0.0+ | 6,706 | 4,757 | -29% |
| Work, project without those rules | 6,706 | 6,579 | -2% |
| Audit | 8,185 | 6,676 | -18% |
| Plan | 6,055 | 5,292 | -13% |
| Execute (moves) | 7,495 | 7,526 | +0.4% (R255 and R183 text added) |
| Execute (records) | 6,753 | 6,542 | -3% |

All Markdown in the skill: 32,515 -> 33,805 tokens. Content moved to on-demand files rather than deleted, and R255/R183 add text, so the package is slightly larger while each mode reads less.

## Guidance

- **Work mode defers to adopted rules (S1).** `work-mode.md` keeps what Project Rules 4.0.0 does not say (save locations, document header, pending-file format and applying leftovers, cloud connectors, handoff checklist). Arrival reading, session-log claiming, add-only agents, the shared-record edit procedure and index/tracker upkeep moved unchanged to `work-mode-baseline.md`, read only when the project has not adopted Project Rules 4.0.0 or later.
- Line trims P01-P10: SKILL.md logging and rules-adoption paragraphs shortened; helper commands, Windows write mechanics and the release-package row moved to on-demand references (`audit-tools.md`, new `release-packages.md`); multi-tracker reconciliation moved to `cleanup-principles.md`; the W7 checklist cut from 8 items to 4.
- **One close entry per session (P13);** later turns refresh the close line instead of reopening.
- **Quick-task fast path (R193)** in Work mode.
- **Split cleanup principles (S2):** Execute-only sections moved to new `execute-principles.md`; the inventory method moved to `audit-mode.md`.
- **Audit edge cases on demand (S3):** rarer inventory checks and confusion sources moved to new `audit-edge-cases.md`, together with journal rotation (P02).
- **Recycle-path test before any delete (R255):** Execute mode sends one test file to the recycle path with the exact command it will use, confirms it reached the Recycle Bin, and stops if not. A delete through a remote shell or device bridge without a passing test does not happen. Observed 2026-10-10: a bridge-shell "send to Recycle Bin" deleted a folder permanently with no error.
- Restored the move-safety sentence (R183); arrival line takes the helper version from a real `--version` run or says `helpers not run` (R181); navigation templates do not add root STATUS/AUTHORITY/HANDOFF/INDEX files beside existing continuity files (R134); Codex/ChatGPT default prompt names the modes (R102); on-demand notes on Git lock files over bridged OneDrive, cloud-only I/O errors and locating PowerShell 7 (R238-R240).
- README FAQ: Grok uses the Microsoft Copilot agent-only ZIP, not UNIVERSAL.

## Helpers (Python and PowerShell, same output; read-only)

- Report `Generated` line carries the UTC offset (R127/R179).
- Session-log start times written as `2026-10-06 22:49:40 -04:00` (space before the offset, as Codex writes them) are read as recorded times, not filename fallbacks (R178).
- `--session-index` lists session logs with no header block (Session ID, Start, Tool/runtime) (R180).
- R139 (report unapplied pending tracker insertions) is already covered by `--pending` since v1.7.0.

## Release tooling (R244)

- `release.yml`: the inline version-agreement step duplicated `packaging/check_versions.py`; it now only checks the marketplace catalog.
- `check_versions.py` and `verify_release.py` note the github-release skill version they were copied from (0.1.0).
- Not done: adding a `Channel` column to `HOST_INSTALL_LOG.md` would rewrite every existing row of an append-only log; left for the owner to decide.
