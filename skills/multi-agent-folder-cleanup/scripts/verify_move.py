#!/usr/bin/env python3
"""Move-map verification for multi-agent folder cleanup.

Never moves, copies, or deletes anything. It only reads a move map, hashes
files, and reports. Exits nonzero on any condition that should stop a move.

Move map: CSV with `source,target` (header optional) or JSON list of
{"source": ..., "target": ...}.

    python verify_move.py baseline  --map moves.csv --out /tmp/baseline.json
    python verify_move.py preflight --map moves.csv --path-threshold 240
    python verify_move.py verify    --baseline /tmp/baseline.json [--stage DIR]

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
import json
import os
import sys
from collections import Counter, defaultdict

CLOUD_ATTRS = {"OFFLINE": 0x1000, "RECALL_ON_OPEN": 0x40000, "RECALL_ON_DATA_ACCESS": 0x400000}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


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


def load_map(path):
    base = os.path.dirname(os.path.abspath(path))
    if path.lower().endswith(".json"):
        # utf-8-sig: tolerate a byte-order mark from Windows editors.
        with open(path, encoding="utf-8-sig") as fh:
            rows = json.load(fh)
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
    # header into a bogus '﻿source' pair and fail preflight.
    with open(path, newline="", encoding="utf-8-sig") as fh:
        for row in csv.reader(fh):
            if len(row) < 2:
                continue
            src, tgt = row[0].strip().lstrip("﻿"), row[1].strip()
            if not src or src.lower() in ("source", "src"):
                continue
            pairs.append((_resolve(src, base), _resolve(tgt, base)))
    if not pairs:
        sys.exit(f"No source,target pairs found in {path}")
    return pairs


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
    it, and normcase keeps it correct on case-insensitive filesystems."""
    if not root:
        return False
    try:
        return os.path.normcase(os.path.commonpath([path, root])) == os.path.normcase(root)
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
    return any(attrs & bit for bit in CLOUD_ATTRS.values())


def cmd_preflight(args):
    pairs = load_map(args.map)
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
    existing_targets = [t for _, t in pairs if os.path.exists(t)]
    long_paths = [t for _, t in pairs if len(t) > args.path_threshold]
    can_check = placeholder_check_available()
    placeholders = ([s for s, _ in pairs if os.path.isfile(s) and is_placeholder(s)]
                    if can_check else [])

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

    if target_root is None:
        print("  INCOMPATIBLE TARGET ROOTS: the targets share no common parent, so "
              "staging\n      cannot mirror them without collisions. Split this into "
              "one map per target root.")
        problems += 1

    for label, items in (("MISSING SOURCE", missing),
                         ("TARGET EXISTS", existing_targets),
                         ("PATH TOO LONG", long_paths),
                         ("NOT HYDRATED", placeholders),
                         ("DUPLICATED SOURCE", dupe_sources)):
        for i in items:
            print(f"  {label}: {i}")
            problems += 1
    for tgt, srcs in collisions.items():
        print(f"  COLLISION: {tgt}")
        for s in srcs:
            print(f"      <- {s}")
        problems += 1

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
    pairs = load_map(args.map)
    out = os.path.abspath(args.out)
    source_root = common_parent([s for s, _ in pairs])
    target_root = common_parent([t for _, t in pairs])
    if target_root is None:
        sys.exit("Targets span incompatible roots; use one approved target root per move map")
    for root in (source_root, target_root):
        if is_within(out, root):
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
    with open(out, "w", encoding="utf-8") as fh:
        json.dump({"target_root": target_root, "pairs": entries}, fh, indent=2)
    print(f"Baseline written: {out}  ({len(entries)} files hashed)")
    return 0


def cmd_verify(args):
    with open(args.baseline, encoding="utf-8") as fh:
        baseline = json.load(fh)
    entries = baseline["pairs"]
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
                and os.path.normcase(e["source"]) != os.path.normcase(e["target"])
                and os.path.exists(e["source"])):
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


def main():
    _safe_stdout()
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("preflight"); p.add_argument("--map", required=True)
    p.add_argument("--path-threshold", type=int, default=240); p.set_defaults(fn=cmd_preflight)

    b = sub.add_parser("baseline"); b.add_argument("--map", required=True)
    b.add_argument("--out", required=True); b.set_defaults(fn=cmd_baseline)

    v = sub.add_parser("verify"); v.add_argument("--baseline", required=True)
    v.add_argument("--stage")
    v.add_argument("--allow-source-present", action="store_true",
                   help="Final verify of an approved COPY: do not fail when sources remain.")
    v.set_defaults(fn=cmd_verify)

    args = ap.parse_args()
    sys.exit(args.fn(args))


if __name__ == "__main__":
    main()
