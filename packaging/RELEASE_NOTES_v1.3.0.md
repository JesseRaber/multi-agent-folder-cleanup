# Multi-Agent Folder Cleanup v1.3.0

An initial Gemini plan displayed 13 rows differently from its preflighted CSV; guided correction later matched all 75 rows. Inspected v1.2.0 wording also allowed direct restoration over a newer target. This release adds bounded safeguards for these preventable failure modes.

## Changes

- Generated CSV/JSON move review with stable ordinal IDs, raw and resolved-path digests, map location/count, and optional proposal receipt.
- Receipt-bound preflight, baseline and verification; a baseline source check immediately before agent-run movement. No move engine and no rewrite of audit helpers.
- Complete upfront navigation/staging/removal package and separate unresolved owner decisions.
- Stop, preserve evidence and reconcile newer contributions on target mismatch; no automatic overwrite from staging.
- Evidenced instruction authority, actual project logging requirements, and navigation examples aligned with adoption boundaries.
- Optional Project Rules 3.0.0 template and adoption guide in all four archives. Installing this skill does not adopt those rules in a project.

## Packages and upgrade

Use the same `-openai.zip`, `-claude.zip`, `-portable.zip` or `-skill.zip` layout as v1.2.0 and verify the accompanying `SHA256SUMS.txt`. The optional rules live under `references/project-rules/` inside the skill folder. Preserve complete directories during installation.

Legacy helper flags, CSV/JSON formats and baseline verification remain supported. Updated skill execution requires approval of the generated view and complete non-move package; use `--approval` and the final `preflight --baseline` check. New baseline/receipt paths must be unused. A relocated relative map requires a new review even when its raw bytes match.

## Validation scope

The release runs package/version/link checks, helper regression tests, Python/PowerShell parity, Windows and Ubuntu CI, and archive extraction/runtime checks. Isolated behavioral evaluations are documented in `tests/behavioral/README.md`; their observed results are separate from automated tests.

No claim of live OneDrive sync/hydration certification, atomic cross-device locking, universal model behavior, human consent proven by a receipt, or automatic project-rule adoption. Guided corrections are distinct from independent initial evaluations. Checks cannot prevent a caller bypassing the helper or a writer changing files after the check.
