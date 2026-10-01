#!/usr/bin/env python3
"""Read-only inventory of a project folder for multi-agent cleanup.

Writes nothing to the target folder. Mirrors audit_folder.ps1 for
macOS/Linux/NAS use, or Windows without PowerShell.

Usage:
    python audit_folder.py --root /path/to/folder --index-path INDEX.md --hash-files

Noise control:
    Generated machine state (browser profiles, caches, __pycache__, .git
    internals, node_modules) can outnumber real documents 3:1 and drown the
    duplicate and per-folder sections. --exclude keeps such paths OUT of the
    detail sections while still COUNTING them, so coverage is never silently
    downgraded. --suggest-excludes reports likely noise clusters without
    excluding anything.

    python audit_folder.py --root . --exclude 'tmp/**' --exclude '**/__pycache__/**'

Token and time control (v1.4):
    --brief          cap every list at 10 lines.
    --out FILE       write the full report to FILE (outside the root) and print
                     only the summary and the findings-at-a-glance block.
    --prune-noise    do not descend into high-confidence generated state
                     (.git, node_modules, Python environments, caches); listed,
                     never counted.
    --max-seconds N  stop walking after N seconds and disclose the gap.
    --host-root P    measure path length against the real host path P (e.g. the
                     Windows path of a folder mounted elsewhere).
"""

import argparse
import contextlib
import io
import csv
import fnmatch
import hashlib
import os
import re
import sys
import time
import urllib.parse
import zipfile
from collections import defaultdict
from datetime import datetime

VERSION = "1.4.0"  # must equal SKILL.md metadata.version

ARCHIVE_EXT = {".zip", ".7z", ".rar", ".tar", ".gz", ".tgz"}

# Names that hosts load as agent instructions automatically. Basename match,
# case-insensitive. A copy of one of these inside an incoming, history or
# scratch folder can be loaded as live rules by a host that walks the tree.
AUTOLOAD_INSTRUCTION_NAMES = {
    "agents.md", "claude.md", "gemini.md", "copilot-instructions.md",
    "cursor.md", ".cursorrules", ".windsurfrules",
}
# Startup documents an agent may be told to read; never auto-loaded.
README_INSTRUCTION_NAMES = {"readme.md", "readme_first.md", "read_me_first.md", "contributing.md"}
INSTRUCTION_NAMES = AUTOLOAD_INSTRUCTION_NAMES | README_INSTRUCTION_NAMES

# Codex reads at most this many bytes of project docs by default
# (project_doc_max_bytes) and silently drops the rest.
CODEX_DOC_LIMIT = 32768

# Path segments that mark material as non-governing (proposals, history, scratch).
NON_GOVERNING_TOKENS = ("incoming", "inbox", "history", "archive", "scratch",
                        "quarantine", "backup", "staging", "unreviewed",
                        "proposed", "skill copies", "superseded")

LIST_CAP_BRIEF = 10

# Names that CLAIM current state or authority. These must be opened and
# verified against artifacts (workflow.md B2) - never trusted from the name.
CLAIM_PATTERNS = [
    "*authority*", "*status*", "*index*", "*manifest*", "*inventory*",
    "*handoff*", "*final*", "*current*", "*roadmap*", "*quick_context*",
    "*state*", "*_v[0-9]*", "*latest*", "*master*", "*policy*", "*summary*",
]

# Directory names that are almost always generated machine state, not evidence.
NOISE_DIR_HINTS = [
    "__pycache__", "node_modules", ".git", ".svn", ".venv", "venv",
    ".mypy_cache", ".pytest_cache", ".ruff_cache", ".tox", ".idea", ".vscode",
    "chrome-profile", "edge-profile", "firefox-profile", "puppeteer",
    "playwright", "browser-profile", "cache", "caches", "logs", "dist",
    "build", ".next", ".terraform", "site-packages", "__pypackages__",
]

# Noise names that recur at many depths. Suggest one '**/name/**' pattern
# instead of one pattern per location.
GLOBAL_NOISE = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "node_modules"}

# Generated state safe to leave unwalked under --prune-noise. Deliberately
# narrower than NOISE_DIR_HINTS: 'logs', 'build', 'dist' and 'cache' can hold
# real project material and are always walked.
PRUNE_SAFE = {"__pycache__", "node_modules", ".git", ".svn", ".venv", "venv",
              ".mypy_cache", ".pytest_cache", ".ruff_cache", ".tox", ".next",
              ".terraform", "site-packages", "__pypackages__"}

# Temporary-file names left behind by interrupted writes.
ORPHAN_TEMP_RULES = [
    (re.compile(r"^zi[A-Za-z0-9]{6}$"), "Info-ZIP temp name"),
    (re.compile(r"^~\$"), "Office lock/temp"),
    (re.compile(r"^\.~lock\..*#$"), "LibreOffice lock"),
    (re.compile(r"(?i)\.(tmp|temp|partial|crdownload)$"), "temporary extension"),
]
ARCHIVE_MAGIC = (b"PK\x03\x04", b"7z\xbc\xaf\x27\x1c", b"Rar!")
CLOUD_ONLY_ATTRS = 0x1000 | 0x40000 | 0x400000  # Offline, RecallOnOpen, RecallOnDataAccess

UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.IGNORECASE)

# Files inside a browser profile that may hold live session credentials.
SECRET_HINT_NAMES = {
    "cookies", "cookies-journal", "login data", "login data-journal",
    "web data", "local state", "credentials", ".env", "id_rsa", "token.json",
    "secrets.json", ".npmrc", ".pypirc", "credentials.json",
    "id_ed25519", "id_ecdsa", "id_dsa", ".netrc", "_netrc", ".git-credentials",
}

# Key and vault containers flagged by extension. Name-only; never opened.
SECRET_HINT_EXTENSIONS = {".pem", ".key", ".pfx", ".p12", ".kdbx", ".ppk", ".jks", ".keystore"}

# Browser engines and tools add account/profile suffixes to these names. Match
# only when the prefix is followed by a separator, so an unrelated word such as
# "cookiesheet.md" is not swept in.
SECRET_HINT_PREFIX_RULES = {
    "cookies": (" ", "-", "_"),
    "login data": (" ", "-", "_"),
    "web data": (" ", "-", "_"),
    ".env": (".", "-", "_"),
    "credentials": (" ", "-", "_", "."),
}

# [text](target), [text](<target with spaces>), [text](target "title").
MARKDOWN_LINK_RE = re.compile(
    r"""\]\(\s*(<[^>\r\n]+>|[^)\s]+)(?:\s+(?:"[^"]*"|'[^']*'))?\s*\)""")
BACKTICK_PATH_RE = re.compile(r"`([^`\r\n]+\.[A-Za-z0-9]{1,8})`")


def section(title):
    print(f"\n== {title} ==")


def rel(path, root):
    if not path.startswith(root):
        return path
    tail = path[len(root):].lstrip("\\/").replace(os.sep, "/")
    return "./" + tail if tail else "."


def relslash(path, root):
    """Root-relative path with '/' separators.

    Do NOT use lstrip("./" ) here: it strips any leading '.' or '/' characters,
    so '.env' becomes 'env' and '.git/config' becomes 'git/config' - which
    silently breaks --exclude '.git/**' and misreports every dotfile.
    """
    out = path[len(root):] if path.startswith(root) else path
    return out.lstrip(os.sep).lstrip("/").replace(os.sep, "/")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


FILE_ATTRIBUTE_REPARSE_POINT = 0x400


# Bit 29 of a reparse tag marks a "name surrogate": the entry stands for another
# path (junction 0xA0000003, symlink 0xA000000C). Cloud-file tags used by
# OneDrive Files On-Demand (0x9000xxxA) are NOT name surrogates: those
# directories hold real project content and must be walked, not skipped.
IO_REPARSE_TAG_NAME_SURROGATE = 0x20000000


