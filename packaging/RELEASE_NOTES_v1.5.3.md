# multi-agent-folder-cleanup 1.5.3

Released 2026-10-06.

## Changes

- Every documented move-verification recipe passes `--root`. All subcommands remain compatible without it but emit one clear warning that paths are not confined (R094).
- Python and PowerShell detect unsafe ZIP members after normalizing slash direction, including embedded `..`, absolute and drive-qualified names; only offending members appear under the unsafe heading (R123).
- Unhashed files are reported in three classes: credential-guarded files as intentionally not hashed, linked paths as not followed, and unreadable, locked or cloud-placeholder files with the existing stop before any Execute pass (R124).
- Session parsing accepts `Started`, `Start`, `Start time` and `Start Time`, falls back to filename time with a no-offset label, uses the parsed start for orient baselines, and does not promote a turn-header fragment to Latest outcome (R096).
- Orient pairs session logs with their matching scratch folders and reports unpaired scratch separately (R126).
- Documentation corrects optional-rules packaging, audit taxonomy routing, record-edit coordination, command fallbacks and the single canonical tracker (R128–R130, R135, R138).

## Known limitations retained for later

- Hard-link identity and move safety remain deferred under R065.
- Move-map swaps and cycles still stop through existing collision behavior; distinct guidance and intermediate-name support remain deferred under R131.
- Claims-section noise from generated files (for example `node_modules/*/index.js`) remains deferred under R125.
- Target collisions are still case-folded on every volume without a banner saying so; deferred under R136.

## Publication boundary

Installed host copies are updated separately; this release does not change any host by itself.
