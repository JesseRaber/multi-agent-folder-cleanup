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
"""

import argparse
import fnmatch
import hashlib
import os
import re
import sys
import zipfile
from collections import defaultdict
from datetime import datetime

ARCHIVE_EXT = {".zip", ".7z", ".rar", ".tar", ".gz", ".tgz"}

# Files that instruct an agent. Basename match, case-insensitive.
INSTRUCTION_NAMES = {
    "agents.md", "claude.md", "readme.md", "readme_first.md", "read_me_first.md",
    "copilot-instructions.md", "gemini.md", "cursor.md", ".cursorrules",
    ".windsurfrules", "contributing.md",
}

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
    "build", ".next", ".terraform",
]

# Files inside a browser profile that may hold live session credentials.
SECRET_HINT_NAMES = {
    "cookies", "cookies-journal", "login data", "login data-journal",
    "web data", "local state", "credentials", ".env", "id_rsa", "token.json",
    "secrets.json", ".npmrc", ".pypirc", "credentials.json",
}

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

MARKDOWN_LINK_RE = re.compile(r"\]\(([^)]+)\)")
BACKTICK_PATH_RE = re.compile(r"`([^`\r\n]+\.[A-Za-z0-9]{1,8})`")


def section(title):
    print(f"\n== {title} ==")


def rel(path, root):
    return "." + path[len(root):] if path.startswith(root) else path


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


def _is_windows_reparse(path):
    """Detect a Windows junction, which os.path.islink misses on older Pythons."""
    try:
        attrs = os.lstat(path).st_file_attributes
    except (AttributeError, OSError):
        return False
    return bool(attrs & FILE_ATTRIBUTE_REPARSE_POINT)


def collect(root):
    files = []
    folders = 0
    empty_folders = []
    metadata_failures = []
    reparse_points = []
    # os.walk does not follow directory symlinks or junctions, which is the
    # correct arithmetic -- an external runtime is not project content. But an
    # unreported skip becomes the claim "not project contents", and on a synced
    # root the provider may have materialized the target as real cloud files
    # that every Graph-indexed agent sees. Name them so that gets checked.
    for dirpath, dirnames, filenames in os.walk(root):
        folders += len(dirnames)
        for d in list(dirnames):
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
                reparse_points.append((full, target))
                dirnames.remove(d)
        if dirpath != root and not dirnames and not filenames:
            empty_folders.append(dirpath)
        for name in filenames:
            full = os.path.join(dirpath, name)
            try:
                st = os.stat(full, follow_symlinks=False)
            except OSError as exc:
                metadata_failures.append((full, exc.__class__.__name__))
                continue
            files.append((full, st.st_size, st.st_mtime))
    return files, folders, empty_folders, metadata_failures, reparse_points


# Only these may match as a prefix (e.g. 'chrome-profile-2'). Everything else
# in NOISE_DIR_HINTS must match the whole segment exactly.
NOISE_PREFIX_HINTS = ("chrome-profile", "edge-profile", "firefox-profile",
                      "browser-profile", "puppeteer", "playwright")


def is_noise_segment(seg):
    s = seg.lower()
    return s in NOISE_DIR_HINTS or s.startswith(NOISE_PREFIX_HINTS)


def matches_any(relpath, patterns):
    for pat in patterns:
        if fnmatch.fnmatch(relpath, pat):
            return True
        # bare directory name, e.g. --exclude tmp
        if "/" not in pat and "*" not in pat:
            if relpath == pat or relpath.startswith(pat + "/") or f"/{pat}/" in relpath:
                return True
    return False


def is_secret_hint_name(name):
    """Conservative filename-only secret hint; never opens file content."""
    lowered = name.lower()
    if lowered in SECRET_HINT_NAMES:
        return True
    return any(lowered.startswith(prefix + sep)
               for prefix, separators in SECRET_HINT_PREFIX_RULES.items()
               for sep in separators)


def clean_local_reference(value):
    """Normalize a local Markdown/code reference without guessing its meaning."""
    value = value.split("#", 1)[0].strip()
    if value.startswith("<") and value.endswith(">"):
        value = value[1:-1].strip()
    return value


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


def main():
    ap = argparse.ArgumentParser()
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
    ap.add_argument("--dup-group-cap", type=int, default=8,
                    help="Max paths printed per duplicate group.")
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

    print(f"Read-only audit of {root}")
    print(f"Generated {datetime.now():%Y-%m-%d %H:%M}")

    all_files, folders, empty_folders, metadata_failures, reparse_points = collect(root)

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
    print(f"  Folders:          {folders}")
    print(f"  Total MB:         {total / (1024*1024):.2f}")
    print(f"  Max depth:        {max(depths)}")
    if args.exclude:
        excluded_total = len(excluded) + len(excluded_metadata_failures)
        pct = 100.0 * excluded_total / discovered_files if discovered_files else 0
        print(f"  Excluded:         {excluded_total} ({pct:.0f}%) by --exclude")
        print(f"  In detail below:  {len(files)}")

    if metadata_failures:
        section("Metadata entries not readable")
        for path, why in metadata_failures[:25]:
            scope = "excluded" if (path, why) in excluded_metadata_failures else "detail gap"
            print(f"  {why:18} [{scope}] {rel(path, root)}")
        if len(metadata_failures) > 25:
            print(f"  ... and {len(metadata_failures) - 25} more")
        print("  These directory entries were counted but could not be stat'ed. "
              "On synced storage this may be transient; re-check before Execute.")

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
        for pat, c in sorted(per_pat.items(), key=lambda x: -x[1]):
            print(f"  {c:6d}  {pat}")
        print("  These files were NOT classified. State this in the report.")

    if args.suggest_excludes:
        section("Suggested exclusions (generated machine state - nothing excluded yet)")
        clusters = defaultdict(int)
        for p, _, _ in all_files:
            rp = relslash(p, root)
            parts = rp.split("/")
            for i, seg in enumerate(parts[:-1]):
                # Exact segment match, or a profile-style prefix such as
                # 'chrome-profile-2'. NEVER a bare substring test: 'logs' is
                # inside 'Catalogs' and 'build' is inside 'rebuild-notes', so
                # substring matching proposes real document folders as junk.
                if is_noise_segment(seg):
                    clusters["/".join(parts[:i + 1]) + "/**"] += 1
                    break
        if clusters:
            for pat, c in sorted(clusters.items(), key=lambda x: -x[1])[:20]:
                pct = 100.0 * c / len(all_files)
                print(f"  {c:6d} ({pct:4.1f}%)  --exclude '{pat}'")
            print("  Confirm with the owner before excluding. Never delete these "
                  "under a standard cleanup approval.")
        else:
            print("  none detected")

    section("Per-folder counts (top 25)")
    per = defaultdict(int)
    for p, _, _ in files:
        per[os.path.dirname(p)] += 1
    for d, c in sorted(per.items(), key=lambda x: -x[1])[:25]:
        print(f"  {c:6d}  {rel(d, root)}")

    section("Reparse points not descended (junctions / directory symlinks)")
    if reparse_points:
        for path, target in reparse_points:
            print(f"  {path}")
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
        for path in sorted(visible_empty_folders)[:40]:
            print(f"     {rel(path, root)}")
        if len(visible_empty_folders) > 40:
            print(f"     ... and {len(visible_empty_folders) - 40} more")
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
    for e, c in sorted(ext.items(), key=lambda x: -x[1])[:20]:
        print(f"  {c:6d}  {e}")

    section("Archives")
    archives = [(p, s, m) for p, s, m in files
                if os.path.splitext(p)[1].lower() in ARCHIVE_EXT]
    if archives:
        for p, s, m in archives:
            print(f"  {s/(1024*1024):8.2f} MB  {datetime.fromtimestamp(m):%Y-%m-%d}  {rel(p, root)}")
        print("  Archives stay closed. Do not bulk-extract to make them searchable.")
    else:
        print("  none")

    if args.inspect_zip:
        section("ZIP central directories (no extraction)")
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
                              if len(root) + 1 + len(n) > args.path_threshold]
                    if long_n:
                        print(f"   would exceed path threshold: {len(long_n)}")
                    for n in names[:15]:
                        print(f"     {n}")
                    if len(names) > 15:
                        print("     ...")
            except Exception as exc:  # noqa: BLE001
                print(f"   unreadable: {exc}")

    section(f"Path length risks (> {args.path_threshold} chars)")
    long_paths = [p for p, _, _ in all_files if len(p) > args.path_threshold]
    if long_paths:
        for p in long_paths[:40]:
            print(f"  {len(p):4d}  {p}")
        if len(long_paths) > 40:
            print(f"  ... and {len(long_paths) - 40} more")
    else:
        print("  none")

    section("Duplicate names across folders")
    by_name = defaultdict(list)
    for p, _, m in files:
        by_name[os.path.basename(p)].append((p, m))
    dups = {k: v for k, v in by_name.items() if len(v) > 1}
    if dups:
        for name, entries in sorted(dups.items(), key=lambda x: -len(x[1]))[:20]:
            print(f"-- {name}  ({len(entries)})")
            for p, m in entries[:args.dup_group_cap]:
                print(f"     {datetime.fromtimestamp(m):%Y-%m-%d}  {rel(p, root)}")
            if len(entries) > args.dup_group_cap:
                print(f"     ... and {len(entries) - args.dup_group_cap} more")
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
            for p, why in unreadable[:25]:
                print(f"  {why:18} {rel(p, root)}")
            if len(unreadable) > 25:
                print(f"  ... and {len(unreadable) - 25} more")
            print(f"  {len(unreadable)} file(s) are not covered by any hash check "
                  "below. On a synced folder this usually means a cloud "
                  "placeholder or an open lock. Resolve before any Execute pass.")

        section("Identical content groups (SHA-256)")
        groups = {h: ps for h, ps in by_hash.items() if len(ps) > 1}
        if groups:
            n_files = sum(len(ps) for ps in groups.values())
            print(f"  {len(groups)} groups, {n_files} files")
            for h, ps in sorted(groups.items(), key=lambda x: -len(x[1])):
                print(f"-- {h[:12]}...  ({len(ps)} copies)")
                for p in ps[:args.dup_group_cap]:
                    print(f"     {rel(p, root)}")
                if len(ps) > args.dup_group_cap:
                    print(f"     ... and {len(ps) - args.dup_group_cap} more")
        else:
            print("  none")

        # The dangerous inverse: one name, several different documents.
        section("Same name, DIFFERENT content (ambiguous citation)")
        ambiguous = 0
        for name, entries in sorted(dups.items()):
            paths = [p for p, _ in entries if p in hashes]
            if len({hashes[p] for p in paths}) > 1:
                ambiguous += 1
                print(f"-- {name}")
                for p in paths[:args.dup_group_cap]:
                    print(f"     {hashes[p][:8]}  {rel(p, root)}")
                if len(paths) > args.dup_group_cap:
                    print(f"     ... and {len(paths) - args.dup_group_cap} more")
        if not ambiguous:
            print("  none")
        else:
            print(f"  {ambiguous} name(s) resolve to more than one document. "
                  "Any citation by filename alone is ambiguous.")

    section("Claims requiring verification (open these - never trust the name)")
    claim_files = []
    for p, s, m in files:
        n = os.path.basename(p).lower()
        if any(fnmatch.fnmatch(n, pat) for pat in CLAIM_PATTERNS):
            claim_files.append((p, s, m))
    if claim_files:
        for p, s, m in sorted(claim_files, key=lambda x: -x[2])[:40]:
            print(f"  {datetime.fromtimestamp(m):%Y-%m-%d}  {s:9d}  {rel(p, root)}")
        if len(claim_files) > 40:
            print(f"  ... and {len(claim_files) - 40} more")
        print("  Each is verified, contradicted or unverifiable. Never upgrade "
              "unverifiable to current.")
    else:
        print("  none")

    section("Possible credential-bearing files")
    discovered_paths = [p for p, _, _ in all_files] + [p for p, _ in metadata_failures]
    secrets = [p for p in discovered_paths if is_secret_hint_name(os.path.basename(p))]
    if secrets:
        print(f"  {len(secrets)} file(s) matched credential-name hints:")
        for p in secrets[:25]:
            print(f"     {rel(p, root)}")
        if len(secrets) > 25:
            print(f"     ... and {len(secrets) - 25} more")
        print("  Do not stage, copy, or index these. Flag to the owner before sharing "
              "the folder. Never copy a secret value into a report or journal.")
    else:
        print("  none detected by name")

    for index_path in (args.index_path or []):
        section(f"Index link check: {index_path}")
        idx = os.path.join(root, index_path)
        if os.path.isfile(idx):
            with open(idx, "r", encoding="utf-8", errors="replace") as fh:
                content = fh.read()
            markdown_links = []
            for match in MARKDOWN_LINK_RE.finditer(content):
                link = clean_local_reference(match.group(1))
                if link and not re.match(r"^(https?:|mailto:|#)", link):
                    markdown_links.append(link)
            markdown_links = list(dict.fromkeys(markdown_links))

            backticked_refs = [clean_local_reference(match.group(1))
                               for match in BACKTICK_PATH_RE.finditer(content)]
            backticked_refs = [ref for ref in dict.fromkeys(backticked_refs)
                               if ref and not re.match(r"^(https?:|mailto:|#)", ref)]
            # A relative link in AI_CONTEXT/CHAT_INDEX.md is relative to
            # AI_CONTEXT/, not to the root. Resolving everything against the
            # root reports working links as broken - the exact false alarm
            # that makes an agent distrust a healthy index. Accept either.
            idx_dir = os.path.dirname(idx)
            broken = [link for link in markdown_links
                      if not reference_resolves(link, idx_dir, root)]
            unresolved_refs = [ref for ref in backticked_refs
                               if not reference_resolves(ref, idx_dir, root)]

            print(f"  Markdown links checked: {len(markdown_links)}")
            if broken:
                print(f"  BROKEN MARKDOWN LINKS: {len(broken)}")
                for b in broken:
                    print(f"     {b}")
            else:
                print("  all Markdown links resolve")

            print(f"  Backticked path references checked: {len(backticked_refs)}")
            if unresolved_refs:
                print(f"  UNRESOLVED BACKTICKED REFERENCES: {len(unresolved_refs)} (review needed)")
                for ref in unresolved_refs:
                    print(f"     {ref}")
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
            print(f"  index NOT FOUND at {idx}")
            print("  An index named in navigation but absent is a top-tier "
                  "confusion source. Report it.")

    section("Instruction files found")
    instr = [(p, m) for p, _, m in all_files
             if os.path.basename(p).lower() in INSTRUCTION_NAMES]
    if instr:
        for p, m in sorted(instr, key=lambda x: rel(x[0], root)):
            print(f"  {datetime.fromtimestamp(m):%Y-%m-%d}  {rel(p, root)}")
        agent_files = [p for p, _ in instr
                       if os.path.basename(p).lower() not in ("readme.md",)]
        roots = [p for p in agent_files if os.path.dirname(p) == root]
        if len(roots) > 1:
            print("  Multiple root-level agent-instruction files - check for "
                  "conflicting scope. Record the conflict; resolve none unilaterally.")
    else:
        print("  NONE FOUND ANYWHERE.")
        print("  No AGENTS.md / CLAUDE.md / README.md in the tree means every agent's "
              "instructions live outside the folder and cannot be read by the next one. "
              "Report this as a finding.")

    if args.exclude:
        excluded_total = len(excluded) + len(excluded_metadata_failures)
        print(f"\nCoverage: {len(files)} of {discovered_files} files examined in detail; "
              f"{excluded_total} excluded by --exclude and classified by nothing. "
              "Say so in the report.")
    if detail_metadata_failures:
        print(f"Coverage gap: {len(detail_metadata_failures)} non-excluded directory "
              "entries could not be stat'ed and were not examined.")
    print(f"\nAudit complete. Nothing was written to {root}.")


if __name__ == "__main__":
    main()
