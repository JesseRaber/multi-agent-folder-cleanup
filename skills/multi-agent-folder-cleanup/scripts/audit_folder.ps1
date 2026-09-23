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

  OneDrive normally marks hydrated files, and synced folders, with the
  ReparsePoint attribute, so that attribute alone is neither a placeholder nor
  a link. Only junctions and directory symlinks are skipped. Offline,
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
    [int]$DupGroupCap = 8,
    [int]$JournalThresholdKB = 100,
    [string[]]$EntryPoint = @(),
    [switch]$Portfolio,
    [switch]$DetectPointers,
    [string[]]$ExpectedUploadManifest = @()
)

$ErrorActionPreference = 'Stop'

# A redirected report (`> report.txt`, a CI log, a calling agent) would otherwise
# use the OEM/ANSI code page and turn every non-ASCII filename into '?'. Match
# audit_folder.py, which writes UTF-8 whenever its output is redirected.
try { if ([Console]::IsOutputRedirected) { [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false) } } catch { }

# `pwsh -File script.ps1 -Exclude 'a/**','b/**'` hands the script ONE string,
# "a/**,b/**", because -File does not parse PowerShell argument syntax. The same
# happens to -IndexPath. Splitting on commas makes both parameters behave
# identically under `-File` and under `& ./script.ps1`, so the invocation
# documented in SKILL.md and the multi-value syntax documented above can be used
# together. A literal comma in a path or pattern is not supported.
$Exclude   = @($Exclude   | Where-Object { $_ } | ForEach-Object { $_ -split ',' } | ForEach-Object { $_.Trim() } | Where-Object { $_ })
$IndexPath = @($IndexPath | Where-Object { $_ } | ForEach-Object { $_ -split ',' } | ForEach-Object { $_.Trim() } | Where-Object { $_ })
$EntryPoint = @($EntryPoint | Where-Object { $_ } | ForEach-Object { $_ -split ',' } | ForEach-Object { $_.Trim() } | Where-Object { $_ })
$ExpectedUploadManifest = @($ExpectedUploadManifest | Where-Object { $_ } | ForEach-Object { $_ -split ',' } | ForEach-Object { $_.Trim() } | Where-Object { $_ })
if ($JournalThresholdKB -lt 0) { throw "JournalThresholdKB must be zero or greater" }