def _is_windows_reparse(path):
    """Detect a Windows junction or directory symlink, which os.path.islink
    misses on older Pythons. A plain FILE_ATTRIBUTE_REPARSE_POINT test is not
    enough: OneDrive marks ordinary synced folders as reparse points too."""
    try:
        st = os.lstat(path)
        attrs = st.st_file_attributes
    except (AttributeError, OSError):
        return False
    if not attrs & FILE_ATTRIBUTE_REPARSE_POINT:
        return False
    tag = getattr(st, "st_reparse_tag", None)
    if tag is None:
        return True  # cannot tell; treat conservatively as a link
    return bool(tag & IO_REPARSE_TAG_NAME_SURROGATE)


def is_env_root(dirnames, filenames):
    """A Python environment or pip --target install: pyvenv.cfg, or three or
    more *.dist-info folders side by side."""
    if any(f.lower() == "pyvenv.cfg" for f in filenames):
        return True
    return sum(1 for d in dirnames if d.lower().endswith(".dist-info")) >= 3


class WalkResult:
    def __init__(self):
        self.files = []
        self.folders = 0
        self.empty_folders = []
        self.metadata_failures = []
        self.reparse_points = []
        self.unreadable_dirs = []
        self.env_roots = []
        self.pruned = []
        self.unvisited = 0


def collect(root, prune_noise=False, max_seconds=0.0):
    """Explicit stack walk (the same shape as audit_folder.ps1).

    Directory symlinks and Windows junctions are recorded, never followed: an
    unreported skip becomes the claim "not project contents", and on a synced
    root the provider may have materialized the target as real cloud files
    that every Graph-indexed agent sees. Unreadable directories are recorded
    because a skipped subtree is a hole in every count. --prune-noise leaves
    high-confidence generated state unwalked and lists it; --max-seconds stops
    the walk and reports how many queued directories were never visited.
    """
    res = WalkResult()
    started = time.monotonic()
    stack = [root]
    while stack:
        if max_seconds and time.monotonic() - started > max_seconds:
            res.unvisited = len(stack)
            break
        dirpath = stack.pop()
        try:
            with os.scandir(dirpath) as it:
                entries = list(it)
        except OSError as exc:
            res.unreadable_dirs.append((dirpath, exc.__class__.__name__))
            continue
        dirnames, filenames = [], []
        for e in entries:
            try:
                is_dir = e.is_dir()
            except OSError:
                is_dir = False
            (dirnames if is_dir else filenames).append(e.name)
        res.folders += len(dirnames)
        if dirpath != root and not entries:
            res.empty_folders.append(dirpath)
        env_here = dirpath != root and is_env_root(dirnames, filenames)
        if env_here:
            res.env_roots.append(dirpath)
        env_pruned = 0
        for d in sorted(dirnames):
            full = os.path.join(dirpath, d)
            if os.path.islink(full) or _is_windows_reparse(full):
                target = ""
                try:
                    target = os.readlink(full)
                except OSError:
                    try:
                        target = os.path.realpath(full)
                    except OSError:
                        target = "<unreadable>"
                res.reparse_points.append((full, target))
                continue
            if prune_noise and env_here:
                env_pruned += 1
                continue
            if prune_noise and (d.lower() in PRUNE_SAFE or d.lower().startswith(NOISE_PREFIX_HINTS)):
                res.pruned.append((full, "generated state"))
                continue
            stack.append(full)
        if env_pruned:
            # One line per environment, not one per package folder.
            res.pruned.append((dirpath, f"Python environment ({env_pruned} subfolders)"))
        for name in filenames:
            full = os.path.join(dirpath, name)
            try:
                st = os.stat(full, follow_symlinks=False)
            except OSError as exc:
                res.metadata_failures.append((full, exc.__class__.__name__))
                continue
            res.files.append((full, st.st_size, st.st_mtime))
    res.metadata_failures.sort()
    res.unreadable_dirs.sort()
    res.reparse_points.sort()
    res.env_roots.sort()
    res.pruned.sort()
    return res


# Only these may match as a prefix (e.g. 'chrome-profile-2'). Everything else
# in NOISE_DIR_HINTS must match the whole segment exactly.
NOISE_PREFIX_HINTS = ("chrome-profile", "edge-profile", "firefox-profile",
                      "browser-profile", "puppeteer", "playwright")


def is_noise_segment(seg):
    s = seg.lower()
    return s in NOISE_DIR_HINTS or s.startswith(NOISE_PREFIX_HINTS)


_GLOB_CACHE = {}


def glob_regex(pat):
    """Translate an --exclude glob into a segment-aware, case-insensitive regex.

    Semantics (identical in audit_folder.ps1):
      *      any characters within ONE path segment
      ?      one character within a segment
      **/    zero or more whole leading segments ('**/logs/**' matches 'logs/a')
      /**    everything below ('tmp/**')
      [..]   character class
    A pattern with no '/' is matched against every path segment, so '*.log'
    matches at any depth and a bare 'tmp' matches any folder named tmp. Matching
    is case-insensitive because the primary targets (Windows, OneDrive,
    SharePoint, default macOS volumes) are case-insensitive.
    """
    cached = _GLOB_CACHE.get(pat)
    if cached:
        return cached
    p = pat.replace("\\", "/").strip()
    anchored = "/" in p.rstrip("/")
    p = p.rstrip("/") if p != "/" else p
    out, i = [], 0
    while i < len(p):
        if p.startswith("**/", i):
            out.append("(?:[^/]*/)*")
            i += 3
        elif p.startswith("/**", i) and i + 3 == len(p):
            out.append("(?:/.*)?")
            i += 3
        elif p.startswith("**", i):
            out.append(".*")
            i += 2
        elif p[i] == "*":
            out.append("[^/]*")
            i += 1
        elif p[i] == "?":
            out.append("[^/]")
            i += 1
        elif p[i] == "[":
            j = p.find("]", i + 1)
            if j == -1:
                out.append(re.escape(p[i]))
                i += 1
            else:
                body = p[i + 1:j]
                if body.startswith("!"):
                    body = "^" + body[1:]
                out.append("[" + body.replace("\\", "\\\\") + "]")
                i = j + 1
        else:
            out.append(re.escape(p[i]))
            i += 1
    body = "".join(out)
    if anchored:
        rx = re.compile(r"\A" + body + r"(?:/.*)?\Z", re.IGNORECASE | re.DOTALL)
    else:
        rx = re.compile(r"(?:\A|.*/)" + body + r"(?:/.*)?\Z", re.IGNORECASE | re.DOTALL)
    _GLOB_CACHE[pat] = rx
    return rx


def matches_any(relpath, patterns):
    relpath = relpath.rstrip("/")
    return any(glob_regex(pat).match(relpath) for pat in patterns)


def is_secret_hint_name(name):
    """Conservative filename-only secret hint; never opens file content."""
    lowered = name.lower()
    if lowered in SECRET_HINT_NAMES:
        return True
    if os.path.splitext(lowered)[1] in SECRET_HINT_EXTENSIONS:
        return True
    return any(lowered.startswith(prefix + sep)
               for prefix, separators in SECRET_HINT_PREFIX_RULES.items()
               for sep in separators)


# Any URI scheme (http:, mailto:, file:, onenote:, ...) but not a Windows drive
# letter such as C:/ - a single letter before the colon is a path.
URI_SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]+:")
# Version strings such as v1.2.0 or 3.11 look like 'name.ext' to the backtick
# pattern but are never paths.
VERSION_RE = re.compile(r"^v?\d+(?:\.\d+)+(?:[-+][0-9A-Za-z.-]+)?$")


