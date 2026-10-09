#!/usr/bin/env python3
"""Move-map verification for multi-agent folder cleanup.

Never moves, copies, or deletes target files. It reads maps, hashes files,
reports, and creates explicitly requested new proposal/baseline evidence.
Exits nonzero on any measured condition that should stop a move.

Move map: CSV with `source,target` (header optional) or JSON list of
{"source": ..., "target": ...}.

    python verify_move.py review --map moves.csv --root PROJECT --approval-out /tmp/proposal.json
    python verify_move.py preflight --map moves.csv --root PROJECT --approval /tmp/proposal.json
    python verify_move.py baseline --map moves.csv --root PROJECT --approval /tmp/proposal.json --out /tmp/baseline.json
    python verify_move.py preflight --map moves.csv --root PROJECT --approval /tmp/proposal.json --baseline /tmp/baseline.json
    python verify_move.py verify --baseline /tmp/baseline.json --root PROJECT [--stage DIR] [--approval /tmp/proposal.json]

Pass --root PROJECT to review, preflight, baseline and verify to refuse any source or
target outside the project folder (and any baseline written inside it).

A proposal receipt identifies a plan; it does not prove owner consent.
Checks do not lock other writers. Legacy unguarded commands remain supported.

Write the baseline OUTSIDE the folder being reorganized.

Relative paths in a move map resolve against the map file's own folder, not
the current directory, so preflight, baseline and verify agree no matter where
they are run from. A UTF-8 byte-order mark (Excel "CSV UTF-8") is accepted.

Final verify (no --stage) also requires every source to be gone: a copy that
leaves the source in place is a dual tree, not a move. Pass
--allow-source-present only when the approved plan is a copy.
"""

import argparse
import csv
import hashlib
import html
import io
import json
import os
import stat
import sys
from collections import Counter, defaultdict

VERSION = "1.6.4"  # must equal SKILL.md metadata.version

CLOUD_ATTRS = {"OFFLINE": 0x1000, "RECALL_ON_OPEN": 0x40000, "RECALL_ON_DATA_ACCESS": 0x400000}


SAFE_STOP = None  # common folder of the plan; set before any hashing


def fold(path):
    """Comparison key for paths. Windows normcase already lowercases; macOS
    volumes are case-insensitive by default but normcase is a no-op there, so
    lowercase explicitly. Linux stays case-sensitive."""
    path = os.path.normcase(path)
    return path.lower() if sys.platform == "darwin" else path


def is_fs_root(path):
    return bool(path) and os.path.dirname(path) == path


def win_long_path(path):
    """Extended-length form for Win32 calls on paths near MAX_PATH."""
    if len(path) < 240 or path.startswith("\\\\?\\"):
        return path
    if path.startswith("\\\\"):
        return "\\\\?\\UNC\\" + path[2:]
    return "\\\\?\\" + path


def same_file(a, b):
    try:
        return os.path.samefile(a, b)
    except OSError:
        return False


def outside_root(paths, root):
    """Paths that are not the project root or below it (R094)."""
    if not root:
        return []
    root = os.path.abspath(root)
    return [p for p in paths if not is_within(os.path.abspath(p), root)]


def plan_stop(paths):
    try:
        return os.path.commonpath([os.path.dirname(os.path.abspath(p)) for p in paths])
    except ValueError:
        return None  # different drives: check every component


def sha256(path):
    require_safe_path(path, SAFE_STOP)
    if is_placeholder(path):
        raise OSError('NOT HYDRATED: refusing content read')
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def require_safe_path(path, stop=None):
    """Reject link traversal in existing components below `stop`.

    Components above `stop` (the common folder of the plan) are the owner's
    chosen location, such as a redirected profile or macOS /tmp. Point-in-time
    only: this does not lock paths against a later replacement.
    """
    current = os.path.abspath(path)
    stop = fold(os.path.abspath(stop)) if stop else None
    while True:
        if stop and fold(current) == stop:
            break
        try:
            info = os.lstat(current)
        except FileNotFoundError:
            pass  # targets may not exist yet; their ancestors still matter
        else:
            tag = getattr(info, 'st_reparse_tag', 0)
            if stat.S_ISLNK(info.st_mode) or tag & 0x20000000:
                raise OSError('LINK PATH: symlink or junction traversal refused')
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent


