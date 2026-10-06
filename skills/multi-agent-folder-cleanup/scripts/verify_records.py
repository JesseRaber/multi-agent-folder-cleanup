#!/usr/bin/env python3
"""Byte-level checks for shared text records (R150/R154).

Read-only: never writes, rewrites or normalizes any file. It reports what it
measured so an agent can cite the output instead of asserting "verified".

Checks per file (Markdown or plain text):
  - readable, valid UTF-8 (first bad byte offset reported)
  - byte-order mark (finding unless --allow-bom)
  - line endings: CRLF / LF / lone CR counts; mixed or lone CR is a finding;
    --newline lf|crlf also enforces one style
  - mojibake markers outside code (UTF-8 read as cp1252, e.g. an em dash
    shown as U+00E2 U+20AC U+201D; also U+FFFD)
  - Markdown relative links resolve (URLs and #anchors are not checked)
  - Markdown tables: separator row present, same column count on every row

Optional comparisons:
  --compare TARGET=SOURCE   exact bytes / equal after newline normalization / differ
  --expect-sha256 PATH=HEX  SHA-256 of PATH must equal HEX (e.g. a recorded activation hash)

    python3 verify_records.py AGENTS.md PROJECT_INDEX.md AI_CONTEXT/SESSION_INDEX.md
    python3 verify_records.py AGENTS.md --compare AGENTS.md=Incoming/rules/AGENTS.md
    python3 verify_records.py AGENTS.md --expect-sha256 AGENTS.md=7ad0955b...
    python3 verify_records.py --json REGISTER.md

Exit status: 0 no findings, 1 findings, 2 usage or read error.
A pass proves only the properties listed above; it does not prove meaning,
adoption, cloud synchronization or that a link target is the right file.
"""

import argparse
import hashlib
import json
import os
import re
import sys
from urllib.parse import unquote

VERSION = "1.6.0"  # must equal SKILL.md metadata.version

BOM = b"\xef\xbb\xbf"
# Common UTF-8-read-as-cp1252/latin-1 sequences, plus the replacement character.
MOJIBAKE = re.compile("â€|â„¢|Ã[\u0080-¿]|Â[ -¿]|ï»¿|�")
FENCE = re.compile(r"^\s*(```|~~~)")
INLINE_CODE = re.compile(r"(`+)(.+?)\1")
LINK = re.compile(r"!?\[[^\]]*\]\(\s*(<[^>]*>|[^)\s]+)(?:\s+\"[^\"]*\")?\s*\)")
SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
TABLE_SEP_CELL = re.compile(r"^\s*:?-{1,}:?\s*$")


def strip_code(line):
    return INLINE_CODE.sub(lambda m: " " * len(m.group(0)), line)


def table_cells(line):
    s = strip_code(line).strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|") and not s.endswith("\\|"):
        s = s[:-1]
    return re.split(r"(?<!\\)\|", s)


def check_newlines(data, mode):
    crlf = data.count(b"\r\n")
    lf = data.count(b"\n") - crlf
    cr = data.count(b"\r") - crlf
    found = []
    if cr:
        found.append(f"line endings: {cr} lone CR")
    if crlf and lf:
        found.append(f"line endings: mixed ({crlf} CRLF, {lf} LF)")
    if mode == "lf" and crlf:
        found.append(f"line endings: {crlf} CRLF where --newline lf")
    if mode == "crlf" and lf:
        found.append(f"line endings: {lf} LF where --newline crlf")
    return {"crlf": crlf, "lf": lf, "lone_cr": cr}, found


def check_text(path, text, check_links):
    found = []
    lines = text.splitlines()
    base = os.path.dirname(os.path.abspath(path))
    in_fence = False
    table = []  # (lineno, line)

    def flush():
        if not table:
            return
        if len(table) == 1:
            found.append(f"line {table[0][0]}: isolated table row (no header or separator)")
            table.clear()
            return
        head = table[0]
        sep = table[1]
        width = len(table_cells(head[1]))
        sep_cells = table_cells(sep[1])
        if not all(TABLE_SEP_CELL.match(c) for c in sep_cells):
            found.append(f"line {sep[0]}: table has no separator row under header at line {head[0]}")
        for n, row in table:
            w = len(table_cells(row))
            if w != width:
                found.append(f"line {n}: table row has {w} columns, header has {width}")
        table.clear()

    for n, line in enumerate(lines, 1):
        if FENCE.match(line):
            flush()
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        plain = strip_code(line)
        m = MOJIBAKE.search(plain)
        if m:
            found.append(f"line {n}: mojibake marker {m.group(0)!r}")
        if line.lstrip().startswith("|"):
            table.append((n, line))
        else:
            flush()
        if not check_links:
            continue
        for lm in LINK.finditer(plain):
            target = lm.group(1)
            if target.startswith("<") and target.endswith(">"):
                target = target[1:-1]
            target = target.split("#", 1)[0].split("?", 1)[0]
            if not target or SCHEME.match(target) or target.startswith("//"):
                continue  # URL, mailto:, drive-letter path or pure anchor: not checked
            resolved = os.path.normpath(os.path.join(base, unquote(target)))
            if not os.path.exists(resolved):
                found.append(f"line {n}: link target not found: {target}")
    flush()
    return found


