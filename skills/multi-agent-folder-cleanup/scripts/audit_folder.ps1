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
    [switch]$Version
)

$ScriptVersion = '1.4.0'   # must equal SKILL.md metadata.version
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
    return [bool](($file.Attributes -band [IO.FileAttributes]::Offline) -or
        ($file.Attributes.value__ -band 0x40000) -or ($file.Attributes.value__ -band 0x400000))
}
function Get-OrphanReason($file) {
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

Write-Line "Read-only audit of $RootFull"
Write-Line "Generated $(Get-Date -Format 'yyyy-MM-dd HH:mm')"

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
    Write-Line "  Generated state, not evidence. Still synced and indexed by cloud providers."
}

if ($Exclude.Count) {
    Write-Section "Excluded from detail sections (counted, not examined)"
    foreach ($k in ($excludedCounts.GetEnumerator() | Sort-Ordinal -Key { (Get-DescKey $_.Value) + [char]0 + $_.Key })) {
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
    foreach ($rd in ($reparseDirs | Sort-Ordinal -Key { (Get-Short $_.FullName).ToLower() })) {
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
    foreach ($z in ($archives | Where-Object { $_.Extension -eq '.zip' })) {
        Write-Line ("-- " + (Get-Short $z.FullName))
        try {
            $zip = [System.IO.Compression.ZipFile]::OpenRead($z.FullName)
            try {
                Write-Line ("   entries: " + $zip.Entries.Count)
                $bad = @($zip.Entries | Where-Object { $_.FullName -match '[:*?"<>|]' -or $_.FullName -match '^(/|\\|\.\.)' })
                if ($bad.Count) { Write-Line ("   INVALID/UNSAFE NAMES: " + $bad.Count) -ForegroundColor Yellow }
                $longE = @($zip.Entries | Where-Object { ($HostBase.Length + 1 + $_.FullName.Length) -gt $PathThreshold })
                if ($longE.Count) { Write-Line ("   would exceed path threshold: " + $longE.Count) -ForegroundColor Yellow }
                $zip.Entries | Select-Object -First $memberCap -ExpandProperty FullName | ForEach-Object { Write-Line "     $_" }
                if ($zip.Entries.Count -gt $memberCap) { Write-Line "     ..." }
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
    $hashes = foreach ($f in $files) {
        try {
            [pscustomobject]@{
                Path = $f.FullName
                Name = $f.Name
                Hash = (Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256).Hash.ToLower()
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
        $unreadable | Select-Object -First (Get-Cap 25) | ForEach-Object { Write-Line ("  " + (Get-Short $_)) }
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
    $secrets | Select-Object -First (Get-Cap 25) | ForEach-Object { Write-Line ("     " + (Get-Short $_.FullName)) }
    if ($secrets.Count -gt (Get-Cap 25)) { Write-Line ("     ... and " + ($secrets.Count - (Get-Cap 25)) + " more") }
    Write-Line "  Do not stage, copy, or index these. Flag to the owner before sharing the folder. Never copy a secret value into a report or journal." -ForegroundColor Yellow
}
else { Write-Line "  none detected by name" }

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
$journals = @($allFiles | Where-Object { $_.Name.ToLower().Contains('journal') -and $_.Length -ge $journalLimit })
$glance['journals'] = $journals.Count
if ($journals.Count) {
    $journals | Sort-Ordinal -Key { (Get-DescKey $_.Length) + [char]0 + (Get-Short $_.FullName).ToLower() } | ForEach-Object {
        Write-Line ("  {0,9}  {1}" -f $_.Length, (Get-Short $_.FullName))
    }
    Write-Line "  Rotation is a proposal only; preserve every entry and require approval."
}
else { Write-Line "  none" }

if ($EntryPoint.Count) {
    Write-Section "Expected entrypoints"
    $missingEntry = 0
    foreach ($value in $EntryPoint) {
        $target = Resolve-InputPath $value
        $state = if (Test-Path -LiteralPath $target) { 'PRESENT' } else { 'MISSING' }
        if ($state -eq 'MISSING') { $missingEntry++ }
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
    foreach ($r in $readSet) { Write-Line ("  {0,7:F1} KB  {1}" -f ($r.Size / 1024), $r.Key) }
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
    Write-Line "  Project | Count scope | Root items | Entrypoints present"
    $children = @(Get-ChildItem -LiteralPath $RootFull -Directory -Force -ErrorAction SilentlyContinue | Sort-Ordinal -Key { $_.Name.ToLower() })
    if ($children.Count) {
        foreach ($child in $children) {
            $count = @(Get-ChildItem -LiteralPath $child.FullName -Force -ErrorAction SilentlyContinue).Count
            $present = @($checks | Where-Object { Test-Path -LiteralPath (Join-Path $child.FullName $_) })
            $value = if ($present.Count) { $present -join ', ' } else { '(none detected)' }
            Write-Line ("  {0} | root-level | {1} | {2}" -f $child.Name, $count, $value)
        }
    }
    else { Write-Line "  no immediate child directories" }
    Write-Line "  Presence does not determine authority or operational state."
}

if ($DetectPointers) {
    Write-Section "Possible pointer stubs (advisory; content not authority)"
    $candidates = @($files | Where-Object { Test-PointerCandidate $_ } | Sort-Ordinal -Key { (Get-Short $_.FullName).ToLower() })
    if ($candidates.Count) {
        $candidates | ForEach-Object { Write-Line ("  " + (Get-Short $_.FullName)) }
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
    foreach ($row in $expected) {
        $target = Resolve-InputPath $row.path
        if (-not (Test-Path -LiteralPath $target -PathType Leaf)) {
            $missing++; Write-Line ("  MISSING        " + $row.path); continue
        }
        $present++
        if ($row.size) {
            [int64]$wanted = 0
            if (-not [int64]::TryParse([string]$row.size, [ref]$wanted)) {
                $sizeBad++; Write-Line ("  BAD SIZE VALUE " + $row.path + " = '" + $row.size + "'")
            }
            else {
                $actual = (Get-Item -LiteralPath $target).Length
                if ($actual -ne $wanted) {
                    $sizeBad++; Write-Line ("  SIZE MISMATCH  {0} expected={1} actual={2}" -f $row.path, $wanted, $actual)
                }
            }
        }
        if ($row.sha256) {
            $actualHash = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLower()
            if ($actualHash -ne ([string]$row.sha256).ToLower()) {
                $hashBad++; Write-Line ("  HASH MISMATCH  " + $row.path)
            }
        }
    }
    Write-Line ("  Expected: {0}  Present: {1}  Missing: {2}  Size mismatches: {3}  Hash mismatches: {4}" -f $expected.Count, $present, $missing, $sizeBad, $hashBad)
    Write-Line "  This verifies listed files only; it does not authorize upload, overwrite, or promotion."
}

$brokenTotal = 0
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
        $brokenTotal += $broken.Count
        Write-Line ("  Markdown links checked: " + $markdownLinks.Count)
        if ($broken.Count) {
            Write-Line ("  BROKEN MARKDOWN LINKS: " + $broken.Count) -ForegroundColor Yellow
            $broken | Select-Object -First (Get-Cap $broken.Count) | ForEach-Object { Write-Line "     $_" }
            if ($broken.Count -gt (Get-Cap $broken.Count)) { Write-Line ("     ... and " + ($broken.Count - (Get-Cap $broken.Count)) + " more") }
        }
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
            $caseMismatched | ForEach-Object { Write-Line "     $_" }
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
    foreach ($g in $multi) {
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
$glance['misplaced'] = $misplaced.Count
$glance['oversized'] = $oversized.Count
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
    foreach ($mp in $misplaced) { Write-Line ("  LIVE-LOADING NAME IN NON-GOVERNING LOCATION: " + (Get-Short $mp.FullName)) -ForegroundColor Yellow }
    if ($misplaced.Count) { Write-Line "  A host that walks the tree may load these as rules. Propose a non-loading name such as AGENTS.proposed.md; never rename without approval." }
    foreach ($ov in $oversized) { Write-Line ("  OVER 32 KiB ({0} bytes): {1}" -f $ov.Length, (Get-Short $ov.FullName)) -ForegroundColor Yellow }
    if ($oversized.Count) { Write-Line "  Codex reads at most 32 KiB of AGENTS.md by default and silently drops the rest. Propose a shorter file that links to on-demand detail." }
}
else {
    Write-Line "  NONE FOUND ANYWHERE." -ForegroundColor Yellow
    Write-Line "  No AGENTS.md / CLAUDE.md / README.md in the tree means every agent's instructions live outside the folder and cannot be read by the next one. Report this as a finding."
}

Write-Section "Findings at a glance"
function Write-GlanceRow([string]$label, $value) { Write-Line ("  {0,-32} {1}" -f $label, $value) }
if ($glance.ContainsKey('broken')) { Write-GlanceRow 'Broken index links / indexes:' $glance['broken'] }
if ($glance.ContainsKey('unreferenced')) { Write-GlanceRow 'Files missing from indexes:' $glance['unreferenced'] }
if ($glance.ContainsKey('missing_entry')) { Write-GlanceRow 'Missing entrypoints:' $glance['missing_entry'] }
$readText = if ($readSet.Count) { ("{0:F1} KB" -f ($readTotal / 1024)) + $(if ($overBudget) { ' OVER BUDGET' } else { '' }) } else { 'not identified' }
Write-GlanceRow 'Startup read set:' $readText
Write-GlanceRow 'AGENTS.md over 32 KiB:' $glance['oversized']
Write-GlanceRow 'Misplaced live-loading names:' $glance['misplaced']
Write-GlanceRow 'Embedded skill copies:' ("{0} ({1} name(s) with several copies)" -f $glance['skills'][0], $glance['skills'][1])
Write-GlanceRow 'Possible orphaned temp files:' $glance['orphans']
Write-GlanceRow 'Path length risks:' $glance['long']
Write-GlanceRow 'Identical content groups:' $(if ($glance.ContainsKey('identical')) { $glance['identical'] } else { 'not hashed' })
Write-GlanceRow 'Same name, different content:' $(if ($glance.ContainsKey('ambiguous')) { $glance['ambiguous'] } else { 'not hashed' })
Write-GlanceRow 'Credential-name hints:' $glance['secrets']
Write-GlanceRow 'Large journals:' $glance['journals']
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