def path_problems(pairs):
    global SAFE_STOP
    problems = []
    stop = SAFE_STOP = plan_stop([p for pair in pairs for p in pair])
    for src, target in pairs:
        for path in (src, target):
            try:
                require_safe_path(path, stop)
            except OSError as exc:
                problems.append((path, str(exc)))
    return problems


def windows_read_probe(path):
    """Momentary exclusive-read probe, not a lease or a guarantee of future access."""
    if os.name != 'nt':
        return
    import ctypes
    from ctypes import wintypes
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    create = kernel.CreateFileW
    create.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                       wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    create.restype = wintypes.HANDLE
    close = kernel.CloseHandle
    close.argtypes = [wintypes.HANDLE]
    close.restype = wintypes.BOOL
    handle = create(win_long_path(os.path.abspath(path)), 0x80000000, 0, None, 3, 0, None)
    if handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    close(handle)


def _safe_stdout():
    """Never crash on a path the console cannot encode (Windows cp1252)."""
    try:
        if sys.stdout.isatty():
            sys.stdout.reconfigure(errors="backslashreplace")
        else:
            sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    except (AttributeError, ValueError):
        pass


def _resolve(value, base):
    value = os.path.expanduser(value.strip())
    return os.path.abspath(value if os.path.isabs(value) else os.path.join(base, value))


def _parse_map(path, data):
    base = os.path.dirname(os.path.abspath(path))
    if path.lower().endswith(".json"):
        # utf-8-sig: tolerate a byte-order mark from Windows editors.
        rows = json.loads(data.decode("utf-8-sig"))
        if isinstance(rows, dict):
            rows = rows.get("pairs") or rows.get("moves") or []
        try:
            pairs = [(_resolve(r["source"], base), _resolve(r["target"], base))
                     for r in rows]
        except (KeyError, TypeError):
            sys.exit(f"JSON map must be a list of {{\"source\": ..., \"target\": ...}}: {path}")
        if not pairs:
            sys.exit(f"No source,target pairs found in {path}")
        return pairs
    pairs = []
    # utf-8-sig: Excel's "CSV UTF-8" writes a BOM, which used to turn the
    # header into a bogus 'U+FEFF + source' pair and fail preflight.
    with io.StringIO(data.decode("utf-8-sig"), newline="") as fh:
        for row in csv.reader(fh):
            if len(row) < 2:
                continue
            src, tgt = row[0].strip().lstrip(chr(0xFEFF)), row[1].strip()
            if not src or src.lower() in ("source", "src"):
                continue
            pairs.append((_resolve(src, base), _resolve(tgt, base)))
    if not pairs:
        sys.exit(f"No source,target pairs found in {path}")
    return pairs


