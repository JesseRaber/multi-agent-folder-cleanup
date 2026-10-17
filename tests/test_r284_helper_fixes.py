"""Behavioral regressions for the local R284 candidate; no release bump."""
from pathlib import Path
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = Path(os.environ.get("R284_TEST_SCRIPTS", REPO / "skills/multi-agent-folder-cleanup/scripts"))
ENGINES = ["python"] + [e for e in ("powershell.exe", "pwsh") if shutil.which(e)]


class R284Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="r284 ")
        self.root = Path(self.tmp.name) / "project space"
        self.root.mkdir()
        self.scratch = self.root / "AI_CONTEXT/scratch/test"
        self.scratch.mkdir(parents=True)
        self.target = self.root / "target file.md"
        self.target.write_text("old content\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def pending(self, name, target=None, status="PENDING", new="new content"):
        target = target or str(self.target)
        digest = hashlib.sha256(self.target.read_bytes()).hexdigest()
        (self.scratch / name).write_text(
            f"Status: {status}\nTarget: {target}\nBase: {digest}\nNew: {new}\n",
            encoding="utf-8")

    def run_helper(self, engine, mode="pending", extra=()):
        if engine == "python":
            cmd = [sys.executable, str(SCRIPTS / "audit_folder.py"), "--root", str(self.root), "--" + mode, *extra]
        else:
            cmd = [shutil.which(engine), "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                   str(SCRIPTS / "audit_folder.ps1"), "-Root", str(self.root), "-" + mode, *extra]
        before = {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=45)
        after = {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(before, after, "Read-only helper changed the fixture")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        return result.stdout

    def test_absolute_in_root_and_relative_targets(self):
        self.pending("PENDING_abs.md")
        self.pending("PENDING_rel.md", self.target.name)
        for engine in ENGINES:
            with self.subTest(engine=engine):
                out = self.run_helper(engine)
                self.assertIn("pending applicable now           2", out)

    def test_outside_and_traversal_are_not_classified_as_applicable(self):
        outside = self.root.parent / "outside.md"
        outside.write_bytes(self.target.read_bytes())
        self.pending("PENDING_abs.md", str(outside))
        self.pending("PENDING_rel.md", "../outside.md")
        self.pending("PENDING_drive.md", "C:relative.md")
        self.pending("PENDING_unc.md", r"\\invalid-server\share\target.md")
        for engine in ENGINES:
            with self.subTest(engine=engine):
                out = self.run_helper(engine)
                self.assertIn("pending applicable now           0", out)
                self.assertEqual(out.count("Unverifiable (target outside root or unsupported path)"), 4)

    def test_prefix_sibling_is_outside(self):
        sibling = self.root.parent / "project space extra"
        sibling.mkdir()
        p = sibling / self.target.name
        p.write_bytes(self.target.read_bytes())
        self.pending("PENDING_escape.md", str(p))
        for engine in ENGINES:
            with self.subTest(engine=engine):
                self.assertIn("target outside root", self.run_helper(engine))

    @unittest.skipUnless(os.name == "nt", "Windows junction regression")
    def test_junction_target_outside_project_not_read(self):
        outside = self.root.parent / "external"
        outside.mkdir()
        (outside / "target.md").write_bytes(self.target.read_bytes())
        link = self.root / "linked"
        env = dict(os.environ, R284_LINK=str(link), R284_OUTSIDE=str(outside))
        created = subprocess.run(["powershell.exe", "-NoProfile", "-Command",
            "$null = New-Item -ItemType Junction -Path $env:R284_LINK -Target $env:R284_OUTSIDE -ErrorAction Stop"],
            capture_output=True, text=True, env=env)
        self.assertEqual(created.returncode, 0, created.stderr)
        self.pending("PENDING_link.md", "linked/target.md")
        for engine in ENGINES:
            with self.subTest(engine=engine):
                self.assertIn("target outside root", self.run_helper(engine))

    def test_missing_target_stays_missing(self):
        self.pending("PENDING_missing.md", "missing.md")
        for engine in ENGINES:
            with self.subTest(engine=engine):
                self.assertIn("Unverifiable (target not found)", self.run_helper(engine))

    def test_actionable_rows_precede_cap_without_losing_totals(self):
        for i in range(20):
            self.pending(f"PENDING_0{i:02}.md", status="APPLIED")
        self.pending("PENDING_zzz.md")
        self.pending("PENDING_yyy.md", "missing.md")
        for engine in ENGINES:
            with self.subTest(engine=engine):
                out = self.run_helper(engine)
                self.assertLess(out.index("PENDING_zzz.md"), out.index("Applied (recorded)"))
                self.assertLess(out.index("PENDING_yyy.md"), out.index("Applied (recorded)"))
                self.assertIn("pending files: 22, edit blocks: 22", out)
                self.assertIn("... and 7 more", out)

    def test_index_fallbacks(self):
        for path in ("INDEX.md", "AI_CONTEXT/PROJECT_INDEX.md"):
            p = self.root / path
            p.write_text("# Index\n", encoding="utf-8")
            for engine in ENGINES:
                with self.subTest(path=path, engine=engine):
                    out = self.run_helper(engine, "orient")
                    self.assertIn("    " + path + "  0 KB", out)
                    self.assertNotIn("unindexed check skipped", out)
            p.unlink()

    def test_declared_index_takes_precedence(self):
        (self.root / "PROJECT_INDEX.md").write_text("unused", encoding="utf-8")
        (self.root / "custom index.md").write_text("# Actual index\n", encoding="utf-8")
        (self.root / "AGENTS.md").write_text(
            "## 13. Project scope\n```text\nIndex: custom index.md\n```\n", encoding="utf-8")
        for engine in ENGINES:
            with self.subTest(engine=engine):
                out = self.run_helper(engine, "orient")
                self.assertIn("    custom index.md  0 KB", out)
                self.assertNotIn("    PROJECT_INDEX.md  0 KB", out)

    def test_explicit_index_overrides_declared_and_defaults(self):
        (self.root / "AGENTS.md").write_text("## 13. Scope\nIndex: missing.md\n", encoding="utf-8")
        (self.root / "chosen.md").write_text("# Chosen\n", encoding="utf-8")
        for engine in ENGINES:
            with self.subTest(engine=engine):
                flag = "--index-path" if engine == "python" else "-IndexPath"
                out = self.run_helper(engine, "orient", (flag, "chosen.md"))
                self.assertIn("    chosen.md  0 KB", out)
                self.assertNotIn("index missing.md", out)

    def test_declared_missing_index_does_not_silently_fallback(self):
        (self.root / "PROJECT_INDEX.md").write_text("# Fallback\n", encoding="utf-8")
        (self.root / "AGENTS.md").write_text("## 13. Scope\nIndex: missing.md\n", encoding="utf-8")
        for engine in ENGINES:
            with self.subTest(engine=engine):
                out = self.run_helper(engine, "orient")
                self.assertIn("index missing.md: NOT FOUND", out)
                self.assertNotIn("    PROJECT_INDEX.md  0 KB", out)

    def test_multiple_indexes_report_ambiguity_and_cover_both(self):
        for path in ("PROJECT_INDEX.md", "INDEX.md"):
            (self.root / path).write_text("# Index\n", encoding="utf-8")
        for engine in ENGINES:
            with self.subTest(engine=engine):
                out = self.run_helper(engine, "orient")
                self.assertIn("multiple index candidates; checking all, authority not selected", out)
                self.assertIn("    INDEX.md  0 KB", out)
                self.assertIn("    PROJECT_INDEX.md  0 KB", out)

    def test_declared_outside_index_not_read(self):
        outside = self.root.parent / "outside.md"
        outside.write_text("secret marker", encoding="utf-8")
        (self.root / "AGENTS.md").write_text("## 13. Scope\nIndex: ../outside.md\n", encoding="utf-8")
        for engine in ENGINES:
            with self.subTest(engine=engine):
                out = self.run_helper(engine, "orient")
                self.assertIn("index ../outside.md: NOT FOUND, unreadable or outside root", out)
                self.assertNotIn("    ../outside.md  0 KB", out)


if __name__ == "__main__":
    unittest.main()
