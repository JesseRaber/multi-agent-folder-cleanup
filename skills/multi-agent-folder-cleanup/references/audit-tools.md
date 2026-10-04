# Deterministic Audit and Move Tools

Use this reference only when the target is available through a mounted filesystem. All bundled helpers are read-only against the target; `verify_move.py` never moves or deletes files.

## Pick the audit helper

- Windows or OneDrive: prefer `audit_folder.ps1` with PowerShell 5.1 or 7+ because it can inspect placeholder attributes.
- POSIX, remote sandboxes, or other mounted filesystems: use `audit_folder.py` with Python 3.8+.
- Connector-only access: neither helper applies. Use `references/connector-audit.md` and mark byte-level checks unverified.
- Helper missing from your install: some host packages omit it on purpose (the Gemini Apps package has no `audit_folder.py`; the Microsoft Copilot package has no `.ps1`). Use the other helper if present; otherwise follow the manual checks in the mode file and mark helper-only checks NOT RUN. Never recreate a helper from memory.

```powershell
pwsh -ExecutionPolicy Bypass -File scripts/audit_folder.ps1 -Root 'C:\Projects\Thing' -SuggestExcludes
pwsh -ExecutionPolicy Bypass -File scripts/audit_folder.ps1 -Root 'C:\Projects\Thing' -HashFiles -Exclude 'tmp/**','**/__pycache__/**' -IndexPath 'INDEX.md','AI_CONTEXT/CHAT_INDEX.md'
# No PowerShell 7 (pwsh)? Windows PowerShell 5.1 takes the same arguments:
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\audit_folder.ps1 -Root 'C:\Projects\Thing' -SuggestExcludes
```

`-ExecutionPolicy Bypass` applies to this one process only; it does not change the machine or user policy. Use it when the default policy blocks unsigned downloaded scripts. Do not change the persistent execution policy as part of an audit.

On Linux and macOS, `python` may be missing or Python 2; use `python3` with the same arguments in every example below (on Windows, `py -3` also works).

```bash
python3 scripts/audit_folder.py --root /work/thing --suggest-excludes
python3 scripts/audit_folder.py --root /work/thing --hash-files \
  --exclude 'tmp/**' --exclude '**/__pycache__/**' \
  --index-path INDEX.md --index-path AI_CONTEXT/CHAT_INDEX.md
```

Run the suggestion pass before exclusions. Confirm every proposed generated-state cluster before excluding it. Excluded paths remain counted and must be disclosed as not individually classified.

Exclusion patterns behave identically in both helpers and are case-insensitive:

| Pattern | Matches |
|---|---|
| `tmp/**` | everything under the root-level `tmp/` |
| `**/logs/**` | everything under any folder named `logs`, including a root-level one; never `Catalogs/` or `changelogs.md` |
| `*.log` | a pattern with no `/` is tested against every path segment, so any `.log` file at any depth |
| `tmp` | any folder named exactly `tmp` |

`*` never crosses a `/`. Use `**` to span folders.

Coverage is disclosed, never assumed. A directory the helper cannot read is listed under **Directories not readable** and repeated in a closing **Coverage gap** line, because nothing below it is in any count. Only junctions and directory symlinks are skipped as reparse points. OneDrive Files On-Demand also marks ordinary synced folders with the ReparsePoint attribute; those folders are walked. The Python helper writes UTF-8 when its output is redirected, so a non-ASCII filename cannot abort a report on a Windows console.

`--inspect-zip` / `-InspectZip` reads ZIP central directories without extracting. `--index-path` is repeatable; a named but missing index is a finding. Reports include empty directories, path risks, archives, duplicate names, optional content hashes, claim-name queues, credential-name hints, reparse points, and case-mismatched references.

These are structural findings, not authority decisions. A suggested exclusion is not permission to remove. A claim-name match is a file to open, not a current-state verdict. Credential findings are tiered as probable private/session material, ambiguous `.pem` material, or recognizable public certificate bundles; the tier is still a warning rather than proof, and every tier retains the conservative no-content-read guard. Identical hashes do not select a canonical copy. A reparse point is skipped, not assessed; check the cloud view separately.

