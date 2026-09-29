#!/usr/bin/env python3
"""Regression checks for the v1.2.0 portfolio, connector and intake features."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

REPO = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO / "skills/multi-agent-folder-cleanup"
PY_AUDIT = SKILL_ROOT / "scripts/audit_folder.py"
VERIFY_MOVE = SKILL_ROOT / "scripts/verify_move.py"


class V12FeatureTests(unittest.TestCase):
    def test_guidance_covers_observed_failure_modes(self) -> None:
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        workflow = (SKILL_ROOT / "references/workflow.md").read_text(encoding="utf-8")
        connector = (SKILL_ROOT / "references/connector-audit.md").read_text(encoding="utf-8")
        portfolio = (SKILL_ROOT / "references/portfolio-audit-template.md").read_text(encoding="utf-8")
        combined = "\n".join((skill, workflow, connector, portfolio)).lower()
        required = [
            "cross-project contamination", "search failure never proves absence",
            "documentary state", "operationally verified state", "root-level",
            "intentional pointer", "divergent competing control", "claim family",
            "virtualized editor", "concurrent", "partial", "multi-file upload",
            "additive intake", "customer", "companion root", "reparse",
            "cloud", "journal", "marker count", "reopen",
        ]
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, combined)

    def test_skill_contains_all_core_sections_and_complete_ending(self) -> None:
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        headings = [
            "## Choose the operating mode and mutation type",
            "## Split mixed-scope requests",
            "## Validate every evidence path",
            "## Audit portfolio roots explicitly",
            "## Distinguish pointers, duplicates, controls, and claim families",
            "## Inventory against artifacts, not names",
            "## Classify each substantive file once",
            "## Create additive intake safely",
            "## Execute with measured verification",
            "## Finish with proof",
        ]
        for heading in headings:
            with self.subTest(heading=heading):
                self.assertEqual(skill.count(heading), 1)
        self.assertTrue(skill.rstrip().endswith("because cleanup succeeded."))

    def make_fixture(self, root: Path) -> Path:
        (root / "ProjectA/AI_CONTEXT").mkdir(parents=True)
        (root / "ProjectB").mkdir()
        (root / "uploads").mkdir()
        (root / "ProjectA/AGENTS.md").write_text("# Agents\n", encoding="utf-8")
        (root / "ProjectA/README_FIRST.md").write_text(
            "Start here: read `AI_CONTEXT/README_FIRST.md`.\n", encoding="utf-8")
        (root / "ProjectA/AI_CONTEXT/README_FIRST.md").write_text("# Start\n", encoding="utf-8")
        (root / "ProjectA/AI_CONTEXT/PROJECT_ACTIVITY_JOURNAL.md").write_text(
            "x" * 2048, encoding="utf-8")
        (root / "ProjectB/notes.md").write_text("notes\n", encoding="utf-8")
        (root / "ProjectB/Cookies").write_text("do not read", encoding="utf-8")
        for name, text in (("a.txt", "alpha\n"), ("b.txt", "beta\n"),
                           ("c.txt", "charlie\n"), ("d.txt", "delta\n"),
                           ("e.txt", "echo\n")):
            (root / "uploads" / name).write_text(text, encoding="utf-8")
        with zipfile.ZipFile(root / "archive.zip", "w") as zf:
            zf.writestr("inside/report.md", "report\n")
        manifest = root / "expected.csv"
        with manifest.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["path", "size", "sha256"])
            for rel in ("uploads/a.txt", "uploads/b.txt", "uploads/c.txt", "uploads/d.txt", "uploads/e.txt"):
                item = root / rel
                writer.writerow([rel, item.stat().st_size, hashlib.sha256(item.read_bytes()).hexdigest()])
            writer.writerow(["uploads/f.txt", "", ""])
        return manifest

    def test_python_audit_reports_new_advisory_sections(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_fixture(root)
            result = subprocess.run([
                sys.executable, str(PY_AUDIT), "--root", str(root),
                "--journal-threshold-kb", "1", "--entrypoint", "AGENTS.md",
                "--entrypoint", "README_FIRST.md", "--portfolio",
                "--detect-pointers", "--expected-upload-manifest", "expected.csv",
                "--inspect-zip",
            ], check=True, capture_output=True, text=True, encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL).stdout
            for text in (
                "Large journals (threshold 1 KB)", "Expected entrypoints",
                "Portfolio root matrix", "ProjectA | root-level",
                "Possible pointer stubs", "ProjectA/README_FIRST.md",
                "Expected upload manifest", "Expected: 6  Present: 5  Missing: 1",
                "Possible credential-bearing files", "Cookies",
                "ZIP central directories (no extraction)", "inside/report.md",
            ):
                with self.subTest(text=text):
                    self.assertIn(text, result.replace("\\", "/"))

    def test_verify_move_detects_unperformed_then_completed_move(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            work = Path(temp)
            src = work / "source/a.txt"
            dst = work / "target/a.txt"
            src.parent.mkdir(); dst.parent.mkdir()
            src.write_text("same bytes\n", encoding="utf-8")
            move_map = work / "moves.csv"
            move_map.write_text(f"source,target\n{src},{dst}\n", encoding="utf-8")
            baseline = work / "baseline.json"
            subprocess.run([sys.executable, str(VERIFY_MOVE), "baseline", "--map", str(move_map),
                            "--out", str(baseline)], check=True, capture_output=True, text=True, encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL)
            failed = subprocess.run([sys.executable, str(VERIFY_MOVE), "verify", "--baseline", str(baseline)],
                                    capture_output=True, text=True, encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL)
            self.assertNotEqual(failed.returncode, 0)
            shutil.move(src, dst)
            completed = subprocess.run([sys.executable, str(VERIFY_MOVE), "verify", "--baseline", str(baseline)],
                                       capture_output=True, text=True, encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL)
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)


if __name__ == "__main__":
    unittest.main()
