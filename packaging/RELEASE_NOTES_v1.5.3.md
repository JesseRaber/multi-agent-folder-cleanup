# multi-agent-folder-cleanup 1.5.3

Status: local candidate; not pushed, tagged, released or installed.

## Changes

- Every documented move-verification recipe passes `--root`. All subcommands remain compatible without it but emit one clear warning that paths are not confined (R094).
- Python and PowerShell detect unsafe ZIP members after normalizing slash direction, including embedded `..`, absolute and drive-qualified names; only offending members appear under the unsafe heading (R123).
- Credential-guarded files are reported as intentionally not hashed, separately from unreadable, locked and placeholder files (R124).
- Session parsing accepts `Started`, `Start`, `Start time` and `Start Time`, falls back to filename time with a no-offset label, uses the parsed start for orient baselines, and does not promote a turn-header fragment to Latest outcome (R096).
- Orient pairs session logs with their matching scratch folders and reports unpaired scratch separately (R126).
- Documentation corrects optional-rules packaging, audit taxonomy routing, record-edit coordination, command fallbacks and the single canonical tracker (R128–R130, R135, R138).

## Known limitations retained for later

- Hard-link identity and move safety remain deferred under R065.
- Move-map swaps and cycles still stop through existing collision behavior; distinct guidance and intermediate-name support remain deferred under R131.

## Publication boundary

This candidate requires owner review, remote push/PR, CI, tag/release authorization and separate host-update authorization. None is implied by local test or package results.
