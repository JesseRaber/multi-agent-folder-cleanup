# Changelog

### 1.7.0 (candidate) — stable release: add-only agents, sequential writers, sync-copy and pending-file checks

- Add-only agent fallback in Work mode: an agent that can only add files uploads into a dated `Incoming/` folder (never a new top-level folder) with a `_PROVENANCE.md` listing tool, time with timezone, files, status and PENDING index/tracker/session-index rows; the next agent with edit access applies them. An upload with neither a log nor a provenance file is incomplete. End-of-request checklist item added.
- `muse` added to tool slugs; an unlisted tool uses its own short lowercase name and never skips the session log.
- Audit mode B5 "Attribute activity": name searches are not evidence of absence, unmatched changes are unattributed-activity findings, timestamps are converted to the owner's local timezone, and timing-only evidence is reported as "consistent with".
- Optional Project Rules 3.3.0: three additive lines in sections 3, 4 and 7. Gemini Apps and Opal packages still omit `references/project-rules/`.
- Sequential-writer declaration (R156 declaration part, R211): Project Rules 3.3.0 section 5 ships it by default; Work mode W5 lets the active agent edit shared records directly with read-back verification when it is present, and keeps PENDING staging for multi-operator projects. Only the declaration establishes this, never a quiet `--orient`.
- Pending files (R201, R212): one name, `PENDING_<TARGET>.md` with a `Status:` first line; a qualifying writer applies leftovers whose base hash or anchor still matches, verifies by read-back and marks them `APPLIED`; anything else is Conflicted. R200 (exact direct-write test) stays on hold.
- Sync conflict copies and same-name files (R030, R195, R197): edit shared files in place, never create a second same-name file in one folder, check for `(1)`/`-COMPUTER` copies and missing originals at arrival and before the final answer; audit reports them and never merges, renames or deletes.
- Cloud connectors and sync folders (R168, R169, R197–R199): new Work-mode subsection — state the view and time of every listing, work by file id and stop when a name maps to several ids, stage replacements in scratch with `Replaces: <old file id>`, one file type per shared record, declare replicas.
- Work mode also: read large trackers by section and journals by tail (R213); session-index row created with the log (R204); cross-agent reviews saved where the reviewed agent will look (R203); cross-project handoffs also delivered to the target's `Incoming/` when authorized (R206); scratch packages kept as ZIP + SHA256SUMS (R207); quick context lists what an in-flight candidate contains (R205); `AI_CONTEXT/` is for continuity records only (R215).
- Audit guidance: AGENTS.md size warning above 16 KB, high above 32 KiB (R214); declared startup read order (R213); retired journals reported once (R161); unpacked packages and repo-shaped folders without `.git` (R207, R208); `AI_CONTEXT/` misuse (R215); B5 does not rely on modified time alone (R209); portfolio rules matrix with rules version, Work routing and core-match columns (R165, R166).
- Project Rules 3.3.0 (unreleased until now) also gains: section 3 `AI_CONTEXT/` continuity-only line, section 5 declaration and same-name/conflict-copy lines, section 7 session-index row at creation.
- Version renamed from the unreleased 1.6.4 candidate to 1.7.0 (owner decision 2026-10-08 23:27 ET) and Batch B folded in, except the mutating `apply_record_patch.py` helper (still deferred).
- Sources: owner handoffs from Muse, GaugeWorx, Windows PC Monitor, GitHub Release Skill and jesseraber.net reviews, 2026-10-08; Claude sessions `0e9d1f7d`, `6dbd138b`, `99022649`.

### 1.6.3 (released 2026-10-08) — portfolio audit corrections

- Preserve filename-derived session times without a machine offset, report nonstandard session filename tool slugs and IDs, and show every portfolio child in brief mode (R158–R160).
- Identify the running audit helper path and version during orientation, and label provider sync/index state unchecked (R164, R167).
- Clarify non-loading instruction backups, pending-edit retention, and the device helper access route (R157, R162, R163).

