#!/usr/bin/env python3
"""v1.4.1 review fix: link checks stop at the chosen root / plan folder.

A project under a symlinked or junctioned ancestor (macOS /tmp, a redirected
Windows profile) must still be readable; a link inside the root or plan must
still be refused.
"""
from __future__ import annotations
import os, subprocess, sys, tempfile, unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/multi-agent-folder-cleanup/scripts"


def run(*args, check=False):
    return subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL, check=check)


@unittest.skipIf(os.name == "nt", "POSIX symlink fixture")
class LinkedAncestorTests(unittest.TestCase):
    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        base = Path(self._t.name)
        real = base / "real"
        (real / "proj/a").mkdir(parents=True)
        (real / "proj/b").mkdir()
        (real / "proj/a/x.md").write_text("same\n")
        (real / "proj/b/x.md").write_text("same\n")
        (base / "alias").symlink_to(real, target_is_directory=True)
        self.base, self.root = base, base / "alias/proj"

    def tearDown(self):
        self._t.cleanup()

    def test_audit_reads_files_under_linked_ancestor(self):
        out = run(SCRIPTS / "audit_folder.py", "--root", self.root, "--hash-files").stdout
        self.assertNotIn("READ BLOCKED", out)
        self.assertIn("1 groups, 2 files", out)

    def test_link_inside_root_still_blocked(self):
        (self.root / "inner").symlink_to(self.root / "a", target_is_directory=True)
        (self.root / "c").mkdir()
        (self.root / "c/inside").symlink_to(self.root / "a/x.md")
        out = run(SCRIPTS / "audit_folder.py", "--root", self.root, "--hash-files").stdout
        self.assertIn("READ BLOCKED", out)

    def test_move_plan_under_linked_ancestor(self):
        m = self.root / "moves.csv"
        m.write_text("source,target\na/x.md,dst/x.md\n")
        r = run(SCRIPTS / "verify_move.py", "preflight", "--map", m)
        self.assertNotIn("UNSAFE PATH", r.stdout)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        b = self.base / "b.json"
        self.assertEqual(run(SCRIPTS / "verify_move.py", "baseline", "--map", m, "--out", b).returncode, 0)

    def test_link_inside_plan_refused(self):
        (self.root / "via").symlink_to(self.root / "a", target_is_directory=True)
        m = self.root / "moves.csv"
        m.write_text("source,target\nvia/x.md,dst/x.md\n")
        r = run(SCRIPTS / "verify_move.py", "preflight", "--map", m)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("UNSAFE PATH", r.stdout)


if __name__ == "__main__":
    unittest.main()
