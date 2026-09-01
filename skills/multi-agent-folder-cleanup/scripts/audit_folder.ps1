<#
.SYNOPSIS
  Read-only inventory of a project folder for multi-agent cleanup.

.DESCRIPTION
  Writes nothing to the target folder. Reports structure, noise clusters,
  archives, duplicates (identical content AND one-name-many-documents),
  authority claims, credential-bearing files, path-length risks, OneDrive
  placeholder status, and index link checks.

  Feature parity with scripts/audit_folder.py, with one intentional exception:
  -Exclude and -IndexPath accept comma-separated values here, because `pwsh
  -File` cannot pass an array. The Python twin refuses a comma instead. The one
  thing only this version can do is the OneDrive placeholder check, which needs
  Windows file attributes.

  Executed on Windows against hydrated OneDrive files and compared with the
  Python version. OneDrive normally marks hydrated files as ReparsePoint, so
  that attribute alone is not treated as a placeholder. Offline,
  RecallOnOpen, or RecallOnDataAccess remains a stop condition.

.PARAMETER Root
  Absolute path of the folder to audit.

.PARAMETER IndexPath
  Index file(s) relative to Root. Repeatable. An index named here but absent
  on disk is reported as a finding, not skipped.

.PARAMETER Exclude
  Repeatable glob, '/' separators, relative to Root (e.g. 'tmp/**',
  '**/__pycache__/**'). Excluded files stay in the totals and are reported per
  pattern; they are kept out of the detail sections only.

.PARAMETER SuggestExcludes
  Report likely generated-machine-state clusters without excluding anything.
  Run this first, confirm with the owner, then re-run with -Exclude.

.PARAMETER HashFiles
  SHA-256 hashing: identical-content duplicate groups, and the inverse check
  for one filename resolving to several different documents.

.PARAMETER InspectZip
  Read ZIP central directories only. Never extracts. Authorize before using.

.PARAMETER PathThreshold
  Path length to flag. Default 240 (conservative Windows/OneDrive).

.EXAMPLE
  pwsh -File audit_folder.ps1 -Root C:\Projects\Thing -SuggestExcludes

.EXAMPLE
  pwsh -File audit_folder.ps1 -Root C:\Projects\Thing -HashFiles `
      -Exclude 'tmp/**','**/__pycache__/**' `
      -IndexPath 'INDEX.md','AI_CONTEXT/CHAT_INDEX.md'
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Root,
    [string[]]$IndexPath = @(),
    [string[]]$Exclude = @(),
    [switch]$SuggestExcludes,
    [switch]$HashFiles,
    [switch]$InspectZip,
    [int]$PathThreshold = 240,
    [int]$DupGroupCap = 8
)

$ErrorActionPreference = 'Stop'

# `pwsh -File script.ps1 -Exclude 'a/**','b/**'` hands the script ONE string,
# "a/**,b/**", because -File does not parse PowerShell argument syntax. The same
# happens to -IndexPath. Splitting on commas makes both parameters behave
# identically under `-File` and under `& ./script.ps1`, so the invocation
# documented in SKILL.md and the multi-value syntax documented above can be used
# together. A literal comma in a path or pattern is not supported.
$Exclude   = @($Exclude   | Where-Object { $_ } | ForEach-Object { $_ -split ',' } | ForEach-Object { $_.Trim() } | Where-Object { $_ })
$IndexPath = @($IndexPath | Where-Object { $_ } | ForEach-Object { $_ -split ',' } | ForEach-Object { $_.Trim() } | Where-Object { $_ })