if (-not (Test-Path -LiteralPath $Root)) { throw "Root not found: $Root" }
# ProviderPath, not Path: for a UNC/NAS root, .Path can come back provider-
# qualified ("Microsoft.PowerShell.Core\FileSystem::\\server\share"), which
# breaks every Substring($RootFull.Length) below.
$RootFull = (Resolve-Path -LiteralPath $Root).ProviderPath
if ($RootFull.Length -gt 3 -or $RootFull -notmatch '^[A-Za-z]:[\\/]$') {
    if ($RootFull -ne '/') { $RootFull = $RootFull.TrimEnd('\', '/') }
}
if (-not (Test-Path -LiteralPath $RootFull -PathType Container)) { throw "Root is not a directory: $RootFull" }

$InstructionNames = @(
    'agents.md', 'claude.md', 'readme.md', 'readme_first.md', 'read_me_first.md',
    'copilot-instructions.md', 'gemini.md', 'cursor.md', '.cursorrules',
    '.windsurfrules', 'contributing.md'
)
$ClaimPatterns = @(
    '*authority*', '*status*', '*index*', '*manifest*', '*inventory*', '*handoff*',
    '*final*', '*current*', '*roadmap*', '*quick_context*', '*state*', '*latest*',
    '*master*', '*policy*', '*summary*', '*_v[0-9]*'
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
    '.npmrc', '.pypirc', 'credentials.json', 'id_ed25519', 'id_ecdsa', 'id_dsa',
    '.netrc', '_netrc', '.git-credentials'
)
$SecretHintExtensions = @('.pem', '.key', '.pfx', '.p12', '.kdbx', '.ppk', '.jks', '.keystore')
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
function Get-Short($full) {
    $tail = $full.Substring($RootFull.Length).TrimStart('\', '/').Replace('\', '/')
    if ($tail) { './' + $tail } else { '.' }
}

function Test-SecretHintName([string]$name) {
    $lowered = $name.ToLower()
    if ($SecretHintNames -contains $lowered) { return $true }
    if ($SecretHintExtensions -contains [System.IO.Path]::GetExtension($lowered)) { return $true }
    foreach ($prefix in $SecretHintPrefixRules.Keys) {
        foreach ($separator in $SecretHintPrefixRules[$prefix]) {
            if ($lowered.StartsWith($prefix + $separator)) { return $true }
        }
    }
    return $false
}

# Same rules as clean_local_reference() in audit_folder.py: <angle target>,
# optional "title", #fragment, and %XX decoding.
function Get-CleanReference([string]$value) {
    $cleaned = $value.Trim()
    if ($cleaned.StartsWith('<') -and $cleaned.Contains('>')) {
        $cleaned = $cleaned.Substring(1, $cleaned.IndexOf('>') - 1).Trim()
    }
    elseif ($cleaned -match '^(\S+)\s+(?:"[^"]*"|''[^'']*''|\([^)]*\))\s*$') {
        $cleaned = $Matches[1]
    }
    $cleaned = ($cleaned -split '#', 2)[0].Trim()
    if ($cleaned.Contains('%')) {
        try { $cleaned = [System.Uri]::UnescapeDataString($cleaned) } catch { }
    }
    return $cleaned
}

function Test-ExternalOrNonPath([string]$value) {
    if (-not $value) { return $true }
    if ($value.StartsWith('#')) { return $true }
    if ($value -match '^[A-Za-z][A-Za-z0-9+.-]+:') { return $true }   # any URI scheme; C:\ is a path
    if ($value -match '^v?\d+(?:\.\d+)+(?:[-+][0-9A-Za-z.-]+)?$') { return $true }  # version string
    return $false
}

# Windows is case-insensitive, so an index reference of 'tools\build_x.ps1'
# against an on-disk 'Build_x.ps1' passes Test-Path and then breaks for any
# agent reading the same index on Linux or a case-sensitive volume. Multi-agent
# means multi-platform, so report it -- as a review item, not a broken link,
# because it is not broken on the owner's own machine.
function Test-CaseExact([string]$full) {
    $cur = $full
    while ($true) {
        $parent = [System.IO.Path]::GetDirectoryName($cur)
        $leaf = [System.IO.Path]::GetFileName($cur)
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

# Segment-aware, case-insensitive glob. Identical semantics to glob_regex() in
# audit_folder.py: '*' stays inside one segment, '**/' spans zero or more whole
# segments, a trailing '/**' means "everything below", and a pattern with no '/'
# is matched against every segment. The v1.1 version fell back to a substring
# test for '**/x/**', so '**/logs/**' also excluded 'Catalogs/' and
# 'changelogs.md' - the exact false match the noise-hint code warns about.
$script:GlobCache = @{}
function Get-GlobRegex([string]$pat) {
    if ($script:GlobCache.ContainsKey($pat)) { return $script:GlobCache[$pat] }
    $p = $pat.Replace('\', '/').Trim()
    $anchored = $p.TrimEnd('/').Contains('/')
    if ($p -ne '/') { $p = $p.TrimEnd('/') }
    $sb = [System.Text.StringBuilder]::new()
    $i = 0
    while ($i -lt $p.Length) {
        if ($p.Substring($i).StartsWith('**/')) { [void]$sb.Append('(?:[^/]*/)*'); $i += 3 }
        elseif ($p.Substring($i) -eq '/**') { [void]$sb.Append('(?:/.*)?'); $i += 3 }
        elseif ($p.Substring($i).StartsWith('**')) { [void]$sb.Append('.*'); $i += 2 }
        elseif ($p[$i] -eq '*') { [void]$sb.Append('[^/]*'); $i += 1 }
        elseif ($p[$i] -eq '?') { [void]$sb.Append('[^/]'); $i += 1 }
        elseif ($p[$i] -eq '[') {
            $j = $p.IndexOf(']', $i + 1)
            if ($j -lt 0) { [void]$sb.Append([regex]::Escape([string]$p[$i])); $i += 1 }
            else {
                $body = $p.Substring($i + 1, $j - $i - 1)
                if ($body.StartsWith('!')) { $body = '^' + $body.Substring(1) }
                [void]$sb.Append('[' + $body.Replace('\', '\\') + ']'); $i = $j + 1
            }
        }
        else { [void]$sb.Append([regex]::Escape([string]$p[$i])); $i += 1 }
    }
    $body = $sb.ToString()
    $pattern = if ($anchored) { '\A' + $body + '(?:/.*)?\z' } else { '(?:\A|.*/)' + $body + '(?:/.*)?\z' }
    $rx = [regex]::new($pattern, [System.Text.RegularExpressions.RegexOptions]'IgnoreCase, Singleline')
    $script:GlobCache[$pat] = $rx
    return $rx
}

function Test-MatchPattern([string]$relPath, [string]$pat) {
    return (Get-GlobRegex $pat).IsMatch($relPath.TrimEnd('/'))
}

function Resolve-InputPath([string]$value) {
    if ([System.IO.Path]::IsPathRooted($value)) { return $value }
    return (Join-Path $RootFull $value.Replace('/', [System.IO.Path]::DirectorySeparatorChar))
}

function Get-ExpectedManifestRows([string]$path) {
    $first = Get-Content -LiteralPath $path -TotalCount 1 -Encoding UTF8 -ErrorAction Stop
    if ($first -match ',' -and $first -match '(?i)path') {
        return @(Import-Csv -LiteralPath $path -Encoding UTF8 | ForEach-Object {
            $value = if ($_.path) { $_.path } else { $_.relative_path }
            if ($value) {
                [PSCustomObject]@{
                    path = ([string]$value).Trim()
                    size = ([string]$_.size).Trim()
                    sha256 = ([string]$_.sha256).Trim().ToLower()
                }
            }
        })
    }
    return @(Get-Content -LiteralPath $path -Encoding UTF8 -ErrorAction Stop |
        Where-Object { $_.Trim() -and -not $_.TrimStart().StartsWith('#') } |
        ForEach-Object { [PSCustomObject]@{ path = $_.Trim(); size = ''; sha256 = '' } })
}

function Test-PointerCandidate($file) {
    if ($file.Length -gt 4096) { return $false }
    if (@('.md', '.txt') -notcontains $file.Extension.ToLower()) { return $false }
    try { $text = Get-Content -LiteralPath $file.FullName -Raw -Encoding UTF8 -ErrorAction Stop }
    catch { return $false }
    $lines = @($text -split "`r?`n" | Where-Object { $_.Trim() })
    if ($lines.Count -eq 0 -or $lines.Count -gt 12) { return $false }
    $directive = $text -match '(?i)\b(read|see|start|canonical|authoritative|use|go to|continue in)\b'
    $localRef = ($text -match '\]\([^)]+\)') -or ($text -match '`[^`\r\n]+\.[A-Za-z0-9]{1,8}`')
    return ($directive -and $localRef)
}

Write-Host "Read-only audit of $RootFull"
Write-Host "Generated $(Get-Date -Format 'yyyy-MM-dd HH:mm')"

# Explicit walk instead of Get-ChildItem -Recurse, for three reasons:
#  1. Windows PowerShell 5.1 follows junctions on -Recurse (PowerShell 7 and
#     Python's os.walk do not), which can count an external runtime as project
#     content or loop on a cyclic junction.
#  2. -ErrorAction SilentlyContinue dropped unreadable directories without a
#     trace; each one is a hole in every total and must be reported.
#  3. Collecting into List[T] keeps the pass linear. The v1.1 '+=' array appends
#     were quadratic (about 64 s for 40,000 files versus 0.7 s in Python).
# Only NAME-SURROGATE reparse points (junctions, directory symlinks) are skipped.
# OneDrive Files On-Demand marks ordinary synced folders with the ReparsePoint
# attribute too; those carry real project content and must be walked.
function Test-LinkDirectory($item) {
    if (-not ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint)) { return $false }
    $lt = $item.LinkType
    return ($lt -eq 'Junction' -or $lt -eq 'SymbolicLink')
}

$allFiles = [System.Collections.Generic.List[System.IO.FileInfo]]::new()
$allFolderItems = [System.Collections.Generic.List[System.IO.DirectoryInfo]]::new()
$reparseDirs = [System.Collections.Generic.List[System.IO.DirectoryInfo]]::new()
$emptyFolders = [System.Collections.Generic.List[System.IO.DirectoryInfo]]::new()
$unreadableDirs = [System.Collections.Generic.List[object]]::new()
$walk = [System.Collections.Generic.Stack[System.IO.DirectoryInfo]]::new()
$walk.Push([System.IO.DirectoryInfo]::new($RootFull))
while ($walk.Count) {
    $dir = $walk.Pop()
    try { $entries = @($dir.EnumerateFileSystemInfos()) }
    catch {
        $inner = $_.Exception
        while ($inner.InnerException) { $inner = $inner.InnerException }
        $unreadableDirs.Add([pscustomobject]@{ Path = $dir.FullName; Why = $inner.GetType().Name })
        continue
    }
    if ($entries.Count -eq 0 -and $dir.FullName -ne $RootFull) { $emptyFolders.Add($dir) }
    foreach ($e in $entries) {
        if ($e -is [System.IO.DirectoryInfo]) {
            $allFolderItems.Add($e)
            if (Test-LinkDirectory $e) { $reparseDirs.Add($e) }
            else { $walk.Push($e) }
        }
        else { $allFiles.Add($e) }
    }
}
$allFolders = $allFolderItems.Count

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
$files = [System.Collections.Generic.List[System.IO.FileInfo]]::new()
foreach ($f in $allFiles) {
    $rp = Get-RelSlash $f.FullName
    $hit = $null
    foreach ($pat in $Exclude) { if (Test-MatchPattern $rp $pat) { $hit = $pat; break } }
    if ($hit) { $excludedCounts[$hit] = [int]$excludedCounts[$hit] + 1 } else { $files.Add($f) }
}

$visibleEmptyFolders = [System.Collections.Generic.List[object]]::new()
$excludedEmptyFolders = [System.Collections.Generic.List[object]]::new()
foreach ($folder in $emptyFolders) {
    $rp = (Get-RelSlash $folder.FullName) + '/'
    $hit = $false
    foreach ($pat in $Exclude) { if (Test-MatchPattern $rp $pat) { $hit = $true; break } }
    if ($hit) { $excludedEmptyFolders.Add($folder) } else { $visibleEmptyFolders.Add($folder) }
}

Write-Section "Summary"
$totalBytes = ($allFiles | Measure-Object Length -Sum).Sum
$maxDepth = 0
foreach ($f in $allFiles) {
    $d = (Get-RelSlash $f.FullName).Split('/').Count - 1
    if ($d -gt $maxDepth) { $maxDepth = $d }
}
Write-Host ("  Files (all):      {0}" -f $allFiles.Count)
if ($unreadableDirs.Count) {
    Write-Host ("  Unreadable dirs:  {0} (contents NOT counted)" -f $unreadableDirs.Count)
}
Write-Host ("  Folders:          {0}" -f $allFolders)
Write-Host ("  Total MB:         {0:N2}" -f ($totalBytes / 1MB))
Write-Host ("  Max depth:        {0}" -f $maxDepth)
if ($Exclude.Count) {
    $exTotal = ($excludedCounts.Values | Measure-Object -Sum).Sum
    $pct = if ($allFiles.Count) { 100.0 * $exTotal / $allFiles.Count } else { 0 }
    Write-Host ("  Excluded:         {0} ({1:N0}%) by -Exclude" -f $exTotal, $pct)
    Write-Host ("  In detail below:  {0}" -f $files.Count)
}

if ($unreadableDirs.Count) {
    Write-Section "Directories not readable (contents missing from every count)"
    $unreadableDirs | Select-Object -First 25 | ForEach-Object {
        Write-Host ("  {0,-18} {1}" -f $_.Why, (Get-Short $_.Path))
    }
    if ($unreadableDirs.Count -gt 25) { Write-Host ("  ... and " + ($unreadableDirs.Count - 25) + " more") }
    Write-Host "  Access was denied or the directory vanished mid-walk. Nothing below these paths is in any total. Resolve access or disclose the gap." -ForegroundColor Yellow
}

if ($Exclude.Count) {
    Write-Section "Excluded from detail sections (counted, not examined)"
    foreach ($k in ($excludedCounts.GetEnumerator() | Sort-Object Value -Descending)) {
        Write-Host ("  {0,6}  {1}" -f $k.Value, $k.Key)
    }
    Write-Host "  These files were NOT classified. State this in the report." -ForegroundColor Yellow
}

Write-Section "Per-folder counts (top 25)"
$perFolder = @{}
foreach ($f in $files) { $perFolder[$f.DirectoryName] = [int]$perFolder[$f.DirectoryName] + 1 }
$perFolder.GetEnumerator() |
Sort-Object @{ Expression = 'Value'; Descending = $true }, @{ Expression = { (Get-Short $_.Key).ToLower() } } | Select-Object -First 25 |
ForEach-Object { Write-Host ("  {0,6}  {1}" -f $_.Value, (Get-Short $_.Key)) }

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
$files | Group-Object { $_.Extension.ToLower() } | Sort-Object @{ Expression = 'Count'; Descending = $true }, Name | Select-Object -First 20 |
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
# All discovered files, like audit_folder.py: an excluded file still has to move.
$longPaths = @($allFiles | Where-Object { $_.FullName.Length -gt $PathThreshold })
if ($longPaths.Count) {
    $longPaths | Select-Object -First 40 | ForEach-Object { Write-Host ("  {0,4}  {1}" -f $_.FullName.Length, $_.FullName) }
    if ($longPaths.Count -gt 40) { Write-Host ("  ... and " + ($longPaths.Count - 40) + " more") }
}
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
$dupNames = @($files | Group-Object { $_.Name.ToLower() } | Where-Object Count -gt 1 |
    Sort-Object @{ Expression = 'Count'; Descending = $true }, Name)
if ($dupNames.Count) {
    foreach ($g in ($dupNames | Select-Object -First 20)) {
        $members = @($g.Group | Sort-Object { (Get-Short $_.FullName).ToLower() })
        Write-Host ("-- " + $members[0].Name + "  (" + $g.Count + ")")
        $members | Select-Object -First $DupGroupCap | ForEach-Object {
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
    $groups = @($hashes | Group-Object Hash | Where-Object Count -gt 1 |
        Sort-Object @{ Expression = 'Count'; Descending = $true }, @{ Expression = { $_.Name.ToLower() } })
    if ($groups.Count) {
        foreach ($g in $groups) {
            Write-Host ("-- " + $g.Name.Substring(0, 12).ToLower() + "  (" + $g.Count + " copies)")
            $g.Group | Sort-Object { (Get-Short $_.Path).ToLower() } | Select-Object -First $DupGroupCap | ForEach-Object { Write-Host ("     " + (Get-Short $_.Path)) }
            if ($g.Count -gt $DupGroupCap) { Write-Host ("     ... +" + ($g.Count - $DupGroupCap) + " more") }
        }
        Write-Host ("  " + $groups.Count + " group(s). Copy-only dual trees: no marker says which side is canonical.")
    }
    else { Write-Host "  none" }

    Write-Section "Same name, DIFFERENT content (ambiguous citation)"
    $ambiguous = @($hashes | Group-Object { $_.Name.ToLower() } |
        Where-Object { $_.Count -gt 1 -and (@($_.Group | Select-Object -ExpandProperty Hash -Unique).Count -gt 1) } |
        Sort-Object @{ Expression = 'Count'; Descending = $true }, Name)
    if ($ambiguous.Count) {
        foreach ($g in ($ambiguous | Select-Object -First 20)) {
            $members = @($g.Group | Sort-Object { (Get-Short $_.Path).ToLower() })
            Write-Host ("-- " + $members[0].Name)
            $members | Select-Object -First $DupGroupCap | ForEach-Object {
                Write-Host ("     " + $_.Hash.Substring(0, 8).ToLower() + "  " + (Get-Short $_.Path))
            }
        }
        Write-Host ("  " + $ambiguous.Count + " name(s) resolve to more than one document. Any citation by filename alone is ambiguous.") -ForegroundColor Yellow
    }
    else { Write-Host "  none" }
}

Write-Section "Claims requiring verification (open these - never trust the name)"
$claimMatchers = @($ClaimPatterns | ForEach-Object {
        [System.Management.Automation.WildcardPattern]::new($_, [System.Management.Automation.WildcardOptions]::IgnoreCase) })
$claims = [System.Collections.Generic.List[System.IO.FileInfo]]::new()
foreach ($f in $files) {
    foreach ($m in $claimMatchers) { if ($m.IsMatch($f.Name)) { $claims.Add($f); break } }
}
if ($claims.Count) {
    $claims | Sort-Object LastWriteTime -Descending | Select-Object -First 40 | ForEach-Object {
        Write-Host ("  {0:yyyy-MM-dd}  {1,9}  {2}" -f $_.LastWriteTime, $_.Length, (Get-Short $_.FullName))
    }
    if ($claims.Count -gt 40) { Write-Host ("  ... +" + ($claims.Count - 40) + " more") }
    Write-Host "  Each is verified, contradicted or unverifiable. Never upgrade unverifiable to current."
}
else { Write-Host "  none" }

Write-Section "Possible credential-bearing files"
$secrets = [System.Collections.Generic.List[System.IO.FileInfo]]::new()
foreach ($f in $allFiles) { if (Test-SecretHintName $f.Name) { $secrets.Add($f) } }
if ($secrets.Count) {
    Write-Host ("  " + $secrets.Count + " file(s) matched credential-name hints:") -ForegroundColor Yellow
    $secrets | Select-Object -First 25 | ForEach-Object { Write-Host ("     " + (Get-Short $_.FullName)) }
    if ($secrets.Count -gt 25) { Write-Host ("     ... +" + ($secrets.Count - 25) + " more") }
    Write-Host "  Do not stage, copy, or index these. Flag to the owner before sharing the folder. Never copy a secret value into a report or journal." -ForegroundColor Yellow
}
else { Write-Host "  none detected by name" }

Write-Section "Large journals (threshold $JournalThresholdKB KB)"
$journalLimit = [int64]$JournalThresholdKB * 1024
$journals = @($allFiles | Where-Object { $_.Name.ToLower().Contains('journal') -and $_.Length -ge $journalLimit })
if ($journals.Count) {
    $journals | Sort-Object Length -Descending | ForEach-Object {
        Write-Host ("  {0,9}  {1}" -f $_.Length, (Get-Short $_.FullName))
    }
    Write-Host "  Rotation is a proposal only; preserve every entry and require approval."
}
else { Write-Host "  none" }

if ($EntryPoint.Count) {
    Write-Section "Expected entrypoints"
    foreach ($value in $EntryPoint) {
        $target = Resolve-InputPath $value
        $state = if (Test-Path -LiteralPath $target) { 'PRESENT' } else { 'MISSING' }
        Write-Host ("  {0,-7}  {1}" -f $state, $value)
    }
    Write-Host "  Missing is established against this direct filesystem root only."
}

if ($Portfolio) {
    Write-Section "Portfolio root matrix (immediate children; advisory)"
    $defaults = @('AGENTS.md', 'README_FIRST.md', 'PROJECT_ROADMAP_STATUS.md',
        'AUTHORITY_MAP.md', 'INDEX.md', 'AI_CONTEXT/README_FIRST.md',
        'AI_CONTEXT/PROJECT_QUICK_CONTEXT.md', 'AI_CONTEXT/PROJECT_ACTIVITY_JOURNAL.md',
        'AI_CONTEXT/CHAT_INDEX.md')
    $checks = @($defaults + $EntryPoint | Select-Object -Unique)
    Write-Host "  Project | Count scope | Root items | Entrypoints present"
    $children = @(Get-ChildItem -LiteralPath $RootFull -Directory -Force -ErrorAction SilentlyContinue | Sort-Object Name)
    if ($children.Count) {
        foreach ($child in $children) {
            $count = @(Get-ChildItem -LiteralPath $child.FullName -Force -ErrorAction SilentlyContinue).Count
            $present = @($checks | Where-Object { Test-Path -LiteralPath (Join-Path $child.FullName $_) })
            $value = if ($present.Count) { $present -join ', ' } else { '(none detected)' }
            Write-Host ("  {0} | root-level | {1} | {2}" -f $child.Name, $count, $value)
        }
    }
    else { Write-Host "  no immediate child directories" }
    Write-Host "  Presence does not determine authority or operational state."
}

if ($DetectPointers) {
    Write-Section "Possible pointer stubs (advisory; content not authority)"
    $candidates = @($files | Where-Object { Test-PointerCandidate $_ })
    if ($candidates.Count) {
        $candidates | ForEach-Object { Write-Host ("  " + (Get-Short $_.FullName)) }
        Write-Host "  Verify the target exists and that the file contains no independent guidance."
    }
    else { Write-Host "  none" }
}

foreach ($manifestValue in $ExpectedUploadManifest) {
    Write-Section "Expected upload manifest: $manifestValue"
    $manifestPath = Resolve-InputPath $manifestValue
    if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
        Write-Host "  MANIFEST NOT FOUND: $manifestPath"
        continue
    }
    try { $expected = @(Get-ExpectedManifestRows $manifestPath) }
    catch { Write-Host ("  MANIFEST UNREADABLE: " + $_.Exception.GetType().Name); continue }
    $present = 0; $missing = 0; $sizeBad = 0; $hashBad = 0
    foreach ($row in $expected) {
        $target = Resolve-InputPath $row.path
        if (-not (Test-Path -LiteralPath $target -PathType Leaf)) {
            $missing++; Write-Host ("  MISSING        " + $row.path); continue
        }
        $present++
        if ($row.size) {
            [int64]$wanted = 0
            if (-not [int64]::TryParse([string]$row.size, [ref]$wanted)) {
                $sizeBad++; Write-Host ("  BAD SIZE VALUE " + $row.path + " = '" + $row.size + "'")
            }
            else {
                $actual = (Get-Item -LiteralPath $target).Length
                if ($actual -ne $wanted) {
                    $sizeBad++; Write-Host ("  SIZE MISMATCH  {0} expected={1} actual={2}" -f $row.path, $wanted, $actual)
                }
            }
        }
        if ($row.sha256) {
            $actualHash = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLower()
            if ($actualHash -ne ([string]$row.sha256).ToLower()) {
                $hashBad++; Write-Host ("  HASH MISMATCH  " + $row.path)
            }
        }
    }
    Write-Host ("  Expected: {0}  Present: {1}  Missing: {2}  Size mismatches: {3}  Hash mismatches: {4}" -f $expected.Count, $present, $missing, $sizeBad, $hashBad)
    Write-Host "  This verifies listed files only; it does not authorize upload, overwrite, or promotion."
}

foreach ($ip in $IndexPath) {
    Write-Section "Index link check: $ip"
    $idx = Join-Path $RootFull $ip
    if (Test-Path -LiteralPath $idx -PathType Leaf) {
        # -Encoding UTF8: Windows PowerShell 5.1 otherwise reads BOM-less UTF-8
        # as ANSI and reports every non-ASCII link target as broken.
        $content = Get-Content -LiteralPath $idx -Raw -Encoding UTF8
        if ($null -eq $content) { $content = '' }
        $mdPattern = '\]\(\s*(<[^>\r\n]+>|[^)\s]+)(?:\s+(?:"[^"]*"|''[^'']*''))?\s*\)'
        $markdownLinks = @([regex]::Matches($content, $mdPattern) |
            ForEach-Object { Get-CleanReference $_.Groups[1].Value } |
            Where-Object { -not (Test-ExternalOrNonPath $_) } | Select-Object -Unique)
        $backtickedRefs = @([regex]::Matches($content, '`([^`\r\n]+\.[A-Za-z0-9]{1,8})`') |
            ForEach-Object { Get-CleanReference $_.Groups[1].Value } |
            Where-Object { -not (Test-ExternalOrNonPath $_) } | Select-Object -Unique)
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
$instr = @($allFiles | Where-Object { $InstructionNames -contains $_.Name.ToLower() } | Sort-Object { Get-Short $_.FullName })
if ($instr.Count) {
    $instr | ForEach-Object { Write-Host ("  {0:yyyy-MM-dd}  {1}" -f $_.LastWriteTime, (Get-Short $_.FullName)) }
    # Root level only, like audit_folder.py: nested files legitimately scope a subtree.
    $rootAgentFiles = @($instr | Where-Object {
            $_.Name.ToLower() -ne 'readme.md' -and $_.DirectoryName.TrimEnd('\', '/') -eq $RootFull.TrimEnd('\', '/') })
    if ($rootAgentFiles.Count -gt 1) {
        Write-Host "  Multiple root-level agent-instruction files - check for conflicting scope. Record the conflict; resolve none unilaterally." -ForegroundColor Yellow
    }
}
else {
    Write-Host "  NONE FOUND ANYWHERE." -ForegroundColor Yellow
    Write-Host "  No AGENTS.md / CLAUDE.md / README.md in the tree means every agent's instructions live outside the folder and cannot be read by the next one. Report this as a finding."
}

Write-Host ""
if ($Exclude.Count) {
    $exTotal = ($excludedCounts.Values | Measure-Object -Sum).Sum
    Write-Host ("Coverage: {0} of {1} files examined in detail; {2} excluded by -Exclude and classified by nothing. Say so in the report." -f $files.Count, $allFiles.Count, $exTotal)
    Write-Host ""
}
if ($unreadableDirs.Count) {
    Write-Host ("Coverage gap: {0} director{1} could not be read; their contents are in no count." -f $unreadableDirs.Count, $(if ($unreadableDirs.Count -eq 1) { 'y' } else { 'ies' }))
    Write-Host ""
}
Write-Host "Audit complete. Nothing was written to $RootFull." -ForegroundColor Green