### 1.6.2 — release safety

- Grok routed to the `-microsoft-copilot-agent-only` package in README and `INSTALL-universal.md` (owner upload test 2026-10-05: Universal rejected for `.ps1`, Copilot ZIP accepted).
- Release workflow: draft-first, refuses an existing release, requires the notes file, no `--clobber`, checkout without persisted credentials, `github.event_name == 'push'` guards; comment corrected to seven archives.
- Added `packaging/check_versions.py`, `packaging/verify_release.py`, `packaging/version_files.json` (from the github-release skill) and `HOST_INSTALL_LOG.md`.
- Packager pins ZIP `create_system`; `.gitattributes` forces LF, so Windows and Linux builds match.
- Source: github-release project, Claude session `fc8b2159-5283-4880-9b59-739c33b8de8f`.

### 1.6.1 (released 2026-10-06) — record verification

- Added read-only `scripts/verify_records.py` (R150, R154): per-file SHA-256, UTF-8 validity, BOM, CRLF/LF/lone-CR counts, mojibake markers outside code, unresolved Markdown relative links and table damage, plus `--compare` (exact / newline-normalized / whitespace-only / differ) and `--expect-sha256`. Work mode now asks agents to cite its output before calling a shared-record edit verified. Regression tests cover each check and confirm inputs are never modified.
- Source: Claude session `7c06e17e-ede7-484c-9d8f-32e0fa6e07c2`; scope confirmed by the Codex (36e6245f) and Manus (07cf1444) audits of 2026-10-06.

### 1.6.0 (released 2026-10-06) — shared-record, rerun and privacy safeguards

- Fixed pre-existing R100 parity under Windows PowerShell 5.1 by giving tied session timestamps and duplicate IDs the same ordinal, case-insensitive relative-filename tie-breaker in both helpers. Added a tied-timestamp regression fixture plus a dependency-gated runner and pinned PyYAML development requirement.
- Require item-level tracker mapping and a completion/supersession false-gap check before a source is treated as merged or retired (R140).
- Require recoverable non-credential pre-edit copies, before/after hashes, exact diffs and line-ending, encoding and Markdown-table structure checks before shared-record edits are called verified, zero-loss or aligned (R141-R142).
- Require idempotent agent-written edit/move scripts, move verification or equivalent guards, preserved archived originals and current-state inspection before a rerun after unexpected behavior (R143).
- Keep session-log ownership with its writer and make open-work lists complete, including owner decisions and corrected-turn restatements (R144-R145).
- Define actual secrets narrowly, require owner approval for other privacy-driven redaction and preserve recoverable non-secret originals (R146).
- Opal review follow-ups: Work-mode pending-edit outcomes go in the acting writer's own log; the universal install fallback includes Work mode; install requirements distinguish `audit_folder.py` from `verify_move.py` hydration checks; archive-and-stub is stated to be outside the move protocol; optional Project Rules bumped to 3.2.0 for the section 9 change.
- Source: Claude handoff/review session `9ea792fb-da82-4728-982b-0d544f7c891e`, T001-T003; implementation tracks register rows R140-R146.

### 1.5.3 (released 2026-10-06) — audit parity and documentation corrections

- Added warn-only `--root` guidance to every move-verification recipe and a clear warning for unconfined helper calls (R094).
- Hardened ZIP member-name checks, separated credential-guarded files from true hash failures, broadened session-header parsing and filename fallback labels, and counted possibly active writers by distinct session in both helpers (R096, R123, R124, R126).
- Added regression coverage and clean no-PowerShell skips; corrected Work/Plan fallbacks, audit taxonomy routing, record-edit coordination, optional Project Rules package wording and canonical-tracker examples (R100, R128–R130, R135, R138).
- Known deferred limitations: hard-link identity checks (R065), move-map swaps/cycles (R131), claims-section noise (R125) and the case-fold collision banner (R136).

