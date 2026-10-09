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

.PARAMETER HostRoot
  Real host path of -Root (for example its Windows path when the folder is
  mounted elsewhere). Path lengths are measured as HostRoot + relative path.

.PARAMETER Brief
  Cap every list at 10 lines.

.PARAMETER Out
  Write the full report to this file (outside Root; never overwritten) and
  print only the summary and the findings-at-a-glance block.

.PARAMETER PruneNoise
  Do not walk high-confidence generated state (.git, node_modules, Python
  environments, caches). Pruned folders are listed and are in no count.

.PARAMETER MaxSeconds
  Stop walking after this many seconds and disclose the unvisited directories.

.PARAMETER IndexCoverage
  Repeatable 'INDEX=DIR': list files directly in DIR that INDEX never mentions.

.PARAMETER ReadBudgetKB
  Flag a startup read set (root instruction files + -EntryPoint files) larger
  than this. Default 40.

.PARAMETER Version
  Print the helper version and exit.

.EXAMPLE
  pwsh -File audit_folder.ps1 -Root C:\Projects\Thing -SuggestExcludes

.EXAMPLE
  pwsh -File audit_folder.ps1 -Root C:\Projects\Thing -HashFiles `
      -Exclude 'tmp/**','**/__pycache__/**' `
      -IndexPath 'INDEX.md','AI_CONTEXT/CHAT_INDEX.md'
#>
[CmdletBinding()]
param(
    [string]$Root,
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
    [string[]]$ExpectedUploadManifest = @(),
    [string]$HostRoot = '',
    [switch]$Brief,
    [string]$Out = '',
    [switch]$PruneNoise,
    [double]$MaxSeconds = 0,
    [string[]]$IndexCoverage = @(),
    [int]$ReadBudgetKB = 40,
    [switch]$Orient,
    [switch]$SessionIndex,
    [switch]$Pending,
    [string]$SessionsDir = 'AI_CONTEXT/SESSIONS',
    [string]$SessionIndexFile = 'AI_CONTEXT/SESSION_INDEX.md',
    [string]$ScratchDir = 'AI_CONTEXT/scratch',
    [string]$QuickContext = 'AI_CONTEXT/PROJECT_QUICK_CONTEXT.md',
    [int]$QuickContextKB = 12,
    [int]$ActiveMinutes = 30,
    [string]$SessionId = '',
    [string]$Since = '',
    [switch]$Version
)

$ScriptVersion = '1.7.1'   # must equal SKILL.md metadata.version
if ($Version) { Write-Output "audit_folder.ps1 $ScriptVersion"; exit 0 }
if (-not $Root) { throw "-Root is required" }

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
$IndexCoverage = @($IndexCoverage | Where-Object { $_ } | ForEach-Object { $_ -split ',' } | ForEach-Object { $_.Trim() } | Where-Object { $_ })
if ($JournalThresholdKB -lt 0) { throw "JournalThresholdKB must be zero or greater" }
if ($ReadBudgetKB -lt 0) { throw "ReadBudgetKB must be zero or greater" }
$CoveragePairs = @()
foreach ($spec in $IndexCoverage) {
    if (($spec.ToCharArray() | Where-Object { $_ -eq '=' }).Count -ne 1) { throw "-IndexCoverage must be INDEX=DIR: '$spec'" }
    $pair = $spec.Split('=')
    $CoveragePairs += , @($pair[0].Trim(), $pair[1].Trim())
}