def clean_local_reference(value):
    """Normalize a local Markdown/code reference without guessing its meaning.

    Handles <angle-bracketed> targets, an optional "title" / 'title' after the
    target, URL-encoded characters (%20), and #fragments.
    """
    value = value.strip()
    if value.startswith("<") and ">" in value:
        value = value[1:value.index(">")].strip()
    else:
        m = re.match(r"""^(\S+)\s+(?:"[^"]*"|'[^']*'|\([^)]*\))\s*$""", value)
        if m:
            value = m.group(1)
    value = value.split("#", 1)[0].strip()
    if "%" in value:
        value = urllib.parse.unquote(value)
    return value


def is_external_or_nonpath(value):
    return (not value or value.startswith("#") or bool(URI_SCHEME_RE.match(value))
            or bool(VERSION_RE.match(value)))


def _resolved_paths(value, index_dir, root):
    candidate = value.replace("\\", "/").lstrip("/")
    hits = []
    for base in (index_dir, root):
        full = os.path.join(base, candidate)
        if os.path.exists(full):
            hits.append(full)
    return hits


def reference_resolves(value, index_dir, root):
    return bool(_resolved_paths(value, index_dir, root))


def case_exact(path):
    """True if every segment of `path` matches the on-disk name byte for byte.

    os.path.exists is case-insensitive on Windows and on default macOS volumes,
    so an index reference of `tools\\build_x.ps1` against an on-disk
    `Build_x.ps1` reports as resolving and then breaks for any agent reading the
    same index on Linux. Multi-agent almost always means multi-platform, so the
    mismatch is worth surfacing as a review item -- not as a broken link, which
    it is not on the owner's own machine.
    """
    path = os.path.abspath(path)
    while True:
        parent, name = os.path.split(path)
        if not name or parent == path:
            return True
        try:
            if name not in os.listdir(parent):
                return False
        except OSError:
            return True  # cannot read the parent; do not claim a mismatch
        path = parent


def reference_case_mismatch(value, index_dir, root):
    hits = _resolved_paths(value, index_dir, root)
    return bool(hits) and not any(case_exact(h) for h in hits)


def _resolve_under_root(value, root):
    return value if os.path.isabs(value) else os.path.join(root, value.replace("/", os.sep))


def load_expected_manifest(path):
    """Return path plus optional size/sha256 rows; never changes the target."""
    with open(path, "r", encoding="utf-8-sig", errors="replace", newline="") as fh:
        sample = fh.read(4096)
        fh.seek(0)
        first = sample.splitlines()[0].lower() if sample.splitlines() else ""
        if "," in first and "path" in first:
            rows = []
            for row in csv.DictReader(fh):
                value = (row.get("path") or row.get("relative_path") or "").strip()
                if value:
                    rows.append({"path": value, "size": (row.get("size") or "").strip(),
                                 "sha256": (row.get("sha256") or "").strip().lower()})
            return rows
        return [{"path": line.strip(), "size": "", "sha256": ""}
                for line in fh if line.strip() and not line.lstrip().startswith("#")]


def pointer_candidate(path, size):
    if size > 4096 or os.path.splitext(path)[1].lower() not in {".md", ".txt"}:
        return False
    try:
        text = open(path, "r", encoding="utf-8", errors="replace").read()
    except OSError:
        return False
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines or len(lines) > 12:
        return False
    directive = re.search(r"(?i)\b(read|see|start|canonical|authoritative|use|go to|continue in)\b", text)
    local_ref = MARKDOWN_LINK_RE.search(text) or BACKTICK_PATH_RE.search(text)
    return bool(directive and local_ref)


def portfolio_rows(root, expected):
    defaults = ["AGENTS.md", "README_FIRST.md", "PROJECT_ROADMAP_STATUS.md",
                "AUTHORITY_MAP.md", "INDEX.md", "AI_CONTEXT/README_FIRST.md",
                "AI_CONTEXT/PROJECT_QUICK_CONTEXT.md",
                "AI_CONTEXT/PROJECT_ACTIVITY_JOURNAL.md", "AI_CONTEXT/CHAT_INDEX.md"]
    checks = list(dict.fromkeys(defaults + list(expected or [])))
    rows = []
    try:
        children = sorted((e for e in os.scandir(root) if e.is_dir(follow_symlinks=False)),
                          key=lambda e: e.name.lower())
    except OSError:
        return []
    for child in children:
        try:
            root_items = len(list(os.scandir(child.path)))
        except OSError:
            root_items = "?"
        present = [x for x in checks if os.path.exists(os.path.join(child.path, x.replace("/", os.sep)))]
        rows.append((child.name, root_items, present))
    return rows

def _safe_stdout():
    """Never crash on a filename the console cannot encode.

    Redirected output on Windows defaults to the ANSI code page (cp1252), so a
    single CJK or emoji filename used to abort the whole audit with
    UnicodeEncodeError. Write UTF-8 when redirected; escape instead of failing.
    """
    try:
        if sys.stdout.isatty():
            sys.stdout.reconfigure(errors="backslashreplace")
        else:
            sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    except (AttributeError, ValueError):
        pass


def is_non_governing(relpath):
    """True when any folder segment marks proposals, history or scratch."""
    for seg in relpath.lower().split("/")[:-1]:
        if any(tok in seg for tok in NON_GOVERNING_TOKENS):
            return True
    return False


def has_segment(relpath, name):
    return name in relpath.lower().split("/")[:-1]


def _cloud_only(path):
    try:
        return bool(os.lstat(path).st_file_attributes & CLOUD_ONLY_ATTRS)
    except (AttributeError, OSError):
        return False


def orphan_reason(path, size):
    name = os.path.basename(path)
    for rx, why in ORPHAN_TEMP_RULES:
        if rx.search(name):
            return why
    # An extensionless file holding archive bytes is usually an interrupted
    # write. Reads 8 bytes; skips cloud-only placeholders so nothing hydrates.
    if "." not in name and size >= 8 and not _cloud_only(path):
        try:
            with open(path, "rb") as fh:
                head = fh.read(8)
        except OSError:
            return None
        if head.startswith(ARCHIVE_MAGIC):
            return "archive data without extension"
    return None


SKILL_NAME_RE = re.compile(r"^name:\s*['\"]?([^'\"\r\n]+?)['\"]?\s*$", re.MULTILINE)
SKILL_VERSION_RE = re.compile(r"^\s*version:\s*['\"]?([^'\"\s]+)['\"]?\s*$", re.MULTILINE)


