# Deterministic Audit and Move Tools

Use this reference only when the target is available through a mounted filesystem. All bundled helpers are read-only against the target; `verify_move.py` never moves or deletes files.

## Pick the audit helper

- Windows or OneDrive: prefer `audit_folder.ps1` with PowerShell 5.1 or 7+ because it can inspect placeholder attributes.
- POSIX, remote sandboxes, or other mounted filesystems: use `audit_folder.py` with Python 3.8+.
- Connector-only access: neither helper applies. Use `references/connector-audit.md` and mark byte-level checks unverified.

```powershell
pwsh -File scripts/audit_folder.ps1 -Root 'C:\Projects\Thing' -SuggestExcludes
pwsh -File scripts/audit_folder.ps1 -Root 'C:\Projects\Thing' -HashFiles -Exclude 'tmp/**','**/__pycache__/**' -IndexPath 'INDEX.md','AI_CONTEXT/CHAT_INDEX.md'
```

```bash
python scripts/audit_folder.py --root /work/thing --suggest-excludes
python scripts/audit_folder.py --root /work/thing --hash-files \
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

These are structural findings, not authority decisions. A suggested exclusion is not permission to remove. A claim-name match is a file to open, not a current-state verdict. A credential-name match is a warning, not proof of a secret. Identical hashes do not select a canonical copy. A reparse point is skipped, not assessed; check the cloud view separately.

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

## Verify an approved move map

```bash
python scripts/verify_move.py preflight --map moves.csv --path-threshold 240
python scripts/verify_move.py baseline --map moves.csv --out /safe/audit/baseline.json
python scripts/verify_move.py verify --baseline /safe/audit/baseline.json --stage /safe/staging
python scripts/verify_move.py verify --baseline /safe/audit/baseline.json
```

Run preflight first; `baseline` refuses a missing source. Relative map paths resolve against the map file's folder. Final `verify` fails while any source still exists (a copy is not a move); pass `--allow-source-present` only for an approved copy. Treat nonzero verification as a stop condition. Run preflight with Windows-native Python for OneDrive; elsewhere hydration remains unchecked. Keep the baseline outside source and target trees. Staging mirrors final relative paths so same-named files cannot overwrite each other.