def pairs_digest(pairs):
    # Include ordered, resolved paths; raw bytes alone do not bind relative paths.
    encoded = json.dumps(pairs, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def read_plan(path):
    path = os.path.abspath(path)
    with open(path, "rb") as fh:
        data = fh.read()
    pairs = _parse_map(path, data)
    identity = {"schema_version": 1, "map_path": path,
                "map_sha256": hashlib.sha256(data).hexdigest(),
                "resolved_pairs_sha256": pairs_digest(pairs), "row_count": len(pairs)}
    return pairs, identity


def load_map(path):
    return read_plan(path)[0]


def check_approval(identity, path):
    if not path:
        return
    with open(path, encoding="utf-8") as fh:
        receipt = json.load(fh)
    if not isinstance(receipt, dict) or any(receipt.get(k) != v for k, v in identity.items()):
        sys.exit("APPROVAL MISMATCH — map bytes, location, resolved paths or row count changed. "
                 "Stop and obtain approval of a new generated review.")


def check_plan_unchanged(path, identity):
    if read_plan(path)[1] != identity:
        sys.exit("MAP CHANGED during this check — stop and review again.")


def baseline_identity(baseline):
    identity = baseline.get("map_identity")
    if identity and (identity.get("row_count") != len(baseline["pairs"]) or
                     identity.get("resolved_pairs_sha256") != pairs_digest(
                         [(e["source"], e["target"]) for e in baseline["pairs"]])):
        sys.exit("BASELINE PLAN MISMATCH — baseline paths differ from its recorded plan.")
    return identity


def check_baseline_sources(path, identity):
    with open(path, encoding="utf-8") as fh:
        baseline = json.load(fh)
    if baseline_identity(baseline) != identity:
        sys.exit("BASELINE PLAN MISMATCH — use the baseline for this approved plan.")
    global SAFE_STOP
    SAFE_STOP = plan_stop([p for e in baseline["pairs"] for p in (e["source"], e["target"])])
    for entry in baseline["pairs"]:
        src = entry["source"]
        if not os.path.isfile(src) or sha256(src) != entry["sha256"]:
            sys.exit(f"SOURCE CHANGED since baseline: {src}. Stop; preserve staging and reconcile.")


def markdown_path(value):
    # HTML code cells preserve backslashes/backticks and escape table delimiters.
    return "<code>" + html.escape(value).replace("|", "&#124;").replace(
        "\r", "&#13;").replace("\n", "&#10;") + "</code>"


def cmd_review(args):
    pairs, identity = read_plan(args.map)
    unsafe = root_problems(pairs, args.root)
    if unsafe:
        for path, why in unsafe:
            print(f'  UNSAFE PATH: {path}: {why}')
        return 1
    check_plan_unchanged(args.map, identity)
    if args.approval_out:
        # A receipt identifies a proposal; its existence is not human approval.
        with open(args.approval_out, "x", encoding="utf-8") as fh:
            json.dump(identity, fh, indent=2)
            fh.write("\n")
    print("# PROPOSED move-map review — not yet approved")
    print(f"Map: {markdown_path(identity['map_path'])}")
    print(f"SHA-256: {identity['map_sha256']}")
    print(f"Resolved-pairs SHA-256: {identity['resolved_pairs_sha256']}")
    print(f"Rows: {identity['row_count']}")
    print("\n| ID | Source (absolute) | Target (absolute) |")
    print("|---|---|---|")
    for number, (src, dst) in enumerate(pairs, 1):
        print(f"| M{number:03d} | {markdown_path(src)} | {markdown_path(dst)} |")
    print("\nIDs are ordinal within this exact plan. Owner decisions and non-move patches "
          "must be reviewed separately. A receipt does not authorize execution.")
    return 0


def common_parent(paths):
    """Common parent directory of a set of paths, or None for mixed roots.

    Staging mirrors the target tree relative to this root. Without it, staging
    was keyed on basename alone, so two same-named files from different source
    folders overwrote each other in staging and the second one verified against
    the first one's bytes - a silent corruption inside the very step meant to
    catch corruption.
    """
    try:
        return os.path.commonpath([os.path.dirname(p) for p in paths])
    except ValueError:
        return None


def is_within(path, root):
    """True when path is root or below it. Compares whole segments, so a
    sibling named like the root ('...\\Projects-old') is not treated as inside
    it, and fold() keeps it correct on case-insensitive filesystems."""
    if not root:
        return False
    try:
        return fold(os.path.commonpath([fold(path), fold(root)])) == fold(root)
    except ValueError:
        return False


def placeholder_check_available():
    """True only where cloud-placeholder detection actually works.

    Needs Windows file attributes. The POSIX fallback that used to live here
    guessed from st_blocks vs st_size; it was never validated against a real
    OneDrive sparse file and would false-positive on any legitimately sparse
    one. Reporting '0 placeholders' from a check that cannot run is the same
    silent failure as an empty exclusion table - say NOT CHECKED instead.
    """
    try:
        return hasattr(os.stat(os.getcwd()), "st_file_attributes")
    except OSError:
        return False


def is_placeholder(path):
    """Windows-only. Callers must gate on placeholder_check_available()."""
    try:
        st = os.stat(path, follow_symlinks=False)
    except OSError:
        return False
    attrs = getattr(st, "st_file_attributes", None)
    if attrs is None:
        return False
    return bool(attrs & (0x1000 | 0x400000) or (attrs & 0x400 and attrs & 0x40000))


def root_problems(pairs, root):
    return [(p, "OUTSIDE ROOT: not inside --root " + os.path.abspath(root))
            for p in outside_root([x for pair in pairs for x in pair], root)]


def cmd_preflight(args):
    pairs, identity = read_plan(args.map)
    check_approval(identity, args.approval)
    unsafe = root_problems(pairs, args.root) + path_problems(pairs)
    if unsafe:
        for path, why in unsafe:
            print(f'  UNSAFE PATH: {path}: {why}')
        return 1
    if args.baseline:
        if not args.approval:
            sys.exit("A pre-move baseline check requires --approval.")
        check_baseline_sources(args.baseline, identity)
    problems = 0
    target_root = common_parent([t for _, t in pairs])

    missing = [s for s, _ in pairs if not os.path.isfile(s)]
    # Case-insensitive: 'A.md' and 'a.md' are one file on Windows, OneDrive,
    # SharePoint and default macOS volumes, which is where these moves land.
    by_target = defaultdict(list)
    for s, t in pairs:
        by_target[os.path.normcase(t).lower()].append((s, t))
    collisions = {group[0][1]: [s for s, _ in group]
                  for group in by_target.values() if len(group) > 1}
    # A case-only rename (readme.md -> README.md) on a case-insensitive volume
    # sees its own source as the "existing" target; that is not a collision.
    existing_targets = [t for s, t in pairs
                        if os.path.exists(t) and not (s != t and s.lower() == t.lower()
                                                      and same_file(s, t))]
    long_paths = [t for _, t in pairs if len(t) > args.path_threshold]
    can_check = placeholder_check_available()
    placeholders = ([s for s, _ in pairs if os.path.isfile(s) and is_placeholder(s)]
                    if can_check else [])
    unavailable = []
    if os.name == 'nt':
        for src, _ in pairs:
            if src in missing or src in placeholders:
                continue
            try:
                windows_read_probe(src)
            except OSError as exc:
                unavailable.append(f'{src} (Windows error {exc.winerror})')

    source_counts = Counter(os.path.normcase(s).lower() for s, _ in pairs)
    seen = set()
    dupe_sources = []
    for s, _ in pairs:
        key = os.path.normcase(s).lower()
        if source_counts[key] > 1 and key not in seen:
            seen.add(key)
            dupe_sources.append(s)

    print(f"Move map: {args.map}")
    print(f"  pairs:                    {len(pairs)}")
    print(f"  missing sources:          {len(missing)}")
    print(f"  target collisions:        {len(collisions)}")
    print(f"  duplicated sources:       {len(dupe_sources)}")
    print(f"  targets already existing: {len(existing_targets)}")
    print(f"  targets over {args.path_threshold} chars:    {len(long_paths)}")
    if can_check:
        print(f"  cloud placeholders:       {len(placeholders)}")
    else:
        print("  cloud placeholders:       NOT CHECKED - needs Windows")
    print(f"  common target root:       {target_root or 'INCOMPATIBLE ROOTS'}")
    print(f"  exclusive-read probe:     {len(unavailable)} unavailable (point-in-time)"
          if os.name == 'nt' else '  exclusive-read probe:     NOT CHECKED - needs Windows')

    if target_root is None:
        print("  INCOMPATIBLE TARGET ROOTS: the targets share no common parent, so "
              "staging\n      cannot mirror them without collisions. Split this into "
              "one map per target root.")
        problems += 1

    for label, items in (("MISSING SOURCE", missing),
                         ("TARGET EXISTS", existing_targets),
                         ("PATH TOO LONG", long_paths),
                         ("NOT HYDRATED", placeholders),
                         ("LOCKED OR UNREADABLE", unavailable),
                         ("DUPLICATED SOURCE", dupe_sources)):
        for i in items:
            print(f"  {label}: {i}")
            problems += 1
    for tgt, srcs in collisions.items():
        print(f"  COLLISION: {tgt}")
        for s in srcs:
            print(f"      <- {s}")
        problems += 1

    check_plan_unchanged(args.map, identity)
    if problems:
        print(f"\nPREFLIGHT FAILED — {problems} condition(s) must be resolved before moving.")
        if not can_check:
            print("Hydration was NOT verified on this platform - re-run preflight on "
                  "Windows before an Execute pass on a synced folder.")
        return 1
    if can_check:
        print("\nPreflight clean. Safe to baseline and stage.")
    else:
        # Never let a check that could not run read as a check that passed.
        print("\nPreflight clean EXCEPT hydration, which was not checked on this "
              "platform.\nEverything above (collisions, missing sources, path length) "
              "is platform-independent\nand trustworthy. On a OneDrive/SharePoint "
              "folder, re-run preflight with\nWindows-native Python before staging - "
              "a cloud placeholder moves as a stub.")
    return 0


def cmd_baseline(args):
    pairs, identity = read_plan(args.map)
    check_approval(identity, args.approval)
    unsafe = root_problems(pairs, args.root) + path_problems(pairs)
    if unsafe:
        sys.exit('UNSAFE PATH: ' + '; '.join(f'{path}: {why}' for path, why in unsafe))
    out = os.path.abspath(args.out)
    require_safe_path(out, os.path.dirname(out))
    source_root = common_parent([s for s, _ in pairs])
    target_root = common_parent([t for _, t in pairs])
    if target_root is None:
        sys.exit("Targets span incompatible roots; use one approved target root per move map")
    guarded = [args.root] if args.root else []
    for root, side in ((source_root, [s for s, _ in pairs]), (target_root, [t for _, t in pairs])):
        # A map spanning top-level folders has '/' (or a drive) as its common
        # root, which would refuse every --out. Guard each pair's folder instead.
        guarded += sorted({os.path.dirname(p) for p in side}) if is_fs_root(root) else [root]
    for root in guarded:
        if is_within(out, os.path.abspath(root)):
            sys.exit("Refusing to write the baseline inside the source or target tree: "
                     f"{out}\n(The baseline is the recovery record; a move must not be "
                     "able to disturb it.)")

    entries = []
    for src, tgt in pairs:
        if not os.path.isfile(src):
            sys.exit(f"Missing source, run preflight first: {src}")
        try:
            digest = sha256(src)
        except OSError as exc:
            # On a synced folder this is usually a cloud placeholder or an open
            # lock. Either way there is no baseline for this file, so the move
            # cannot be verified - stop rather than record a partial baseline.
            sys.exit(f"Cannot read source ({exc.__class__.__name__}): {src}\n"
                     "Hydrate the file or close whatever holds it, then re-run. "
                     "A baseline missing even one file cannot verify the move.")
        entries.append({"source": src, "target": tgt,
                        "size": os.path.getsize(src), "sha256": digest})

    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    check_plan_unchanged(args.map, identity)
    with open(out, "x", encoding="utf-8") as fh:
        json.dump({"target_root": target_root, "map_identity": identity, "pairs": entries}, fh, indent=2)
    print(f"Baseline written: {out}  ({len(entries)} files hashed)")
    return 0


def cmd_verify(args):
    with open(args.baseline, encoding="utf-8") as fh:
        baseline = json.load(fh)
    identity = baseline_identity(baseline)
    if args.approval:
        if not identity:
            sys.exit("Legacy baseline has no map identity; cannot bind --approval.")
        check_approval(identity, args.approval)
    entries = baseline["pairs"]
    escaped = outside_root([p for e in entries for p in (e["source"], e["target"])], args.root)
    if escaped:
        sys.exit("OUTSIDE ROOT: baseline paths are not inside --root: " + "; ".join(escaped))
    global SAFE_STOP
    SAFE_STOP = plan_stop([p for e in entries for p in (e["source"], e["target"])]
                          + ([os.path.join(os.path.abspath(args.stage), "x")] if args.stage else []))
    # Baselines written before target_root was recorded still verify: recompute it.
    target_root = baseline.get("target_root") or common_parent(
        [e["target"] for e in entries])
    if args.stage and not target_root:
        sys.exit("Baseline targets have incompatible roots; cannot resolve a safe "
                 "staging tree")

    ok = missing = mismatch = still_at_source = 0
    for e in entries:
        if args.stage:
            # Mirror the target tree under staging. Flattening to basename lets
            # two same-named files from different folders overwrite each other.
            relative_target = os.path.relpath(e["target"], target_root)
            check = os.path.abspath(os.path.join(args.stage, relative_target))
            if not is_within(check, os.path.abspath(args.stage)):
                print(f"  UNSAFE staged path (escapes the staging root): {check}")
                mismatch += 1
                continue
            label = "staged"
        else:
            check = e["target"]
            label = "target"
        if not os.path.isfile(check):
            print(f"  MISSING at {label}: {check}")
            missing += 1
            continue
        try:
            digest = sha256(check)
        except OSError as exc:
            print(f"  UNREADABLE ({exc.__class__.__name__}): {check}")
            mismatch += 1
            continue
        if digest != e["sha256"]:
            print(f"  HASH MISMATCH: {check}")
            mismatch += 1
            continue
        ok += 1
        # A verified target with the source still present is a copy - the
        # dual-tree state this protocol exists to prevent - not a move.
        if (not args.stage and not args.allow_source_present
                and fold(e["source"]) != fold(e["target"])
                and os.path.exists(e["source"])
                and not same_file(e["source"], check)):
            print(f"  STILL AT SOURCE (copied, not moved): {e['source']}")
            still_at_source += 1

    print(f"\nVerified {ok}/{len(entries)}   missing {missing}   mismatched {mismatch}"
          + ("" if args.stage else f"   still at source {still_at_source}"))
    if still_at_source:
        print("Sources still present: this is a dual tree, not a completed move. "
              "Finish or reverse the move; use --allow-source-present only for an "
              "approved copy.")
    if missing or mismatch or still_at_source:
        print("VERIFY FAILED — stop. Do not remove staging or source folders.")
        return 1
    print("All files verified. Staging may be removed once sources are confirmed empty.")
    return 0


ROOT_HELP = "Project folder; refuse sources/targets outside it (and a baseline inside it)"


def main():
    _safe_stdout()
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", action="version", version=f"verify_move.py {VERSION}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("review", help="Render the exact map and optionally save its proposal identity")
    r.add_argument("--map", required=True)
    r.add_argument("--root", help=ROOT_HELP)
    r.add_argument("--approval-out", help="New receipt path; never overwrites an existing file")
    r.set_defaults(fn=cmd_review)

    p = sub.add_parser("preflight"); p.add_argument("--map", required=True)
    p.add_argument("--approval", help="Receipt identifying the owner-approved review")
    p.add_argument("--baseline", help="Also require unchanged baselined sources before moving")
    p.add_argument("--path-threshold", type=int, default=240)
    p.add_argument("--root", help=ROOT_HELP); p.set_defaults(fn=cmd_preflight)

    b = sub.add_parser("baseline"); b.add_argument("--map", required=True)
    b.add_argument("--approval", help="Receipt identifying the owner-approved review")
    b.add_argument("--out", required=True)
    b.add_argument("--root", help=ROOT_HELP); b.set_defaults(fn=cmd_baseline)

    v = sub.add_parser("verify"); v.add_argument("--baseline", required=True)
    v.add_argument("--stage")
    v.add_argument("--root", help=ROOT_HELP)
    v.add_argument("--approval", help="Bind verification to the approved plan identity")
    v.add_argument("--allow-source-present", action="store_true",
                   help="Final verify of an approved COPY: do not fail when sources remain.")
    v.set_defaults(fn=cmd_verify)

    args = ap.parse_args()
    if not args.root:
        location = os.path.abspath(os.path.dirname(getattr(args, "map", None) or args.baseline))
        print("WARNING: --root was not supplied; source and target paths are not confined "
              f"to a project folder. Relative paths resolve against {location}", file=sys.stderr)
    try:
        sys.exit(args.fn(args))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        sys.exit(f"CHECK FAILED — {exc.__class__.__name__}: {exc}")


if __name__ == "__main__":
    main()
