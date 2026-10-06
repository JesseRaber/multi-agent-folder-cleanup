"""R150/R154: scripts/verify_records.py — read-only shared-record checker."""

from pathlib import Path
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "skills/multi-agent-folder-cleanup/scripts/verify_records.py"


def run(*args, cwd=None):
    proc = subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                          capture_output=True, text=True, encoding="utf-8", cwd=cwd)
    return proc.returncode, proc.stdout + proc.stderr


class VerifyRecordsTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="verify-records-")
        self.dir = Path(self._tmp.name)
        (self.dir / "sub dir").mkdir()
        (self.dir / "sub dir" / "target é.md").write_bytes(b"# t\n")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def write(self, name: str, data: bytes) -> Path:
        path = self.dir / name
        path.write_bytes(data)
        return path

    def assertPass(self, *args) -> str:
        code, out = run(*args)
        self.assertEqual(code, 0, out)
        return out

    def assertFinding(self, needle: str, *args) -> str:
        code, out = run(*args)
        self.assertEqual(code, 1, out)
        self.assertIn(needle, out)
        return out

    def test_version_matches_skill(self) -> None:
        skill = (REPO / "skills/multi-agent-folder-cleanup/SKILL.md").read_text(encoding="utf-8")
        code, out = run("--version")
        self.assertEqual(code, 0)
        version = out.strip().split()[-1]
        declared = re.search(r"^\s+version:\s*[\"']?([0-9.]+)", skill, re.M).group(1)
        self.assertEqual(version, declared)

    def test_clean_lf_and_clean_crlf_pass(self) -> None:
        lf = self.write("lf.md", "# Title — ok\n\n| A | B |\n|---|---|\n| 1 | 2 |\n".encode())
        crlf = self.write("crlf.md", b"# T\r\n\r\n| A |\r\n|:--:|\r\n| x |\r\n")
        self.assertPass(lf, crlf)

    def test_mixed_and_lone_cr_line_endings_fail(self) -> None:
        self.assertFinding("mixed (1 CRLF, 1 LF)", self.write("m.md", b"a\r\nb\n"))
        self.assertFinding("lone CR", self.write("c.md", b"a\rb\n"))

    def test_newline_mode_is_enforced(self) -> None:
        crlf = self.write("x.md", b"a\r\nb\r\n")
        self.assertPass(crlf, "--newline", "crlf")
        self.assertFinding("CRLF where --newline lf", crlf, "--newline", "lf")
        self.assertFinding("LF where --newline crlf", self.write("y.md", b"a\n"), "--newline", "crlf")

    def test_bom_is_reported_unless_allowed(self) -> None:
        bom = self.write("bom.md", b"\xef\xbb\xbf# t\n")
        self.assertFinding("byte-order mark", bom)
        self.assertPass(bom, "--allow-bom")

    def test_invalid_utf8_fails_with_offset(self) -> None:
        self.assertFinding("not valid UTF-8 at byte 3", self.write("bad.md", b"abc\x96def\n"))

    def test_mojibake_fails_but_not_inside_code(self) -> None:
        damaged = "— dash".encode("utf-8").decode("cp1252").encode("utf-8")  # em dash read as cp1252
        self.assertFinding("mojibake marker", self.write("moj.md", b"text " + damaged + b"\n"))
        self.assertPass(self.write("quoted.md", "Example: `â€”` was the bug.\n\n```\nâ€”\n```\n".encode()))

    def test_relative_links_resolve_and_dead_links_fail(self) -> None:
        ok = self.write("ok.md", b"[a](<sub dir/target \xc3\xa9.md>) [b](sub%20dir/target%20%C3%A9.md#x) "
                                  b"[u](https://example.com/x) [m](mailto:a@b.c) [h](#top)\n")
        self.assertPass(ok)
        self.assertFinding("link target not found: missing/file.md",
                           self.write("dead.md", b"see [x](missing/file.md)\n"))

    def test_links_inside_code_are_ignored(self) -> None:
        self.assertPass(self.write("code.md", b"`[x](nope.md)`\n\n```\n[y](nope.md)\n```\n"))

    def test_table_shape_findings(self) -> None:
        self.assertFinding("table row has 3 columns, header has 2",
                           self.write("t1.md", b"| A | B |\n|---|---|\n| 1 | 2 | 3 |\n"))
        self.assertFinding("no separator row",
                           self.write("t2.md", b"| A | B |\n| 1 | 2 |\n"))
        # Escaped pipes and pipes in code spans are not column breaks.
        self.assertPass(self.write("t3.md", b"| A | B |\n|---|---|\n| a \\| b | `x|y` |\n"))

    def test_rows_split_from_their_table_are_caught(self) -> None:
        # Rows appended under a later heading (the 2026-10-06 register incident).
        data = b"| ID | P |\n|---|---|\n| R1 | x |\n\n## Later\n\n| R2 | y |\n| R3 | z |\n"
        self.assertFinding("no separator row", self.write("split.md", data))
        one = b"| ID | P |\n|---|---|\n| R1 | x |\n\n## Later\n\n| R2 | y |\n"
        self.assertFinding("isolated table row", self.write("one.md", one))

    def test_compare_reports_exact_normalized_and_different(self) -> None:
        a = self.write("a.md", b"x\ny\n")
        same = self.write("b.md", b"x\ny\n")
        crlf = self.write("c.md", b"x\r\ny\r\n")
        padded = self.write("d.md", b"x\n\n\ny\n")
        other = self.write("e.md", b"z\n")
        self.assertPass("--compare", f"{a}={same}")
        self.assertFinding("equal only after newline normalization", "--compare", f"{a}={crlf}")
        self.assertFinding("differ (whitespace only)", "--compare", f"{a}={padded}")
        self.assertFinding("compare", "--compare", f"{a}={other}")

    def test_expected_sha256(self) -> None:
        path = self.write("h.md", b"hello\n")
        digest = hashlib.sha256(b"hello\n").hexdigest()
        self.assertPass("--expect-sha256", f"{path}={digest.upper()}")
        self.assertFinding("expected", "--expect-sha256", f"{path}={'0' * 64}")

    def test_unreadable_file_is_exit_2(self) -> None:
        code, out = run(self.dir / "nope.md")
        self.assertEqual(code, 2, out)

    def test_json_output(self) -> None:
        path = self.write("j.md", b"a\r\nb\n")
        code, out = run("--json", path)
        self.assertEqual(code, 1)
        data = json.loads(out)
        self.assertEqual(data["files"][0]["newlines"], {"crlf": 1, "lf": 1, "lone_cr": 0})
        self.assertEqual(data["findings"], 1)

    def test_never_modifies_inputs(self) -> None:
        paths = [self.write("n1.md", b"\xef\xbb\xbfa\r\nb\n"), self.write("n2.md", b"[x](gone.md)\n")]
        before = [(p.read_bytes(), os.stat(p).st_mtime_ns) for p in paths]
        run(*paths, "--compare", f"{paths[0]}={paths[1]}")
        self.assertEqual(before, [(p.read_bytes(), os.stat(p).st_mtime_ns) for p in paths])
        self.assertEqual(sorted(x.name for x in self.dir.iterdir()),
                         sorted(["sub dir", "n1.md", "n2.md"]))


if __name__ == "__main__":
    unittest.main()