if (-not (Test-Path -LiteralPath $Root)) { throw "Root not found: $Root" }
# ProviderPath, not Path: for a UNC/NAS root, .Path can come back provider-
# qualified ("Microsoft.PowerShell.Core\FileSystem::\\server\share"), which
# breaks every Substring($RootFull.Length) below.
$RootFull = (Resolve-Path -LiteralPath $Root).ProviderPath
if ($RootFull.Length -gt 3 -or $RootFull -notmatch '^[A-Za-z]:[\\/]$') {
    if ($RootFull -ne '/') { $RootFull = $RootFull.TrimEnd('\', '/') }
}
if (-not (Test-Path -LiteralPath $RootFull -PathType Container)) { throw "Root is not a directory: $RootFull" }
# The walk's own spelling of the root. On Windows, .NET can hand back
# enumerated paths with 8.3 short names expanded (C:\Users\RUNNER~1 becomes
# C:\Users\runneradmin), so Substring($RootFull.Length) would cut the wrong
# number of characters and push every file one bogus folder deeper. Take the
# prefix from what enumeration actually returns; Get-RootTail accepts either.
$RootDirInfo = [System.IO.DirectoryInfo]::new($RootFull)
$RootWalk = $RootDirInfo.FullName
try {
    $firstEntry = $RootDirInfo.EnumerateFileSystemInfos() | Select-Object -First 1
    if ($firstEntry) { $RootWalk = [System.IO.Path]::GetDirectoryName($firstEntry.FullName) }
} catch { }

# Names hosts load as agent instructions automatically, and startup documents
# an agent may be told to read. Same sets as audit_folder.py.
$AutoloadNames = @('agents.md', 'claude.md', 'gemini.md', 'copilot-instructions.md',
    'cursor.md', '.cursorrules', '.windsurfrules')
$ReadmeNames = @('readme.md', 'readme_first.md', 'read_me_first.md', 'contributing.md')
$InstructionNames = @($AutoloadNames + $ReadmeNames)
$CodexDocLimit = 32768
$NonGoverningTokens = @('incoming', 'inbox', 'history', 'archive', 'scratch', 'quarantine',
    'backup', 'staging', 'unreviewed', 'proposed', 'skill copies', 'superseded')
$GlobalNoise = @('__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache', 'node_modules')
$PruneSafe = @('__pycache__', 'node_modules', '.git', '.svn', '.venv', 'venv', '.mypy_cache',
    '.pytest_cache', '.ruff_cache', '.tox', '.next', '.terraform', 'site-packages', '__pypackages__')
$OrphanRules = @(
    @('^zi[A-Za-z0-9]{6}$', 'Info-ZIP temp name', $false),
    @('^~\$', 'Office lock/temp', $false),
    @('^\.~lock\..*#$', 'LibreOffice lock', $false),
    @('\.(tmp|temp|partial|crdownload)$', 'temporary extension', $true)
)
$UuidPattern = '[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}'
function Get-Cap([int]$n) { if ($Brief) { [Math]::Min($n, 10) } else { $n } }
$DupCap = if ($Brief) { [Math]::Min($DupGroupCap, 3) } else { $DupGroupCap }
$ClaimPatterns = @(
    '*authority*', '*status*', '*index*', '*manifest*', '*inventory*', '*handoff*',
    '*final*', '*current*', '*roadmap*', '*quick_context*', '*state*', '*latest*',
    '*master*', '*policy*', '*summary*', '*_v[0-9]*'
)
$NoiseDirHints = @(
    '__pycache__', 'node_modules', '.git', '.svn', '.venv', 'venv', '.mypy_cache',
    '.pytest_cache', '.ruff_cache', '.tox', '.idea', '.vscode', 'chrome-profile',
    'edge-profile', 'firefox-profile', 'puppeteer', 'playwright', 'browser-profile',
    'cache', 'caches', 'logs', 'dist', 'build', '.next', '.terraform', 'site-packages', '__pypackages__'
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

# Every report line goes through Write-Line so -Out can save the full report
# and print only the summary. Without -Out, lines are written immediately.
$script:ReportLines = [System.Collections.Generic.List[string]]::new()
function Write-Line {
    param([Parameter(Position = 0)][object]$Object = '', [string]$ForegroundColor = '')
    $text = [string]$Object
    [void]$script:ReportLines.Add($text)
    if (-not $Out) {
        if ($ForegroundColor) { Write-Host $text -ForegroundColor $ForegroundColor } else { Write-Host $text }
    }
}
function Write-Section($t) { Write-Line ""; Write-Line "== $t ==" -ForegroundColor Cyan }
function Get-RootTail([string]$full) {
    foreach ($prefix in @($RootWalk, $RootFull)) {
        if ($prefix -and $full.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
            return $full.Substring($prefix.Length).TrimStart('\', '/').Replace('\', '/')
        }
    }
    return $full.Replace('\', '/')
}
function Get-RelSlash($full) { Get-RootTail $full }
function Get-Short($full) {
    $tail = Get-RootTail $full
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

function Get-ContentReadBlockReason([string]$path) {
    $cur = [IO.Path]::GetFullPath($path)
    $inside = $false
    foreach ($base in @($RootFull, $RootWalk)) {
        $boundary = $base.TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar
        if ($cur -eq $base -or $cur.StartsWith($boundary, [StringComparison]::OrdinalIgnoreCase)) { $inside = $true }
    }
    if (-not $inside) { return 'unreadable' }
    $first = $true
    while ($cur) {
        # Folders above the chosen root are the owner's location, not traversal.
        if ($cur.TrimEnd('\', '/') -ieq $RootFull.TrimEnd('\', '/') -or $cur.TrimEnd('\', '/') -ieq $RootWalk.TrimEnd('\', '/')) { break }
        if (Test-SecretHintName ([IO.Path]::GetFileName($cur))) { return 'credential' }
        try {
            $item = Get-Item -LiteralPath $cur -Force -ErrorAction Stop
            # Cloud-only state matters for the file itself; folders are only
            # checked for links (OneDrive folders carry recall attributes).
            if ($item.LinkType) { return 'link' }
            if ($first -and (Test-CloudOnly $item)) { return 'unreadable' }
        } catch { return 'unreadable' }
        $first = $false
        $parent = [IO.Path]::GetDirectoryName($cur)
        if ($parent -eq $cur) { break }
        $cur = $parent
    }
    return $null
}
function Test-ContentReadAllowed([string]$path) {
    return $null -eq (Get-ContentReadBlockReason $path)
}
function Assert-ContentRead([string]$path) {
    if (-not (Test-ContentReadAllowed $path)) { throw 'READ BLOCKED: credential hint, link, or cloud placeholder' }
}
function Select-BriefItems {
    param([Parameter(ValueFromPipeline=$true)]$InputObject)
    begin { $items = [Collections.Generic.List[object]]::new() }
    process { $items.Add($InputObject) }
    end {
        $items | Select-Object -First (Get-Cap $items.Count)
        if ($items.Count -gt (Get-Cap $items.Count)) { Write-Line ("  ... and " + ($items.Count - (Get-Cap $items.Count)) + " more") }
    }
}
function Get-MarkdownTargets([string]$text) {
    foreach ($match in [regex]::Matches($text, '\]\(\s*')) {
        $start = $match.Index + $match.Length
        $i = $start
        if ($i -lt $text.Length -and $text[$i] -eq '<') {
            $end = $text.IndexOf('>', $i + 1)
            if ($end -ge 0 -and -not $text.Substring($i, $end - $i).Contains("`n")) { $text.Substring($i, $end - $i + 1) }
            continue
        }
        $depth = 0
        while ($i -lt $text.Length) {
            $ch = $text[$i]
            if ($ch -eq '\' -and $i + 1 -lt $text.Length) { $i += 2; continue }
            if ($ch -eq '(') { $depth++ }
            elseif ($ch -eq ')') { if ($depth -eq 0) { break }; $depth-- }
            elseif ([char]::IsWhiteSpace($ch) -and $depth -eq 0) { break }
            $i++
        }
        if ($i -gt $start -and $depth -eq 0 -and $i -lt $text.Length) { $text.Substring($start, $i - $start) }
    }
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
    return ($cleaned -replace '\\([()])', '$1')
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
    $cur = [IO.Path]::GetFullPath($full)
    while ($true) {
        if ($cur -eq $RootFull -or $cur -eq $RootWalk) { return $true }
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
    $normalized = $value.Replace('\', '/')
    if ($normalized.StartsWith('//') -or $normalized -match '^[A-Za-z]:/') {
        if (Test-Path -LiteralPath $normalized) { return $normalized }; return @()
    }
    $candidate = $normalized.TrimStart('/')
    $hits = @()
    $bases = if ($normalized.StartsWith('/')) { @($RootFull) } else { @($indexDir, $RootFull) }
    foreach ($base in $bases) {
        $full = [IO.Path]::GetFullPath((Join-Path $base $candidate))
        if (Test-Path -LiteralPath $full) { $hits += $full; break }
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
    return @(Get-ResolvedReferencePaths $value $indexDir).Count -gt 0
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
    Assert-ContentRead $path
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
    if (-not (Test-ContentReadAllowed $file.FullName)) { return $false }
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

# Ordinal sorting on one composite string key, so ties and punctuation order
# exactly like Python's sorted(). Sort-Object compares with the current
# culture, which orders '~', '_' and '-' differently and breaks report parity.
function Sort-Ordinal {
    param([Parameter(ValueFromPipeline = $true)]$InputObject, [scriptblock]$Key)
    begin { $items = [System.Collections.Generic.List[object]]::new() }
    process { if ($null -ne $InputObject) { $items.Add($InputObject) } }
    end {
        $arr = $items.ToArray()
        if ($arr.Count -lt 2) { return $arr }
        # Sort the keys alone (each carries its original index) to avoid
        # overload resolution copying the item array behind our back.
        $keys = [string[]]::new($arr.Count)
        for ($i = 0; $i -lt $arr.Count; $i++) {
            $keys[$i] = [string]($arr[$i] | ForEach-Object $Key) + [char]1 + $i.ToString('D10')
        }
        [Array]::Sort($keys, [System.StringComparer]::Ordinal)
        foreach ($k in $keys) { $arr[[int]$k.Substring($k.Length - 10)] }
    }
}
function Get-DescKey([int64]$n) { return (1000000000000000 - $n).ToString('D16') }
function Get-SessionNameKey($s) {
    return $s.Name.ToLowerInvariant() + [char]0 + $s.Name
}
function Get-SessionLoadKey($s) {
    $missing = if ($null -eq $s.Started) { '1' } else { '0' }
    $ticks = if ($null -eq $s.Started) { 0 } else { $s.Started.UtcTicks }
    return $missing + [char]0 + $ticks.ToString('D19') + [char]0 + $s.Id + [char]0 + (Get-SessionNameKey $s)
}
function Get-SessionRecentKey($s) {
    $ticks = (Get-Activity $s).UtcTicks
    return ([DateTimeOffset]::MaxValue.UtcTicks - $ticks).ToString('D19') + [char]0 + (Get-SessionNameKey $s)
}
function Get-SessionLatestStartKey($s) {
    return ([DateTimeOffset]::MaxValue.UtcTicks - $s.Started.UtcTicks).ToString('D19') + [char]0 + (Get-SessionNameKey $s)
}
function Test-NonGoverning([string]$relPath) {
    $segs = $relPath.ToLower().Split('/')
    for ($i = 0; $i -lt $segs.Count - 1; $i++) {
        foreach ($tok in $NonGoverningTokens) { if ($segs[$i].Contains($tok)) { return $true } }
    }
    return $false
}
function Test-HasSegment([string]$relPath, [string]$name) {
    $segs = $relPath.ToLower().Split('/')
    for ($i = 0; $i -lt $segs.Count - 1; $i++) { if ($segs[$i] -eq $name) { return $true } }
    return $false
}
function Test-CloudOnly($file) {
    $attrs = [int64]$file.Attributes
    return [bool](($attrs -band 0x1000) -or ($attrs -band 0x400000) -or
        (($attrs -band 0x400) -and ($attrs -band 0x40000)))
}
function Get-OrphanReason($file) {
    if (-not (Test-ContentReadAllowed $file.FullName)) { return $null }
    foreach ($rule in $OrphanRules) {
        $hit = if ($rule[2]) { $file.Name -match $rule[0] } else { $file.Name -cmatch $rule[0] }
        if ($hit) { return $rule[1] }
    }
    # Extensionless file holding archive bytes: usually an interrupted write.
    # Reads 8 bytes; skips cloud-only placeholders so nothing hydrates.
    if (-not $file.Name.Contains('.') -and $file.Length -ge 8 -and -not (Test-CloudOnly $file)) {
        try {
            $fs = [System.IO.File]::OpenRead($file.FullName)
            try { $buf = New-Object byte[] 8; [void]$fs.Read($buf, 0, 8) } finally { $fs.Dispose() }
        }
        catch { return $null }
        $hex = -join ($buf | ForEach-Object { $_.ToString('x2') })
        if ($hex.StartsWith('504b0304') -or $hex.StartsWith('377abcaf271c') -or $hex.StartsWith('52617221')) {
            return 'archive data without extension'
        }
    }
    return $null
}
function Get-SkillIdentity([string]$path) {
    try {
        Assert-ContentRead $path
        $fs = [System.IO.File]::OpenRead($path)
        try {
            $buf = New-Object byte[] 8192
            $n = $fs.Read($buf, 0, 8192)
            $head = [System.Text.Encoding]::UTF8.GetString($buf, 0, $n)
        } finally { $fs.Dispose() }
    }
    catch { return @('(unreadable)', '?') }
    $name = '(no name)'; $ver = '(no version)'
    if ($head.StartsWith('---')) {
        $end = $head.IndexOf("`n---", 3)
        $front = if ($end -ge 0) { $head.Substring(3, $end - 3) } else { $head }
        $m = [regex]::Match($front, '^name:\s*[''"]?([^''"\r\n]+?)[''"]?\s*$', 'Multiline')
        if ($m.Success) { $name = $m.Groups[1].Value.Trim() }
        $m = [regex]::Match($front, '^\s*version:\s*[''"]?([^''"\s]+)[''"]?\s*$', 'Multiline')
        if ($m.Success) { $ver = $m.Groups[1].Value.Trim() }
    }
    return @($name, $ver)
}
function Test-IndexMentions([string]$content, [string]$name) {
    if ($content.Contains($name)) { return $true }
    if ($content.Contains([System.Uri]::EscapeDataString($name).Replace('%2F', '/'))) { return $true }
    $m = [regex]::Match($name, $UuidPattern)
    return ($m.Success -and $content.ToLower().Contains($m.Value.ToLower()))
}
function Test-EnvRoot($dirs, $fileNames) {
    foreach ($f in $fileNames) { if ($f.ToLower() -eq 'pyvenv.cfg') { return $true } }
    $n = 0
    foreach ($d in $dirs) { if ($d.ToLower().EndsWith('.dist-info')) { $n++ } }
    return ($n -ge 3)
}

if ($Out) {
    $OutFull = [System.IO.Path]::GetFullPath($Out)
    $rootPrefix = $RootFull.TrimEnd('\', '/') + [System.IO.Path]::DirectorySeparatorChar
    if ($OutFull.StartsWith($rootPrefix, [System.StringComparison]::OrdinalIgnoreCase)) { throw "-Out must be outside the audited root: $OutFull" }
    if (Test-Path -LiteralPath $OutFull) { throw "-Out already exists; choose a new file: $OutFull" }
}

if (-not ($Orient -or $SessionIndex -or $Pending)) {
    Write-Line "Read-only audit of $RootFull"
    Write-Line "Generated $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
}

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
# -PruneNoise leaves high-confidence generated state unwalked and lists it;
# -MaxSeconds stops the walk and reports the directories never visited.
function Test-LinkDirectory($item) {
    if (-not ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint)) { return $false }
    $lt = $item.LinkType
    return ($lt -eq 'Junction' -or $lt -eq 'SymbolicLink')
}

# ---------------------------------------------------------------------------
# v1.7 checks: sync conflict copies, pending files, rules matrix, continuity
# folders. Report only; same output as audit_folder.py.
# ---------------------------------------------------------------------------
$PendingNameRx = '(?i)^pending[._ -]|\.pending[.-]'
$ConflictParenRx = '^(.+?) \((\d{1,3})\)(\.[^.]+)?$'
$ConflictHostRx = '^(.+)-([A-Z0-9][A-Z0-9-]{3,14})(\.[^.]+)$'
# The owner's opt-in line (Project Rules 3.3.0 section 5): a line that begins
# "Sequential writers:". Prose that merely describes the rule does not count.
$DeclarationRx = '(?im)^[ \t]*(?:[-*][ \t]*)?\**Sequential writers\**[ \t]*:'
$RulesVersionRx = '(?im)^\s*\**Version\**\s*:\s*\**\s*(\d+\.\d+\.\d+)'
$PlaceholderRx = '<(?![A-Za-z][A-Za-z0-9+.-]*:)[A-Za-z][^<>\n]{0,80}>'
$StatusLineRx = '^\s*(?:[-*]\s*)?\**Status\**\s*:\s*\**\s*([A-Za-z]+)'
$Hex64Rx = '\b[0-9a-fA-F]{64}\b'
$ToLineRx = '(?im)^\s*(?:[-*]\s*)?\**To\**\s*:\s*(.+)$'
$KnownContinuity = @('project_quick_context.md', 'session_index.md', 'policy_installation.md',
    'readme_first.md', 'chat_index.md', 'project_activity_journal.md')
$ContinuityTextExts = @('.md', '.txt', '.json', '.csv', '.yml', '.yaml', '.log')
$TemplatePath = [IO.Path]::Combine($PSScriptRoot, '..', 'references', 'project-rules', 'AGENTS.proposed.md')
$AgentsWarnBytes = 16384
$script:InWork = $false

function Join-RootRel([string]$relPath) {
    $acc = $RootFull
    foreach ($seg in $relPath.Replace('\', '/').Split('/')) { if ($seg) { $acc = [IO.Path]::Combine($acc, $seg) } }
    return $acc
}
function Read-SmallText([string]$path) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { return $null }
    if (-not (Test-ContentReadAllowed $path)) { return $null }
    try {
        $sr = [IO.StreamReader]::new($path, [Text.UTF8Encoding]::new($false), $true)
        try {
            $buf = New-Object char[] 1048577
            $n = $sr.ReadBlock($buf, 0, $buf.Length)
            if ($n -gt 1048576) {
                Write-Line ("  read incomplete (over 1048576 characters): {0}; not parsed" -f [IO.Path]::GetFileName($path))
                return $null
            }
            return [string]::new($buf, 0, $n)
        } finally { $sr.Dispose() }
    } catch { return $null }
}
# Python's `limited`: work mode caps at 15 (10 with -Brief), the full audit
# only with -Brief; the overflow line differs in indentation.
function Write-Limited($items, [string]$indent) {
    $items = @($items)
    if ($script:InWork) {
        $take = [Math]::Min($items.Count, $(if ($Brief) { 10 } else { 15 }))
        $more = '      ... and {0} more'
    } else {
        $take = Get-Cap $items.Count
        $more = '  ... and {0} more'
    }
    for ($i = 0; $i -lt $take; $i++) { Write-Line ($indent + $items[$i]) }
    if ($items.Count -gt $take) { Write-Line ($more -f ($items.Count - $take)) }
}
function Test-PendingName([string]$name) {
    $low = $name.ToLower()
    if (-not ($low.EndsWith('.md') -or $low.EndsWith('.json'))) { return $false }
    return [regex]::IsMatch($name, $PendingNameRx)
}
function Get-OrdinalKey([string]$s) { return $s.ToLowerInvariant() + [char]0 + $s }
function Get-ConflictCopies([string[]]$rels) {
    $present = [Collections.Generic.HashSet[string]]::new()
    foreach ($r in $rels) { [void]$present.Add($r.ToLowerInvariant()) }
    $out = foreach ($r in $rels) {
        $cut = $r.LastIndexOf('/')
        $prefix = if ($cut -ge 0) { $r.Substring(0, $cut + 1) } else { '' }
        $name = $r.Substring($cut + 1)
        $m = [regex]::Match($name, $ConflictParenRx)
        if ($m.Success) {
            $original = $prefix + $m.Groups[1].Value + $m.Groups[3].Value
            $state = if ($present.Contains($original.ToLowerInvariant())) { 'original present' } else { 'ORIGINAL MISSING' }
            [pscustomobject]@{ Kind = '(n) copy'; State = $state; Rel = $r }
            continue
        }
        $m = [regex]::Match($name, $ConflictHostRx)
        if ($m.Success -and [regex]::IsMatch($m.Groups[2].Value, '[A-Z]')) {
            $original = $prefix + $m.Groups[1].Value + $m.Groups[3].Value
            if ($present.Contains($original.ToLowerInvariant())) { [pscustomobject]@{ Kind = '-HOST copy'; State = 'original present'; Rel = $r } }
        }
    }
    return @($out | Sort-Ordinal -Key { Get-OrdinalKey $_.Rel })
}
function Get-CaseCollisions([string[]]$rels) {
    $groups = @{}
    foreach ($r in $rels) {
        $k = $r.ToLowerInvariant()
        if (-not $groups.ContainsKey($k)) { $groups[$k] = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal) }
        [void]$groups[$k].Add($r)
    }
    $out = foreach ($k in $groups.Keys) {
        if ($groups[$k].Count -gt 1) {
            [string[]]$arr = @($groups[$k])
            [Array]::Sort($arr, [StringComparer]::Ordinal)
            [pscustomobject]@{ First = $arr[0]; Items = $arr }
        }
    }
    return @($out | Sort-Ordinal -Key { $_.First.ToLowerInvariant() })
}
function Write-ConflictBlock([string[]]$rels) {
    $copies = @(Get-ConflictCopies $rels)
    $collisions = @(Get-CaseCollisions $rels)
    $missing = @($copies | Where-Object { $_.State -eq 'ORIGINAL MISSING' }).Count
    Write-Line ("  sync conflict copies: {0} (original missing: {1})" -f $copies.Count, $missing)
    Write-Limited @($copies | ForEach-Object { "{0,-10} {1,-16} {2}" -f $_.Kind, $_.State, $_.Rel }) '    '
    Write-Line ("  case-only name collisions: {0}" -f $collisions.Count)
    Write-Limited @($collisions | ForEach-Object { $_.Items -join ' | ' }) '    '
    if ($copies.Count -or $collisions.Count) { Write-Line '    Reconcile before shared-record edits; never merge, rename or delete without approval.' }
    return @($copies.Count, $collisions.Count)
}
$StatusWords = @('PENDING', 'APPLIED', 'SUPERSEDED', 'CONFLICTED', 'UNVERIFIABLE')
$TargetLineRx = '(?i)^\s*(?:[-*]\s*)?\**Target\**\s*:\s*(.*)$'
$LabelLineRx = '^\s*(?:[-*]\s*)?\**([A-Za-z][A-Za-z /-]{0,40}?)\**\s*:[ \t]*(.*)$'
$HeadingRx = '^\s*#'
$OldWordsRx = '(?i)\b(old|anchor|after|before|replace|remove)\b'
$NewWordsRx = '(?i)\b(new|insert|add|row|append|edit|text|line)\b'
function Get-StatusOf([string]$line) {
    $m = [regex]::Match($line, $StatusLineRx)
    if ($m.Success) { return $m.Groups[1].Value.ToUpper() }
    return $null
}
function Get-FenceAt([string[]]$lines, [int]$i) {
    while ($i -lt $lines.Count -and -not $lines[$i].Trim()) { $i++ }
    if ($i -ge $lines.Count -or -not $lines[$i].TrimStart().StartsWith('```')) { return @($null, $i) }
    $body = [Collections.Generic.List[string]]::new()
    $j = $i + 1
    while ($j -lt $lines.Count -and -not $lines[$j].TrimStart().StartsWith('```')) { $body.Add($lines[$j].TrimEnd("`r")); $j++ }
    return @(($body -join "`n"), ($j + 1))
}
function Get-BlockEdits([string[]]$lines) {
    $new = [Collections.Generic.List[string]]::new(); $old = [Collections.Generic.List[string]]::new()
    $i = 0
    while ($i -lt $lines.Count) {
        $m = [regex]::Match($lines[$i], $LabelLineRx)
        if (-not $m.Success) { $i++; continue }
        $label = $m.Groups[1].Value.Trim().ToLower(); $value = $m.Groups[2].Value.Trim()
        $kind = if ([regex]::IsMatch($label, $OldWordsRx)) { 'old' } elseif ([regex]::IsMatch($label, $NewWordsRx)) { 'new' } else { $null }
        if (-not $kind) { $i++; continue }
        if ($kind -eq 'old') { $bucket = $old } else { $bucket = $new }
        if ($value -and $label -ne 'edit') {
            if ($value.Length -gt 2 -and $value.StartsWith('`') -and $value.EndsWith('`')) { $value = $value.Substring(1, $value.Length - 2) }
            $bucket.Add($value.Trim())
        }
        $fence = Get-FenceAt $lines ($i + 1)
        if ($null -ne $fence[0]) { $bucket.Add($fence[0].Trim()); $i = $fence[1]; continue }
        if (-not $value) {
            $j = $i + 1
            while ($j -lt $lines.Count -and -not $lines[$j].Trim()) { $j++ }
            if ($j -lt $lines.Count -and -not [regex]::IsMatch($lines[$j], $LabelLineRx) -and -not [regex]::IsMatch($lines[$j], $HeadingRx)) { $bucket.Add($lines[$j].Trim()) }
        }
        $i++
    }
    $keep = {
        param($vals)
        $seen = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
        , @($vals | Where-Object { $_.Length -ge 12 -and $seen.Add($_) })
    }
    return @((& $keep $new), (& $keep $old))
}
function Get-PendingInfo([string]$text, [string]$name) {
    $out = @{ Status = $null; StatusFirst = $false; Blocks = [Collections.Generic.List[object]]::new() }
    if ($name.ToLower().EndsWith('.json')) {
        try { $obj = $text | ConvertFrom-Json -ErrorAction Stop } catch { $obj = $null }
        if ($obj -is [pscustomobject]) {
            $st = $obj.status
            if ($st -and ([string]$st).Trim()) { $out.Status = ([string]$st).Trim().Split([string[]]@(' ', "`t", "`r", "`n"), [StringSplitOptions]::RemoveEmptyEntries)[0].ToUpper() }
            $out.StatusFirst = $null -ne $out.Status
            $tgt = ''; foreach ($k in @('target', 'path')) { if (-not $tgt -and $obj.$k) { $tgt = [string]$obj.$k } }
            $bas = ''; foreach ($k in @('base', 'base_sha256')) { if (-not $bas -and $obj.$k) { $bas = [string]$obj.$k } }
            $new = [Collections.Generic.List[string]]::new(); $old = [Collections.Generic.List[string]]::new()
            foreach ($e in @($obj.edits)) {
                if ($e -isnot [pscustomobject]) { continue }
                foreach ($pair in @(@('new', $new), @('new_line', $new), @('new_text', $new), @('old', $old), @('insert_after', $old), @('anchor', $old))) {
                    $v = $e.($pair[0])
                    if ($v -is [string] -and $v.Trim().Length -ge 12) { $pair[1].Add($v.Trim()) }
                }
            }
            $out.Blocks.Add([pscustomobject]@{ Status = $out.Status; Target = $tgt; Base = $bas; New = $new.ToArray(); Old = $old.ToArray() })
        }
        return $out
    }
    [string[]]$lines = $text -split "`n"
    $first = ''; foreach ($ln in $lines) { if ($ln.Trim()) { $first = $ln; break } }
    $out.StatusFirst = $null -ne (Get-StatusOf $first)
    foreach ($ln in $lines) { $s = Get-StatusOf $ln; if ($s) { $out.Status = $s; break } }
    if (-not $out.Status -and $first.Trim()) {
        $word = $first.Trim().Split(' ')[0].Trim([char[]]@('*', ':', '(')).ToUpper()
        if ($StatusWords -contains $word) { $out.Status = $word }
    }
    $targets = @(for ($i = 0; $i -lt $lines.Count; $i++) { if ([regex]::IsMatch($lines[$i], $TargetLineRx)) { $i } })
    $starts = [Collections.Generic.List[int]]::new()
    for ($k = 0; $k -lt $targets.Count; $k++) {
        if ($k -eq 0) { $starts.Add(0); continue }
        $s = $targets[$k]
        while (($s - 1) -gt $targets[$k - 1] -and ((-not $lines[$s - 1].Trim()) -or [regex]::IsMatch($lines[$s - 1], $HeadingRx) -or (Get-StatusOf $lines[$s - 1]))) { $s-- }
        $starts.Add($s)
    }
    $spans = [Collections.Generic.List[object]]::new()
    if ($targets.Count) {
        for ($k = 0; $k -lt $starts.Count; $k++) { $spans.Add([int[]]@($starts[$k], $(if ($k + 1 -lt $starts.Count) { $starts[$k + 1] } else { $lines.Count }))) }
    } else { $spans.Add([int[]]@(0, $lines.Count)) }
    for ($k = 0; $k -lt $spans.Count; $k++) {
        $a = $spans[$k][0]; $b = $spans[$k][1]
        [string[]]$chunk = if ($b -gt $a) { $lines[$a..($b - 1)] } else { @() }
        $target = if ($targets.Count) { [regex]::Match($lines[$targets[$k]], $TargetLineRx).Groups[1].Value.Trim() } else { '' }
        $st = $out.Status
        foreach ($ln in $chunk) { $s = Get-StatusOf $ln; if ($s) { $st = $s; break } }
        $base = ''
        foreach ($ln in $chunk) {
            if ($ln -match '(?i)\bbase\b') { $h = [regex]::Match($ln, $Hex64Rx); if ($h.Success) { $base = $h.Value; break } }
        }
        $edits = Get-BlockEdits @($chunk | Where-Object { -not [regex]::IsMatch($_, $TargetLineRx) })
        $out.Blocks.Add([pscustomobject]@{ Status = $st; Target = $target; Base = $base; New = @($edits[0]); Old = @($edits[1]) })
    }
    return $out
}
function Get-SubstringCount([string]$hay, [string]$needle) {
    $n = 0; $i = 0
    while (($i = $hay.IndexOf($needle, $i, [StringComparison]::Ordinal)) -ge 0) { $n++; $i += $needle.Length }
    return $n
}
function Get-BlockState($block, [string]$projectRoot, [string]$sourceId) {
    $recorded = @{ 'APPLIED' = 'Applied'; 'SUPERSEDED' = 'Superseded'; 'CONFLICTED' = 'Conflicted'; 'UNVERIFIABLE' = 'Unverifiable' }
    $raw = $block.Target.Trim().Trim([char[]]@('`', "'", '"', '\', ' '))
    $target = if ($raw) { Get-CleanReference $raw } else { '' }
    if ($block.Status -and $recorded.ContainsKey($block.Status)) { return @(($recorded[$block.Status] + ' (recorded)'), $target) }
    if (-not $target) { return @('Unverifiable (no Target)', '') }
    $full = $projectRoot
    foreach ($seg in $target.Replace('\', '/').TrimStart('/').Split('/')) { if ($seg) { $full = [IO.Path]::Combine($full, $seg) } }
    if (-not (Test-Path -LiteralPath $full -PathType Leaf)) { return @('Unverifiable (target not found)', $target) }
    $current = Read-SmallText $full
    if ($null -eq $current) { return @('Unverifiable (target unreadable)', $target) }
    try { $digest = (Get-FileHash -LiteralPath $full -Algorithm SHA256 -ErrorAction Stop).Hash.ToLower() }
    catch { return @('Unverifiable (target unreadable)', $target) }
    $base = [regex]::Match([string]$block.Base, $Hex64Rx)
    $present = @(@($block.New) | ForEach-Object { $current.Contains($_) })
    if ($present.Count -and -not ($present -contains $false)) { return @('Applied (not marked)', $target) }
    if ($present -contains $true) { return @('Conflicted (partly present)', $target) }
    if ($base.Success -and $base.Value.ToLower() -eq $digest) { return @('Pending (base matches)', $target) }
    if (@($block.Old).Count -and -not (@(@($block.Old) | ForEach-Object { (Get-SubstringCount $current $_) -eq 1 }) -contains $false)) {
        return @('Pending (anchor matches)', $target)
    }
    if ($base.Success -or ($sourceId -and $current.ToLower().Contains($sourceId))) {
        $why = if ($sourceId -and $current.ToLower().Contains($sourceId)) { '; source session ID in target' } else { '' }
        return @(('Conflicted (text absent' + $(if ($base.Success) { ', base differs' } else { '' }) + $why + ')'), $target)
    }
    if (@($block.New).Count) { return @('Unverifiable (text absent; no base or anchor)', $target) }
    return @('Unverifiable (no edit text)', $target)
}
function Get-PendingState([string]$path, [string]$projectRoot) {
    $text = Read-SmallText $path
    if ($null -eq $text) { return [pscustomobject]@{ Blocks = @(, @('Unverifiable (unreadable)', '')); Flag = '' } }
    $info = Get-PendingInfo $text ([IO.Path]::GetFileName($path))
    $flag = ''
    if (-not $info.StatusFirst) {
        $anyBlock = @($info.Blocks | Where-Object { $_.Status }).Count
        $flag = if (-not $anyBlock -and $null -eq $info.Status) { 'no Status: line' } else { 'Status: not first line' }
    }
    $m = [regex]::Match((Get-RelUnder $path $projectRoot), $UuidPattern)
    $sid = if ($m.Success) { $m.Value.ToLower() } else { '' }
    $blocks = @(foreach ($b in $info.Blocks) { , (Get-BlockState $b $projectRoot $sid) })
    return [pscustomobject]@{ Blocks = $blocks; Flag = $flag }
}
function Get-RelUnder([string]$full, [string]$base) {
    $b = $base.TrimEnd('\', '/')
    if ($full.StartsWith($b, [StringComparison]::OrdinalIgnoreCase)) { return $full.Substring($b.Length).TrimStart('\', '/').Replace('\', '/') }
    return $full.Replace('\', '/')
}
function Find-PendingFiles([string]$project, [string]$scratchRel = 'AI_CONTEXT/scratch') {
    $dirs = [Collections.Generic.List[string]]::new()
    $dirs.Add($project); $dirs.Add([IO.Path]::Combine($project, 'AI_CONTEXT'))
    $scratch = $project
    foreach ($seg in $scratchRel.Replace('\', '/').Split('/')) { if ($seg) { $scratch = [IO.Path]::Combine($scratch, $seg) } }
    if (Test-Path -LiteralPath $scratch -PathType Container) {
        $si = Get-Item -LiteralPath $scratch -Force
        if (-not $si.LinkType) {
            $dirs.Add($scratch)
            @(Get-ChildItem -LiteralPath $scratch -Directory -Force -ErrorAction SilentlyContinue | Where-Object { -not $_.LinkType } |
                Sort-Ordinal -Key { $_.FullName }) | ForEach-Object { $dirs.Add($_.FullName) }
        }
    }
    $found = [Collections.Generic.HashSet[string]]::new()
    foreach ($d in $dirs) {
        if (-not (Test-Path -LiteralPath $d -PathType Container)) { continue }
        foreach ($f in @(Get-ChildItem -LiteralPath $d -File -Force -ErrorAction SilentlyContinue)) {
            if (Test-PendingName $f.Name) { [void]$found.Add($f.FullName) }
        }
    }
    return @($found | Sort-Ordinal -Key { Get-OrdinalKey (Get-RelUnder $_ $project) })
}
function Get-DeclarationSources([string]$project, [string]$quickRel = 'AI_CONTEXT/PROJECT_QUICK_CONTEXT.md') {
    $out = foreach ($relName in @('AGENTS.md', 'CLAUDE.md', $quickRel)) {
        $p = $project
        foreach ($seg in $relName.Split('/')) { if ($seg) { $p = [IO.Path]::Combine($p, $seg) } }
        $t = Read-SmallText $p
        if ($t -and [regex]::IsMatch($t, $DeclarationRx)) { $relName }
    }
    return @($out)
}
function Get-RulesCore([string]$text) {
    $lines = $text -split "`n"
    $start = -1
    # Rules 4.0.0 adds section 0 to the shared core; 3.x cores start at section 1.
    for ($i = 0; $i -lt $lines.Count; $i++) { if ($lines[$i] -match '^## 0\.') { $start = $i; break } }
    if ($start -lt 0) { for ($i = 0; $i -lt $lines.Count; $i++) { if ($lines[$i] -match '^## 1\.') { $start = $i; break } } }
    if ($start -lt 0) { return $null }
    $end = $lines.Count
    for ($i = $start + 1; $i -lt $lines.Count; $i++) { if ($lines[$i] -match '^## 13\.') { $end = $i; break } }
    $core = [Collections.Generic.List[string]]::new()
    for ($i = $start; $i -lt $end; $i++) { $t = $lines[$i].Trim(); if ($t) { $core.Add($t) } }
    return , $core.ToArray()
}
function Get-Section13Complete([string]$text) {
    $lines = $text -split "\r?\n"
    $start = -1
    for ($i = 0; $i -lt $lines.Count; $i++) { if ($lines[$i] -match '^## 13\.') { $start = $i; break } }
    if ($start -lt 0) { return 'n/a' }
    $end = $lines.Count
    for ($i = $start + 1; $i -lt $lines.Count; $i++) { if ($lines[$i] -match '^## ') { $end = $i; break } }
    $body = if ($end -gt $start + 1) { ($lines[($start + 1)..($end - 1)]) -join "`n" } else { '' }
    $holes = [regex]::Matches($body, $PlaceholderRx).Count
    if (-not [regex]::IsMatch($body, '(?im)^\s*Adopted\s*:')) { return 'no (no Adopted: line)' }
    if ($holes -eq 0) { return 'yes' }
    return "no ($holes placeholders)"
}
function Get-CoreDifference([string[]]$a, [string[]]$b) {
    $c = @{}
    foreach ($x in $a) { $c[$x] = [int]$c[$x] + 1 }
    foreach ($x in $b) { $c[$x] = [int]$c[$x] - 1 }
    $n = 0
    foreach ($k in $c.Keys) { $n += [Math]::Abs($c[$k]) }
    return $n
}
function Get-TemplateCore {
    # The skill's own bundled template: outside the audited root by design, so
    # it is read directly rather than through the root-confined reader.
    try { $text = [IO.File]::ReadAllText($TemplatePath, [Text.UTF8Encoding]::new($false)) } catch { return @($null, $null) }
    if (-not $text) { return @($null, $null) }
    $m = [regex]::Match($text, $RulesVersionRx)
    $ver = if ($m.Success) { $m.Groups[1].Value } else { '?' }
    return @((Get-RulesCore $text), $ver)
}
function Get-RulesInfo([string]$project, $tcore) {
    $agents = [IO.Path]::Combine($project, 'AGENTS.md')
    $text = if (Test-Path -LiteralPath $agents -PathType Leaf) { Read-SmallText $agents } else { $null }
    $seq = if (@(Get-DeclarationSources $project).Count) { 'yes' } else { 'no' }
    if ($null -eq $text) { return @('n/a', 'n/a', 'n/a', $seq, 'n/a') }
    $source = $text; $byRef = ''
    $m = [regex]::Match($text, $RulesVersionRx)
    if (-not $m.Success) {
        $head = (($text -split "`n") | Select-Object -First 20) -join "`n"
        foreach ($target in @(Get-MarkdownTargets $head)) {
            $clean = Get-CleanReference $target
            if ($clean -match '(?i)rules[^/]*\.md$') {
                $full = $project
                foreach ($seg in $clean.Replace('\', '/').TrimStart('/').Split('/')) { if ($seg) { $full = [IO.Path]::Combine($full, $seg) } }
                $ref = if (Test-Path -LiteralPath $full -PathType Leaf) { Read-SmallText $full } else { $null }
                if ($ref -and [regex]::IsMatch($ref, $RulesVersionRx)) { $source = $ref; $byRef = ' (by reference)'; $m = [regex]::Match($ref, $RulesVersionRx); break }
            }
        }
    }
    $version = if ($m.Success) { $m.Groups[1].Value + $byRef } else { 'unversioned' }
    $routing = if ($source.Contains('Day-to-day saving and indexing') -or $source.Contains('multi-agent-folder-cleanup')) { 'yes' } else { 'no' }
    $core = Get-RulesCore $source
    if ($null -eq $tcore) { $match = 'unknown (no template bundled)' }
    elseif ($null -eq $core) { $match = 'unknown (no sections 1-12)' }
    else {
        $n = Get-CoreDifference $core $tcore
        $match = if ($n -eq 0) { 'match' } else { "differs ($n lines)" }
    }
    return @($version, $routing, $match, $seq, (Get-Section13Complete $source))
}
$CloseEntryRx = '(?im)^\s*(?:[-*#]+\s*)?\**\s*(?:Session\s+(?:closed|close)\b|Closed\s*:|Close\s*:|Status\s*:\s*\**\s*closed\b)'
$CloseTitleRx = '(?i)(?:\bsession\s+clos(?:e|ed|ing)\b|\|\s*(?:session\s+)?clos(?:e|ed)\s*$)'
$FinishedStatuses = @('completed', 'complete', 'closed', 'done', 'finished', 'abandoned', 'superseded', 'stopped', 'ended')
function Get-ScopeInfo([string]$project) {
    # Section 13 values the helpers use: declared tool slugs and the active-writer window.
    $agents = [IO.Path]::Combine($project, 'AGENTS.md')
    $text = if (Test-Path -LiteralPath $agents -PathType Leaf) { Read-SmallText $agents } else { $null }
    $slugs = [Collections.Generic.List[string]]::new(); $window = $null
    if ($text) {
        $m = [regex]::Match($text, '(?im)^\s*Tool slugs in use\s*:\s*(.+)$')
        if ($m.Success) {
            foreach ($item in ($m.Groups[1].Value -split '[;,]')) {
                $key = $item.Split('=')[0].Split([char]0x2192)[0]
                $ix = $key.IndexOf('->'); if ($ix -ge 0) { $key = $key.Substring(0, $ix) }
                $key = $key.Trim().Trim('`').ToLowerInvariant()
                if ($key -cmatch '^[a-z0-9][a-z0-9-]*$') { $slugs.Add($key) }
            }
        }
        $w = [regex]::Match($text, '(?im)^\s*Active-writer window\s*:\s*(\d+)\s*min')
        if ($w.Success) { $window = [int]$w.Groups[1].Value }
    }
    return [pscustomobject]@{ Slugs = @($slugs); Window = $window }
}
$GenericRuntimeWords = @('desktop', 'app', 'cli', 'web', 'ide', 'device', 'cloud', 'session', 'powershell', 'python', 'windows', 'mac', 'linux', 'agent', 'local', 'user', 'chat', 'the')
function Get-RuntimeName([string]$header) {
    # The runtime part of a Tool/runtime header (same rules as runtime_name in audit_folder.py).
    $text = [regex]::Replace(([string]$header).ToLowerInvariant(), '\([^)]*\)', ' ')
    $text = [regex]::Split($text, '[,;/`|\u2013\u2014]| on | via | - ')[0]
    $words = @([regex]::Matches($text, '[a-z0-9][a-z0-9.-]*') | ForEach-Object { $_.Value } | Where-Object { $GenericRuntimeWords -notcontains $_ })
    return ($words -join ' ')
}
function Get-SlugVariants($sessions) {
    # Slugs that appear with more than one Tool/runtime header (R228).
    $seen = @{}
    foreach ($s in @($sessions)) {
        $runtime = Get-RuntimeName $s.Header
        if ($s.Slug -and $runtime) {
            if (-not $seen.ContainsKey($s.Slug)) { $seen[$s.Slug] = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal) }
            [void]$seen[$s.Slug].Add($runtime)
        }
    }
    $out = [ordered]@{}
    foreach ($k in @($seen.Keys | Sort-Ordinal -Key { $_ })) { if ($seen[$k].Count -gt 1) { $out[$k] = @($seen[$k] | Sort-Ordinal -Key { $_ }) } }
    return $out
}
function Get-IndexStatuses([string]$indexText) {
    # True for an 'in progress' row, False for a finished status cell; rows without a status are unknown.
    $out = @{}
    foreach ($line in (([string]$indexText) -split "\r?\n")) {
        if (-not $line.TrimStart().StartsWith('|')) { continue }
        $cells = @($line.Trim().Trim('|').Split('|') | ForEach-Object { $_.Trim().Trim('*').Trim().ToLowerInvariant() })
        if ($cells -contains 'in progress') { $state = $true }
        elseif (@($cells | Where-Object { $FinishedStatuses -contains $_ }).Count) { $state = $false }
        else { continue }
        foreach ($u in [regex]::Matches($line, $UuidPattern)) { $out[$u.Value.ToLowerInvariant()] = $state }
    }
    return $out
}
function Get-NewestFileTime([string]$folder, [int]$limit = 2000) {
    # Newest file modified time under a folder (file times, not folder times; bounded).
    $newest = $null; $n = 0
    foreach ($f in @(Get-ChildItem -LiteralPath $folder -File -Recurse -Force -ErrorAction SilentlyContinue)) {
        $n++; if ($n -gt $limit) { break }
        $t = [DateTimeOffset]$f.LastWriteTime
        if ($null -eq $newest -or $t -gt $newest) { $newest = $t }
    }
    return $newest
}
function Get-ProvenancePending([string]$project) {
    # Incoming/*/_PROVENANCE.md lines marked PENDING and not APPLIED (R232).
    $out = [Collections.Generic.List[object]]::new()
    $inc = [IO.Path]::Combine($project, 'Incoming')
    if (-not (Test-Path -LiteralPath $inc -PathType Container)) { return @() }
    foreach ($child in @(Get-ChildItem -LiteralPath $inc -Directory -Force -ErrorAction SilentlyContinue | Where-Object { -not $_.LinkType } | Sort-Ordinal -Key { Get-OrdinalKey $_.Name })) {
        foreach ($pf in @(Get-ChildItem -LiteralPath $child.FullName -File -Force -ErrorAction SilentlyContinue | Where-Object { $_.Name.ToLower() -eq '_provenance.md' } | Sort-Ordinal -Key { $_.Name })) {
            $t = Read-SmallText $pf.FullName; if ($null -eq $t) { $t = '' }
            $rows = @(($t -split "\r?\n") | Where-Object { $_ -notmatch '^\s*#' -and $_ -cmatch '\bPENDING\b' -and $_ -cnotmatch '\bAPPLIED\b' } | ForEach-Object { $_.Trim() })
            if ($rows.Count) { $out.Add([pscustomobject]@{ Rel = ("Incoming/{0}/{1}" -f $child.Name, $pf.Name); Rows = $rows }) }
        }
    }
    return @($out)
}
function Get-JournalRetired($file, [int]$rulesMajor, [string]$contextText) {
    $r = Get-RelSlash $file.FullName
    $segs = $r.ToLower().Split('/')
    for ($i = 0; $i -lt $segs.Count - 1; $i++) {
        if ($segs[$i].Contains('history') -or $segs[$i].Contains('_superseded') -or $segs[$i].Contains('archive')) { return 'under a History/archive path' }
    }
    foreach ($line in ($contextText -split "`n")) {
        if ($line.Contains($file.Name) -and $line -match '(?i)retired|legacy|history') { return 'declared retired in AGENTS.md or quick context' }
    }
    $sessions = [IO.Path]::Combine($file.DirectoryName, 'SESSIONS')
    if ($rulesMajor -ge 3 -and (Test-Path -LiteralPath $sessions -PathType Container)) {
        if (@(Get-ChildItem -LiteralPath $sessions -Force -ErrorAction SilentlyContinue | Where-Object { $_.Name.ToLower().EndsWith('.md') }).Count) { return 'superseded by SESSIONS/ logs (rules 3.x)' }
    }
    return $null
}
function Get-CommonFolder([string[]]$rels) {
    $parts = @($rels | ForEach-Object { $s = $_.Split('/'); , @($s[0..($s.Count - 1)] | Select-Object -First ($s.Count - 1)) })
    $out = [Collections.Generic.List[string]]::new()
    $min = ($parts | ForEach-Object { @($_).Count } | Measure-Object -Minimum).Minimum
    for ($i = 0; $i -lt $min; $i++) {
        $seg = @($parts[0])[$i]
        if (@($parts | Where-Object { @($_)[$i] -cne $seg }).Count) { break }
        $out.Add($seg)
    }
    if ($out.Count) { return ($out -join '/') }
    return '.'
}
function Get-AiContextMisuse($items) {
    $out = foreach ($it in $items) {
        $segs = $it.Rel.Split('/')
        if ($segs.Count -lt 2 -or $segs[0].ToLower() -ne 'ai_context') { continue }
        if ($segs.Count -gt 2 -and @('scratch', 'sessions') -contains $segs[1].ToLower()) { continue }
        $ext = [IO.Path]::GetExtension($segs[-1]).ToLower()
        if ($ContinuityTextExts -notcontains $ext) { [pscustomobject]@{ Rel = $it.Rel; Size = $it.Size; Why = 'non-text file' } }
        elseif ($segs.Count -eq 2 -and $KnownContinuity -notcontains $segs[1].ToLower()) { [pscustomobject]@{ Rel = $it.Rel; Size = $it.Size; Why = 'loose file' } }
    }
    return @($out | Sort-Ordinal -Key { Get-OrdinalKey $_.Rel })
}
function Get-RepoFoldersWithoutGit([string[]]$rels) {
    $dirs = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    foreach ($r in $rels) {
        $segs = $r.Split('/')
        $noise = $false
        for ($i = 0; $i -lt $segs.Count - 1; $i++) { if (Test-NoiseSegment $segs[$i]) { $noise = $true } }
        if ($noise) { continue }
        $leaf = $segs[-1].ToLower()
        if ($leaf -eq '.gitignore' -or $leaf -eq '.gitattributes') { [void]$dirs.Add((@($segs | Select-Object -First ($segs.Count - 1)) -join '/')) }
        for ($i = 0; $i -lt $segs.Count - 1; $i++) {
            if ($segs[$i].ToLower() -eq '.github') { [void]$dirs.Add((@($segs | Select-Object -First $i) -join '/')); break }
        }
    }
    $out = foreach ($d in $dirs) {
        $gitPath = if ($d) { Join-RootRel ($d + '/.git') } else { [IO.Path]::Combine($RootFull, '.git') }
        if (-not (Test-Path -LiteralPath $gitPath)) { if ($d) { $d } else { '.' } }
    }
    return @($out | Sort-Ordinal -Key { Get-OrdinalKey $_ })
}

# ---------------------------------------------------------------------------
# Work-mode helpers (v1.5): -Orient and -SessionIndex. Same output as
# audit_folder.py --orient / --session-index. Read-only; modified-time evidence
# is labeled local and replica-unsafe.
# ---------------------------------------------------------------------------
if ($Orient -or $SessionIndex -or $Pending) {
    $script:InWork = $true
    $SessionNameRx = '^(\d{4}-\d{2}-\d{2})_(\d{6}|unknown-time)_([^_]+)_(.+)_(' + $UuidPattern + ')\.md$'
    $CanonicalToolSlugs = @('claude', 'claude-code', 'codex', 'antigravity', 'gemini', 'copilot', 'manus', 'opal', 'grok', 'muse')
    $IsoRx = '\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:?\d{2})?'
    $TurnRx = '(?m)^(?:#{2,4}\s+|\*\*)?(T\d{3,})\b(?!-)(.*)$'
    $WorkCap = if ($Brief) { 10 } else { 15 }
    $Now = [DateTimeOffset]::Now
    function ConvertFrom-Iso([string]$value) {
        if (-not $value) { return $null }
        $m = [regex]::Match($value, $IsoRx)
        if (-not $m.Success) { return $null }
        $t = $m.Value.Replace(' ', 'T')
        $t = [regex]::Replace($t, '([+-]\d{2})(\d{2})$', '$1:$2')
        try { return [DateTimeOffset]::Parse($t, [Globalization.CultureInfo]::InvariantCulture, [Globalization.DateTimeStyles]::AssumeLocal) } catch { return $null }
    }
    function Format-WorkTime($dto) { if ($null -eq $dto) { 'unknown' } else { $dto.ToLocalTime().ToString("yyyy-MM-dd'T'HH:mmzzz") } }
    function ConvertFrom-RecordedTime([string]$value) {
        $m = [regex]::Match($value, $IsoRx)
        if (-not $m.Success -or $m.Value -notmatch '(Z|[+-]\d{2}:?\d{2})$') { return $null }
        return ConvertFrom-Iso $m.Value
    }
    function Get-WorkPathState([string]$path) {
        try { $null = Get-Item -LiteralPath $path -Force -ErrorAction Stop; return 'present' }
        catch [System.Management.Automation.ItemNotFoundException] { return 'NOT FOUND' }
        catch { return 'UNAVAILABLE' }
    }
    function Format-Activity($s) {
        if ($null -ne $s.LastTime) { return Format-WorkTime $s.LastTime }
        return ((Format-WorkTime $s.MTime) + ' (file mtime; not recorded activity)')
    }
    function Get-DuplicateIds($items) {
        $counts = @{}
        foreach ($s in $items) { if ($counts.ContainsKey($s.Id)) { $counts[$s.Id]++ } else { $counts[$s.Id] = 1 } }
        return @($counts.Keys | Where-Object { $counts[$_] -gt 1 } | Sort-Object)
    }
    function Write-Capped($items, [string]$indent = '    ') {
        $items = @($items)
        $take = [Math]::Min($items.Count, $WorkCap)
        for ($i = 0; $i -lt $take; $i++) { Write-Line ($indent + $items[$i]) }
        if ($items.Count -gt $take) { Write-Line ("      ... and {0} more" -f ($items.Count - $take)) }
    }
    function Get-Sessions {
        $sdir = Join-RootRel $SessionsDir
        $res = [pscustomobject]@{ Dir = $sdir; Sessions = $null; Nonstandard = @(); Blocked = @(); State = (Get-WorkPathState $sdir) }
        if ($res.State -ne 'present') { return $res }
        if (-not (Test-ContentReadAllowed $sdir)) { $res.State = 'UNAVAILABLE (read blocked)'; return $res }
        $list = [Collections.Generic.List[object]]::new()
        $non = [Collections.Generic.List[string]]::new(); $blk = [Collections.Generic.List[string]]::new()
        try { $names = @(Get-ChildItem -LiteralPath $sdir -File -Force -ErrorAction Stop | Where-Object { $_.Name.ToLower().EndsWith('.md') } | Sort-Ordinal -Key { $_.Name }) }
        catch { $res.State = 'UNAVAILABLE (listing failed)'; return $res }
        $declaredSlugs = @((Get-ScopeInfo $RootFull).Slugs)
        foreach ($f in $names) {
            $text = Read-SmallText $f.FullName
            if ($null -eq $text) { $blk.Add($f.Name); continue }
            $head = if ($text.Length -gt 4096) { $text.Substring(0, 4096) } else { $text }
            $fields = @{}
            foreach ($fm in [regex]::Matches($head, '(?im)^\s*(?:[-*]\s*)?(Session ID|Started|Start(?:\s+time)?|Tool/runtime)\s*:\s*(.+?)\s*$')) { $fields[$fm.Groups[1].Value.ToLower()] = $fm.Groups[2].Value }
            $nm = [regex]::Match($f.Name, $SessionNameRx)
            $sid = if ($fields['session id']) { $fields['session id'] } elseif ($nm.Success) { $nm.Groups[5].Value } else { '' }
            $uid = [regex]::Match($(if ($sid) { $sid } else { $f.Name }), $UuidPattern)
            if (-not $uid.Success) { $non.Add($f.Name + ' (no session UUID; not treated as a session log)'); continue }
            $header = if ($fields['tool/runtime']) { ([regex]::Replace($fields['tool/runtime'], '\s+', ' ')).Trim() } else { '' }
            $tool = if ($header) { $header } elseif ($nm.Success) { $nm.Groups[3].Value } else { 'unknown' }
            $tool = $tool.Split('(')[0].Trim(); if (-not $tool) { $tool = 'unknown' }
            $topic = if ($nm.Success) { $nm.Groups[4].Value.Replace('-', ' ') } else { [IO.Path]::GetFileNameWithoutExtension($f.Name) }
            $startValue = @('started', 'start', 'start time') | ForEach-Object { if ($fields[$_]) { $fields[$_] } } | Select-Object -First 1
            $started = ConvertFrom-RecordedTime $startValue
            $startSource = 'recorded'; $filenameStart = $null
            if ($null -eq $started -and $nm.Success -and $nm.Groups[2].Value -ne 'unknown-time') {
                [datetime]$fallback = [datetime]::MinValue
                if ([datetime]::TryParseExact($nm.Groups[1].Value + $nm.Groups[2].Value, 'yyyy-MM-ddHHmmss', [Globalization.CultureInfo]::InvariantCulture, [Globalization.DateTimeStyles]::None, [ref]$fallback)) {
                    $filenameStart = $fallback.ToString("yyyy-MM-dd'T'HH:mm")
                    $started = [DateTimeOffset]::new($fallback, [TimeSpan]::Zero)
                    $startSource = 'filename; offset unknown'
                }
            }
            $turns = [regex]::Matches($text, $TurnRx)
            $ids = @{}; foreach ($t in $turns) { $ids[$t.Groups[1].Value] = 1 }
            $lastTitle = ''; $lastTime = $null
            if ($turns.Count) {
                $tail = $turns[$turns.Count - 1].Groups[2].Value
                $lastTime = ConvertFrom-RecordedTime $tail
            }
            $outcomes = [regex]::Matches($text, '(?im)^\s*(?:[-*]\s*)?(?:Work/result|Latest outcome|Outcome)\s*:\s*(.+?)\s*$')
            if ($outcomes.Count) { $lastTitle = $outcomes[$outcomes.Count - 1].Groups[1].Value.Trim() }
            if (-not $nm.Success) { $non.Add($f.Name + ' (nonstandard filename)') }
            elseif (($CanonicalToolSlugs -cnotcontains $nm.Groups[3].Value) -and ($declaredSlugs -cnotcontains $nm.Groups[3].Value)) { $non.Add($f.Name + ' (nonstandard tool slug)') }
            # Closed only when the LAST turn closes the session or a close entry follows the last
            # turn heading; an earlier close followed by more turns means the session resumed.
            if ($turns.Count) {
                $lastTurn = $turns[$turns.Count - 1]
                $closed = [regex]::IsMatch($lastTurn.Groups[2].Value, $CloseTitleRx) -or [regex]::new($CloseEntryRx).IsMatch($text, $lastTurn.Index)
            } else { $closed = [regex]::IsMatch($text, $CloseEntryRx) }
            $list.Add([pscustomobject]@{ Name = $f.Name; Id = $uid.Value.ToLower(); Tool = $tool; Topic = $topic; Started = $started
                Slug = $(if ($nm.Success) { $nm.Groups[3].Value.ToLowerInvariant() } else { '' }); Header = $header; Closed = $closed
                Turns = $ids.Count; LastTitle = $lastTitle; LastTime = $lastTime; MTime = [DateTimeOffset]$f.LastWriteTime; StartSource = $startSource; FilenameStart = $filenameStart })
        }
        $res.Sessions = @($list | Sort-Ordinal -Key { Get-SessionLoadKey $_ })
        $res.Nonstandard = @($non); $res.Blocked = @($blk)
        return $res
    }
    function Get-Activity($s) { if ($s.LastTime) { $s.LastTime } else { $s.MTime } }
    function Write-SlugVariants($sessions) {
        $v = Get-SlugVariants $sessions
        Write-Line ("  tool slugs used with more than one Tool/runtime header: {0} (leads: one slug per runtime; a different runtime never shares one; consider <runtime>-<agent>)" -f $v.Count)
        Write-Capped @($v.Keys | ForEach-Object {
            $k = $_
            "{0}: {1}" -f $k, ((@($v[$k] | Select-Object -First 4 | ForEach-Object { if ($_.Length -gt 60) { $_.Substring(0, 60) } else { $_ } })) -join ' | ') })
        return $v.Count
    }
    function Test-Mine($id) { return ($SessionId -and $id.ToLower().StartsWith($SessionId.ToLower())) }

    Write-Line "Read-only work-mode check of $RootFull"
    if ($Orient) { Write-Line ("Helper: {0} (audit_folder.ps1 {1})" -f $PSCommandPath, $ScriptVersion) }
    Write-Line "Generated $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
    $glance = [ordered]@{}

    if ($Orient) {
        Write-Section 'Orient'
        Write-Line '  basis: file modified times on this machine; unreliable across sync replicas,'
        Write-Line '         after cloud hydration and for clock skew. Leads only, not proof.'
        $idxList = if ($IndexPath.Count) { @($IndexPath) } else { @('PROJECT_INDEX.md') }
        $startup = [Collections.Generic.List[string]]::new()
        foreach ($n in @('AGENTS.md', 'CLAUDE.md', 'GEMINI.md', 'README.md')) { if (Test-Path -LiteralPath (Join-RootRel $n) -PathType Leaf) { $startup.Add($n) } }
        foreach ($extra in @($QuickContext) + $idxList) { if ((Test-Path -LiteralPath (Join-RootRel $extra) -PathType Leaf) -and -not $startup.Contains($extra)) { $startup.Add($extra) } }
        $total = 0
        Write-Line '  startup read set:'
        foreach ($n in $startup) { $sz = (Get-Item -LiteralPath (Join-RootRel $n) -Force).Length; $total += $sz; Write-Line ("    {0}  {1} KB" -f $n, [Math]::Floor($sz / 1024)) }
        Write-Line (("    total {0} KB (budget {1} KB)" -f [Math]::Floor($total / 1024), $ReadBudgetKB) + $(if ($total -gt $ReadBudgetKB * 1024) { '  OVER BUDGET' } else { '' }))
        $qcFlag = $false
        $qcPath = Join-RootRel $QuickContext
        if (Test-Path -LiteralPath $qcPath -PathType Leaf) {
            $qs = (Get-Item -LiteralPath $qcPath -Force).Length
            $qcFlag = $qs -gt $QuickContextKB * 1024
            Write-Line (("  quick context {0}: {1} KB" -f $QuickContext, [Math]::Floor($qs / 1024)) + $(if ($qcFlag) { "  OVER $QuickContextKB KB: replace stale lines, don't append" } else { '' }))
            try {
                $qhead = @(Get-Content -LiteralPath $qcPath -TotalCount 40 -ErrorAction Stop)
                $updates = @($qhead | Where-Object { $_ -match '(?i)(updated|latest state|^\s*\*\*20\d\d-|^\s*20\d\d-)' })
                $dates = @($updates | ForEach-Object { if ($_ -match '20\d\d-\d\d-\d\d') { $Matches[0] } })
                $sortedDates = @($dates | Sort-Object -Descending)
                $outOfOrder = (($dates -join '|') -ne ($sortedDates -join '|'))
                if ($updates.Count -gt 2 -or $outOfOrder) {
                    Write-Line (("  quick context header structure: {0} update-like lines" -f $updates.Count) + $(if ($outOfOrder) { '; dates out of descending order' } else { '' }) + '; keep one current-state section')
                }
            } catch { }
        } else { Write-Line "  quick context ${QuickContext}: NOT FOUND" }

        $S = Get-Sessions
        $scope = Get-ScopeInfo $RootFull
        if ($PSBoundParameters.ContainsKey('ActiveMinutes')) { $minutes = $ActiveMinutes; $windowSrc = '--active-minutes' }
        elseif ($null -ne $scope.Window) { $minutes = $scope.Window; $windowSrc = "AGENTS.md 'Active-writer window:' line" }
        else { $minutes = 30; $windowSrc = "default; no 'Active-writer window:' line" }
        $windowSec = $minutes * 60
        $idxFull = Join-RootRel $SessionIndexFile
        $statuses = Get-IndexStatuses $(if (Test-Path -LiteralPath $idxFull -PathType Leaf) { Read-SmallText $idxFull } else { '' })
        $scratchFull = Join-RootRel $ScratchDir
        $scratchTimes = [ordered]@{}
        if (Test-Path -LiteralPath $scratchFull -PathType Container) {
            foreach ($d in @(Get-ChildItem -LiteralPath $scratchFull -Directory -Force | Where-Object { -not $_.LinkType } | Sort-Ordinal -Key { $_.Name })) { $scratchTimes[$d.Name] = Get-NewestFileTime $d.FullName }
        }
        function Test-Closed($s) { return ($s.Closed -or ($statuses.ContainsKey($s.Id) -and $statuses[$s.Id] -eq $false)) }
        function Test-RecentScratch([string]$sid) {
            foreach ($k in $scratchTimes.Keys) { $t = $scratchTimes[$k]; if ($k.ToLower().StartsWith($sid) -and $null -ne $t -and ($Now - $t).TotalSeconds -le $windowSec) { return $true } }
            return $false
        }
        $sessions = @(); $active = [Collections.Generic.List[object]]::new(); $closedRecent = [Collections.Generic.List[object]]::new(); $idleOpen = 0
        if ($null -eq $S.Sessions) { Write-Line ("  sessions folder {0}: {1} (coverage unavailable)" -f $SessionsDir, $S.State) }
        else {
            $sessions = @($S.Sessions)
            $recent = @($sessions | Sort-Ordinal -Key { Get-SessionRecentKey $_ } | Select-Object -First 5)
            Write-Line ("  recent sessions (of {0}):" -f $sessions.Count)
            Write-Capped @($recent | ForEach-Object {
                $t = $_.LastTitle; if ($t.Length -gt 70) { $t = $t.Substring(0, 70) }
                "{0}  {1}  {2}  {3}  [{4} turns]{6} {5}" -f (Format-Activity $_), $_.Tool, $_.Id.Substring(0, [Math]::Min(8, $_.Id.Length)), $_.Topic, $_.Turns, $t, $(if (Test-Closed $_) { '  closed' } else { '' }) })
            foreach ($ss in $sessions) {
                if (Test-Mine $ss.Id) { continue }
                $fresh = (($Now - $ss.MTime).TotalSeconds -le $windowSec) -or (Test-RecentScratch $ss.Id)
                if ($fresh -and (Test-Closed $ss)) { $closedRecent.Add($ss) }
                elseif ($fresh) { $active.Add($ss) }
                elseif ($statuses.ContainsKey($ss.Id) -and $statuses[$ss.Id] -eq $true -and -not $ss.Closed) { $idleOpen++ }
            }
        }
        if ($S.Blocked.Count -and $null -ne $S.Sessions) { Write-Line ("  session logs not parsed (blocked, unreadable or incomplete): {0}" -f $S.Blocked.Count) }
        $duplicates = @(Get-DuplicateIds $sessions)
        if ($duplicates.Count) { Write-Line ("  duplicate session IDs: {0}; excluded from baseline selection" -f $duplicates.Count) }
        $knownIds = @($sessions | ForEach-Object { $_.Id })
        $unpairedScratch = @($scratchTimes.Keys | Where-Object {
            $n = $_; $t = $scratchTimes[$n]
            $null -ne $t -and ($Now - $t).TotalSeconds -le $windowSec -and -not (Test-Mine $n) -and -not @($knownIds | Where-Object { $n.ToLower().StartsWith($_) }).Count })
        $activeIds = @($active | ForEach-Object { $_.Id } | Select-Object -Unique)
        Write-Line ("  active-writer window: {0} min ({1}); activity = session log or scratch file modified times, not folder times" -f $minutes, $windowSrc)
        Write-Line ("  possibly active writers (changed in last {0} min): {1} distinct sessions, {2} unpaired scratch folders" -f $minutes, $activeIds.Count, $unpairedScratch.Count)
        Write-Capped @($active | ForEach-Object { "session {0} {1} {2}" -f $_.Id.Substring(0, 8), $_.Tool, $_.Topic })
        Write-Capped @($unpairedScratch | ForEach-Object { "unpaired scratch/$_" })
        if ($closedRecent.Count) {
            Write-Line ("  closed sessions with recent file activity (not active writers): {0}" -f $closedRecent.Count)
            Write-Capped @($closedRecent | ForEach-Object { "session {0} {1} {2}" -f $_.Id.Substring(0, 8), $_.Tool, $_.Topic })
        }
        if ($idleOpen) { Write-Line ("  'in progress' index rows with no file activity in the window (not active writers): {0}" -f $idleOpen) }
        Write-Line "  closed = close entry in the log or session-index status other than 'in progress'."
        Write-Line '  An owner handoff message also closes a session; this helper cannot see chat.'
        $declared = @(Get-DeclarationSources $RootFull $QuickContext.Replace('\', '/'))
        if ($declared.Count) { Write-Line ("  coordination: sequential-writer declaration found ({0})" -f ($declared -join ', ')) }
        else { Write-Line '  coordination: no sequential-writer declaration; stage PENDING edits unless other coordination is established' }
        if ($active.Count -or $unpairedScratch.Count) {
            Write-Line '    -> another agent may be working: coordinate shared edits before writing;'
            Write-Line '       stage exact pending edits in your scratch if coordination is unavailable.'
            if ($declared.Count) { Write-Line '       The declaration covers agents working one after another, not overlap: stage shared-record edits this session.' }
        }
        $slugVariantCount = Write-SlugVariants $sessions
        $provO = @(Get-ProvenancePending $RootFull)
        Write-Line (("  _PROVENANCE.md files with PENDING rows: {0}" -f $provO.Count) + $(if ($provO.Count) { ' (list and apply state: --pending)' } else { '' }))
        Write-Capped @($provO | ForEach-Object { "{0} ({1} PENDING lines)" -f $_.Rel, $_.Rows.Count })
        $onWindows = ($PSVersionTable.PSVersion.Major -lt 6) -or $IsWindows
        if ($onWindows) {
            Write-Line "  Windows: writing shared records from Windows PowerShell 5.1? Never use '>>' or"
            Write-Line "    Set-Content/Out-File without -Encoding utf8, and replace only your own session-ID line (W5)."
        }
        if ($PSVersionTable.PSVersion.Major -lt 6) {
            # stderr, not the warning stream: PowerShell 5.1 -File copies warnings to stdout,
            # which would break the Python/PowerShell report parity.
            [Console]::Error.WriteLine("WARNING: this shell is Windows PowerShell $($PSVersionTable.PSVersion). Its '>>' and default Set-Content/Out-File write UTF-16LE or ANSI into UTF-8 records; use UTF-8 explicitly (W5).")
        }

        # Declared startup read order (README_FIRST links, in order).
        $readOrderKB = 'none found'
        $rfRel = $null
        foreach ($c in @('README_FIRST.md', 'AI_CONTEXT/README_FIRST.md')) { if (Test-Path -LiteralPath (Join-RootRel $c) -PathType Leaf) { $rfRel = $c; break } }
        if ($rfRel) {
            $rfFull = Join-RootRel $rfRel
            $rfText = Read-SmallText $rfFull; if ($null -eq $rfText) { $rfText = '' }
            $order = [Collections.Generic.List[string]]::new(); $order.Add($rfRel)
            $seen = [Collections.Generic.HashSet[string]]::new(); [void]$seen.Add($rfRel.ToLower())
            $refs = @(Get-MarkdownTargets $rfText) + @([regex]::Matches($rfText, '`([^`\r\n]+\.[A-Za-z0-9]{1,8})`') | ForEach-Object { $_.Groups[1].Value })
            foreach ($ref in $refs) {
                $clean = Get-CleanReference $ref
                if ((Test-ExternalOrNonPath $clean) -or -not $clean.ToLower().EndsWith('.md')) { continue }
                $hits = @(Get-ResolvedReferencePaths $clean ([IO.Path]::GetDirectoryName($rfFull)))
                if (-not $hits.Count -or -not (Test-Path -LiteralPath $hits[0] -PathType Leaf)) { continue }
                # .NET Framework's GetFullPath may expand 8.3 short names, so test
                # containment against both spellings of the root (see $RootWalk).
                $hit = [IO.Path]::GetFullPath($hits[0])
                $insideRoot = $false
                foreach ($rp in @($RootFull, $RootWalk)) {
                    if ($rp -and $hit.StartsWith($rp.TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { $insideRoot = $true }
                }
                if (-not $insideRoot) { continue }
                $key = Get-RelSlash $hit
                if (-not $seen.Add($key.ToLower())) { continue }
                $order.Add($key)
            }
            $orderTotal = 0
            $orderLines = foreach ($key in $order) {
                $sz = (Get-Item -LiteralPath (Join-RootRel $key) -Force).Length; $orderTotal += $sz
                ("{0}  {1} KB" -f $key, [Math]::Floor($sz / 1024)) + $(if ($sz -gt $CodexDocLimit) { '  LARGE: read by section/ID or tail' } else { '' })
            }
            Write-Line ("  declared read order ({0} and the .md files it links, in order; may include optional reads): {1} files" -f $rfRel, $order.Count)
            Write-Capped @($orderLines)
            Write-Line (("    total {0} KB (budget {1} KB)" -f [Math]::Floor($orderTotal / 1024), $ReadBudgetKB) + $(if ($orderTotal -gt $ReadBudgetKB * 1024) { '  OVER BUDGET' } else { '' }))
            $readOrderKB = "{0} KB" -f [Math]::Floor($orderTotal / 1024)
        } else { Write-Line '  declared read order: no README_FIRST.md at the root or in AI_CONTEXT/' }

        if ($Since) {
            $sinceT = ConvertFrom-Iso $Since
            if ($null -eq $sinceT) { throw "-Since is not an ISO date/time: '$Since'" }
            $basis = "--since $Since"
        } else {
            $dated = @($sessions | Where-Object { $_.Id -notin $duplicates -and $_.Started -and -not (Test-Mine $_.Id) })
            if ($dated.Count) {
                $latest = $dated | Sort-Ordinal -Key { Get-SessionLatestStartKey $_ } | Select-Object -First 1
                $sinceT = $latest.Started; $basis = "start of latest session $($latest.Id.Substring(0, 8))"
            } else { $sinceT = $Now.AddDays(-1); $basis = 'last 24 hours (no dated sessions)' }
        }
        $skip = @(($SessionsDir.Replace('\', '/').Trim('/') + '/').ToLower(), ($ScratchDir.Replace('\', '/').Trim('/') + '/').ToLower())
        $changed = [Collections.Generic.List[object]]::new()
        $allW = [Collections.Generic.List[object]]::new()
        $prunedCount = 0; $unvisitedW = 0
        $clockW = [Diagnostics.Stopwatch]::StartNew()
        $stackW = [Collections.Generic.Stack[IO.DirectoryInfo]]::new(); $stackW.Push($RootDirInfo)
        while ($stackW.Count) {
            if ($MaxSeconds -gt 0 -and $clockW.Elapsed.TotalSeconds -gt $MaxSeconds) { $unvisitedW = $stackW.Count; break }
            $d = $stackW.Pop()
            try { $ents = @($d.EnumerateFileSystemInfos()) } catch { continue }
            $isRootW = [object]::ReferenceEquals($d, $RootDirInfo)
            $subs = @($ents | Where-Object { $_ -is [IO.DirectoryInfo] })
            $envW = (-not $isRootW) -and (Test-EnvRoot @($subs | ForEach-Object { $_.Name }) @($ents | Where-Object { $_ -isnot [IO.DirectoryInfo] } | ForEach-Object { $_.Name }))
            $envP = 0
            foreach ($e in $ents) {
                if ($e -is [IO.DirectoryInfo]) {
                    if (Test-LinkDirectory $e) { continue }
                    if ($envW) { $envP++; continue }
                    if (($PruneSafe -contains $e.Name.ToLower()) -or (@($NoisePrefixHints | Where-Object { $e.Name.ToLower().StartsWith($_) }).Count)) { $prunedCount++; continue }
                    $stackW.Push($e)
                } else {
                    $r = Get-RelSlash $e.FullName
                    $mt = [DateTimeOffset]$e.LastWriteTime
                    $allW.Add([pscustomobject]@{ Rel = $r; MTime = $mt; Full = $e.FullName; Name = $e.Name })
                    if ($mt -lt $sinceT) { continue }
                    $rl = $r.ToLower(); if ($rl.StartsWith($skip[0]) -or $rl.StartsWith($skip[1])) { continue }
                    $ex = $false; foreach ($pat in $Exclude) { if (Test-MatchPattern $r $pat) { $ex = $true } }
                    if ($ex) { continue }
                    $changed.Add([pscustomobject]@{ Rel = $r; MTime = $mt })
                }
            }
            if ($envP) { $prunedCount++ }
        }
        # Newest first, then ordinal path order, exactly like audit_folder.py.
        $changedS = @($changed | Sort-Ordinal -Key { ([DateTimeOffset]::MaxValue.UtcTicks - $_.MTime.UtcTicks).ToString('D19') + [char]0 + $_.Rel })
        $sinceLabel = if (-not $Since -and $dated.Count -and $latest.FilenameStart) { $latest.FilenameStart + ' (filename; offset unknown)' } else { Format-WorkTime $sinceT }
        Write-Line ("  files changed since {0} ({1}), excluding session logs and scratch: {2}" -f $sinceLabel, $basis, $changedS.Count)
        Write-Capped @($changedS | ForEach-Object { "{0}  {1}" -f (Format-WorkTime $_.MTime), $_.Rel })
        if ($unvisitedW) { Write-Line "  WALK INCOMPLETE: $unvisitedW folders not visited (--max-seconds)" }
        if ($prunedCount) { Write-Line "  generated-state folders not walked: $prunedCount" }

        # Activity no record accounts for (R189/R209).
        $recordTexts = [Collections.Generic.List[string]]::new()
        if ($null -ne $S.Sessions) {
            foreach ($sf in @(Get-ChildItem -LiteralPath $S.Dir -Force -ErrorAction SilentlyContinue | Where-Object { $_.Name.ToLower().EndsWith('.md') } | Sort-Ordinal -Key { $_.Name })) {
                $t = Read-SmallText $sf.FullName; if ($t) { $recordTexts.Add($t) }
            }
        }
        foreach ($w in $allW) { if ($w.Name.ToLower() -eq '_provenance.md') { $t = Read-SmallText $w.Full; if ($t) { $recordTexts.Add($t) } } }
        $unattributed = @($changedS | Where-Object {
            $r = $_.Rel; $leaf = $r.Split('/')[-1]
            -not @($recordTexts | Where-Object { $_.Contains($r) -or $_.Contains($leaf) }).Count } | ForEach-Object { $_.Rel })
        Write-Line ("  changed files no session log or _PROVENANCE.md names: {0} (leads; a log may cover them by folder)" -f $unattributed.Count)
        Write-Capped $unattributed
        $byTime = @{}
        foreach ($w in $allW) {
            $sec = [int64][Math]::Floor($w.MTime.ToUnixTimeMilliseconds() / 1000)
            if (-not $byTime.ContainsKey($sec)) { $byTime[$sec] = [Collections.Generic.List[string]]::new() }
            $byTime[$sec].Add($w.Rel)
        }
        $clusters = @($byTime.Keys | Where-Object { $byTime[$_].Count -ge 10 } | ForEach-Object {
            [pscustomobject]@{ Count = $byTime[$_].Count; Sec = $_; Folder = (Get-CommonFolder @($byTime[$_])) } } |
            Sort-Ordinal -Key { (Get-DescKey $_.Count) + [char]0 + ($_.Sec + 100000000000).ToString('D16') } | Select-Object -First 3)
        foreach ($c in $clusters) {
            $where = if ($c.Folder -eq '.') { 'the root' } else { $c.Folder + '/' }
            Write-Line ("  identical modified times: {0} files at {1} under {2} (typical of archive extraction; not activity evidence)" -f $c.Count, (Format-WorkTime ([DateTimeOffset]::FromUnixTimeSeconds($c.Sec))), $where)
        }
        $conf = Write-ConflictBlock @($allW | ForEach-Object { $_.Rel })
        # Sibling projects are outside this root, so their contents are never read here.
        Write-Line '  handoffs from sibling projects: not read (outside this root); run --portfolio on the parent folder to list handoffs addressed to this project'
        $idxText = ''
        foreach ($ip in $idxList) { $t = Read-SmallText (Join-RootRel $ip); if ($t) { $idxText += $t } }
        $unindexed = @()
        $sessIdx = $SessionIndexFile.Replace('\', '/')
        if ($idxText) {
            $unindexed = @($changedS | Where-Object {
                $r = $_.Rel; $nm = $r.Split('/')[-1]
                -not ($startup.Contains($r) -or $r -eq $sessIdx -or ($idxList -contains $r) -or (Test-IndexMentions $idxText $nm) -or (Test-IndexMentions $idxText $r)) } | ForEach-Object { $_.Rel })
            Write-Line ("  changed files the index never names: {0} (folder-level coverage may already include them)" -f $unindexed.Count)
            Write-Capped $unindexed
        } else { Write-Line ("  index {0}: NOT FOUND or unreadable; unindexed check skipped" -f ($idxList -join ', ')) }
        $glance['possibly active writers'] = $activeIds.Count + $unpairedScratch.Count
        $glance['slugs with several headers'] = $slugVariantCount
        $glance['provenance PENDING files'] = $provO.Count
        $glance['changed since baseline'] = $changedS.Count
        $glance['changed but unnamed in index'] = $(if ($idxText) { $unindexed.Count } else { 'n/a' })
        $glance['quick context over size'] = $(if ($qcFlag) { 'yes' } else { 'no' })
        $glance['sequential-writer declaration'] = $(if ($declared.Count) { 'yes' } else { 'no' })
        $glance['declared read order'] = $readOrderKB
        $glance['changed but unattributed'] = $unattributed.Count
        $glance['sync conflict copies'] = $conf[0]
        $glance['case-only name collisions'] = $conf[1]
    }

    if ($SessionIndex) {
        Write-Section 'Session index check'
        $S = Get-Sessions
        $indexFull = Join-RootRel $SessionIndexFile
        Write-Line "  sessions folder: $SessionsDir"
        if ($null -eq $S.Sessions) {
            Write-Line ("  sessions folder {0} (coverage unavailable)" -f $S.State)
            $glance['sessions missing from index'] = 'n/a (folder not inspected)'
        } else {
            $sessions = @($S.Sessions)
            Write-Line ("  session logs: {0}" -f $sessions.Count)
            $state = $null
            $indexState = Get-WorkPathState $indexFull
            $idx = Read-SmallText $indexFull
            if ($null -eq $idx) {
                $state = if ($indexState -ne 'present') { $indexState } else { 'UNAVAILABLE (blocked, unreadable or incomplete)' }
                Write-Line "  index file ${SessionIndexFile}: $state"; $idx = ''
            } else { Write-Line "  index file ${SessionIndexFile}: present" }
            if ($state -and $state -ne 'NOT FOUND') {
                Write-Line '  sessions missing from index: n/a (index not inspected)'
                $glance['sessions missing from index'] = 'n/a (index not inspected)'
            } else {
            $duplicates = @(Get-DuplicateIds $sessions)
            Write-Line ("  duplicate session IDs: {0} (no proposed rows for ambiguous IDs)" -f $duplicates.Count)
            Write-Capped $duplicates
            Write-Line '  filename timestamps are used only as fallbacks and labelled offset unknown'
            $low = $idx.ToLower()
            $missing = @($sessions | Where-Object { $_.Id -notin $duplicates -and -not $low.Contains($_.Id.ToLower()) -and -not $idx.Contains($_.Name) })
            Write-Line ("  sessions missing from index: {0}" -f $missing.Count)
            if ($missing.Count) {
                $idxDir = [IO.Path]::GetDirectoryName($indexFull)
                $baseUri = [Uri]::new($idxDir.TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar)
                $relDir = [Uri]::UnescapeDataString($baseUri.MakeRelativeUri([Uri]::new($S.Dir)).ToString()).Replace('\', '/').TrimEnd('/')
                Write-Line '  Proposed rows (review Latest outcome and Status before saving):'
                function Get-Cell($v) { ([string]$v).Replace('|', '\|').Replace("`n", ' ').Trim() }
                Write-Capped @($missing | ForEach-Object {
                    $outcomeText = if ($_.LastTitle) { $_.LastTitle } else { '(fill in)' }
                    $startText = if ($_.FilenameStart) { $_.FilenameStart + ' (filename; offset unknown)' } else { Format-WorkTime $_.Started }
                    "| {0} | {1} | {2} | {3} | {4} | {5} | (fill in) | [Session]({6}/{7}) |" -f $startText, (Format-Activity $_), $_.Id, (Get-Cell $_.Tool), (Get-Cell $_.Topic), (Get-Cell $outcomeText), $relDir, [Uri]::EscapeDataString($_.Name) }) '  '
            }
            $stale = [Collections.Generic.SortedSet[string]]::new([StringComparer]::Ordinal)
            if ($idx) {
                $leaf = $SessionsDir.Replace('\', '/').Trim('/').Split('/')[-1]
                $idxDir2 = [IO.Path]::GetDirectoryName($indexFull)
                foreach ($tgt in (Get-MarkdownTargets $idx)) {
                    $clean = Get-CleanReference $tgt
                    if (-not $clean -or (Test-ExternalOrNonPath $clean)) { continue }
                    $norm = $clean.Replace('\', '/')
                    if (-not (('/' + $norm).Contains('/' + $leaf + '/'))) { continue }
                    if (-not (Test-ReferenceResolves $clean $idxDir2)) { [void]$stale.Add($clean) }
                }
            }
            Write-Line ("  index links to missing session logs: {0}" -f $stale.Count)
            Write-Capped @($stale)
            Write-Line ("  nonstandard session filenames: {0}" -f $S.Nonstandard.Count)
            Write-Capped $S.Nonstandard
            $slugVariantCountI = Write-SlugVariants $S.Sessions
            if ($S.Blocked.Count) { Write-Line ("  session logs not parsed (blocked, unreadable or incomplete): {0}" -f $S.Blocked.Count); Write-Capped $S.Blocked }
            $glance['sessions missing from index'] = $missing.Count
            $glance['index links to missing logs'] = $stale.Count
            $glance['slugs with several headers'] = $slugVariantCountI
            }
        }
    }

    if ($Pending) {
        Write-Section 'Pending files (report only)'
        $pfound = @(Find-PendingFiles $RootFull $ScratchDir)
        $plines = [Collections.Generic.List[string]]::new(); $pstates = [Collections.Generic.List[string]]::new()
        $missingN = 0; $lateN = 0
        foreach ($pf in $pfound) {
            $res = Get-PendingState $pf $RootFull
            if ($res.Flag -eq 'no Status: line') { $missingN++ }
            if ($res.Flag -eq 'Status: not first line') { $lateN++ }
            $nb = @($res.Blocks).Count
            for ($k = 0; $k -lt $nb; $k++) {
                $bst = @($res.Blocks)[$k]
                $pstates.Add($bst[0])
                $part = if ($nb -gt 1) { " [{0}/{1}]" -f ($k + 1), $nb } else { '' }
                $tg = if ($bst[1]) { $bst[1] } else { '(no Target)' }
                $plines.Add((("{0,-49} {1}{2} -> {3}" -f $bst[0], (Get-RelSlash $pf), $part, $tg) + $(if ($res.Flag -and $k -eq 0) { "  [$($res.Flag)]" } else { '' })))
            }
        }
        Write-Line ("  pending files: {0}, edit blocks: {1} (no Status: line: {2}; Status: not first line: {3})" -f $pfound.Count, $pstates.Count, $missingN, $lateN)
        Write-Capped @($plines)
        $applicableN = @($pstates | Where-Object { $_.StartsWith('Pending (') }).Count
        $appliedN = @($pstates | Where-Object { $_ -eq 'Applied (not marked)' }).Count
        $malformedN = $missingN
        $prov = @(Get-ProvenancePending $RootFull)
        Write-Line ("  _PROVENANCE.md files with PENDING rows: {0} (lines marked PENDING and not APPLIED; apply under W5, then mark 'APPLIED <hash8> by <session>/<turn>')" -f $prov.Count)
        $provTake = [Math]::Min($prov.Count, $WorkCap)
        for ($i = 0; $i -lt $provTake; $i++) {
            Write-Line ("    {0} ({1} PENDING lines)" -f $prov[$i].Rel, $prov[$i].Rows.Count)
            Write-Capped @($prov[$i].Rows | ForEach-Object { if ($_.Length -gt 160) { $_.Substring(0, 160) } else { $_ } }) '      '
        }
        if ($prov.Count -gt $provTake) { Write-Line ("      ... and {0} more" -f ($prov.Count - $provTake)) }
        if (@(Get-DeclarationSources $RootFull $QuickContext.Replace('\', '/')).Count) { Write-Line "  sequential-writer declaration found: the active writer may apply 'Pending (base/anchor matches)' entries (W5)." }
        Write-Line '  Conflicted means compare by hand: the edit may already be in the target in other words,'
        Write-Line '  or may still be needed. Never discard or apply on the label alone.'
        Write-Line '  Nothing was applied. Apply under Work mode W5, then set the first line to'
        Write-Line "  'Status: APPLIED <after-sha8> by <session>/<turn>'."
        $glance['pending files'] = $pfound.Count
        $glance['pending edit blocks'] = $pstates.Count
        $glance['pending without Status line'] = $malformedN
        $glance['pending applicable now'] = $applicableN
        $glance['applied but still PENDING'] = $appliedN
        $glance['provenance files with PENDING'] = $prov.Count
    }

    Write-Section 'Findings at a glance'
    foreach ($k in $glance.Keys) { Write-Line ("  {0,-32} {1}" -f $k, $glance[$k]) }
    if ($Out) {
        $utf8w = [System.Text.UTF8Encoding]::new($false)
        $streamW = [System.IO.File]::Open($OutFull, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write)
        try { $bytesW = $utf8w.GetBytes((($script:ReportLines) -join "`n") + "`n"); $streamW.Write($bytesW, 0, $bytesW.Length) } finally { $streamW.Dispose() }
        $onW = $false
        foreach ($ln in $script:ReportLines) {
            if ($ln.StartsWith('== ') -and $ln.EndsWith(' ==')) { $onW = ($ln -eq '== Findings at a glance ==') }
            if ($onW -and $ln.Trim()) { Write-Host $ln }
        }
        Write-Host ""
        Write-Host ("Full report: {0} ({1} lines). Read sections from it as needed." -f $OutFull, $script:ReportLines.Count)
    }
    exit 0
}

$allFiles = [System.Collections.Generic.List[System.IO.FileInfo]]::new()
$allFolderItems = [System.Collections.Generic.List[System.IO.DirectoryInfo]]::new()
$reparseDirs = [System.Collections.Generic.List[System.IO.DirectoryInfo]]::new()
$emptyFolders = [System.Collections.Generic.List[System.IO.DirectoryInfo]]::new()
$unreadableDirs = [System.Collections.Generic.List[object]]::new()
$envRoots = [System.Collections.Generic.List[string]]::new()
$pruned = [System.Collections.Generic.List[object]]::new()
$unvisited = 0
$clock = [System.Diagnostics.Stopwatch]::StartNew()
$walk = [System.Collections.Generic.Stack[System.IO.DirectoryInfo]]::new()
$walk.Push($RootDirInfo)
while ($walk.Count) {
    if ($MaxSeconds -gt 0 -and $clock.Elapsed.TotalSeconds -gt $MaxSeconds) { $unvisited = $walk.Count; break }
    $dir = $walk.Pop()
    try { $entries = @($dir.EnumerateFileSystemInfos()) }
    catch {
        $inner = $_.Exception
        while ($inner.InnerException) { $inner = $inner.InnerException }
        $unreadableDirs.Add([pscustomobject]@{ Path = $dir.FullName; Why = $inner.GetType().Name })
        continue
    }
    $isRoot = [object]::ReferenceEquals($dir, $RootDirInfo)
    if ($entries.Count -eq 0 -and -not $isRoot) { $emptyFolders.Add($dir) }
    $subDirs = @($entries | Where-Object { $_ -is [System.IO.DirectoryInfo] })
    $envHere = (-not $isRoot) -and (Test-EnvRoot @($subDirs | ForEach-Object { $_.Name }) @($entries | Where-Object { $_ -isnot [System.IO.DirectoryInfo] } | ForEach-Object { $_.Name }))
    if ($envHere) { $envRoots.Add($dir.FullName) }
    $envPruned = 0
    foreach ($e in $entries) {
        if ($e -is [System.IO.DirectoryInfo]) {
            $allFolderItems.Add($e)
            if (Test-LinkDirectory $e) { $reparseDirs.Add($e) }
            elseif ($PruneNoise -and $envHere) { $envPruned++ }
            elseif ($PruneNoise -and (($PruneSafe -contains $e.Name.ToLower()) -or (@($NoisePrefixHints | Where-Object { $e.Name.ToLower().StartsWith($_) }).Count))) {
                $pruned.Add([pscustomobject]@{ Path = $e.FullName; Why = 'generated state' })
            }
            else { $walk.Push($e) }
        }
        else { $allFiles.Add($e) }
    }
    # One line per environment, not one per package folder.
    if ($envPruned) { $pruned.Add([pscustomobject]@{ Path = $dir.FullName; Why = "Python environment ($envPruned subfolders)" }) }
}
$allFolders = $allFolderItems.Count

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
$glance = @{}

Write-Section "Summary"
$totalBytes = ($allFiles | Measure-Object Length -Sum).Sum
if ($null -eq $totalBytes) { $totalBytes = 0 }
$maxDepth = 0
foreach ($f in $allFiles) {
    $d = (Get-RelSlash $f.FullName).Split('/').Count - 1
    if ($d -gt $maxDepth) { $maxDepth = $d }
}
Write-Line ("  Files (all):      {0}" -f $allFiles.Count)
if ($unreadableDirs.Count) {
    Write-Line ("  Unreadable dirs:  {0} (contents NOT counted)" -f $unreadableDirs.Count)
}
Write-Line ("  Folders:          {0}" -f $allFolders)
Write-Line ("  Total MB:         {0:F2}" -f ($totalBytes / 1MB))
Write-Line ("  Max depth:        {0}" -f $maxDepth)
if ($Exclude.Count) {
    $exTotal = ($excludedCounts.Values | Measure-Object -Sum).Sum
    if ($null -eq $exTotal) { $exTotal = 0 }
    $pct = if ($allFiles.Count) { 100.0 * $exTotal / $allFiles.Count } else { 0 }
    Write-Line ("  Excluded:         {0} ({1:F0}%) by -Exclude" -f $exTotal, $pct)
    Write-Line ("  In detail below:  {0}" -f $files.Count)
}
if ($pruned.Count) { Write-Line ("  Pruned folders:   {0} (not walked; contents NOT counted)" -f $pruned.Count) }
if ($unvisited) { Write-Line ("  WALK INCOMPLETE:  time budget {0} s reached; {1} queued directories not visited" -f $MaxSeconds, $unvisited) }

if ($unreadableDirs.Count) {
    Write-Section "Directories not readable (contents missing from every count)"
    $unreadableDirs | Sort-Ordinal -Key { (Get-Short $_.Path).ToLower() } | Select-Object -First (Get-Cap 25) | ForEach-Object {
        Write-Line ("  {0,-18} {1}" -f $_.Why, (Get-Short $_.Path))
    }
    if ($unreadableDirs.Count -gt (Get-Cap 25)) { Write-Line ("  ... and " + ($unreadableDirs.Count - (Get-Cap 25)) + " more") }
    Write-Line "  Access was denied or the directory vanished mid-walk. Nothing below these paths is in any total. Resolve access or disclose the gap." -ForegroundColor Yellow
}

if ($pruned.Count) {
    Write-Section "Pruned generated state (not walked; contents in no count)"
    $pruned | Sort-Ordinal -Key { (Get-Short $_.Path).ToLower() } | Select-Object -First (Get-Cap 25) | ForEach-Object {
        Write-Line ("  {0,-26} {1}" -f $_.Why, (Get-Short $_.Path))
    }
    if ($pruned.Count -gt (Get-Cap 25)) { Write-Line ("  ... and " + ($pruned.Count - (Get-Cap 25)) + " more") }
    Write-Line "  Generated state, not evidence. Provider sync/index state not checked."
}

if ($Exclude.Count) {
    Write-Section "Excluded from detail sections (counted, not examined)"
    foreach ($k in @($excludedCounts.GetEnumerator() | Sort-Ordinal -Key { (Get-DescKey $_.Value) + [char]0 + $_.Key } | Select-BriefItems)) {
        Write-Line ("  {0,6}  {1}" -f $k.Value, $k.Key)
    }
    Write-Line "  These files were NOT classified. State this in the report." -ForegroundColor Yellow
}

if ($SuggestExcludes) {
    Write-Section "Suggested exclusions (generated machine state - nothing excluded yet)"
    $envRel = @($envRoots | ForEach-Object { (Get-RelSlash $_) + '/' })
    $clusters = @{}
    $kinds = @{}
    foreach ($f in $allFiles) {
        $rp = Get-RelSlash $f.FullName
        $env = $null
        foreach ($e in $envRel) { if ($rp.ToLower().StartsWith($e.ToLower())) { $env = $e; break } }
        if ($env) {
            $key = $env + '**'
            $clusters[$key] = [int]$clusters[$key] + 1
            $kinds[$key] = '  [Python environment]'
            continue
        }
        $parts = $rp.Split('/')
        for ($i = 0; $i -lt $parts.Count - 1; $i++) {
            # Exact segment or profile-style prefix; never a substring test.
            if (Test-NoiseSegment $parts[$i]) {
                if ($GlobalNoise -contains $parts[$i].ToLower()) { $key = '**/' + $parts[$i] + '/**' }
                else { $key = ($parts[0..$i] -join '/') + '/**' }
                $clusters[$key] = [int]$clusters[$key] + 1
                break
            }
        }
    }
    if ($clusters.Count) {
        $ordered = @($clusters.GetEnumerator() | Sort-Ordinal -Key { (Get-DescKey $_.Value) + [char]0 + $_.Key.ToLower() })
        foreach ($k in ($ordered | Select-Object -First (Get-Cap 20))) {
            $pct = if ($allFiles.Count) { 100.0 * $k.Value / $allFiles.Count } else { 0 }
            Write-Line ("  {0,6} ({1,4:F1}%)  -Exclude '{2}'{3}" -f $k.Value, $pct, $k.Key, [string]$kinds[$k.Key])
        }
        if ($ordered.Count -gt (Get-Cap 20)) { Write-Line ("  ... and " + ($ordered.Count - (Get-Cap 20)) + " more") }
        Write-Line "  Confirm with the owner before excluding. Never delete these under a standard cleanup approval." -ForegroundColor Yellow
    }
    else { Write-Line "  none detected" }
}

Write-Section ("Per-folder counts (top {0})" -f (Get-Cap 25))
$perFolder = @{}
foreach ($f in $files) { $perFolder[$f.DirectoryName] = [int]$perFolder[$f.DirectoryName] + 1 }
$perFolder.GetEnumerator() |
Sort-Ordinal -Key { (Get-DescKey $_.Value) + [char]0 + (Get-Short $_.Key).ToLower() } | Select-Object -First (Get-Cap 25) |
ForEach-Object { Write-Line ("  {0,6}  {1}" -f $_.Value, (Get-Short $_.Key)) }

Write-Section "Reparse points not descended (junctions / directory symlinks)"
if ($reparseDirs.Count) {
    foreach ($rd in @($reparseDirs | Sort-Ordinal -Key { (Get-Short $_.FullName).ToLower() } | Select-BriefItems)) {
        Write-Line ("  " + (Get-Short $rd.FullName))
        $tgt = @($rd.Target) | Select-Object -First 1
        if (-not $tgt) { $tgt = "<unresolved>" }
        Write-Line ("     -> " + $tgt)
    }
    Write-Line "  Descendants of these are in NO count in this report."
    Write-Line "  That is correct locally. If this root is OneDrive/SharePoint-synced," -ForegroundColor Yellow
    Write-Line "  the provider may hold the target as real files that other agents" -ForegroundColor Yellow
    Write-Line "  index. Check the cloud-side view before calling them external." -ForegroundColor Yellow
}
else { Write-Line "  none" }

Write-Section "Empty directories (cosmetic; no removal implied)"
if ($visibleEmptyFolders.Count) {
    Write-Line ("  " + $visibleEmptyFolders.Count + " empty director" + $(if ($visibleEmptyFolders.Count -eq 1) { 'y in detail:' } else { 'ies in detail:' }))
    $visibleEmptyFolders | Sort-Ordinal -Key { (Get-Short $_.FullName).ToLower() } | Select-Object -First (Get-Cap 40) |
        ForEach-Object { Write-Line ("     " + (Get-Short $_.FullName)) }
    if ($visibleEmptyFolders.Count -gt (Get-Cap 40)) { Write-Line ("     ... and " + ($visibleEmptyFolders.Count - (Get-Cap 40)) + " more") }
    Write-Line "  Leave in place unless removal is explicitly authorized and uses recoverable platform semantics."
}
else { Write-Line "  none" }
if ($excludedEmptyFolders.Count) {
    Write-Line ("  " + $excludedEmptyFolders.Count + " additional empty directories fall under -Exclude patterns; counted but not listed.")
}

Write-Section "Extensions"
$files | Group-Object { $_.Extension.ToLower() } | Sort-Ordinal -Key { (Get-DescKey $_.Count) + [char]0 + $(if ($_.Name) { $_.Name } else { '(none)' }) } | Select-Object -First (Get-Cap 20) |
ForEach-Object { Write-Line ("  {0,6}  {1}" -f $_.Count, $(if ($_.Name) { $_.Name } else { '(none)' })) }

Write-Section "Archives"
$archives = @($files | Where-Object { $_.Extension -match '^\.(zip|7z|rar|tar|gz|tgz)$' } | Sort-Ordinal -Key { (Get-Short $_.FullName).ToLower() })
if ($archives.Count) {
    $archives | Select-Object -First (Get-Cap $archives.Count) | ForEach-Object {
        Write-Line ("  {0,8:F2} MB  {1:yyyy-MM-dd}  {2}" -f ($_.Length / 1MB), $_.LastWriteTime, (Get-Short $_.FullName))
    }
    if ($archives.Count -gt (Get-Cap $archives.Count)) { Write-Line ("  ... and " + ($archives.Count - (Get-Cap $archives.Count)) + " more") }
    Write-Line "  Archives stay closed. Do not bulk-extract to make them searchable."
}
else { Write-Line "  none" }

$HostBase = if ($HostRoot) { $HostRoot.TrimEnd('\', '/') } else { $RootFull }
if ($InspectZip) {
    Write-Section "ZIP central directories (no extraction)"
    $memberCap = if ($Brief) { 5 } else { 15 }
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    foreach ($z in @($archives | Where-Object { $_.Extension -eq '.zip' } | Select-BriefItems)) {
        Write-Line ("-- " + (Get-Short $z.FullName))
        try {
            Assert-ContentRead $z.FullName
            $zip = [System.IO.Compression.ZipFile]::OpenRead($z.FullName)
            try {
                Write-Line ("   entries: " + $zip.Entries.Count)
                $bad = @($zip.Entries | Where-Object {
                    $normalized = $_.FullName.Replace('\', '/')
                    $parts = @($normalized.Split('/'))
                    $normalized.StartsWith('/') -or $normalized -match '^[A-Za-z]:' -or
                        $parts -contains '..' -or $normalized -match '[:*?"<>|]'
                })
                if ($bad.Count) {
                    Write-Line ("   INVALID/UNSAFE NAMES: " + $bad.Count) -ForegroundColor Yellow
                    $bad | Select-Object -First $memberCap -ExpandProperty FullName | ForEach-Object { Write-Line "     $_" }
                    if ($bad.Count -gt $memberCap) { Write-Line '     ...' }
                }
                else {
                    $zip.Entries | Select-Object -First $memberCap -ExpandProperty FullName | ForEach-Object { Write-Line "     $_" }
                    if ($zip.Entries.Count -gt $memberCap) { Write-Line '     ...' }
                }
                $longE = @($zip.Entries | Where-Object { ($HostBase.Length + 1 + $_.FullName.Length) -gt $PathThreshold })
                if ($longE.Count) { Write-Line ("   would exceed path threshold: " + $longE.Count) -ForegroundColor Yellow }
            }
            finally { $zip.Dispose() }
        }
        catch { Write-Line "   unreadable: $_" -ForegroundColor Red }
    }
}

Write-Section "Path length risks (> $PathThreshold chars)"
# Measured as host root + relative path, so a folder mounted under another
# prefix is judged by its real Windows/OneDrive length when -HostRoot is set.
# All discovered files, like audit_folder.py: an excluded file still has to move.
$longPaths = @($allFiles | ForEach-Object {
        $r = Get-RelSlash $_.FullName
        $n = if ($r) { $HostBase.Length + 1 + $r.Length } else { $HostBase.Length }
        if ($n -gt $PathThreshold) { [pscustomobject]@{ N = $n; Path = $_.FullName } }
    } | Sort-Ordinal -Key { (Get-DescKey $_.N) + [char]0 + (Get-Short $_.Path).ToLower() })
$glance['long'] = $longPaths.Count
Write-Line ("  Measured against: " + $HostBase)
if ($longPaths.Count) {
    $longPaths | Select-Object -First (Get-Cap 40) | ForEach-Object { Write-Line ("  {0,4}  {1}" -f $_.N, (Get-Short $_.Path)) }
    if ($longPaths.Count -gt (Get-Cap 40)) { Write-Line ("  ... and " + ($longPaths.Count - (Get-Cap 40)) + " more") }
}
else { Write-Line "  none" }
if (-not $HostRoot) {
    Write-Line "  If this root is a mounted copy of a Windows/OneDrive folder, re-run with the host-root option set to its real path."
}

Write-Section "OneDrive / cloud placeholders"
$offline = @($files | Where-Object { Test-CloudOnly $_ })
if ($offline.Count) {
    Write-Line ("  " + $offline.Count + " file(s) not hydrated - hydrate before any move") -ForegroundColor Yellow
    $offline | Select-Object -First (Get-Cap 20) | ForEach-Object { Write-Line ("     " + (Get-Short $_.FullName)) }
    if ($offline.Count -gt (Get-Cap 20)) { Write-Line ("     ... and " + ($offline.Count - (Get-Cap 20)) + " more") }
}
else { Write-Line "  none detected" }

Write-Section "Duplicate names across folders"
$dupNames = @($files | Group-Object { $_.Name.ToLower() } | Where-Object Count -gt 1 |
    Sort-Ordinal -Key { (Get-DescKey $_.Count) + [char]0 + $_.Name })
if ($dupNames.Count) {
    foreach ($g in ($dupNames | Select-Object -First (Get-Cap 20))) {
        $members = @($g.Group | Sort-Ordinal -Key { (Get-Short $_.FullName).ToLower() })
        Write-Line ("-- " + $members[0].Name + "  (" + $g.Count + ")")
        $members | Select-Object -First $DupCap | ForEach-Object {
            Write-Line ("     " + $_.LastWriteTime.ToString('yyyy-MM-dd') + "  " + (Get-Short $_.FullName))
        }
        if ($g.Count -gt $DupCap) { Write-Line ("     ... and " + ($g.Count - $DupCap) + " more") }
    }
    if ($dupNames.Count -gt (Get-Cap 20)) { Write-Line ("  ... and " + ($dupNames.Count - (Get-Cap 20)) + " more duplicated names") }
}
else { Write-Line "  none" }

if ($HashFiles) {
    $unreadable = [System.Collections.ArrayList]::new()
    $guarded = [System.Collections.ArrayList]::new()
    $linked = [System.Collections.ArrayList]::new()
    $hashes = foreach ($f in $files) {
        try {
            Assert-ContentRead $f.FullName
            [pscustomobject]@{
                Path = $f.FullName
                Name = $f.Name
                Hash = (Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256 -ErrorAction Stop).Hash.ToLower()
            }
        }
        catch {
            # Never drop these silently: an unhashed file is a hole in the
            # coverage claim, and on OneDrive it usually means a placeholder
            # or a lock, both of which block an Execute pass.
            $reason = Get-ContentReadBlockReason $f.FullName
            if ($reason -eq 'credential') { [void]$guarded.Add($f.FullName) }
            elseif ($reason -eq 'link') { [void]$linked.Add($f.FullName) }
            else { [void]$unreadable.Add([pscustomobject]@{ Path = $f.FullName; Why = 'UNREADABLE' }) }
        }
    }

    if ($guarded.Count) {
        Write-Section 'Not hashed by design (credential guard)'
        $guarded | Select-Object -First (Get-Cap 25) | ForEach-Object { Write-Line ("  CREDENTIAL GUARD   " + (Get-Short $_)) }
        if ($guarded.Count -gt (Get-Cap 25)) { Write-Line ("  ... and " + ($guarded.Count - (Get-Cap 25)) + " more") }
        Write-Line ("  " + $guarded.Count + " file(s) were not hashed by design. Their content-read guard remains active.")
    }

    if ($linked.Count) {
        Write-Section 'LINKED PATH - not followed or hashed'
        $linked | Select-Object -First (Get-Cap 25) | ForEach-Object { Write-Line ("  READ BLOCKED       " + (Get-Short $_)) }
        if ($linked.Count -gt (Get-Cap 25)) { Write-Line ("  ... and " + ($linked.Count - (Get-Cap 25)) + " more") }
        Write-Line ("  " + $linked.Count + " linked path(s) were not followed or hashed. Their content-read guard remains active.")
    }

    if ($unreadable.Count) {
        Write-Section "UNREADABLE - could not hash"
        $unreadable | Select-Object -First (Get-Cap 25) | ForEach-Object { Write-Line ("  {0,-18} {1}" -f $_.Why, (Get-Short $_.Path)) }
        if ($unreadable.Count -gt (Get-Cap 25)) { Write-Line ("  ... and " + ($unreadable.Count - (Get-Cap 25)) + " more") }
        Write-Line ("  " + $unreadable.Count + " file(s) are not covered by any hash check below. On a synced folder this usually means a cloud placeholder or an open lock. Resolve before any Execute pass.") -ForegroundColor Yellow
    }

    Write-Section "Identical content groups (SHA-256)"
    $groups = @($hashes | Group-Object Hash | Where-Object Count -gt 1 |
        Sort-Ordinal -Key { (Get-DescKey $_.Count) + [char]0 + $_.Name })
    $glance['identical'] = $groups.Count
    if ($groups.Count) {
        $nFiles = ($groups | Measure-Object Count -Sum).Sum
        Write-Line ("  {0} groups, {1} files" -f $groups.Count, $nFiles)
        foreach ($g in ($groups | Select-Object -First (Get-Cap $groups.Count))) {
            Write-Line ("-- " + $g.Name.Substring(0, 12) + "...  (" + $g.Count + " copies)")
            $g.Group | Sort-Ordinal -Key { (Get-Short $_.Path).ToLower() } | Select-Object -First $DupCap | ForEach-Object { Write-Line ("     " + (Get-Short $_.Path)) }
            if ($g.Count -gt $DupCap) { Write-Line ("     ... and " + ($g.Count - $DupCap) + " more") }
        }
        if ($groups.Count -gt (Get-Cap $groups.Count)) { Write-Line ("  ... and " + ($groups.Count - (Get-Cap $groups.Count)) + " more groups") }
    }
    else { Write-Line "  none" }

    Write-Section "Same name, DIFFERENT content (ambiguous citation)"
    $ambiguous = @($hashes | Group-Object { $_.Name.ToLower() } |
        Where-Object { $_.Count -gt 1 -and (@($_.Group | Select-Object -ExpandProperty Hash -Unique).Count -gt 1) } |
        Sort-Ordinal -Key { (Get-DescKey $_.Count) + [char]0 + $_.Name })
    $glance['ambiguous'] = $ambiguous.Count
    if ($ambiguous.Count) {
        foreach ($g in ($ambiguous | Select-Object -First (Get-Cap 20))) {
            $members = @($g.Group | Sort-Ordinal -Key { (Get-Short $_.Path).ToLower() })
            Write-Line ("-- " + $members[0].Name)
            $members | Select-Object -First $DupCap | ForEach-Object {
                Write-Line ("     " + $_.Hash.Substring(0, 8) + "  " + (Get-Short $_.Path))
            }
            if ($members.Count -gt $DupCap) { Write-Line ("     ... and " + ($members.Count - $DupCap) + " more") }
        }
        Write-Line ("  " + $ambiguous.Count + " name(s) resolve to more than one document. Any citation by filename alone is ambiguous.") -ForegroundColor Yellow
    }
    else { Write-Line "  none" }
}

Write-Section "Claims requiring verification (open these - never trust the name)"
$claimMatchers = @($ClaimPatterns | ForEach-Object {
        [System.Management.Automation.WildcardPattern]::new($_, [System.Management.Automation.WildcardOptions]::IgnoreCase) })
$claims = [System.Collections.Generic.List[System.IO.FileInfo]]::new()
$scratchClaims = 0
foreach ($f in $files) {
    foreach ($m in $claimMatchers) {
        if ($m.IsMatch($f.Name)) {
            if (Test-HasSegment (Get-RelSlash $f.FullName) 'scratch') { $scratchClaims++ } else { $claims.Add($f) }
            break
        }
    }
}
if ($claims.Count) {
    $claims | Sort-Ordinal -Key { (Get-DescKey ([int64]([double]([System.DateTimeOffset]$_.LastWriteTimeUtc).ToUnixTimeMilliseconds()))) + [char]0 + (Get-Short $_.FullName).ToLower() } | Select-Object -First (Get-Cap 40) | ForEach-Object {
        Write-Line ("  {0:yyyy-MM-dd}  {1,9}  {2}" -f $_.LastWriteTime, $_.Length, (Get-Short $_.FullName))
    }
    if ($claims.Count -gt (Get-Cap 40)) { Write-Line ("  ... and " + ($claims.Count - (Get-Cap 40)) + " more") }
    Write-Line "  Each is verified, contradicted or unverifiable. Never upgrade unverifiable to current."
}
else { Write-Line "  none" }
if ($scratchClaims) { Write-Line ("  {0} more under scratch/ folders not listed (session working copies)." -f $scratchClaims) }

Write-Section "Possible credential-bearing files"
$secrets = @($allFiles | Where-Object { Test-SecretHintName $_.Name } | Sort-Ordinal -Key { (Get-Short $_.FullName).ToLower() })
$glance['secrets'] = $secrets.Count
if ($secrets.Count) {
    Write-Line ("  " + $secrets.Count + " file(s) matched credential-name hints:") -ForegroundColor Yellow
    $publicBundles = @($secrets | Where-Object { $_.Name.ToLower() -eq 'cacert.pem' -and (Get-Short $_.FullName).ToLower().Split('/') -contains 'certifi' })
    $ambiguousCrypto = @($secrets | Where-Object { $publicBundles -notcontains $_ -and $_.Extension.ToLower() -eq '.pem' })
    $probablePrivate = @($secrets | Where-Object { $publicBundles -notcontains $_ -and $ambiguousCrypto -notcontains $_ })
    Write-Line ("  probable private/session credential: " + $probablePrivate.Count)
    $probablePrivate | Select-Object -First (Get-Cap 25) | ForEach-Object { Write-Line ("     " + (Get-Short $_.FullName)) }
    Write-Line ("  ambiguous cryptographic material: " + $ambiguousCrypto.Count)
    $ambiguousCrypto | Select-Object -First (Get-Cap 25) | ForEach-Object { Write-Line ("     " + (Get-Short $_.FullName)) }
    Write-Line ("  recognizable public CA bundle: " + $publicBundles.Count)
    $publicBundles | Select-Object -First (Get-Cap 25) | ForEach-Object { Write-Line ("     " + (Get-Short $_.FullName)) }
    if ($secrets.Count -gt (Get-Cap 25)) { Write-Line ("     ... and " + ($secrets.Count - (Get-Cap 25)) + " more") }
    Write-Line "  Do not stage, copy, or index these. Flag to the owner before sharing the folder. Never copy a secret value into a report or journal." -ForegroundColor Yellow
}
else { Write-Line "  none detected by name" }

Write-Section "Handoff and pending-update lifecycle warnings"
$handoffs = @($files | Where-Object { $r = Get-Short $_.FullName; -not (Test-NonGoverning $r) -and ($_.Name -match '(?i)handoff|next[ _-].*prompt') })
$pendingUpdates = @($files | Where-Object { Test-PendingName $_.Name } | ForEach-Object {
        $t = Read-SmallText $_.FullName
        $st = if ($null -ne $t) { (Get-PendingInfo $t $_.Name).Status } else { $null }
        $mark = if ($st) { $st.Substring(0, 1).ToUpper() + $st.Substring(1).ToLower() } else { 'no Status:' }
        [pscustomobject]@{ Rel = (Get-RelSlash $_.FullName); Mark = $mark } } | Sort-Ordinal -Key { $_.Rel + [char]0 + $_.Mark })
$packageChannels = @($files | Where-Object { $_.Extension.ToLower() -eq '.zip' -and (Get-Short $_.FullName) -match '(?i)(candidate|superseded|release)' })
Write-Line ("  handoff/next-prompt files outside non-governing areas: " + $handoffs.Count)
Write-Limited @($handoffs | ForEach-Object { Get-RelSlash $_.FullName } | Sort-Ordinal -Key { $_ }) '    '
Write-Line ("  pending shared-update artifacts: {0} (without a Status: first line: {1})" -f $pendingUpdates.Count, @($pendingUpdates | Where-Object { $_.Mark -eq 'no Status:' }).Count)
Write-Limited @($pendingUpdates | ForEach-Object { "{0,-12} {1}" -f $_.Mark, $_.Rel }) '    '
if ($pendingUpdates.Count) { Write-Line '  Run --pending for target and base checks; a status here is only what the file records.' }
Write-Line ("  candidate/release/superseded ZIPs requiring channel review: " + $packageChannels.Count)
Write-Limited @($packageChannels | ForEach-Object { Get-RelSlash $_.FullName } | Sort-Ordinal -Key { $_ }) '    '
$glance['handoffs'] = $handoffs.Count; $glance['pending_updates'] = $pendingUpdates.Count; $glance['package_channels'] = $packageChannels.Count

Write-Section "Possible orphaned temporary files"
$orphans = @($files | ForEach-Object {
        $why = Get-OrphanReason $_
        if ($why) { [pscustomobject]@{ File = $_; Why = $why } }
    } | Sort-Ordinal -Key { (Get-Short $_.File.FullName).ToLower() })
$glance['orphans'] = $orphans.Count
if ($orphans.Count) {
    $orphans | Select-Object -First (Get-Cap 25) | ForEach-Object {
        Write-Line ("  {0,-30} {1,9}  {2}" -f $_.Why, $_.File.Length, (Get-Short $_.File.FullName))
    }
    if ($orphans.Count -gt (Get-Cap 25)) { Write-Line ("  ... and " + ($orphans.Count - (Get-Cap 25)) + " more") }
    Write-Line "  Usually left by an interrupted write. Confirm the finished copy exists before proposing removal; never delete under a standard cleanup approval."
}
else { Write-Line "  none" }

Write-Section "Large journals (threshold $JournalThresholdKB KB)"
$journalLimit = [int64]$JournalThresholdKB * 1024
$bigJournals = @($allFiles | Where-Object { $_.Name.ToLower().Contains('journal') -and $_.Length -ge $journalLimit })
$rootAgentsPath = [IO.Path]::Combine($RootFull, 'AGENTS.md')
$rootAgents = if (Test-Path -LiteralPath $rootAgentsPath -PathType Leaf) { Read-SmallText $rootAgentsPath } else { $null }
$vm = [regex]::Match([string]$rootAgents, $RulesVersionRx)
$rulesMajor = if ($vm.Success) { [int]$vm.Groups[1].Value.Split('.')[0] } else { 0 }
$qcPathMain = [IO.Path]::Combine($RootFull, 'AI_CONTEXT', 'PROJECT_QUICK_CONTEXT.md')
$qcTextMain = if (Test-Path -LiteralPath $qcPathMain -PathType Leaf) { Read-SmallText $qcPathMain } else { $null }
$contextText = [string]$rootAgents + "`n" + [string]$qcTextMain
$journals = [Collections.Generic.List[object]]::new(); $retiredJournals = [Collections.Generic.List[object]]::new()
foreach ($j in $bigJournals) {
    $why = Get-JournalRetired $j $rulesMajor $contextText
    if ($why) { $retiredJournals.Add([pscustomobject]@{ File = $j; Why = $why }) } else { $journals.Add([pscustomobject]@{ File = $j; Why = $null }) }
}
$glance['journals'] = $journals.Count
$glance['retired_journals'] = $retiredJournals.Count
$jKey = { (Get-DescKey $_.File.Length) + [char]0 + (Get-Short $_.File.FullName).ToLower() }
if ($journals.Count) {
    Write-Limited @($journals | Sort-Ordinal -Key $jKey | ForEach-Object { "{0,9}  {1}" -f $_.File.Length, (Get-Short $_.File.FullName) }) '  '
    Write-Line "  Rotation is a proposal only; preserve every entry and require approval."
}
else { Write-Line "  none" }
Write-Limited @($retiredJournals | Sort-Ordinal -Key $jKey | ForEach-Object { "retired legacy journal, {0} KB: {1} ({2}); no rotation proposed" -f [Math]::Floor($_.File.Length / 1024), (Get-Short $_.File.FullName), $_.Why }) '  '

if ($EntryPoint.Count) {
    Write-Section "Expected entrypoints"
    $missingEntry = @($EntryPoint | Where-Object { -not (Test-Path -LiteralPath (Resolve-InputPath $_)) }).Count
    foreach ($value in @($EntryPoint | Select-BriefItems)) {
        $target = Resolve-InputPath $value
        $state = if (Test-Path -LiteralPath $target) { 'PRESENT' } else { 'MISSING' }
        Write-Line ("  {0,-7}  {1}" -f $state, $value)
    }
    Write-Line "  Missing is established against this direct filesystem root only."
    $glance['missing_entry'] = $missingEntry
}

# What a cold agent must read before it can act: root auto-loaded instruction
# files plus the declared entrypoints.
Write-Section "Startup read set (budget $ReadBudgetKB KB)"
$readSet = [System.Collections.Generic.List[object]]::new()
$allFiles | Where-Object { -not (Get-RelSlash $_.FullName).Contains('/') -and ($AutoloadNames -contains $_.Name.ToLower()) } |
    Sort-Ordinal -Key { (Get-RelSlash $_.FullName).ToLower() } |
    ForEach-Object { $readSet.Add([pscustomobject]@{ Key = (Get-RelSlash $_.FullName); Size = $_.Length }) }
foreach ($value in $EntryPoint) {
    $full = Resolve-InputPath $value
    if (Test-Path -LiteralPath $full -PathType Leaf) {
        $item = Get-Item -LiteralPath $full -Force
        $key = Get-RelSlash $item.FullName
        if (-not (@($readSet | Where-Object { $_.Key.ToLower() -eq $key.ToLower() }).Count)) {
            $readSet.Add([pscustomobject]@{ Key = $key; Size = $item.Length })
        }
    }
}
$readTotal = [int64](($readSet | Measure-Object Size -Sum).Sum)
$overBudget = $readTotal -gt ([int64]$ReadBudgetKB * 1024)
if ($readSet.Count) {
    $readSet | Select-BriefItems | ForEach-Object { Write-Line ("  {0,7:F1} KB  {1}" -f ($_.Size / 1024), $_.Key) }
    Write-Line ("  Total: {0:F1} KB (about {1} tokens)" -f ($readTotal / 1024), [int64][Math]::Floor($readTotal / 4))
    if ($overBudget) { Write-Line "  OVER BUDGET: every session pays this before working. Propose a short router plus on-demand detail files; do not delete content." -ForegroundColor Yellow }
}
else { Write-Line "  none identified (pass the project's read order as entrypoints)" }

if ($Portfolio) {
    Write-Section "Portfolio root matrix (immediate children; advisory)"
    $defaults = @('AGENTS.md', 'README_FIRST.md', 'PROJECT_ROADMAP_STATUS.md',
        'AUTHORITY_MAP.md', 'INDEX.md', 'AI_CONTEXT/README_FIRST.md',
        'AI_CONTEXT/PROJECT_QUICK_CONTEXT.md', 'AI_CONTEXT/PROJECT_ACTIVITY_JOURNAL.md',
        'AI_CONTEXT/CHAT_INDEX.md')
    $checks = @($defaults + $EntryPoint | Select-Object -Unique)
    $tpl = Get-TemplateCore
    $tcore = $tpl[0]; $tver = $tpl[1]
    Write-Line "  Project | Count scope | State | Root items | Sessions | Missing index rows | Pending updates | Rules version | Work routing | Core match | Sequential writer | Section 13 complete | Entrypoints present"
    $children = @(Get-ChildItem -LiteralPath $RootFull -Directory -Force -ErrorAction SilentlyContinue | Sort-Ordinal -Key { $_.Name.ToLower() })
    if ($children.Count) {
        foreach ($child in $children) {
            $count = @(Get-ChildItem -LiteralPath $child.FullName -Force -ErrorAction SilentlyContinue).Count
            $present = @($checks | Where-Object { Test-Path -LiteralPath (Join-Path $child.FullName $_) })
            $value = if ($present.Count) { $present -join ', ' } else { '(none detected)' }
            $state = if ($count -eq 0) { 'empty' } elseif ($present.Count) { 'managed' } else { 'unmanaged' }
            $sessionDir = [IO.Path]::Combine($child.FullName, 'AI_CONTEXT', 'SESSIONS')
            $sessionCount = 0; $missingRows = 'n/a'
            if (Test-Path -LiteralPath $sessionDir -PathType Container) {
                $sessionNames = @(Get-ChildItem -LiteralPath $sessionDir -Force -ErrorAction SilentlyContinue | Where-Object { $_.Name.ToLower().EndsWith('.md') } | ForEach-Object { $_.Name })
                $sessionCount = $sessionNames.Count
                $indexText = Read-SmallText ([IO.Path]::Combine($child.FullName, 'AI_CONTEXT', 'SESSION_INDEX.md'))
                if ($null -ne $indexText) {
                    $missingRows = @($sessionNames | Where-Object {
                        $n = $_
                        -not $indexText.Contains($n) -and -not @([regex]::Matches($n, $UuidPattern) | Where-Object { $indexText.Contains($_.Value) }).Count }).Count
                }
            }
            $pend = @(Find-PendingFiles $child.FullName)
            $noStatus = @($pend | Where-Object { $t = Read-SmallText $_; ($null -eq $t) -or ($null -eq (Get-PendingInfo $t ([IO.Path]::GetFileName($_))).Status) }).Count
            $ri = Get-RulesInfo $child.FullName $tcore
            Write-Line ("  {0} | root-level | {1} | {2} | {3} | {4} | {5} ({6} no Status) | {7} | {8} | {9} | {10} | {11} | {12}" -f $child.Name, $state, $count, $sessionCount, $missingRows, $pend.Count, $noStatus, $ri[0], $ri[1], $ri[2], $ri[3], $ri[4], $value)
        }
    }
    else { Write-Line "  no immediate child directories" }
    Write-Line "  Presence does not determine authority or operational state."
    Write-Line ("  Core match compares sections 0-12 (1-12 before Rules 4.0.0) with the bundled template" + $(if ($tver) { " $tver" } else { ' (not bundled in this package: unknown)' }) + ".")
    $names = @($children | ForEach-Object { $_.Name })
    $groups = @{}
    foreach ($n in $names) {
        $b = ([regex]::Replace($n, '(?i)( \(\d+\)| - copy| copy|-copy)$', '')).ToLower()
        if (-not $groups.ContainsKey($b)) { $groups[$b] = [Collections.Generic.List[string]]::new() }
        $groups[$b].Add($n)
    }
    $twins = @($groups.Keys | Where-Object { $groups[$_].Count -gt 1 } | ForEach-Object {
            $sortedNames = @($groups[$_] | Sort-Ordinal -Key { Get-OrdinalKey $_ })
            [pscustomobject]@{ First = $sortedNames[0]; Items = $sortedNames } } | Sort-Ordinal -Key { $_.First.ToLower() })
    foreach ($v in $twins) { Write-Line ("  possible replicas under this root: " + ($v.Items -join ' ~ ')) }
    $handoffsTo = [Collections.Generic.List[string]]::new()
    $lowered = @{}; foreach ($n in $names) { $lowered[$n.ToLower()] = $n }
    $lowKeys = @($lowered.Keys | Sort-Ordinal -Key { $_ })
    foreach ($n in $names) {
        $hdir = [IO.Path]::Combine($RootFull, $n, 'Handoffs')
        if (-not (Test-Path -LiteralPath $hdir -PathType Container)) { continue }
        foreach ($h in @(Get-ChildItem -LiteralPath $hdir -Force -ErrorAction SilentlyContinue | Where-Object { $_.Name.ToLower().EndsWith('.md') } | Sort-Ordinal -Key { $_.Name })) {
            $t = Read-SmallText $h.FullName; if ($null -eq $t) { $t = '' }
            if ($t.Length -gt 4096) { $t = $t.Substring(0, 4096) }
            $m = [regex]::Match($t, $ToLineRx)
            if (-not $m.Success) { continue }
            $val = $m.Groups[1].Value.ToLower()
            foreach ($low in $lowKeys) { if ($lowered[$low] -ne $n -and $val.Contains($low)) { $handoffsTo.Add(("{0}/Handoffs/{1} -> {2}" -f $n, $h.Name, $lowered[$low])) } }
        }
    }
    Write-Line ("  handoffs addressed to another project here: {0} (check each target's Incoming/ for a copy or pointer)" -f $handoffsTo.Count)
    Write-Limited @($handoffsTo) '    '
    if (Test-Path -LiteralPath ([IO.Path]::Combine($RootFull, 'PORTFOLIO.md')) -PathType Leaf) { Write-Line '  replica declaration: PORTFOLIO.md present; read it before trusting any copy' }
    else { Write-Line '  replica declaration: none (PORTFOLIO.md); copies under other providers cannot be seen from this root' }
}

if ($DetectPointers) {
    Write-Section "Possible pointer stubs (advisory; content not authority)"
    $candidates = @($files | Where-Object { Test-PointerCandidate $_ } | Sort-Ordinal -Key { (Get-Short $_.FullName).ToLower() })
    if ($candidates.Count) {
        $candidates | Select-BriefItems | ForEach-Object { Write-Line ("  " + (Get-Short $_.FullName)) }
        Write-Line "  Verify the target exists and that the file contains no independent guidance."
    }
    else { Write-Line "  none" }
}

foreach ($manifestValue in $ExpectedUploadManifest) {
    Write-Section "Expected upload manifest: $manifestValue"
    $manifestPath = Resolve-InputPath $manifestValue
    if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
        Write-Line "  MANIFEST NOT FOUND: $manifestPath"
        continue
    }
    try { $expected = @(Get-ExpectedManifestRows $manifestPath) }
    catch { Write-Line ("  MANIFEST UNREADABLE: " + $_.Exception.GetType().Name); continue }
    $present = 0; $missing = 0; $sizeBad = 0; $hashBad = 0
    $script:ManifestDetails = 0
    function Write-ManifestDetail([string]$message) {
        $script:ManifestDetails++
        if (-not $Brief -or $script:ManifestDetails -le 10) { Write-Line $message }
    }
    foreach ($row in $expected) {
        $target = Resolve-InputPath $row.path
        if (-not (Test-Path -LiteralPath $target -PathType Leaf)) {
            $missing++; Write-ManifestDetail ("  MISSING        " + $row.path); continue
        }
        $present++
        if ($row.size) {
            [int64]$wanted = 0
            if (-not [int64]::TryParse([string]$row.size, [ref]$wanted)) {
                $sizeBad++; Write-ManifestDetail ("  BAD SIZE VALUE " + $row.path + " = '" + $row.size + "'")
            }
            else {
                $actual = (Get-Item -LiteralPath $target).Length
                if ($actual -ne $wanted) {
                    $sizeBad++; Write-ManifestDetail ("  SIZE MISMATCH  {0} expected={1} actual={2}" -f $row.path, $wanted, $actual)
                }
            }
        }
        if ($row.sha256) {
            try {
                Assert-ContentRead $target
                $actualHash = (Get-FileHash -LiteralPath $target -Algorithm SHA256 -ErrorAction Stop).Hash.ToLower()
            } catch { $hashBad++; Write-ManifestDetail ("  HASH UNCHECKED (READ BLOCKED or unreadable) " + $row.path); continue }
            if ($actualHash -ne ([string]$row.sha256).ToLower()) {
                $hashBad++; Write-ManifestDetail ("  HASH MISMATCH  " + $row.path)
            }
        }
    }
    if ($ManifestDetails -gt (Get-Cap $ManifestDetails)) { Write-Line ("  ... and " + ($ManifestDetails - (Get-Cap $ManifestDetails)) + " more") }
    Write-Line ("  Expected: {0}  Present: {1}  Missing: {2}  Size mismatches: {3}  Hash mismatches: {4}" -f $expected.Count, $present, $missing, $sizeBad, $hashBad)
    Write-Line "  This verifies listed files only; it does not authorize upload, overwrite, or promotion."
}

$brokenTotal = 0
foreach ($ip in $IndexPath) {
    Write-Section "Index link check: $ip"
    $idx = Join-Path $RootFull $ip
    if (Test-Path -LiteralPath $idx -PathType Leaf) {
        if (-not (Test-ContentReadAllowed $idx)) { Write-Line '  READ BLOCKED: index not inspected'; continue }
        # -Encoding UTF8: Windows PowerShell 5.1 otherwise reads BOM-less UTF-8
        # as ANSI and reports every non-ASCII link target as broken.
        $content = Get-Content -LiteralPath $idx -Raw -Encoding UTF8
        if ($null -eq $content) { $content = '' }
        $markdownLinks = @(Get-MarkdownTargets $content |
            ForEach-Object { Get-CleanReference $_ } |
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
        $brokenTotal += $broken.Count
        Write-Line ("  Markdown links checked: " + $markdownLinks.Count)
        $fallback = @($markdownLinks | Where-Object {
            $candidate = $_.Replace('\', '/').TrimStart('/')
            -not $_.StartsWith('/') -and -not $_.StartsWith('\') -and $_ -notmatch '^[A-Za-z]:' -and
                -not (Test-Path -LiteralPath (Join-Path $idxDir $candidate)) -and (Test-Path -LiteralPath (Join-Path $RootFull $candidate))
        })
        if ($fallback.Count) {
            Write-Line ("  ROOT-FALLBACK REFERENCES: " + $fallback.Count + " (not document-relative)")
            $fallback | Select-BriefItems | ForEach-Object { Write-Line "     $_" }
        }
        if ($broken.Count) {
            Write-Line ("  BROKEN MARKDOWN LINKS: " + $broken.Count) -ForegroundColor Yellow
            $broken | Select-Object -First (Get-Cap $broken.Count) | ForEach-Object { Write-Line "     $_" }
            if ($broken.Count -gt (Get-Cap $broken.Count)) { Write-Line ("     ... and " + ($broken.Count - (Get-Cap $broken.Count)) + " more") }
        }
        elseif ($fallback.Count) { Write-Line '  document-relative links need repair; see root fallbacks' }
        else { Write-Line "  all Markdown links resolve" }

        Write-Line ("  Backticked path references checked: " + $backtickedRefs.Count)
        if ($unresolvedRefs.Count) {
            Write-Line ("  UNRESOLVED BACKTICKED REFERENCES: " + $unresolvedRefs.Count + " (review needed)") -ForegroundColor Yellow
            $unresolvedRefs | Select-Object -First (Get-Cap $unresolvedRefs.Count) | ForEach-Object { Write-Line "     $_" }
            if ($unresolvedRefs.Count -gt (Get-Cap $unresolvedRefs.Count)) { Write-Line ("     ... and " + ($unresolvedRefs.Count - (Get-Cap $unresolvedRefs.Count)) + " more") }
            Write-Line "  These are not confirmed broken links; examples and historical labels may be intentionally non-live."
        }
        else { Write-Line "  all backticked references resolve" }

        $caseMismatched = @(@($markdownLinks + $backtickedRefs) |
            Where-Object { Test-ReferenceCaseMismatch $_ $idxDir })
        if ($caseMismatched.Count) {
            Write-Line ("  CASE-MISMATCHED REFERENCES: " + $caseMismatched.Count + " (review needed)") -ForegroundColor Yellow
            $caseMismatched | Select-BriefItems | ForEach-Object { Write-Line "     $_" }
            Write-Line "  These resolve only because this filesystem is case-insensitive. They break for an agent on Linux or a case-sensitive volume."
        }
    }
    else {
        $brokenTotal++
        Write-Line "  index NOT FOUND at $idx" -ForegroundColor Yellow
        Write-Line "  An index named in navigation but absent is a top-tier confusion source. Report it."
    }
}
if ($IndexPath.Count) { $glance['broken'] = $brokenTotal }

$unreferencedTotal = 0
foreach ($pair in $CoveragePairs) {
    $idxValue = $pair[0]; $dirValue = $pair[1]
    Write-Section "Index coverage: $idxValue <- $dirValue"
    $idx = Resolve-InputPath $idxValue
    $folder = Resolve-InputPath $dirValue
    if (-not (Test-Path -LiteralPath $idx -PathType Leaf)) { Write-Line "  index NOT FOUND: $idxValue"; continue }
    if (-not (Test-Path -LiteralPath $folder -PathType Container)) { Write-Line "  directory NOT FOUND: $dirValue"; continue }
    if (-not (Test-ContentReadAllowed $idx)) { Write-Line '  READ BLOCKED: coverage index not inspected'; continue }
    $content = Get-Content -LiteralPath $idx -Raw -Encoding UTF8
    if ($null -eq $content) { $content = '' }
    $folderRel = (Get-RelSlash ([System.IO.Path]::GetFullPath($folder))).TrimEnd('/')
    $members = @($allFiles | Where-Object { (Get-RelSlash $_.DirectoryName).TrimEnd('/') -eq $folderRel } |
        ForEach-Object { $_.Name } | Sort-Ordinal -Key { $_.ToLower() })
    $missingRefs = @($members | Where-Object { -not (Test-IndexMentions $content $_) })
    $unreferencedTotal += $missingRefs.Count
    Write-Line ("  Files directly in {0}: {1}" -f $dirValue, $members.Count)
    Write-Line ("  Mentioned by the index:  {0}" -f ($members.Count - $missingRefs.Count))
    if ($missingRefs.Count) {
        Write-Line ("  NOT MENTIONED: " + $missingRefs.Count) -ForegroundColor Yellow
        $missingRefs | Select-Object -First (Get-Cap $missingRefs.Count) | ForEach-Object { Write-Line "     $_" }
        if ($missingRefs.Count -gt (Get-Cap $missingRefs.Count)) { Write-Line ("     ... and " + ($missingRefs.Count - (Get-Cap $missingRefs.Count)) + " more") }
        Write-Line "  An index that omits existing files tells the next agent they do not exist. Regenerate or append; never infer absence from an index."
    }
    else { Write-Line "  every file is mentioned" }
}
if ($CoveragePairs.Count) { $glance['unreferenced'] = $unreferencedTotal }

Write-Section "Embedded skill copies"
$skills = @($allFiles | ForEach-Object {
        $low = $_.Name.ToLower()
        if ($low -eq 'skill.md') {
            $id = Get-SkillIdentity $_.FullName
            [pscustomobject]@{ Name = $id[0]; Version = $id[1]; Path = $_.FullName }
        }
        elseif ($low.EndsWith('.skill')) {
            [pscustomobject]@{ Name = [System.IO.Path]::GetFileNameWithoutExtension($_.Name); Version = '(packaged)'; Path = $_.FullName }
        }
    } | Sort-Ordinal -Key { $_.Name.ToLower() + [char]0 + (Get-Short $_.Path).ToLower() })
$multi = @($skills | Group-Object { $_.Name.ToLower() } | Where-Object Count -gt 1 | Sort-Ordinal -Key { $_.Name })
$glance['skills'] = @($skills.Count, $multi.Count)
if ($skills.Count) {
    $skills | Select-Object -First (Get-Cap 40) | ForEach-Object { Write-Line ("  {0}  {1}  {2}" -f $_.Name, $_.Version, (Get-Short $_.Path)) }
    if ($skills.Count -gt (Get-Cap 40)) { Write-Line ("  ... and " + ($skills.Count - (Get-Cap 40)) + " more") }
    foreach ($g in @($multi | Select-BriefItems)) {
        [string[]]$vers = @($g.Group | ForEach-Object { $_.Version } | Select-Object -Unique)
        [Array]::Sort($vers, [System.StringComparer]::Ordinal)
        Write-Line ("  {0} copies of {1} (versions: {2})" -f $g.Count, $g.Name, ($vers -join ', '))
    }
    Write-Line "  Copies inside a project are not installed skills. Hosts that scan .codex/skills, .claude/skills or .agents/skills folders may load them. Compare against the canonical release before using any copy."
}
else { Write-Line "  none" }

Write-Section "Instruction files found"
$instr = @($allFiles | Where-Object { $InstructionNames -contains $_.Name.ToLower() } | Sort-Ordinal -Key { (Get-Short $_.FullName).ToLower() })
$autoload = @($instr | Where-Object { $AutoloadNames -contains $_.Name.ToLower() })
$readmes = @($instr | Where-Object { $ReadmeNames -contains $_.Name.ToLower() })
$misplaced = @($autoload | Where-Object { Test-NonGoverning (Get-RelSlash $_.FullName) })
$oversized = @($autoload | Where-Object { $_.Name.ToLower() -eq 'agents.md' -and $_.Length -gt $CodexDocLimit })
$agentsWarn = @($autoload | Where-Object { $_.Name.ToLower() -eq 'agents.md' -and $_.Length -gt $AgentsWarnBytes -and $_.Length -le $CodexDocLimit })
$glance['misplaced'] = $misplaced.Count
$glance['oversized'] = $oversized.Count
$glance['agents_warn'] = $agentsWarn.Count
if ($instr.Count) {
    Write-Line "  Auto-loaded names:"
    if ($autoload.Count) {
        $autoload | Select-Object -First (Get-Cap 40) | ForEach-Object { Write-Line ("  {0:yyyy-MM-dd}  {1,9}  {2}" -f $_.LastWriteTime, $_.Length, (Get-Short $_.FullName)) }
        if ($autoload.Count -gt (Get-Cap 40)) { Write-Line ("  ... and " + ($autoload.Count - (Get-Cap 40)) + " more") }
    }
    else { Write-Line "     none" }
    Write-Line ("  README / startup files: " + $readmes.Count)
    $readmes | Select-Object -First (Get-Cap 15) | ForEach-Object { Write-Line ("  {0:yyyy-MM-dd}  {1,9}  {2}" -f $_.LastWriteTime, $_.Length, (Get-Short $_.FullName)) }
    if ($readmes.Count -gt (Get-Cap 15)) { Write-Line ("  ... and " + ($readmes.Count - (Get-Cap 15)) + " more") }
    # Root level only, like audit_folder.py: nested files legitimately scope a subtree.
    $rootAgentFiles = @($instr | Where-Object {
            $_.Name.ToLower() -ne 'readme.md' -and -not (Get-RelSlash $_.FullName).Contains('/') })
    if ($rootAgentFiles.Count -gt 1) {
        Write-Line "  Multiple root-level agent-instruction files - check for conflicting scope. Record the conflict; resolve none unilaterally." -ForegroundColor Yellow
    }
    foreach ($mp in @($misplaced | Select-BriefItems)) { Write-Line ("  LIVE-LOADING NAME IN NON-GOVERNING LOCATION: " + (Get-Short $mp.FullName)) -ForegroundColor Yellow }
    if ($misplaced.Count) { Write-Line "  A host that walks the tree may load these as rules. Propose a non-loading name such as AGENTS.proposed.md; never rename without approval." }
    foreach ($ov in @($oversized | Select-BriefItems)) { Write-Line ("  OVER 32 KiB ({0} bytes): {1}" -f $ov.Length, (Get-Short $ov.FullName)) -ForegroundColor Yellow }
    if ($oversized.Count) { Write-Line "  Codex reads at most 32 KiB of AGENTS.md by default and silently drops the rest. Propose a shorter file that links to on-demand detail." }
    foreach ($aw in @($agentsWarn | Select-BriefItems)) { Write-Line ("  OVER 16 KB, warning ({0} bytes): {1}" -f $aw.Length, (Get-Short $aw.FullName)) }
    if ($agentsWarn.Count) { Write-Line "  Little headroom before the 32 KiB Codex limit once project clauses are added." }
}
else {
    Write-Line "  NONE FOUND ANYWHERE." -ForegroundColor Yellow
    Write-Line "  No AGENTS.md / CLAUDE.md / README.md in the tree means every agent's instructions live outside the folder and cannot be read by the next one. Report this as a finding."
}

Write-Section "Sync copies, unpacked packages and continuity folders"
$relsFiles = @($files | ForEach-Object { Get-RelSlash $_.FullName })
$confMain = Write-ConflictBlock $relsFiles
$glance['copies'] = $confMain[0]; $glance['collisions'] = $confMain[1]
$unpacked = @($relsFiles | Where-Object { $_.Split('/')[-1].ToLower() -eq 'skill.md' -and (Test-NonGoverning $_) } | Sort-Ordinal -Key { Get-OrdinalKey $_ })
$glance['unpacked'] = $unpacked.Count
Write-Line ("  unpacked skill trees under scratch/backup/history/incoming: {0}" -f $unpacked.Count)
Write-Limited $unpacked '    '
if ($unpacked.Count) { Write-Line '    Keep staged or backup packages as ZIP + SHA256SUMS, or rename SKILL.md to a non-loading name.' }
$repos = @(Get-RepoFoldersWithoutGit $relsFiles)
$glance['repos'] = $repos.Count
Write-Line ("  repository-shaped folders without .git: {0}" -f $repos.Count)
Write-Limited $repos '    '
if ($repos.Count) { Write-Line '    A working copy, not a clone: the index should name the remote and the commit or tag it mirrors.' }
$misuse = @(Get-AiContextMisuse @($files | ForEach-Object { [pscustomobject]@{ Rel = (Get-RelSlash $_.FullName); Size = $_.Length } }))
$glance['ai_context'] = $misuse.Count
$misuseBytes = [int64](($misuse | Measure-Object Size -Sum).Sum)
Write-Line ("  AI_CONTEXT/ files that are not continuity records: {0} ({1} KB)" -f $misuse.Count, [Math]::Floor($misuseBytes / 1024))
Write-Limited @($misuse | ForEach-Object { "{0,-13} {1,9}  {2}" -f $_.Why, $_.Size, $_.Rel }) '    '
if ($misuse.Count) { Write-Line '    Propose a content folder the index names (for example Research/ or Proposals/); move nothing in Audit mode.' }

Write-Section "Findings at a glance"
function Write-GlanceRow([string]$label, $value) { Write-Line ("  {0,-32} {1}" -f $label, $value) }
if ($glance.ContainsKey('broken')) { Write-GlanceRow 'Broken index links / indexes:' $glance['broken'] }
if ($glance.ContainsKey('unreferenced')) { Write-GlanceRow 'Files missing from indexes:' $glance['unreferenced'] }
if ($glance.ContainsKey('missing_entry')) { Write-GlanceRow 'Missing entrypoints:' $glance['missing_entry'] }
$readText = if ($readSet.Count) { ("{0:F1} KB" -f ($readTotal / 1024)) + $(if ($overBudget) { ' OVER BUDGET' } else { '' }) } else { 'not identified' }
Write-GlanceRow 'Startup read set:' $readText
Write-GlanceRow 'AGENTS.md over 32 KiB:' $glance['oversized']
Write-GlanceRow 'AGENTS.md over 16 KB (warning):' $glance['agents_warn']
Write-GlanceRow 'Misplaced live-loading names:' $glance['misplaced']
Write-GlanceRow 'Embedded skill copies:' ("{0} ({1} name(s) with several copies)" -f $glance['skills'][0], $glance['skills'][1])
Write-GlanceRow 'Possible orphaned temp files:' $glance['orphans']
Write-GlanceRow 'Path length risks:' $glance['long']
Write-GlanceRow 'Identical content groups:' $(if ($glance.ContainsKey('identical')) { $glance['identical'] } else { 'not hashed' })
Write-GlanceRow 'Same name, different content:' $(if ($glance.ContainsKey('ambiguous')) { $glance['ambiguous'] } else { 'not hashed' })
Write-GlanceRow 'Credential-name hints:' $glance['secrets']
Write-GlanceRow 'Handoff / next-prompt files:' $glance['handoffs']
Write-GlanceRow 'Pending shared-update artifacts:' $glance['pending_updates']
Write-GlanceRow 'Package-channel review items:' $glance['package_channels']
Write-GlanceRow 'Large journals:' $glance['journals']
Write-GlanceRow 'Retired journals (no rotation):' $glance['retired_journals']
Write-GlanceRow 'Sync conflict copies:' $glance['copies']
Write-GlanceRow 'Case-only name collisions:' $glance['collisions']
Write-GlanceRow 'Unpacked skill trees:' $glance['unpacked']
Write-GlanceRow 'Repo folders without .git:' $glance['repos']
Write-GlanceRow 'AI_CONTEXT non-continuity files:' $glance['ai_context']
Write-Line "  Counts only. Open the matching section before acting on any of them."

Write-Line ""
if ($Exclude.Count) {
    $exTotal = ($excludedCounts.Values | Measure-Object -Sum).Sum
    if ($null -eq $exTotal) { $exTotal = 0 }
    Write-Line ("Coverage: {0} of {1} files examined in detail; {2} excluded by -Exclude and classified by nothing. Say so in the report." -f $files.Count, $allFiles.Count, $exTotal)
}
if ($unreadableDirs.Count) {
    Write-Line ("Coverage gap: {0} director{1} could not be read; their contents are in no count." -f $unreadableDirs.Count, $(if ($unreadableDirs.Count -eq 1) { 'y' } else { 'ies' }))
}
if ($pruned.Count) {
    Write-Line ("Coverage gap: {0} director{1} pruned as generated state; their contents are in no count." -f $pruned.Count, $(if ($pruned.Count -eq 1) { 'y was' } else { 'ies were' }))
}
if ($unvisited) {
    Write-Line ("Coverage gap: walk stopped at the {0} s budget; {1} queued directories were never visited." -f $MaxSeconds, $unvisited)
}
Write-Line ""
Write-Line "Audit complete. Nothing was written to $RootFull." -ForegroundColor Green

if ($Out) {
    $utf8 = [System.Text.UTF8Encoding]::new($false)
    $stream = [System.IO.File]::Open($OutFull, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write)
    try {
        $bytes = $utf8.GetBytes((($script:ReportLines) -join "`n") + "`n")
        $stream.Write($bytes, 0, $bytes.Length)
    } finally { $stream.Dispose() }
    $keep = @('Summary', 'Findings at a glance')
    $on = $true
    foreach ($ln in $script:ReportLines) {
        if ($ln.StartsWith('== ') -and $ln.EndsWith(' ==')) {
            $on = $keep -contains $ln.Substring(3, $ln.Length - 6)
            if ($on) { Write-Host "" }
        }
        if ($ln.StartsWith('Coverage') -or $ln.StartsWith('Audit complete') -or $ln.StartsWith('Walk ')) { $on = $true }
        if ($on -and $ln.Trim()) { Write-Host $ln }
    }
    Write-Host ""
    Write-Host ("Full report: {0} ({1} lines). Read sections from it as needed." -f $OutFull, $script:ReportLines.Count)
}