def skill_identity(path):
    """(name, version) from SKILL.md frontmatter; never executes anything."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            head = fh.read(8192)
    except OSError:
        return ("(unreadable)", "?")
    name, version = "(no name)", "(no version)"
    if head.startswith("---"):
        end = head.find("\n---", 3)
        front = head[3:end] if end != -1 else head
        m = SKILL_NAME_RE.search(front)
        if m:
            name = m.group(1).strip()
        m = SKILL_VERSION_RE.search(front)
        if m:
            version = m.group(1).strip()
    return (name, version)


def index_mentions(content, name):
    if name in content or urllib.parse.quote(name) in content:
        return True
    m = UUID_RE.search(name)
    return bool(m and m.group(0).lower() in content.lower())


def host_length(relpath, host_base_len):
    return host_base_len + 1 + len(relpath) if relpath else host_base_len


def main():
    _safe_stdout()
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", action="version", version=f"audit_folder.py {VERSION}")
    ap.add_argument("--root", required=True)
    ap.add_argument("--index-path", action="append", default=[],
                    help="Repeatable. Index/navigation file to link-check, relative to root.")
    ap.add_argument("--hash-files", action="store_true")
    ap.add_argument("--inspect-zip", action="store_true")
    ap.add_argument("--exclude", action="append", default=[],
                    help="Repeatable glob (relative to root, / separators) kept OUT of "
                         "detail sections. Excluded files are still counted and reported.")
    ap.add_argument("--suggest-excludes", action="store_true",
                    help="Report likely generated-noise clusters; exclude nothing.")
    ap.add_argument("--path-threshold", type=int, default=240)
    ap.add_argument("--host-root",
                    help="Real host path of --root (e.g. its Windows path) for path-length checks.")
    ap.add_argument("--dup-group-cap", type=int, default=8,
                    help="Max paths printed per duplicate group.")
    ap.add_argument("--journal-threshold-kb", type=int, default=100,
                    help="Flag journal-like files at or above this size; default 100 KB.")
    ap.add_argument("--entrypoint", action="append", default=[],
                    help="Repeatable expected entrypoint relative to root. Also the startup read set.")
    ap.add_argument("--read-budget-kb", type=int, default=40,
                    help="Flag a startup read set (root instruction files + entrypoints) above this size.")
    ap.add_argument("--index-coverage", action="append", default=[],
                    help="Repeatable INDEX=DIR: list files directly in DIR that INDEX never mentions.")
    ap.add_argument("--portfolio", action="store_true",
                    help="Report an advisory immediate-child project matrix.")
    ap.add_argument("--detect-pointers", action="store_true",
                    help="Report conservative small pointer-stub candidates.")
    ap.add_argument("--expected-upload-manifest", action="append", default=[],
                    help="Repeatable CSV or line manifest of expected relative paths; optional size and sha256 columns.")
    ap.add_argument("--brief", action="store_true", help="Cap every list at 10 lines.")
    ap.add_argument("--out", help="Write the full report here (outside the root); print only the summary.")
    ap.add_argument("--prune-noise", action="store_true",
                    help="Do not walk high-confidence generated state; list it instead.")
    ap.add_argument("--max-seconds", type=float, default=0.0,
                    help="Stop walking after this many seconds and disclose the gap.")
    args = ap.parse_args()

    # A comma inside a pattern is almost always someone reaching for the PowerShell
    # form. argparse would accept it silently and match nothing, producing a clean-
    # looking report with an empty exclusion table -- the same silent failure the
    # PowerShell comma-split exists to prevent. Refuse instead of guessing: unlike
    # -File in PowerShell, --exclude can always be repeated, so there is no reason to
    # invent a comma syntax here (and a path may legitimately contain a comma).
    for pat in (args.exclude or []):
        if "," in pat:
            sys.exit(
                f"--exclude pattern contains a comma: {pat!r}\n"
                "Repeat the flag instead: --exclude 'a/**' --exclude 'b/**'\n"
                "(PowerShell's -Exclude takes comma-separated values; Python's does not.)"
            )

    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        sys.exit(f"Root not found: {root}")

    # --index-path has the same failure mode and a worse symptom: a comma form
    # resolves to one nonexistent path, so a present INDEX.md is reported as
    # "index NOT FOUND" and the agent is told to rank that at the top of the
    # report. A silent miss is bad; a fabricated headline finding is worse.
    for ip in (args.index_path or []):
        if "," in ip:
            sys.exit(
                f"--index-path contains a comma: {ip!r}\n"
                "Repeat the flag instead: --index-path A.md --index-path B.md\n"
                "(PowerShell's -IndexPath takes comma-separated values; Python's does not.)"
            )

    for ep in (args.entrypoint or []):
        if "," in ep:
            sys.exit("--entrypoint contains a comma; repeat the flag instead.")
    coverage_pairs = []
    for spec in (args.index_coverage or []):
        if "," in spec or spec.count("=") != 1:
            sys.exit(f"--index-coverage must be INDEX=DIR (repeat the flag for more): {spec!r}")
        idx_value, dir_value = (x.strip() for x in spec.split("="))
        coverage_pairs.append((idx_value, dir_value))
    if args.journal_threshold_kb < 0:
        sys.exit("--journal-threshold-kb must be zero or greater")
    if args.read_budget_kb < 0:
        sys.exit("--read-budget-kb must be zero or greater")

    out_path = None
    if args.out:
        out_path = os.path.abspath(args.out)
        try:
            inside = os.path.commonpath([out_path, root]) == root
        except ValueError:
            inside = False
        if inside:
            sys.exit(f"--out must be outside the audited root: {out_path}")
        if os.path.exists(out_path):
            sys.exit(f"--out already exists; choose a new file: {out_path}")

    buffer = io.StringIO()
    target = buffer if out_path else sys.stdout
    with contextlib.redirect_stdout(target):
        glance = run_report(args, root, coverage_pairs)
    if out_path:
        text = buffer.getvalue()
        with open(out_path, "x", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        print_summary_only(text, out_path)
    return glance


def print_summary_only(text, out_path):
    keep = {"Summary", "Findings at a glance"}
    lines = text.splitlines()
    out, on = [], True
    for ln in lines:
        if ln.startswith("== ") and ln.endswith(" =="):
            on = ln[3:-3] in keep
            if on:
                out.append("")
        if ln.startswith(("Coverage", "Audit complete", "Walk ")):
            on = True
        if on and ln.strip():
            out.append(ln)
    for ln in out:
        print(ln)
    print(f"\nFull report: {out_path} ({len(lines)} lines). Read sections from it as needed.")


def run_report(args, root, coverage_pairs):
    cap = (lambda n: min(n, LIST_CAP_BRIEF)) if args.brief else (lambda n: n)
    dup_cap = min(args.dup_group_cap, 3) if args.brief else args.dup_group_cap
    host_base = (args.host_root.rstrip("\\/") if args.host_root else root)
    host_base_len = len(host_base)
    glance = {}

    print(f"Read-only audit of {root}")
    print(f"Generated {datetime.now():%Y-%m-%d %H:%M}")

    walk = collect(root, prune_noise=args.prune_noise, max_seconds=args.max_seconds)
    all_files, folders = walk.files, walk.folders
    empty_folders, metadata_failures = walk.empty_folders, walk.metadata_failures
    reparse_points, unreadable_dirs = walk.reparse_points, walk.unreadable_dirs

    excluded = []
    files = []
    for entry in all_files:
        if args.exclude and matches_any(relslash(entry[0], root), args.exclude):
            excluded.append(entry)
        else:
            files.append(entry)

    excluded_metadata_failures = []
    detail_metadata_failures = []
    for entry in metadata_failures:
        if args.exclude and matches_any(relslash(entry[0], root), args.exclude):
            excluded_metadata_failures.append(entry)
        else:
            detail_metadata_failures.append(entry)

    visible_empty_folders = []
    excluded_empty_folders = []
    for path in empty_folders:
        if args.exclude and matches_any(relslash(path, root) + "/", args.exclude):
            excluded_empty_folders.append(path)
        else:
            visible_empty_folders.append(path)

    section("Summary")
    total = sum(s for _, s, _ in all_files)
    discovered_files = len(all_files) + len(metadata_failures)
    # depth = directory levels below the root; a file in the root is depth 0.
    # Must match audit_folder.ps1, which computes (segments - 1).
    depths = [relslash(p, root).count("/") for p, _, _ in all_files] or [0]
    print(f"  Files (all):      {discovered_files}")
    if metadata_failures:
        print(f"  Metadata readable: {len(all_files)}")
    if unreadable_dirs:
        print(f"  Unreadable dirs:  {len(unreadable_dirs)} (contents NOT counted)")
    print(f"  Folders:          {folders}")
    print(f"  Total MB:         {total / (1024*1024):.2f}")
    print(f"  Max depth:        {max(depths)}")
    if args.exclude:
        excluded_total = len(excluded) + len(excluded_metadata_failures)
        pct = 100.0 * excluded_total / discovered_files if discovered_files else 0
        print(f"  Excluded:         {excluded_total} ({pct:.0f}%) by --exclude")
        print(f"  In detail below:  {len(files)}")
    if walk.pruned:
        print(f"  Pruned folders:   {len(walk.pruned)} (not walked; contents NOT counted)")
    if walk.unvisited:
        print(f"  WALK INCOMPLETE:  time budget {args.max_seconds:g} s reached; "
              f"{walk.unvisited} queued directories not visited")

    if metadata_failures:
        section("Metadata entries not readable")
        for path, why in metadata_failures[:cap(25)]:
            scope = "excluded" if (path, why) in excluded_metadata_failures else "detail gap"
            print(f"  {why:18} [{scope}] {rel(path, root)}")
        if len(metadata_failures) > cap(25):
            print(f"  ... and {len(metadata_failures) - cap(25)} more")
        print("  These directory entries were counted but could not be stat'ed. "
              "On synced storage this may be transient; re-check before Execute.")

    if unreadable_dirs:
        section("Directories not readable (contents missing from every count)")
        for path, why in sorted(unreadable_dirs, key=lambda x: rel(x[0], root).lower())[:cap(25)]:
            print(f"  {why:18} {rel(path, root)}")
        if len(unreadable_dirs) > cap(25):
            print(f"  ... and {len(unreadable_dirs) - cap(25)} more")
        print("  Access was denied or the directory vanished mid-walk. Nothing below "
              "these paths is in any total. Resolve access or disclose the gap.")

    if walk.pruned:
        section("Pruned generated state (not walked; contents in no count)")
        for path, why in sorted(walk.pruned, key=lambda x: rel(x[0], root).lower())[:cap(25)]:
            print(f"  {why:26} {rel(path, root)}")
        if len(walk.pruned) > cap(25):
            print(f"  ... and {len(walk.pruned) - cap(25)} more")
        print("  Generated state, not evidence. Still synced and indexed by cloud providers.")

    if args.exclude:
        section("Excluded from detail sections (counted, not examined)")
        per_pat = defaultdict(int)
        for p, _, _ in excluded:
            rp = relslash(p, root)
            for pat in args.exclude:
                if matches_any(rp, [pat]):
                    per_pat[pat] += 1
                    break
        for p, _ in excluded_metadata_failures:
            rp = relslash(p, root)
            for pat in args.exclude:
                if matches_any(rp, [pat]):
                    per_pat[pat] += 1
                    break
        for pat, c in sorted(per_pat.items(), key=lambda x: (-x[1], x[0])):
            print(f"  {c:6d}  {pat}")
        print("  These files were NOT classified. State this in the report.")

    if args.suggest_excludes:
        section("Suggested exclusions (generated machine state - nothing excluded yet)")
        env_rel = [relslash(e, root) + "/" for e in walk.env_roots]
        clusters = defaultdict(int)
        kinds = {}
        for p, _, _ in all_files:
            rp = relslash(p, root)
            env = next((e for e in env_rel if rp.lower().startswith(e.lower())), None)
            if env:
                key = env + "**"
                clusters[key] += 1
                kinds[key] = "  [Python environment]"
                continue
            parts = rp.split("/")
            for i, seg in enumerate(parts[:-1]):
                # Exact segment match, or a profile-style prefix such as
                # 'chrome-profile-2'. NEVER a bare substring test: 'logs' is
                # inside 'Catalogs' and 'build' is inside 'rebuild-notes', so
                # substring matching proposes real document folders as junk.
                if is_noise_segment(seg):
                    if seg.lower() in GLOBAL_NOISE:
                        key = "**/" + seg + "/**"
                    else:
                        key = "/".join(parts[:i + 1]) + "/**"
                    clusters[key] += 1
                    break
        if clusters:
            for pat, c in sorted(clusters.items(), key=lambda x: (-x[1], x[0].lower()))[:cap(20)]:
                pct = 100.0 * c / len(all_files)
                print(f"  {c:6d} ({pct:4.1f}%)  --exclude '{pat}'{kinds.get(pat, '')}")
            if len(clusters) > cap(20):
                print(f"  ... and {len(clusters) - cap(20)} more")
            print("  Confirm with the owner before excluding. Never delete these "
                  "under a standard cleanup approval.")
        else:
            print("  none detected")

    section(f"Per-folder counts (top {cap(25)})")
    per = defaultdict(int)
    for p, _, _ in files:
        per[os.path.dirname(p)] += 1
    for d, c in sorted(per.items(), key=lambda x: (-x[1], rel(x[0], root).lower()))[:cap(25)]:
        print(f"  {c:6d}  {rel(d, root)}")

    section("Reparse points not descended (junctions / directory symlinks)")
    if reparse_points:
        for path, target in sorted(reparse_points, key=lambda x: rel(x[0], root).lower()):
            print(f"  {rel(path, root)}")
            print(f"     -> {target or '<unresolved>'}")
        print("  Descendants of these are in NO count in this report.")
        print("  That is correct locally. If this root is OneDrive/SharePoint-synced,")
        print("  the provider may hold the target as real files that other agents")
        print("  index. Check the cloud-side view before calling them external.")
    else:
        print("  none")

    section("Empty directories (cosmetic; no removal implied)")
    if visible_empty_folders:
        print(f"  {len(visible_empty_folders)} empty director{'y' if len(visible_empty_folders) == 1 else 'ies'} in detail:")
        for path in sorted(visible_empty_folders, key=lambda q: rel(q, root).lower())[:cap(40)]:
            print(f"     {rel(path, root)}")
        if len(visible_empty_folders) > cap(40):
            print(f"     ... and {len(visible_empty_folders) - cap(40)} more")
        print("  Leave in place unless removal is explicitly authorized and uses "
              "recoverable platform semantics.")
    else:
        print("  none")
    if excluded_empty_folders:
        print(f"  {len(excluded_empty_folders)} additional empty directories fall under "
              "--exclude patterns; counted but not listed.")

    section("Extensions")
    ext = defaultdict(int)
    for p, _, _ in files:
        name = os.path.basename(p)
        suffix = os.path.splitext(name)[1].lower()
        # PowerShell treats a single-suffix dotfile such as .gitignore as its
        # extension. Match that behavior so both audit helpers classify the
        # same mounted tree identically.
        if not suffix and name.startswith(".") and name.count(".") == 1:
            suffix = name.lower()
        ext[suffix or "(none)"] += 1
    for e, c in sorted(ext.items(), key=lambda x: (-x[1], x[0]))[:cap(20)]:
        print(f"  {c:6d}  {e}")

    section("Archives")
    archives = sorted([(p, s, m) for p, s, m in files
                       if os.path.splitext(p)[1].lower() in ARCHIVE_EXT],
                      key=lambda x: rel(x[0], root).lower())
    if archives:
        for p, s, m in archives[:cap(len(archives))]:
            print(f"  {s/(1024*1024):8.2f} MB  {datetime.fromtimestamp(m):%Y-%m-%d}  {rel(p, root)}")
        if len(archives) > cap(len(archives)):
            print(f"  ... and {len(archives) - cap(len(archives))} more")
        print("  Archives stay closed. Do not bulk-extract to make them searchable.")
    else:
        print("  none")

    if args.inspect_zip:
        section("ZIP central directories (no extraction)")
        member_cap = 5 if args.brief else 15
        for p, _, _ in archives:
            if not p.lower().endswith(".zip"):
                continue
            print(f"-- {rel(p, root)}")
            try:
                with zipfile.ZipFile(p) as zf:
                    names = zf.namelist()
                    print(f"   entries: {len(names)}")
                    bad = [n for n in names
                           if re.search(r'[:*?"<>|]', n) or n.startswith(("/", "\\", ".."))]
                    if bad:
                        print(f"   INVALID/UNSAFE NAMES: {len(bad)}")
                    long_n = [n for n in names
                              if host_base_len + 1 + len(n) > args.path_threshold]
                    if long_n:
                        print(f"   would exceed path threshold: {len(long_n)}")
                    for n in names[:member_cap]:
                        print(f"     {n}")
                    if len(names) > member_cap:
                        print("     ...")
            except Exception as exc:  # noqa: BLE001
                print(f"   unreadable: {exc}")

    section(f"Path length risks (> {args.path_threshold} chars)")
    # Measured as host root + relative path, so a folder mounted under a
    # different prefix (a sandbox, WSL, a bridge) is judged by its real
    # Windows/OneDrive length when --host-root is supplied.
    long_paths = sorted(((host_length(relslash(p, root), host_base_len), p) for p, _, _ in all_files
                         if host_length(relslash(p, root), host_base_len) > args.path_threshold),
                        key=lambda x: (-x[0], rel(x[1], root).lower()))
    glance["long"] = len(long_paths)
    print(f"  Measured against: {host_base}")
    if long_paths:
        for n, p in long_paths[:cap(40)]:
            print(f"  {n:4d}  {rel(p, root)}")
        if len(long_paths) > cap(40):
            print(f"  ... and {len(long_paths) - cap(40)} more")
    else:
        print("  none")
    if not args.host_root:
        print("  If this root is a mounted copy of a Windows/OneDrive folder, re-run with "
              "the host-root option set to its real path.")

    section("Duplicate names across folders")
    by_name = defaultdict(list)
    for p, _, m in files:
        # Case-insensitive, like Windows/OneDrive and audit_folder.ps1.
        by_name[os.path.basename(p).lower()].append((p, m))
    dups = {k: sorted(v, key=lambda e: rel(e[0], root).lower())
            for k, v in by_name.items() if len(v) > 1}
    if dups:
        ordered = sorted(dups.items(), key=lambda x: (-len(x[1]), x[0]))
        for name, entries in ordered[:cap(20)]:
            print(f"-- {os.path.basename(entries[0][0])}  ({len(entries)})")
            for p, m in entries[:dup_cap]:
                print(f"     {datetime.fromtimestamp(m):%Y-%m-%d}  {rel(p, root)}")
            if len(entries) > dup_cap:
                print(f"     ... and {len(entries) - dup_cap} more")
        if len(ordered) > cap(20):
            print(f"  ... and {len(ordered) - cap(20)} more duplicated names")
    else:
        print("  none")

    if args.hash_files:
        by_hash = defaultdict(list)
        hashes = {}
        unreadable = []
        for p, _, _ in files:
            try:
                h = sha256(p)
            except OSError as exc:
                # Never drop these silently: an unhashed file is a hole in the
                # coverage claim, and on OneDrive it usually means a
                # placeholder or a lock, both of which block an Execute pass.
                unreadable.append((p, exc.__class__.__name__))
                continue
            hashes[p] = h
            by_hash[h].append(p)

        if unreadable:
            section("UNREADABLE - could not hash")
            for p, why in unreadable[:cap(25)]:
                print(f"  {why:18} {rel(p, root)}")
            if len(unreadable) > cap(25):
                print(f"  ... and {len(unreadable) - cap(25)} more")
            print(f"  {len(unreadable)} file(s) are not covered by any hash check "
                  "below. On a synced folder this usually means a cloud "
                  "placeholder or an open lock. Resolve before any Execute pass.")

        section("Identical content groups (SHA-256)")
        groups = {h: ps for h, ps in by_hash.items() if len(ps) > 1}
        glance["identical"] = len(groups)
        if groups:
            n_files = sum(len(ps) for ps in groups.values())
            print(f"  {len(groups)} groups, {n_files} files")
            ordered = sorted(groups.items(), key=lambda x: (-len(x[1]), x[0]))
            for h, ps in ordered[:cap(len(ordered))]:
                ps = sorted(ps, key=lambda q: rel(q, root).lower())
                print(f"-- {h[:12]}...  ({len(ps)} copies)")
                for p in ps[:dup_cap]:
                    print(f"     {rel(p, root)}")
                if len(ps) > dup_cap:
                    print(f"     ... and {len(ps) - dup_cap} more")
            if len(ordered) > cap(len(ordered)):
                print(f"  ... and {len(ordered) - cap(len(ordered))} more groups")
        else:
            print("  none")

        # The dangerous inverse: one name, several different documents.
        section("Same name, DIFFERENT content (ambiguous citation)")
        ambiguous = 0
        for name, entries in sorted(dups.items(), key=lambda x: (-len(x[1]), x[0])):
            paths = [p for p, _ in entries if p in hashes]
            if len({hashes[p] for p in paths}) > 1:
                ambiguous += 1
                if ambiguous > cap(20):
                    continue
                print(f"-- {os.path.basename(entries[0][0])}")
                for p in paths[:dup_cap]:
                    print(f"     {hashes[p][:8]}  {rel(p, root)}")
                if len(paths) > dup_cap:
                    print(f"     ... and {len(paths) - dup_cap} more")
        glance["ambiguous"] = ambiguous
        if not ambiguous:
            print("  none")
        else:
            print(f"  {ambiguous} name(s) resolve to more than one document. "
                  "Any citation by filename alone is ambiguous.")

    section("Claims requiring verification (open these - never trust the name)")
    claim_files = []
    scratch_claims = 0
    for p, s, m in files:
        n = os.path.basename(p).lower()
        if any(fnmatch.fnmatch(n, pat) for pat in CLAIM_PATTERNS):
            if has_segment(relslash(p, root), "scratch"):
                scratch_claims += 1
                continue
            claim_files.append((p, s, m))
    if claim_files:
        for p, s, m in sorted(claim_files, key=lambda x: (-int(x[2] * 1000), rel(x[0], root).lower()))[:cap(40)]:
            print(f"  {datetime.fromtimestamp(m):%Y-%m-%d}  {s:9d}  {rel(p, root)}")
        if len(claim_files) > cap(40):
            print(f"  ... and {len(claim_files) - cap(40)} more")
        print("  Each is verified, contradicted or unverifiable. Never upgrade "
              "unverifiable to current.")
    else:
        print("  none")
    if scratch_claims:
        print(f"  {scratch_claims} more under scratch/ folders not listed (session working copies).")

    section("Possible credential-bearing files")
    discovered_paths = [p for p, _, _ in all_files] + [p for p, _ in metadata_failures]
    secrets = sorted((p for p in discovered_paths if is_secret_hint_name(os.path.basename(p))),
                     key=lambda q: rel(q, root).lower())
    glance["secrets"] = len(secrets)
    if secrets:
        print(f"  {len(secrets)} file(s) matched credential-name hints:")
        for p in secrets[:cap(25)]:
            print(f"     {rel(p, root)}")
        if len(secrets) > cap(25):
            print(f"     ... and {len(secrets) - cap(25)} more")
        print("  Do not stage, copy, or index these. Flag to the owner before sharing "
              "the folder. Never copy a secret value into a report or journal.")
    else:
        print("  none detected by name")

    section("Possible orphaned temporary files")
    orphans = []
    for p, size, _ in files:
        why = orphan_reason(p, size)
        if why:
            orphans.append((p, size, why))
    orphans.sort(key=lambda x: rel(x[0], root).lower())
    glance["orphans"] = len(orphans)
    if orphans:
        for p, size, why in orphans[:cap(25)]:
            print(f"  {why:30} {size:9d}  {rel(p, root)}")
        if len(orphans) > cap(25):
            print(f"  ... and {len(orphans) - cap(25)} more")
        print("  Usually left by an interrupted write. Confirm the finished copy exists "
              "before proposing removal; never delete under a standard cleanup approval.")
    else:
        print("  none")

    section(f"Large journals (threshold {args.journal_threshold_kb} KB)")
    journal_limit = args.journal_threshold_kb * 1024
    journals = [(p, size) for p, size, _ in all_files
                if "journal" in os.path.basename(p).lower() and size >= journal_limit]
    glance["journals"] = len(journals)
    if journals:
        for path, size in sorted(journals, key=lambda x: (-x[1], rel(x[0], root).lower())):
            print(f"  {size:9d}  {rel(path, root)}")
        print("  Rotation is a proposal only; preserve every entry and require approval.")
    else:
        print("  none")

    missing_entrypoints = 0
    if args.entrypoint:
        section("Expected entrypoints")
        for value in args.entrypoint:
            target_path = _resolve_under_root(value, root)
            state = "PRESENT" if os.path.exists(target_path) else "MISSING"
            if state == "MISSING":
                missing_entrypoints += 1
            print(f"  {state:7}  {value}")
        print("  Missing is established against this direct filesystem root only.")
        glance["missing_entry"] = missing_entrypoints

    # What a cold agent must read before it can act. Root auto-loaded
    # instruction files plus the declared entrypoints.
    section(f"Startup read set (budget {args.read_budget_kb} KB)")
    read_set = sorted(((relslash(p, root), size) for p, size, _ in all_files
                       if os.path.dirname(p) == root
                       and os.path.basename(p).lower() in AUTOLOAD_INSTRUCTION_NAMES),
                      key=lambda x: x[0].lower())
    for value in (args.entrypoint or []):
        full = _resolve_under_root(value, root)
        key = relslash(os.path.abspath(full), root)
        if os.path.isfile(full) and key.lower() not in {k.lower() for k, _ in read_set}:
            read_set.append((key, os.path.getsize(full)))
    read_total = sum(sz for _, sz in read_set)
    over_budget = read_total > args.read_budget_kb * 1024
    glance["read"] = (read_total, over_budget, bool(read_set))
    if read_set:
        for key, size in read_set:
            print(f"  {size / 1024:7.1f} KB  {key}")
        print(f"  Total: {read_total / 1024:.1f} KB (about {read_total // 4} tokens)")
        if over_budget:
            print(f"  OVER BUDGET: every session pays this before working. Propose a short "
                  f"router plus on-demand detail files; do not delete content.")
    else:
        print("  none identified (pass the project's read order as entrypoints)")

    if args.portfolio:
        section("Portfolio root matrix (immediate children; advisory)")
        rows = portfolio_rows(root, args.entrypoint)
        print("  Project | Count scope | Root items | Entrypoints present")
        if rows:
            for name, count, present in rows:
                value = ", ".join(present) if present else "(none detected)"
                print(f"  {name} | root-level | {count} | {value}")
        else:
            print("  no immediate child directories")
        print("  Presence does not determine authority or operational state.")

    if args.detect_pointers:
        section("Possible pointer stubs (advisory; content not authority)")
        candidates = sorted((p for p, size, _ in files if pointer_candidate(p, size)),
                            key=lambda q: rel(q, root).lower())
        if candidates:
            for path in candidates:
                print(f"  {rel(path, root)}")
            print("  Verify the target exists and that the file contains no independent guidance.")
        else:
            print("  none")

    for manifest_value in (args.expected_upload_manifest or []):
        section(f"Expected upload manifest: {manifest_value}")
        manifest_path = _resolve_under_root(manifest_value, root)
        if not os.path.isfile(manifest_path):
            print(f"  MANIFEST NOT FOUND: {manifest_path}")
            continue
        try:
            expected = load_expected_manifest(manifest_path)
        except (OSError, csv.Error) as exc:
            print(f"  MANIFEST UNREADABLE: {exc.__class__.__name__}")
            continue
        present = missing = size_bad = hash_bad = 0
        for row in expected:
            target_path = _resolve_under_root(row["path"], root)
            if not os.path.isfile(target_path):
                missing += 1
                print(f"  MISSING        {row['path']}")
                continue
            present += 1
            if row["size"]:
                try:
                    wanted = int(row["size"])
                except ValueError:
                    print(f"  BAD SIZE VALUE {row['path']} = {row['size']!r}")
                    size_bad += 1
                else:
                    actual = os.path.getsize(target_path)
                    if actual != wanted:
                        size_bad += 1
                        print(f"  SIZE MISMATCH  {row['path']} expected={wanted} actual={actual}")
            if row["sha256"]:
                actual_hash = sha256(target_path)
                if actual_hash.lower() != row["sha256"]:
                    hash_bad += 1
                    print(f"  HASH MISMATCH  {row['path']}")
        print(f"  Expected: {len(expected)}  Present: {present}  Missing: {missing}  Size mismatches: {size_bad}  Hash mismatches: {hash_bad}")
        print("  This verifies listed files only; it does not authorize upload, overwrite, or promotion.")

    broken_total = 0
    for index_path in (args.index_path or []):
        section(f"Index link check: {index_path}")
        idx = os.path.join(root, index_path)
        if os.path.isfile(idx):
            with open(idx, "r", encoding="utf-8", errors="replace") as fh:
                content = fh.read()
            markdown_links = []
            for match in MARKDOWN_LINK_RE.finditer(content):
                link = clean_local_reference(match.group(1))
                if not is_external_or_nonpath(link):
                    markdown_links.append(link)
            markdown_links = list(dict.fromkeys(markdown_links))

            backticked_refs = [clean_local_reference(match.group(1))
                               for match in BACKTICK_PATH_RE.finditer(content)]
            backticked_refs = [ref for ref in dict.fromkeys(backticked_refs)
                               if not is_external_or_nonpath(ref)]
            # A relative link in AI_CONTEXT/CHAT_INDEX.md is relative to
            # AI_CONTEXT/, not to the root. Resolving everything against the
            # root reports working links as broken - the exact false alarm
            # that makes an agent distrust a healthy index. Accept either.
            idx_dir = os.path.dirname(idx)
            broken = [link for link in markdown_links
                      if not reference_resolves(link, idx_dir, root)]
            unresolved_refs = [ref for ref in backticked_refs
                               if not reference_resolves(ref, idx_dir, root)]
            broken_total += len(broken)

            print(f"  Markdown links checked: {len(markdown_links)}")
            if broken:
                print(f"  BROKEN MARKDOWN LINKS: {len(broken)}")
                for b in broken[:cap(len(broken))]:
                    print(f"     {b}")
                if len(broken) > cap(len(broken)):
                    print(f"     ... and {len(broken) - cap(len(broken))} more")
            else:
                print("  all Markdown links resolve")

            print(f"  Backticked path references checked: {len(backticked_refs)}")
            if unresolved_refs:
                print(f"  UNRESOLVED BACKTICKED REFERENCES: {len(unresolved_refs)} (review needed)")
                for ref in unresolved_refs[:cap(len(unresolved_refs))]:
                    print(f"     {ref}")
                if len(unresolved_refs) > cap(len(unresolved_refs)):
                    print(f"     ... and {len(unresolved_refs) - cap(len(unresolved_refs))} more")
                print("  These are not confirmed broken links; examples and historical "
                      "labels may be intentionally non-live.")
            else:
                print("  all backticked references resolve")

            case_mismatched = [r for r in (markdown_links + backticked_refs)
                               if reference_case_mismatch(r, idx_dir, root)]
            if case_mismatched:
                print(f"  CASE-MISMATCHED REFERENCES: {len(case_mismatched)} (review needed)")
                for ref in case_mismatched:
                    print(f"     {ref}")
                print("  These resolve only because this filesystem is case-insensitive. "
                      "They break for an agent on Linux or a case-sensitive volume.")
        else:
            broken_total += 1
            print(f"  index NOT FOUND at {idx}")
            print("  An index named in navigation but absent is a top-tier "
                  "confusion source. Report it.")
    if args.index_path:
        glance["broken"] = broken_total

    unreferenced_total = 0
    for idx_value, dir_value in coverage_pairs:
        section(f"Index coverage: {idx_value} <- {dir_value}")
        idx = _resolve_under_root(idx_value, root)
        folder = _resolve_under_root(dir_value, root)
        if not os.path.isfile(idx):
            print(f"  index NOT FOUND: {idx_value}")
            continue
        if not os.path.isdir(folder):
            print(f"  directory NOT FOUND: {dir_value}")
            continue
        with open(idx, "r", encoding="utf-8", errors="replace") as fh:
            content = fh.read()
        folder_rel = relslash(os.path.abspath(folder), root).rstrip("/")
        members = sorted((os.path.basename(p) for p, _, _ in all_files
                          if relslash(os.path.dirname(p), root).rstrip("/") == folder_rel),
                         key=str.lower)
        missing_refs = [n for n in members if not index_mentions(content, n)]
        unreferenced_total += len(missing_refs)
        print(f"  Files directly in {dir_value}: {len(members)}")
        print(f"  Mentioned by the index:  {len(members) - len(missing_refs)}")
        if missing_refs:
            print(f"  NOT MENTIONED: {len(missing_refs)}")
            for n in missing_refs[:cap(len(missing_refs))]:
                print(f"     {n}")
            if len(missing_refs) > cap(len(missing_refs)):
                print(f"     ... and {len(missing_refs) - cap(len(missing_refs))} more")
            print("  An index that omits existing files tells the next agent they do not "
                  "exist. Regenerate or append; never infer absence from an index.")
        else:
            print("  every file is mentioned")
    if coverage_pairs:
        glance["unreferenced"] = unreferenced_total

    section("Embedded skill copies")
    skills = []
    for p, size, _ in all_files:
        low = os.path.basename(p).lower()
        if low == "skill.md":
            name, version = skill_identity(p)
            skills.append((name, version, p))
        elif low.endswith(".skill"):
            skills.append((os.path.splitext(os.path.basename(p))[0], "(packaged)", p))
    skills.sort(key=lambda x: (x[0].lower(), rel(x[2], root).lower()))
    by_skill = defaultdict(list)
    for name, version, p in skills:
        by_skill[name.lower()].append(version)
    multi = {k: v for k, v in by_skill.items() if len(v) > 1}
    glance["skills"] = (len(skills), len(multi))
    if skills:
        for name, version, p in skills[:cap(40)]:
            print(f"  {name}  {version}  {rel(p, root)}")
        if len(skills) > cap(40):
            print(f"  ... and {len(skills) - cap(40)} more")
        for key in sorted(multi):
            versions = ", ".join(sorted(set(multi[key])))
            print(f"  {len(multi[key])} copies of {key} (versions: {versions})")
        print("  Copies inside a project are not installed skills. Hosts that scan "
              ".codex/skills, .claude/skills or .agents/skills folders may load them. "
              "Compare against the canonical release before using any copy.")
    else:
        print("  none")

    section("Instruction files found")
    instr = sorted(((p, s, m) for p, s, m in all_files
                    if os.path.basename(p).lower() in INSTRUCTION_NAMES),
                   key=lambda x: rel(x[0], root).lower())
    autoload = [x for x in instr if os.path.basename(x[0]).lower() in AUTOLOAD_INSTRUCTION_NAMES]
    readmes = [x for x in instr if os.path.basename(x[0]).lower() in README_INSTRUCTION_NAMES]
    misplaced = [p for p, _, _ in autoload if is_non_governing(relslash(p, root))]
    oversized = [(p, s) for p, s, _ in autoload
                 if os.path.basename(p).lower() == "agents.md" and s > CODEX_DOC_LIMIT]
    glance["misplaced"] = len(misplaced)
    glance["oversized"] = len(oversized)
    if instr:
        print("  Auto-loaded names:")
        if autoload:
            for p, s, m in autoload[:cap(40)]:
                print(f"  {datetime.fromtimestamp(m):%Y-%m-%d}  {s:9d}  {rel(p, root)}")
            if len(autoload) > cap(40):
                print(f"  ... and {len(autoload) - cap(40)} more")
        else:
            print("     none")
        print(f"  README / startup files: {len(readmes)}")
        for p, s, m in readmes[:cap(15)]:
            print(f"  {datetime.fromtimestamp(m):%Y-%m-%d}  {s:9d}  {rel(p, root)}")
        if len(readmes) > cap(15):
            print(f"  ... and {len(readmes) - cap(15)} more")
        agent_files = [p for p, _, _ in instr
                       if os.path.basename(p).lower() not in ("readme.md",)]
        roots = [p for p in agent_files if os.path.dirname(p) == root]
        if len(roots) > 1:
            print("  Multiple root-level agent-instruction files - check for "
                  "conflicting scope. Record the conflict; resolve none unilaterally.")
        for p in misplaced:
            print(f"  LIVE-LOADING NAME IN NON-GOVERNING LOCATION: {rel(p, root)}")
        if misplaced:
            print("  A host that walks the tree may load these as rules. Propose a "
                  "non-loading name such as AGENTS.proposed.md; never rename without approval.")
        for p, s in oversized:
            print(f"  OVER 32 KiB ({s} bytes): {rel(p, root)}")
        if oversized:
            print("  Codex reads at most 32 KiB of AGENTS.md by default and silently drops "
                  "the rest. Propose a shorter file that links to on-demand detail.")
    else:
        print("  NONE FOUND ANYWHERE.")
        print("  No AGENTS.md / CLAUDE.md / README.md in the tree means every agent's "
              "instructions live outside the folder and cannot be read by the next one. "
              "Report this as a finding.")

    section("Findings at a glance")
    def row(label, value):
        print(f"  {label:32} {value}")
    if "broken" in glance:
        row("Broken index links / indexes:", glance["broken"])
    if "unreferenced" in glance:
        row("Files missing from indexes:", glance["unreferenced"])
    if "missing_entry" in glance:
        row("Missing entrypoints:", glance["missing_entry"])
    total_read, over, has_read = glance["read"]
    row("Startup read set:", (f"{total_read / 1024:.1f} KB" + (" OVER BUDGET" if over else ""))
        if has_read else "not identified")
    row("AGENTS.md over 32 KiB:", glance["oversized"])
    row("Misplaced live-loading names:", glance["misplaced"])
    skill_total, skill_multi = glance["skills"]
    row("Embedded skill copies:", f"{skill_total} ({skill_multi} name(s) with several copies)")
    row("Possible orphaned temp files:", glance["orphans"])
    row("Path length risks:", glance["long"])
    row("Identical content groups:", glance.get("identical", "not hashed"))
    row("Same name, different content:", glance.get("ambiguous", "not hashed"))
    row("Credential-name hints:", glance["secrets"])
    row("Large journals:", glance["journals"])
    print("  Counts only. Open the matching section before acting on any of them.")

    if args.exclude:
        excluded_total = len(excluded) + len(excluded_metadata_failures)
        print(f"\nCoverage: {len(files)} of {discovered_files} files examined in detail; "
              f"{excluded_total} excluded by --exclude and classified by nothing. "
              "Say so in the report.")
    if unreadable_dirs:
        print(f"Coverage gap: {len(unreadable_dirs)} director"
              f"{'y' if len(unreadable_dirs) == 1 else 'ies'} could not be read; "
              "their contents are in no count.")
    if detail_metadata_failures:
        print(f"Coverage gap: {len(detail_metadata_failures)} non-excluded directory "
              "entries could not be stat'ed and were not examined.")
    if walk.pruned:
        print(f"Coverage gap: {len(walk.pruned)} director"
              f"{'y was' if len(walk.pruned) == 1 else 'ies were'} pruned as generated state; "
              "their contents are in no count.")
    if walk.unvisited:
        print(f"Coverage gap: walk stopped at the {args.max_seconds:g} s budget; "
              f"{walk.unvisited} queued directories were never visited.")
    print(f"\nAudit complete. Nothing was written to {root}.")
    return glance


if __name__ == "__main__":
    main()