## Check the helper version first

```bash
python3 scripts/audit_folder.py --version    # audit_folder.py 1.5.2
python3 scripts/verify_move.py --version     # verify_move.py 1.5.2
pwsh -ExecutionPolicy Bypass -File scripts/audit_folder.ps1 -Version # audit_folder.ps1 1.5.2
```

Each must equal the `metadata.version` in SKILL.md. A mismatch means a mixed install (for example a new SKILL.md over older scripts): its documented checks may not exist. Reinstall from one release before relying on it.

In v1.4.1, credential-name hints, link traversal and detected cloud placeholders block content reads (hashes, archive inspection, pointer/skill/index/manifest reads). Metadata remains counted. These guards do not identify every secret or prove cloud synchronization. Inline Markdown destinations support balanced parentheses and escaped parentheses; reference-style definitions and full CommonMark parsing remain out of scope. Root-only fallback matches are labeled separately rather than silently treated as document-relative links.

Move preflight rejects linked source/target components and probes Windows sources for exclusive read access. This momentary check closes its handle immediately; it does not reserve files, prove application inactivity, or replace writer coordination. Baseline and verification refuse linked paths and detected placeholders before hashing. Receipt identity is unchanged and does not bind a host or volume. In v1.5.2, pass `--root <project>` to `preflight`, `baseline` and `verify` so any source or target outside the project is refused as OUTSIDE ROOT and a baseline written inside the project is refused. Case-only renames (`readme.md` to `README.md`) on case-insensitive volumes are no longer reported as TARGET EXISTS, maps spanning top-level folders no longer refuse every baseline location, macOS paths compare case-insensitively, and Windows probes use the extended-length form for long paths. Re-review on a different host; never treat receipt equality as cross-device authorization.

## Work-mode checks (v1.5)

Two read-only checks for agents working in a shared folder ([work-mode.md](work-mode.md)). Both skip the full audit, write nothing to the root, and honor `--brief`, `--out`, `--exclude` and `--max-seconds`.

```bash
python scripts/audit_folder.py --root <root> --orient --session-id <your-id>
python scripts/audit_folder.py --root <root> --session-index
pwsh -File scripts/audit_folder.ps1 -Root <root> -Orient -SessionIndex -SessionId <your-id>
```

- `--orient` / `-Orient`: startup read-set size against `--read-budget-kb`; quick-context size against `--quick-context-kb` (default 12); the five most recent sessions; session logs and scratch folders changed within `--active-minutes` (default 30) as possibly active writers, leaving out your own `--session-id`; files changed since `--since` or, by default, the start of the latest other session (session logs and scratch excluded, generated state not walked); and which of those changed files the index (`--index-path`, default `PROJECT_INDEX.md`) never names.
- `--session-index` / `-SessionIndex`: compares session logs in `--sessions-dir` (default `AI_CONTEXT/SESSIONS`) with `--session-index-file` (default `AI_CONTEXT/SESSION_INDEX.md`); prints proposed rows for missing sessions, index links to logs that no longer exist, and session files without a standard name or UUID. Review the proposed rows' outcome and status before saving them with a guarded append.
- Session logs are parsed for the header fields `Session ID`, `Started` and `Tool/runtime`, and turn headings such as `## T001 — <time> — <title>` or `T001 | <time> | <title>`; the filename pattern is the fallback.
- Activity and change lists come from local modified times. They are leads: sync replicas, hydration and clock skew change them. They never prove that another agent is or is not working.
- A full audit also inventories handoff/next-prompt ambiguity, pending-update artifacts and their evidenced lifecycle state, and candidate/released/superseded ZIPs that share a folder. It reports review candidates; it does not choose a current handoff, apply a pending edit, move a package or authorize deletion.
- `--portfolio` / `-Portfolio` reports immediate-child state (`managed`, `unmanaged` or `empty`), root-item scope, detected entrypoints, sessions, missing session-index rows when the index is readable, and pending-update artifacts. Empty and unmanaged are distinct observations, not quality verdicts.