### 1.5.2 (released 2026-10-04) — move-safety fixes and helper examples

- `verify_move.py`: new `--root` on `preflight`, `baseline` and `verify` refuses sources/targets outside the project (OUTSIDE ROOT) and a baseline written inside it (register R094).
- `verify_move.py`: a map whose common root is the filesystem root now guards each pair's folder instead of refusing every `--out` (R105); case-only renames on case-insensitive volumes are not reported as TARGET EXISTS (R106); macOS path comparisons fold case (R107); the Windows exclusive-read probe uses the `\\?\` extended-length form for long paths (R108).
- `audit-tools.md`: `-ExecutionPolicy Bypass`, a `powershell.exe` fallback and `python3` examples (R089–R091); guidance when a host package omits a helper (R103 follow-up).
- SKILL.md: what to do when a package does not bundle `references/project-rules/` (R104).
- Removed the legacy `references/workflow.md` router, which duplicated SKILL.md's mode table; fixed the stale `workflow.md B2` comment (R098, R110).
- pyflakes cleanup in `audit_folder.py`; no behavior change (R099).
- Author link to jesseraber.net in plugin metadata and a README credit line (R088).

### 1.5.1 candidate — root identity and shared-work convergence

- Stop root-dependent work when a connector or search returns multiple same-name candidate project roots. Record full paths/sites and stable IDs; do not silently combine results or select a winner.
- Canonical-root selection can come only from owner direction or applicable adopted authority/navigation—not filename, modified time, search rank, size or hash equality.
- Audit reports now include a compact claim table separating Documented, Observed, Inferred and Unknown conclusions with evidence, scope/date and the verification needed.
- Work mode performs a bounded pre-write lookup in the intended folder, project index and canonical tracker before creating an important standalone file.
- Work mode and the optional Project Rules require one authoritative project-wide tracker for all proposed changes, future work, deferred work and open tasks. Supporting plans link to stable tracker IDs instead of growing independent backlogs; existing competing lists are reconciled with provenance, and unsafe shared writes become one exact pending tracker insertion rather than another roadmap file.
- Add `-microsoft-copilot-agent-only.zip`: the full skill and Python helpers without `audit_folder.ps1`, which Microsoft Copilot's upload validator rejects as an unsupported skill-script type.

### 1.5.0 candidate — Work mode

- New **Work** mode (`references/work-mode.md`, W1–W7) for ordinary work in a shared multi-agent folder: arrive within a read budget, claim your own session log and scratch folder, save new files where the next agent will look, give new documents a status header, edit shared records with re-read/minimal-edit/verify, index deliverables only, and hand off at the end of every request. Work mode never moves, renames or deletes existing files.
- `audit_folder.py --orient` / `audit_folder.ps1 -Orient`: startup read-set and quick-context size, recent sessions, possibly active writers (session logs and scratch folders changed within `--active-minutes`, excluding `--session-id`), files changed since `--since` or the latest other session, and changed files the index never names. Modified-time evidence is labeled as leads only. Absorbs register item R025 (orient mode inside existing helpers).
- `--session-index` / `-SessionIndex`: session logs missing from the session index (with proposed rows), index links to missing logs, nonstandard session files. Read-only. Absorbs R026.
- SKILL.md slimmed from 15 KB to 7 KB: a mode router plus authorization, instruction and evidence rules. Cleanup-only sections moved unchanged to `references/cleanup-principles.md`, which Audit, Plan and Execute read after `preconditions.md`. Description broadened so the skill also loads for saving, naming and indexing work.
- Optional Project Rules template 3.1.0: one subsection pointing to Work mode.
- Python/PowerShell parity for the new checks verified on Windows PowerShell 5.1; tests in `tests/test_v15_work_mode.py`.
- Portfolio follow-up adds managed/unmanaged/empty project state, session and missing-index counts, pending-update counts, and guidance to reuse recent same-task evidence before starting expensive duplicate work.
- Full audits now surface handoff ambiguity, pending-update lifecycle state, candidate/released/superseded package-channel ambiguity, quick-context header drift, and credential-risk tiers while preserving the conservative content-read guard.