def check_file(path, args):
    result = {"path": path, "findings": []}
    try:
        with open(path, "rb") as fh:
            data = fh.read()
    except OSError as exc:
        result["error"] = f"cannot read ({exc.__class__.__name__}: {exc})"
        return result
    result["bytes"] = len(data)
    result["sha256"] = hashlib.sha256(data).hexdigest()
    f = result["findings"]
    if data.startswith(BOM):
        result["bom"] = True
        if not args.allow_bom:
            f.append("UTF-8 byte-order mark present")
    else:
        result["bom"] = False
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        f.append(f"not valid UTF-8 at byte {exc.start}")
        text = data.decode("utf-8", errors="replace")
        result["utf8"] = False
    else:
        result["utf8"] = True
    if text.startswith("﻿"):
        text = text[1:]
    result["newlines"], nl = check_newlines(data, args.newline)
    f.extend(nl)
    is_md = path.lower().endswith((".md", ".markdown"))
    if result["utf8"]:
        # Replacement characters from a failed decode would be double-reported.
        f.extend(check_text(path, text, check_links=is_md and not args.no_links))
    return result


def compare(target, source):
    with open(target, "rb") as a, open(source, "rb") as b:
        x, y = a.read(), b.read()
    if x == y:
        return "exact bytes"
    norm = lambda d: d.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    if norm(x) == norm(y):
        return "equal only after newline normalization"
    if norm(x).strip() == norm(y).strip() or \
            re.sub(rb"\s+", b"", x) == re.sub(rb"\s+", b"", y):
        return "differ (whitespace only)"
    return "differ"


def pair(value, label):
    if "=" not in value:
        raise argparse.ArgumentTypeError(f"{label} must be PATH=VALUE")
    left, right = value.split("=", 1)
    if not left or not right:
        raise argparse.ArgumentTypeError(f"{label} must be PATH=VALUE")
    return left, right


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", action="version", version=f"verify_records.py {VERSION}")
    ap.add_argument("files", nargs="*", help="Text/Markdown records to check")
    ap.add_argument("--newline", choices=("consistent", "lf", "crlf"), default="consistent",
                    help="Required line-ending style (default: any one style, not mixed)")
    ap.add_argument("--allow-bom", action="store_true", help="Do not report a UTF-8 BOM")
    ap.add_argument("--no-links", action="store_true", help="Skip Markdown link resolution")
    ap.add_argument("--compare", action="append", default=[],
                    type=lambda v: pair(v, "--compare"), metavar="TARGET=SOURCE")
    ap.add_argument("--expect-sha256", action="append", default=[],
                    type=lambda v: pair(v, "--expect-sha256"), metavar="PATH=HEX")
    ap.add_argument("--json", action="store_true", help="Machine-readable output")
    args = ap.parse_args(argv)
    if not args.files and not args.compare and not args.expect_sha256:
        ap.error("give at least one file, --compare or --expect-sha256")

    results = [check_file(p, args) for p in args.files]
    comparisons, hashes, errors = [], [], 0
    for target, source in args.compare:
        try:
            outcome = compare(target, source)
        except OSError as exc:
            outcome = f"error ({exc.__class__.__name__})"
            errors += 1
        comparisons.append({"target": target, "source": source, "result": outcome,
                            "finding": outcome != "exact bytes"})
    for path, want in args.expect_sha256:
        try:
            with open(path, "rb") as fh:
                got = hashlib.sha256(fh.read()).hexdigest()
        except OSError as exc:
            got = None
            errors += 1
        hashes.append({"path": path, "expected": want.lower(), "actual": got,
                       "finding": got != want.lower()})

    errors += sum(1 for r in results if "error" in r)
    findings = sum(len(r["findings"]) for r in results) + \
        sum(c["finding"] for c in comparisons) + sum(h["finding"] for h in hashes)

    if args.json:
        print(json.dumps({"version": VERSION, "files": results, "compare": comparisons,
                          "sha256": hashes, "findings": findings, "errors": errors},
                         indent=2, ensure_ascii=False))
    else:
        for r in results:
            if "error" in r:
                print(f"ERROR {r['path']}: {r['error']}")
                continue
            nl = r["newlines"]
            status = "PASS" if not r["findings"] else "FAIL"
            print(f"{status} {r['path']}  sha256={r['sha256']}  bytes={r['bytes']}  "
                  f"utf8={'yes' if r['utf8'] else 'NO'}  bom={'yes' if r['bom'] else 'no'}  "
                  f"CRLF={nl['crlf']} LF={nl['lf']} loneCR={nl['lone_cr']}")
            for item in r["findings"]:
                print(f"  - {item}")
        for c in comparisons:
            print(f"{'FAIL' if c['finding'] else 'PASS'} compare {c['target']} vs {c['source']}: {c['result']}")
        for h in hashes:
            print(f"{'FAIL' if h['finding'] else 'PASS'} sha256 {h['path']}: "
                  f"expected {h['expected']}, actual {h['actual'] or 'unreadable'}")
        print(f"verify_records.py {VERSION}: {len(results)} file(s), {findings} finding(s), {errors} error(s). "
              "Checks: UTF-8, BOM, line endings, mojibake, relative links, table shape"
              + (", comparisons" if comparisons else "") + (", hashes" if hashes else "") + ".")
    if errors:
        return 2
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
