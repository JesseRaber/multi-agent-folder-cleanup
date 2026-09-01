# Deterministic Audit and Move Tools

Use this reference only when the target is available through a mounted filesystem. All bundled helpers are read-only against the target; `verify_move.py` never moves or deletes files.

## Pick the audit helper

- Windows or OneDrive: prefer `audit_folder.ps1` with PowerShell 5.1 or 7+ because it can inspect placeholder attributes.
- POSIX, remote sandboxes, or other mounted filesystems: use `audit_folder.py` with Python 3.8+.
- Connector-only access: neither helper applies. Use the degraded connector protocol in `SKILL.md` and mark byte-level checks unverified.

From the skill directory:

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

`--inspect-zip` / `-InspectZip` reads ZIP central directories without extracting. Use it only when archive structure matters. `--index-path` is repeatable; a named but missing index is a finding. Markdown links that fail to resolve are broken links, while unresolved backticked path references are review items because examples or historical labels may be intentional.

The reports include empty directories, path risks, archives, duplicate names, optional identical-content and divergent-content groups, claim-name reading queues, credential-name hints, reparse points, and case-mismatched references. These are structural findings, not authority decisions:

- A suggested exclusion is not permission to remove anything.
- A claim-name match is a file to open, not a current-state verdict.
- A credential-name match is a warning, not proof of a secret; never inspect its contents.
- Identical hashes prove identical bytes, not which copy is canonical.
- A reparse point is skipped, not assessed. Check the cloud view separately for synced roots.

## Verify an approved move map

Create a CSV or JSON map with literal `source,target` entries. Keep the baseline outside both trees.

```bash
python scripts/verify_move.py baseline --map moves.csv --out /safe/audit/baseline.json
python scripts/verify_move.py preflight --map moves.csv --path-threshold 240
python scripts/verify_move.py verify --baseline /safe/audit/baseline.json --stage /safe/staging
python scripts/verify_move.py verify --baseline /safe/audit/baseline.json
```

`verify` exits nonzero on any mismatch. Treat that as a stop condition. Run preflight with Windows-native Python for OneDrive: elsewhere the hydration result explicitly remains unchecked. The baseline records a common target root and rejects unsafe placement. Staging mirrors final relative paths so same-named files cannot overwrite each other during verification.