- Release ZIPs renamed by audience: `-UNIVERSAL-skill` (replaces `-skill` and `-portable`), `-claude-code-plugin`, `-codex-chatgpt-plugin`, `-gemini-apps-only`, `-opal-only` (new), `-project-rules-optional`. Install guides and README open with a which-ZIP table.
- New `-opal-only` package: `SKILL.md` with name/description-only frontmatter plus `references/*.md`, no folder entries, matching an Opal export (confirmed by import).
- `-gemini-apps-only` leaves out `audit_folder.py`, which Gemini Apps' upload security scan rejects in 1.4.1.
- One packager, `packaging/build_packages.py`, now builds, byte-checks and smoke-tests every archive for both releases and local candidates.

## 1.4.1 - 2026-10-02

- Content-read guard in both audit helpers: credential-hinted paths, links inside the root and detected cloud placeholders are never opened; blocked reads are not counted as verified hashes.
- Markdown links: balanced/escaped parentheses, document-relative resolution, root-only fallback disclosed; case checks stop at the audit root.
- `--brief` caps applied to every detail list.
- `verify_move.py`: refuses junction/symlink traversal inside the plan, refuses to hash detected placeholders, and runs a Windows exclusive-read preflight that reports sharing violations.
- Link checks stop at the audited root or the plan's common folder, so projects under a linked parent folder stay usable. Found in review of the candidate.
- Regression tests added (68 total). CLI defaults and receipt format unchanged.

## 1.4.0 - 2026-10-01