## Keep the report small (v1.4)

```bash
python scripts/audit_folder.py --root <root> --brief \
  --entrypoint AGENTS.md --entrypoint AI_CONTEXT/PROJECT_QUICK_CONTEXT.md \
  --index-coverage AI_CONTEXT/SESSION_INDEX.md=AI_CONTEXT/SESSIONS \
  --host-root 'C:\Users\me\OneDrive - Org\Projects\Thing'
python scripts/audit_folder.py --root <root> --hash-files --out /safe/outside/report.txt
```

```powershell
pwsh -File scripts/audit_folder.ps1 -Root <root> -Brief `
  -EntryPoint 'AGENTS.md','AI_CONTEXT/PROJECT_QUICK_CONTEXT.md' `
  -IndexCoverage 'AI_CONTEXT/SESSION_INDEX.md=AI_CONTEXT/SESSIONS'
pwsh -File scripts/audit_folder.ps1 -Root <root> -HashFiles -Out C:\Temp\report.txt
```

- `--brief` caps every list at 10 lines (duplicate groups at 3 paths).
- `--out FILE` writes the full report to a new file outside the root and prints only **Summary** and **Findings at a glance**. Read the glance block first, then open only the sections it points to. The file is never overwritten.
- Every report ends with **Findings at a glance**: counts only, never a verdict.
- `--entrypoint` doubles as the **startup read set**: list the project's read order. The helper totals it with the root auto-loaded instruction files and flags a total above `--read-budget-kb` (default 40) and any `AGENTS.md` over 32 KiB (Codex's default `project_doc_max_bytes`).
- `--index-coverage INDEX=DIR` lists files directly in `DIR` that `INDEX` never mentions by filename, URL-encoded filename or embedded UUID.
- `--host-root` measures path length as host root + relative path. Use it whenever the folder is mounted under a different prefix than the one OneDrive or Windows enforces.

### Work-helper evidence limits

- Missing folders are distinct from denied, guarded or failed listings. Unavailable coverage is reported as `n/a`, not zero sessions.
- Session/index reads are bounded at 1,048,576 text characters. Oversized content is disclosed and not parsed; an incomplete index never produces apparently complete missing-row or stale-link counts.
- Duplicate session IDs are reported for review. Helpers neither merge logs nor propose rows or select an orientation baseline for ambiguous IDs.
- Recorded session/turn timestamps need explicit timezone offsets. Missing/naive recorded times remain unknown; filenames do not establish a timezone. Displayed known instants include the local offset. A file-modification-time fallback is labeled and does not establish recorded activity or writer ownership. For an explicit `--since`, provide an offset; a naive CLI value uses the executing machine's local timezone.
- Proposed rows require human/agent review. Helpers do not update indexes, establish writer exclusivity or prove remote sync. Manual fallback on hosts without scripts follows Work mode W1/W6 and discloses limited coverage.

## Large roots and time limits

- `--suggest-excludes` collapses recurring generated names (`**/__pycache__/**`, `**/node_modules/**`) and reports a Python environment (`pyvenv.cfg`, or three or more `*.dist-info` folders, as left by `pip --target`) as one cluster.
- `--prune-noise` does not descend into high-confidence generated state: `.git`, `node_modules`, `__pycache__`, virtual environments, `site-packages`, tool caches, browser profiles and the inside of a detected Python environment. Pruned folders are listed and their contents are in no count; say so. Folders named `logs`, `build`, `dist` or `cache` are always walked because they can hold real material.
- `--max-seconds N` stops the walk and reports how many queued directories were never visited. Use it when the shell enforces a time limit, then narrow the root or add `--prune-noise`.
- Lists print relative paths; scratch working copies are counted but not listed under claims.

## Know the access route before you run anything