if (-not (Test-Path -LiteralPath $Root)) { throw "Root not found: $Root" }
$RootFull = (Resolve-Path -LiteralPath $Root).Path.TrimEnd('\', '/')

$InstructionNames = @(
    'agents.md', 'claude.md', 'readme.md', 'readme_first.md', 'read_me_first.md',
    'copilot-instructions.md', 'gemini.md', 'cursor.md', '.cursorrules',
    '.windsurfrules', 'contributing.md'
)
$ClaimPatterns = @(
    '*authority*', '*status*', '*index*', '*manifest*', '*inventory*', '*handoff*',
    '*final*', '*current*', '*roadmap*', '*quick_context*', '*state*', '*latest*',
    '*master*', '*policy*', '*summary*'
)
$NoiseDirHints = @(
    '__pycache__', 'node_modules', '.git', '.svn', '.venv', 'venv', '.mypy_cache',
    '.pytest_cache', '.ruff_cache', '.tox', '.idea', '.vscode', 'chrome-profile',
    'edge-profile', 'firefox-profile', 'puppeteer', 'playwright', 'browser-profile',
    'cache', 'caches', 'logs', 'dist', 'build', '.next', '.terraform'
)
$SecretHintNames = @(
    'cookies', 'cookies-journal', 'login data', 'login data-journal', 'web data',
    'local state', 'credentials', '.env', 'id_rsa', 'token.json', 'secrets.json',
    '.npmrc', '.pypirc', 'credentials.json'
)
$SecretHintPrefixRules = @{
    'cookies' = @(' ', '-', '_')
    'login data' = @(' ', '-', '_')
    'web data' = @(' ', '-', '_')
    '.env' = @('.', '-', '_')
    'credentials' = @(' ', '-', '_', '.')
}

# Only these may match as a prefix (e.g. 'chrome-profile-2'). Everything else
# in $NoiseDirHints must match the whole segment exactly. Never a bare
# substring test: 'logs' is inside 'Catalogs' and 'build' is inside
# 'rebuild-notes', so substring matching proposes real document folders as junk.
$NoisePrefixHints = @('chrome-profile', 'edge-profile', 'firefox-profile',
    'browser-profile', 'puppeteer', 'playwright')

function Test-NoiseSegment([string]$seg) {
    $s = $seg.ToLower()
    if ($NoiseDirHints -contains $s) { return $true }
    foreach ($p in $NoisePrefixHints) { if ($s.StartsWith($p)) { return $true } }
    return $false
}

function Write-Section($t) { Write-Host ""; Write-Host "== $t ==" -ForegroundColor Cyan }
function Get-RelSlash($full) { $full.Substring($RootFull.Length).TrimStart('\', '/').Replace('\', '/') }
function Get-Short($full) { '.' + $full.Substring($RootFull.Length).Replace('\', '/') }

function Test-SecretHintName([string]$name) {
    $lowered = $name.ToLower()
    if ($SecretHintNames -contains $lowered) { return $true }
    foreach ($prefix in $SecretHintPrefixRules.Keys) {
        foreach ($separator in $SecretHintPrefixRules[$prefix]) {
            if ($lowered.StartsWith($prefix + $separator)) { return $true }
        }
    }
    return $false
}

function Get-CleanReference([string]$value) {
    $cleaned = ($value -split '#', 2)[0].Trim()
    if ($cleaned.StartsWith('<') -and $cleaned.EndsWith('>')) {
        $cleaned = $cleaned.Substring(1, $cleaned.Length - 2).Trim()
    }
    return $cleaned
}

# Windows is case-insensitive, so an index reference of 'tools\build_x.ps1'
# against an on-disk 'Build_x.ps1' passes Test-Path and then breaks for any
# agent reading the same index on Linux or a case-sensitive volume. Multi-agent
# means multi-platform, so report it -- as a review item, not a broken link,
# because it is not broken on the owner's own machine.
function Test-CaseExact([string]$full) {
    $cur = $full
    while ($true) {
        $parent = Split-Path -LiteralPath $cur -Parent
        $leaf = Split-Path -LiteralPath $cur -Leaf
        if (-not $parent -or -not $leaf -or $parent -eq $cur) { return $true }
        $names = @(Get-ChildItem -LiteralPath $parent -Force -ErrorAction SilentlyContinue |
                   ForEach-Object { $_.Name })
        if ($names.Count -eq 0) { return $true }
        if (-not ($names -ccontains $leaf)) { return $false }
        $cur = $parent
    }
}

function Get-ResolvedReferencePaths([string]$value, [string]$indexDir) {
    $candidate = $value.Replace('\', '/').TrimStart('/')
    $hits = @()
    foreach ($base in @($indexDir, $RootFull)) {
        $full = Join-Path $base $candidate
        if (Test-Path -LiteralPath $full) { $hits += $full }
    }
    return $hits
}

function Test-ReferenceCaseMismatch([string]$value, [string]$indexDir) {
    $hits = @(Get-ResolvedReferencePaths $value $indexDir)
    if ($hits.Count -eq 0) { return $false }
    foreach ($h in $hits) { if (Test-CaseExact $h) { return $false } }
    return $true
}

function Test-ReferenceResolves([string]$value, [string]$indexDir) {
    $candidate = $value.Replace('\', '/').TrimStart('/')
    return ((Test-Path -LiteralPath (Join-Path $indexDir $candidate)) -or
            (Test-Path -LiteralPath (Join-Path $RootFull $candidate)))
}

function Test-MatchPattern([string]$relPath, [string]$pat) {
    if ($relPath -like $pat) { return $true }
    if ($pat.EndsWith('/**')) {
        $prefix = $pat.Substring(0, $pat.Length - 3)
        if ($relPath.StartsWith("$prefix/")) { return $true }
    }
    if ($pat.StartsWith('**/')) {
        $inner = $pat.Substring(3).TrimEnd('*', '/')
        if ($relPath -like "*$inner*") { return $true }
    }
    if ($pat -notmatch '[/*]') {
        if ($relPath -eq $pat -or $relPath.StartsWith("$pat/") -or $relPath.Contains("/$pat/")) { return $true }
    }
    return $false
}

Write-Host "Read-only audit of $RootFull"
Write-Host "Generated $(Get-Date -Format 'yyyy-MM-dd HH:mm')"

$allFiles = @(Get-ChildItem -LiteralPath $RootFull -Recurse -File -Force -ErrorAction SilentlyContinue)
$allFolderItems = @(Get-ChildItem -LiteralPath $RootFull -Recurse -Directory -Force -ErrorAction SilentlyContinue)

# Junctions and directory symlinks. Windows PowerShell 5.1 traverses them on
# -Recurse while PowerShell 6+ and Python's os.walk do not, so without this the
# two helpers disagree on the same folder and 5.1 silently counts an external
# runtime as project content. Enumerate them, drop their descendants, and report
# them -- an unreported skip is what turns into the claim "not project contents",
# which on a synced root is only true of the LOCAL view.
$reparseDirs = @($allFolderItems | Where-Object {
        $_.Attributes.value__ -band 0x400
    })
$reparsePrefixes = @($reparseDirs | ForEach-Object { $_.FullName.TrimEnd('\') + '\' })
function Test-UnderReparse([string]$full) {
    foreach ($pre in $reparsePrefixes) { if ($full.StartsWith($pre, 'OrdinalIgnoreCase')) { return $true } }
    return $false
}
if ($reparsePrefixes.Count) {
    $allFiles = @($allFiles | Where-Object { -not (Test-UnderReparse $_.FullName) })
    $allFolderItems = @($allFolderItems | Where-Object { -not (Test-UnderReparse $_.FullName) })
}
$allFolders = $allFolderItems.Count
$emptyFolders = @($allFolderItems | Where-Object {
        @(Get-ChildItem -LiteralPath $_.FullName -Force -ErrorAction SilentlyContinue).Count -eq 0
    })

if ($SuggestExcludes) {
    Write-Section "Suggested exclusions (generated machine state - nothing excluded yet)"
    $clusters = @{}
    foreach ($f in $allFiles) {
        $parts = (Get-RelSlash $f.FullName).Split('/')
        for ($i = 0; $i -lt $parts.Count - 1; $i++) {
            if (Test-NoiseSegment $parts[$i]) {
                $key = ($parts[0..$i] -join '/') + '/**'
                $clusters[$key] = [int]$clusters[$key] + 1
                break
            }
        }
    }
    if ($clusters.Count) {
        foreach ($k in ($clusters.GetEnumerator() | Sort-Object Value -Descending)) {
            $pct = if ($allFiles.Count) { 100.0 * $k.Value / $allFiles.Count } else { 0 }
            Write-Host ("  {0,6} ({1,5:N1}%)  -Exclude '{2}'" -f $k.Value, $pct, $k.Key)
        }
        Write-Host "  Confirm with the owner before excluding. Never delete these under a standard cleanup approval." -ForegroundColor Yellow
    }
    else { Write-Host "  No obvious generated-state clusters found." }
}

$excludedCounts = @{}
$files = @()
foreach ($f in $allFiles) {
    $rp = Get-RelSlash $f.FullName
    $hit = $null
    foreach ($pat in $Exclude) { if (Test-MatchPattern $rp $pat) { $hit = $pat; break } }
    if ($hit) { $excludedCounts[$hit] = [int]$excludedCounts[$hit] + 1 } else { $files += $f }
}

$visibleEmptyFolders = @()
$excludedEmptyFolders = @()
foreach ($folder in $emptyFolders) {
    $rp = (Get-RelSlash $folder.FullName) + '/'
    $hit = $false
    foreach ($pat in $Exclude) { if (Test-MatchPattern $rp $pat) { $hit = $true; break } }
    if ($hit) { $excludedEmptyFolders += $folder } else { $visibleEmptyFolders += $folder }
}

Write-Section "Summary"
$totalBytes = ($allFiles | Measure-Object Length -Sum).Sum
$maxDepth = ($allFiles | ForEach-Object { (Get-RelSlash $_.FullName).Split('/').Count - 1 } |
    Measure-Object -Maximum).Maximum
Write-Host ("  Files (all):      {0}" -f $allFiles.Count)
Write-Host ("  Folders:          {0}" -f $allFolders)
Write-Host ("  Total MB:         {0:N2}" -f ($totalBytes / 1MB))
Write-Host ("  Max depth:        {0}" -f $maxDepth)
if ($Exclude.Count) {
    $exTotal = ($excludedCounts.Values | Measure-Object -Sum).Sum
    $pct = if ($allFiles.Count) { 100.0 * $exTotal / $allFiles.Count } else { 0 }
    Write-Host ("  Excluded:         {0} ({1:N0}%) by -Exclude" -f $exTotal, $pct)
    Write-Host ("  In detail below:  {0}" -f $files.Count)

    Write-Section "Excluded from detail sections (counted, not examined)"
    foreach ($k in ($excludedCounts.GetEnumerator() | Sort-Object Value -Descending)) {
        Write-Host ("  {0,6}  {1}" -f $k.Value, $k.Key)
    }
    Write-Host "  These files were NOT classified. State this in the report." -ForegroundColor Yellow
}

Write-Section "Per-folder counts (top 25)"
$files | Group-Object { Split-Path $_.FullName -Parent } |
Sort-Object Count -Descending | Select-Object -First 25 |
ForEach-Object { Write-Host ("  {0,6}  {1}" -f $_.Count, (Get-Short $_.Name)) }

Write-Section "Reparse points not descended (junctions / directory symlinks)"
if ($reparseDirs.Count) {
    foreach ($rd in $reparseDirs) {
        Write-Host ("  " + (Get-Short $rd.FullName))
        $tgt = @($rd.Target) | Select-Object -First 1
        if (-not $tgt) { $tgt = "<unresolved>" }
        Write-Host ("     -> " + $tgt)
    }
    Write-Host "  Descendants of these are in NO count in this report."
    Write-Host "  That is correct locally. If this root is OneDrive/SharePoint-synced," -ForegroundColor Yellow
    Write-Host "  the provider may hold the target as real files that other agents" -ForegroundColor Yellow
    Write-Host "  index. Check the cloud-side view before calling them external." -ForegroundColor Yellow
}
else { Write-Host "  none" }

Write-Section "Empty directories (cosmetic; no removal implied)"
if ($visibleEmptyFolders.Count) {
    Write-Host ("  " + $visibleEmptyFolders.Count + " empty director" + $(if ($visibleEmptyFolders.Count -eq 1) { 'y in detail:' } else { 'ies in detail:' }))
    $visibleEmptyFolders | Sort-Object FullName | Select-Object -First 40 |
        ForEach-Object { Write-Host ("     " + (Get-Short $_.FullName)) }
    if ($visibleEmptyFolders.Count -gt 40) { Write-Host ("     ... +" + ($visibleEmptyFolders.Count - 40) + " more") }
    Write-Host "  Leave in place unless removal is explicitly authorized and uses recoverable platform semantics."
}
else { Write-Host "  none" }
if ($excludedEmptyFolders.Count) {
    Write-Host ("  " + $excludedEmptyFolders.Count + " additional empty directories fall under -Exclude patterns; counted but not listed.")
}

Write-Section "Extensions"
$files | Group-Object Extension | Sort-Object Count -Descending | Select-Object -First 20 |
ForEach-Object { Write-Host ("  {0,6}  {1}" -f $_.Count, $(if ($_.Name) { $_.Name } else { '(none)' })) }

Write-Section "Archives"
$archives = @($files | Where-Object { $_.Extension -match '^\.(zip|7z|rar|tar|gz|tgz)$' })
if ($archives.Count) {
    $archives | ForEach-Object {
        Write-Host ("  {0,8:N2} MB  {1:yyyy-MM-dd}  {2}" -f ($_.Length / 1MB), $_.LastWriteTime, (Get-Short $_.FullName))
    }
    Write-Host "  Archives stay closed. Do not bulk-extract to make them searchable."
}
else { Write-Host "  none" }

if ($InspectZip) {
    Write-Section "ZIP central directories (no extraction)"
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    foreach ($z in ($archives | Where-Object Extension -eq '.zip')) {
        Write-Host ("-- " + (Get-Short $z.FullName))
        try {
            $zip = [System.IO.Compression.ZipFile]::OpenRead($z.FullName)
            try {
                Write-Host ("   entries: " + $zip.Entries.Count)
                $bad = @($zip.Entries | Where-Object { $_.FullName -match '[:*?"<>|]' -or $_.FullName -match '^(/|\\|\.\.)' })
                if ($bad.Count) { Write-Host ("   INVALID/UNSAFE NAMES: " + $bad.Count) -ForegroundColor Yellow }
                $longE = @($zip.Entries | Where-Object { ($RootFull.Length + 1 + $_.FullName.Length) -gt $PathThreshold })
                if ($longE.Count) { Write-Host ("   would exceed path threshold: " + $longE.Count) -ForegroundColor Yellow }
                $zip.Entries | Select-Object -First 15 -ExpandProperty FullName | ForEach-Object { Write-Host "     $_" }
                if ($zip.Entries.Count -gt 15) { Write-Host "     ..." }
            }
            finally { $zip.Dispose() }
        }
        catch { Write-Host "   unreadable: $_" -ForegroundColor Red }
    }
}

Write-Section "Path length risks (> $PathThreshold chars)"
$longPaths = @($files | Where-Object { $_.FullName.Length -gt $PathThreshold })
if ($longPaths.Count) { $longPaths | ForEach-Object { Write-Host ("  {0,4}  {1}" -f $_.FullName.Length, $_.FullName) } }
else { Write-Host "  none" }

Write-Section "OneDrive / cloud placeholders"
$offline = @($files | Where-Object {
        ($_.Attributes -band [IO.FileAttributes]::Offline) -or
        ($_.Attributes.value__ -band 0x40000) -or
        ($_.Attributes.value__ -band 0x400000)
    })
if ($offline.Count) {
    Write-Host ("  " + $offline.Count + " file(s) not hydrated - hydrate before any move") -ForegroundColor Yellow
    $offline | Select-Object -First 20 | ForEach-Object { Write-Host ("     " + (Get-Short $_.FullName)) }
    if ($offline.Count -gt 20) { Write-Host ("     ... +" + ($offline.Count - 20) + " more") }
}
else { Write-Host "  none detected" }

Write-Section "Duplicate names across folders"
$dupNames = @($files | Group-Object Name | Where-Object Count -gt 1 | Sort-Object Count -Descending)
if ($dupNames.Count) {
    foreach ($g in ($dupNames | Select-Object -First 20)) {
        Write-Host ("-- " + $g.Name + "  (" + $g.Count + ")")
        $g.Group | Select-Object -First $DupGroupCap | ForEach-Object {
            Write-Host ("     " + $_.LastWriteTime.ToString('yyyy-MM-dd') + "  " + (Get-Short $_.FullName))
        }
        if ($g.Count -gt $DupGroupCap) { Write-Host ("     ... +" + ($g.Count - $DupGroupCap) + " more") }
    }
    if ($dupNames.Count -gt 20) { Write-Host ("  ... +" + ($dupNames.Count - 20) + " more duplicated names") }
}
else { Write-Host "  none" }

if ($HashFiles) {
    $unreadable = [System.Collections.ArrayList]::new()
    $hashes = foreach ($f in $files) {
        try {
            [pscustomobject]@{
                Path = $f.FullName
                Name = $f.Name
                Hash = (Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256).Hash
            }
        }
        catch {
            # Never drop these silently: an unhashed file is a hole in the
            # coverage claim, and on OneDrive it usually means a placeholder
            # or a lock, both of which block an Execute pass.
            [void]$unreadable.Add($f.FullName)
        }
    }

    if ($unreadable.Count) {
        Write-Section "UNREADABLE - could not hash"
        $unreadable | Select-Object -First 25 | ForEach-Object { Write-Host ("  " + (Get-Short $_)) }
        if ($unreadable.Count -gt 25) { Write-Host ("  ... +" + ($unreadable.Count - 25) + " more") }
        Write-Host ("  " + $unreadable.Count + " file(s) are not covered by any hash check below. On a synced folder this usually means a cloud placeholder or an open lock. Resolve before any Execute pass.") -ForegroundColor Yellow
    }

    Write-Section "Identical content groups (SHA-256)"
    $groups = @($hashes | Group-Object Hash | Where-Object Count -gt 1)
    if ($groups.Count) {
        foreach ($g in $groups) {
            Write-Host ("-- " + $g.Name.Substring(0, 12).ToLower() + "  (" + $g.Count + " copies)")
            $g.Group | Select-Object -First $DupGroupCap | ForEach-Object { Write-Host ("     " + (Get-Short $_.Path)) }
            if ($g.Count -gt $DupGroupCap) { Write-Host ("     ... +" + ($g.Count - $DupGroupCap) + " more") }
        }
        Write-Host ("  " + $groups.Count + " group(s). Copy-only dual trees: no marker says which side is canonical.")
    }
    else { Write-Host "  none" }

    Write-Section "Same name, DIFFERENT content (ambiguous citation)"
    $ambiguous = @($hashes | Group-Object Name |
        Where-Object { $_.Count -gt 1 -and (@($_.Group | Select-Object -ExpandProperty Hash -Unique).Count -gt 1) })
    if ($ambiguous.Count) {
        foreach ($g in ($ambiguous | Sort-Object Count -Descending | Select-Object -First 20)) {
            Write-Host ("-- " + $g.Name)
            $g.Group | Select-Object -First $DupGroupCap | ForEach-Object {
                Write-Host ("     " + $_.Hash.Substring(0, 8).ToLower() + "  " + (Get-Short $_.Path))
            }
        }
        Write-Host ("  " + $ambiguous.Count + " name(s) resolve to more than one document. Any citation by filename alone is ambiguous.") -ForegroundColor Yellow
    }
    else { Write-Host "  none" }
}

Write-Section "Claims requiring verification (open these - never trust the name)"
$claims = @($files | Where-Object {
        $n = $_.Name.ToLower()
        @($ClaimPatterns | Where-Object { $n -like $_ }).Count -gt 0
    })
if ($claims.Count) {
    $claims | Sort-Object LastWriteTime -Descending | Select-Object -First 40 | ForEach-Object {
        $lines = try { @(Get-Content -LiteralPath $_.FullName -ErrorAction Stop).Count } catch { '?' }
        Write-Host ("  {0:yyyy-MM-dd}  {1,8}  {2}" -f $_.LastWriteTime, $lines, (Get-Short $_.FullName))
    }
    if ($claims.Count -gt 40) { Write-Host ("  ... +" + ($claims.Count - 40) + " more") }
    Write-Host "  Each is verified, contradicted or unverifiable. Never upgrade unverifiable to current."
}
else { Write-Host "  none" }

Write-Section "Possible credential-bearing files"
$secrets = @($allFiles | Where-Object { Test-SecretHintName $_.Name })
if ($secrets.Count) {
    Write-Host ("  " + $secrets.Count + " file(s) matched credential-name hints:") -ForegroundColor Yellow
    $secrets | Select-Object -First 25 | ForEach-Object { Write-Host ("     " + (Get-Short $_.FullName)) }
    if ($secrets.Count -gt 25) { Write-Host ("     ... +" + ($secrets.Count - 25) + " more") }
    Write-Host "  Do not stage, copy, or index these. Flag to the owner before sharing the folder. Never copy a secret value into a report or journal." -ForegroundColor Yellow
}
else { Write-Host "  none matched by name" }

foreach ($ip in $IndexPath) {
    Write-Section "Index link check: $ip"
    $idx = Join-Path $RootFull $ip
    if (Test-Path -LiteralPath $idx) {
        $content = Get-Content -LiteralPath $idx -Raw
        $markdownLinks = @([regex]::Matches($content, '\]\(([^)]+)\)') |
            ForEach-Object { Get-CleanReference $_.Groups[1].Value } |
            Where-Object { $_ -notmatch '^(https?:|mailto:|#)' } |
            Where-Object { $_ } | Select-Object -Unique)
        $backtickedRefs = @([regex]::Matches($content, '`([^`\r\n]+\.[A-Za-z0-9]{1,8})`') |
            ForEach-Object { Get-CleanReference $_.Groups[1].Value } |
            Where-Object { $_ -notmatch '^(https?:|mailto:|#)' } |
            Where-Object { $_ } | Select-Object -Unique)
        # A relative link in AI_CONTEXT/CHAT_INDEX.md is relative to
        # AI_CONTEXT/, not to the root. Resolving everything against the root
        # reports working links as broken - the false alarm that makes an agent
        # distrust a healthy index. Accept either.
        $idxDir = Split-Path -Parent $idx
        $broken = @($markdownLinks | Where-Object { -not (Test-ReferenceResolves $_ $idxDir) })
        $unresolvedRefs = @($backtickedRefs | Where-Object { -not (Test-ReferenceResolves $_ $idxDir) })
        Write-Host ("  Markdown links checked: " + $markdownLinks.Count)
        if ($broken.Count) {
            Write-Host ("  BROKEN MARKDOWN LINKS: " + $broken.Count) -ForegroundColor Yellow
            $broken | ForEach-Object { Write-Host "     $_" }
        }
        else { Write-Host "  all Markdown links resolve" }

        Write-Host ("  Backticked path references checked: " + $backtickedRefs.Count)
        if ($unresolvedRefs.Count) {
            Write-Host ("  UNRESOLVED BACKTICKED REFERENCES: " + $unresolvedRefs.Count + " (review needed)") -ForegroundColor Yellow
            $unresolvedRefs | ForEach-Object { Write-Host "     $_" }
            Write-Host "  These are not confirmed broken links; examples and historical labels may be intentionally non-live."
        }
        else { Write-Host "  all backticked references resolve" }

        $caseMismatched = @(@($markdownLinks + $backtickedRefs) |
            Where-Object { Test-ReferenceCaseMismatch $_ $idxDir })
        if ($caseMismatched.Count) {
            Write-Host ("  CASE-MISMATCHED REFERENCES: " + $caseMismatched.Count + " (review needed)") -ForegroundColor Yellow
            $caseMismatched | ForEach-Object { Write-Host "     $_" }
            Write-Host "  These resolve only because this filesystem is case-insensitive. They break for an agent on Linux or a case-sensitive volume."
        }
    }
    else {
        Write-Host "  index NOT FOUND at $idx" -ForegroundColor Yellow
        Write-Host "  An index named in navigation but absent is a top-tier confusion source. Report it."
    }
}

Write-Section "Instruction files found"
$instr = @($allFiles | Where-Object { $InstructionNames -contains $_.Name.ToLower() })
if ($instr.Count) {
    $instr | ForEach-Object { Write-Host ("  {0:yyyy-MM-dd}  {1}" -f $_.LastWriteTime, (Get-Short $_.FullName)) }
    $agentFiles = @($instr | Where-Object { $_.Name.ToLower() -ne 'readme.md' })
    if ($agentFiles.Count -gt 1) {
        Write-Host "  Multiple agent-instruction files - check for conflicting scope." -ForegroundColor Yellow
    }
}
else {
    Write-Host "  NONE anywhere in the tree." -ForegroundColor Yellow
    Write-Host "  All agent guidance lives outside the folder in per-tool settings: invisible to the next agent, unversioned. Report as a finding."
}

Write-Host ""
if ($Exclude.Count) {
    $exTotal = ($excludedCounts.Values | Measure-Object -Sum).Sum
    Write-Host ("Coverage: {0} of {1} files examined in detail; {2} excluded by -Exclude and classified by nothing. Say so in the report." -f $files.Count, $allFiles.Count, $exTotal)
    Write-Host ""
}
Write-Host "Audit complete. Nothing was written to $RootFull." -ForegroundColor Green