Changes come from a read-only scan of an 18-project shared portfolio used by Claude, Codex, Antigravity/Gemini and other agents (findings in the owner's project records, 2026-10-01).

### Token and time efficiency

- Split `references/workflow.md` into `preconditions.md`, `audit-mode.md`, `plan-mode.md`, `execute-moves.md` and `execute-records.md`. `workflow.md` is now a short router; section labels (A1–G) are unchanged. An Audit run reads about 15 KB instead of 35 KB.
- `audit_folder.py` / `audit_folder.ps1`: `--brief` / `-Brief` caps every list at 10 lines; `--out` / `-Out` writes the full report to a new file outside the root and prints only Summary and the new **Findings at a glance** block. Every report now ends with that block.
- Suggested exclusions collapse recurring names to one `**/name/**` pattern and report a Python environment (`pyvenv.cfg`, or three or more `*.dist-info` folders, as from `pip --target`) as one cluster. Previously a 1.3 GB vendored install produced 20 fragment patterns and was never named.
- `--prune-noise` / `-PruneNoise` leaves high-confidence generated state unwalked and lists it; `--max-seconds` / `-MaxSeconds` stops the walk and discloses unvisited directories. Both are reported as coverage gaps.
- Lists print relative paths; scratch working copies are counted but not listed as claims.

### Multi-agent checks

- **Startup read set** section: root auto-loaded instruction files plus `--entrypoint` files, totalled against `--read-budget-kb` (default 40).
- `AGENTS.md` over 32 KiB is flagged: Codex reads 32 KiB by default and drops the rest silently.
- Instruction files are split into auto-loaded names and README/startup files. Auto-loaded names inside incoming, history, archive, scratch, backup, staging, proposed or skill-copy folders are flagged as live-loading names in non-governing locations.
- `--index-coverage INDEX=DIR` / `-IndexCoverage` lists files directly in a folder that its index never mentions (by name, URL-encoded name or UUID).
- **Embedded skill copies** section lists every `SKILL.md` and `.skill` with name and version and counts names with several copies.
- **Possible orphaned temporary files** section: Info-ZIP `zi??????` temp names, Office `~$` files, LibreOffice locks, `.tmp`/`.temp`/`.partial`/`.crdownload`, and extensionless files with archive magic bytes (8-byte read; cloud-only placeholders are skipped).
- `--host-root` / `-HostRoot` measures path length as the real host path plus the relative path, for folders mounted under another prefix. The report states what it measured against.
- `--version` on `audit_folder.py` and `verify_move.py`, `-Version` on `audit_folder.ps1`; a test pins all three to the SKILL.md version so mixed installs are detectable.

### Parity and packaging

- PowerShell sorts with ordinal composite keys so ties and punctuation order exactly like Python; unified "... and N more" wording, identical-group header and per-group overflow lines. A new parity suite compares full reports with every new option, `--brief`/`--prune-noise`, and `--out` summaries.
- Release builds two more assets: `-gemini-apps.zip` (skill without `audit_folder.ps1`, `agents/openai.yaml` and `references/project-rules/`, which the Gemini Apps uploader rejects) and `-project-rules.zip`.

### Behavior changes to review when upgrading

- Report section changes: path-length lines are relative and preceded by `Measured against:`; "Instruction files found" lists auto-loaded names and README files separately; new sections appear in every report. Scripts that parse the old text may need updating.
- Links to `references/workflow.md` still resolve, but it is now a router; read `preconditions.md` and the mode file.

## 1.3.0 - 2026-09-30

- Added `verify_move.py review` to render exact CSV/JSON execution pairs, ordinal IDs, raw-map and resolved-pairs SHA-256 digests, map location and row count. Optional proposal receipts identify plans; they do not prove owner approval.
- Added `--approval` guards to preflight, baseline and verification, and `preflight --baseline` source checks immediately before agent-run movement. New baselines retain map identity; evidence outputs refuse overwrite. Legacy unguarded commands remain supported, but do not meet the updated execution protocol.
- Required complete proposed navigation patches, staging/removal paths and separated owner choices before approval. No automatic movement engine was added.
- Replaced automatic target restoration with evidence preservation and reconciliation of intervening contributions before authorized recovery.
- Clarified evidenced instruction adoption, scoped policies and actual project continuity obligations, including every-request logging and provenance/safe-save fallbacks. Aligned navigation examples so classification and folder names do not create authority.
- Bundled optional reusable Project Rules 3.0.0 with a separate adoption/merge guide in every skill package. Installing the skill does not adopt or overwrite project policies.
- Added focused helper regression tests and isolated behavioral evaluations. These address preventable failure modes from inspected wording and one guided Gemini test family; they do not establish universal model/host compatibility.

### Upgrade notes

- New proposals use generated receipts; changing map bytes or relocating the map requires a fresh review/approval. Retained legacy baselines remain verifiable but cannot be receipt-bound retroactively.
- Use new baseline/receipt filenames; creation refuses existing files to preserve evidence.
- Source/map checks remain point-in-time; exclusive writers, cloud state and actual authorization must be established separately.

## 1.2.0 - 2026-09-29

- Added portfolio-root auditing, strict retrieved-path validation, count-scope labels, documentary-versus-operational state, and intentional-pointer versus divergent-control classification.
- Added connector-safe record-only and additive-intake protocols, including complete-document guards, virtualized-editor prohibitions, concurrent-writer checks, partial-upload recovery, privacy minimization, and reopen-after-save verification.
- Added `references/connector-audit.md` and `references/portfolio-audit-template.md`.
- Added five explicit lookup outcomes: exact match, likely same family, no result returned, verified absent, and inaccessible.
- Added journal-size threshold reporting, repeatable expected-entrypoint checks, advisory portfolio matrices, conservative pointer-stub candidates, and expected-upload manifest verification to both audit helpers.
- Expanded Python/PowerShell parity and regression tests, including a partial six-file upload fixture and move-verification failure/success checks.
- Updated OpenAI, Claude, marketplace, portable, install, README, release-note, and version metadata for one shared canonical skill body.
- Preserved the v1.1 move protocol, reparse-point handling, case-mismatched reference checks, credential-name warnings, ZIP no-extract inspection, and package/release safeguards.
- Included the post-v1.1 release-workflow and installation corrections that had remained under `Unreleased`.

### Fixed (from the 2026-09-23 deep scan of v1.1.0)

- `--exclude` / `-Exclude` now use one segment-aware, case-insensitive glob in both helpers. Python missed a root-level `logs/` for `**/logs/**`; PowerShell substring-matched it and also excluded `Catalogs/` and `changelogs.md`.
- Unreadable directories are reported under **Directories not readable** and in a closing **Coverage gap** line instead of silently vanishing from every count.
- Only junctions and directory symlinks (name-surrogate reparse points) are skipped. A bare ReparsePoint attribute, which OneDrive Files On-Demand puts on ordinary synced folders, no longer hides a folder's contents.
- The Python audit no longer crashes with `UnicodeEncodeError` on non-ASCII filenames when output is redirected on Windows.
- `verify_move.py`: accepts Excel "CSV UTF-8" maps with a byte-order mark; resolves relative map paths against the map file; detects case-only target collisions; and fails final verify while a source still exists (a copy is not a move). The new `--allow-source-present` flag is for approved copies.
- `audit_folder.ps1` walks the tree explicitly: it is linear instead of quadratic (40,000 files in about 8 s instead of 64 s), does not follow junctions under Windows PowerShell 5.1, resolves UNC/NAS roots via `ProviderPath`, reads indexes as UTF-8 on 5.1, and no longer crashes when an index path is a directory.
- Index link checks now understand `<angle targets>`, `"titles"`, `%20` escapes and any URI scheme, and ignore version strings such as `v1.1.0` in backticks.
- Python/PowerShell output parity: case-insensitive duplicate names, lower-case extensions, same path-length scope and cap, root-level-only instruction conflict warning, deterministic ordering. A new test compares the two full reports line by line.
- More credential-name hints: `*.pem`, `*.key`, `*.pfx`, `*.p12`, `*.kdbx`, `*.ppk`, `*.jks`, `id_ed25519`, `id_ecdsa`, `.netrc`, `.git-credentials`.
- Documentation: removed dead `SKILL.md §3/§4` references; preflight now runs before baseline everywhere; staging is recommended outside synced roots; the Claude.ai upload instructions no longer contradict the package layout; checksum steps include Windows `Get-FileHash`.
- Release and CI: new `-skill.zip` asset (the skill folder only) for Claude.ai and other skill uploaders; a Windows CI job runs the full suite with PowerShell 7 plus a Windows PowerShell 5.1 junction smoke test; actions are pinned by commit SHA; the dispatch version input is passed through the environment and validated as semver.
- `audit_folder.ps1` relativizes paths against the walk's own spelling of the root. On Windows, enumerated paths can carry expanded 8.3 short names (`RUNNER~1` → `runneradmin`), which previously added a bogus leading folder to every path, overstated max depth by one, and skipped the root-level instruction-file conflict warning. Found by the new Windows CI job's full-report parity test.
- `claude plugin validate` was run against `plugin.json` and `marketplace.json` on 2026-09-23 and passed, resolving the v1.1.0 "not verified" note.

### Behavior changes to review when upgrading

- `verify_move.py verify` (without `--stage`) now exits nonzero while any source file still exists. Pass `--allow-source-present` for an approved copy.
- Relative paths in a move map resolve against the map file's folder instead of the current directory.
- `--exclude` / `-Exclude` matching is case-insensitive, and `*` no longer crosses `/`. A pattern with no `/` (for example `*.log`) still matches at any depth.

## 1.1.0 - 2026-09-01

- Added a native OpenAI skills-only plugin manifest at
  `.codex-plugin/plugin.json` and skill presentation metadata at
  `skills/multi-agent-folder-cleanup/agents/openai.yaml`.
- Refactored the 30 KB `SKILL.md` into a concise routing and safety contract;
  detailed helper usage now lives in `references/audit-tools.md`, while the
  complete operational protocol remains in `references/workflow.md`.
- Fixed Python/PowerShell parity for versioned claim filenames, claim byte-size
  reporting, and dotfile extension classification.
- Added pull-request CI with OpenAI's pinned validators, package consistency
  checks, PowerShell parsing, and a shared-fixture cross-language parity test.
- Added a separate `-openai.zip` release package, OpenAI install guide, and
  v1.1.0 release notes. Synchronized both plugin manifests and skill metadata.

- Added `.claude-plugin/marketplace.json`. `/plugin marketplace add` reads a
  marketplace catalog from that path; `plugin.json` alone is a plugin manifest
  and is not a catalog, so the GitHub install command shipped in the v1.0.0
  `-claude.zip` could not have worked. The repository is now both the catalog
  and the plugin it lists (`"source": "./"`).
- Corrected `packaging/INSTALL-claude.md`, which told users to run
  `/plugin marketplace add` against a repository with no catalog, and omitted
  the required `/plugin install <plugin>@<marketplace>` second step.
- Corrected the "Verified in this release" section of
  `packaging/RELEASE_NOTES_v1.0.0.md`. It claimed a verification of
  `audit_folder.ps1` that had not actually been performed.

Not verified: `claude plugin validate` has not been run against the new
marketplace catalog. The file was checked against the documented schema by hand.

## 1.0.0 - 2026-08-31

First GitHub-canonical release. Assembled from the two local packages rather than invented.

Included from the nested Claude package, unchanged except where noted below:

- `SKILL.md` protocol (connector audit, record-only Execute, dual-root / reparse notes)
- `references/workflow.md` (includes Access and Other roots report sections)
- `scripts/audit_folder.py` (Windows reparse helper, case-exact reference checks)
- `scripts/audit_folder.ps1` - **modified before the tag was cut, see below**
- `scripts/verify_move.py`
- `references/navigation-templates.md`

Fixed before the tag was cut:

- `scripts/audit_folder.ps1`: `Test-CaseExact` called
  `Split-Path -LiteralPath $cur -Parent`. `-LiteralPath` and `-Parent` belong to
  different parameter sets, so that call threw
  "Parameter set cannot be resolved" on every platform, Windows included. The
  function only runs once an index reference resolves, so the script worked on a
  folder with broken links and aborted as soon as one was good - which is why it
  went unnoticed. The case-mismatch check had therefore never worked in the
  PowerShell script. Replaced with `[System.IO.Path]::GetDirectoryName` and
  `GetFileName`, which keep the literal, non-globbing semantics `-LiteralPath`
  was there for. `audit_folder.py` implements the same check correctly and was
  never affected.

Repo-only edits in this tag:

- Added Grok to the skill description agent list
- Added `license` and `metadata.version` / `metadata.repository` (Agent Skills spec)
- Added README, LICENSE, this changelog, `.gitignore`
- Added `.claude-plugin/plugin.json` with version, author, homepage, repository,
  license and keywords. Removed `adapters/claude/plugin.json`: plugin loaders read
  `.claude-plugin/plugin.json`, so the `adapters/` copy was inert, and two
  manifests with different contents were an ambiguity this skill exists to prevent
- Added `packaging/` (install docs and release notes consumed by the build) and
  `.github/workflows/release.yml`, which validates, smoke-tests, builds and
  publishes both ZIPs on a `v*` tag

Not claimed in this tag (present in some local copies, not shipped here):

- Grok-sandbox-only section 0 rewrite from the installed Grok skill (180-line SKILL.md)
- Older v2 `workflow.md` / audit scripts (smaller, no Access/Other-roots / reparse helpers)