| Route | Shell | Typical limits | Hydration check |
|---|---|---|---|
| Windows desktop agent (Codex, Claude Code, Antigravity) | PowerShell and/or Python on Windows | None beyond the agent's own timeout | Yes, with `audit_folder.ps1` or Windows Python |
| Cloud agent linked to a Windows PC through a bridge | Often Linux over a mounted copy | Per-command time cap; background jobs may be killed; PowerShell may be absent | No; report it as unchecked |
| Cloud sandbox with uploaded files | Linux | Files are a snapshot, not the live folder | No |
| Connector or web listing only | None | See [connector-audit.md](connector-audit.md) | No |

Record which route ran, the helper version, the flags, and which checks are therefore unavailable.

## v1.2 advisory checks

```bash
python scripts/audit_folder.py --root <portfolio> \
  --journal-threshold-kb 100 \
  --entrypoint AGENTS.md --entrypoint AI_CONTEXT/README_FIRST.md \
  --portfolio --detect-pointers \
  --expected-upload-manifest expected-files.csv
```

```powershell
pwsh -File scripts/audit_folder.ps1 -Root <portfolio> `
  -JournalThresholdKB 100 `
  -EntryPoint 'AGENTS.md','AI_CONTEXT/README_FIRST.md' `
  -Portfolio -DetectPointers `
  -ExpectedUploadManifest expected-files.csv
```

Journal reporting flags journal-like files at or above the threshold. Entrypoint checks are grounded only in the direct root. Portfolio mode reports immediate children and root-level counts without determining authority. Pointer detection is conservative and advisory. An expected-upload manifest may be a line list or CSV with `path` and optional `size` and `sha256`; it verifies listed files but authorizes nothing.

## Review and verify a move map

```bash
python3 scripts/verify_move.py review --map /safe/plan/moves.csv \
  --approval-out /safe/plan/proposal.json > /safe/plan/review.md
# Planning preflight may be unguarded. After owner approval of the generated view:
python3 scripts/verify_move.py preflight --map /safe/plan/moves.csv --approval /safe/plan/proposal.json --root /work/thing
python3 scripts/verify_move.py baseline --map /safe/plan/moves.csv \
  --approval /safe/plan/proposal.json --out /safe/plan/baseline.json --root /work/thing
python3 scripts/verify_move.py verify --baseline /safe/plan/baseline.json \
  --approval /safe/plan/proposal.json --stage /safe/staging --root /work/thing
# Immediately before the agent performs the approved moves:
python3 scripts/verify_move.py preflight --map /safe/plan/moves.csv \
  --approval /safe/plan/proposal.json --baseline /safe/plan/baseline.json --root /work/thing
python3 scripts/verify_move.py verify --baseline /safe/plan/baseline.json --approval /safe/plan/proposal.json --root /work/thing
```

`review` renders CSV or JSON through the same parser used by preflight/baseline. It prints the map's absolute location, raw-byte SHA-256, ordered resolved-pairs SHA-256, row count and ordinal row IDs. Relative paths resolve against the map file's folder, not the current directory. Both digests and that location bind the proposal; relocating a relative map requires a new review even if the raw bytes match. Review output is a proposal, not permission; record the actual owner authorization separately.

`--approval` rejects changed bytes, location, resolved pairs or count. New baselines retain that identity. `preflight --baseline` additionally checks current source hashes and requires `--approval`; use it before moving, not after a partial move. Baselines and proposal receipts use exclusive creation and never overwrite prior evidence. Unguarded preflight/baseline and legacy baseline verification remain supported for earlier callers; they do not satisfy the new skill execution contract. A legacy baseline cannot be bound to a receipt after the fact.

The helpers do not move files, prove human consent, guard separately proposed content patches, lock other writers, or verify cloud idle/sync state. Checks are point-in-time. Recheck changed scope and reconcile partial runs before resuming. Do not regenerate a receipt to bypass a mismatch. Final verify fails while any source remains; `--allow-source-present` is only for an approved copy. Preserve staging on failure and reconcile newer targets before authorized recovery.

Run Windows-native preflight for OneDrive; elsewhere hydration remains unchecked. Keep proposal/review/baseline outputs outside the trees being moved, using new session-owned paths. Staging mirrors final relative paths. Required project continuity records keep their adopted location.
