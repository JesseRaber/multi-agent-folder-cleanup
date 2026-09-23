#!/usr/bin/env python3
"""Regression tests for defects found in the 2026-09-23 deep scan of v1.1.0.

Each test names the scan finding it pins down (DS#n in the project backlog).
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "skills/multi-agent-folder-cleanup/scripts"
PY_AUDIT = SCRIPTS / "audit_folder.py"
PS_AUDIT = SCRIPTS / "audit_folder.ps1"
VERIFY = SCRIPTS / "verify_move.py"
POWERSHELL = shutil.which("pwsh") or shutil.which("powershell.exe")


def run_py(*args: str, env_extra: dict | None = None, check: bool = True) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["NO_COLOR"] = "1"
    env.update(env_extra or {})
    return subprocess.run([sys.executable, *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=env,
                          stdin=subprocess.DEVNULL, check=check)


def run_ps(*args: str) -> str:
    return subprocess.run([POWERSHELL, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                           str(PS_AUDIT), *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL,
                          check=True).stdout


def section(text: str, title_prefix: str) -> str:
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.startswith(f"== {title_prefix}"):
            out = []
            for nxt in lines[i + 1:]:
                if nxt.startswith("== "):
                    break
                out.append(nxt)
            return "\n".join(out)
    raise AssertionError(f"missing section {title_prefix!r}\n{text}")


def build_fixture(root: Path) -> None:
    for d in ("logs", "Catalogs", "sub/logs", "My Docs", "dupA", "dupB", "real/x", ".git", "empty"):
        (root / d).mkdir(parents=True, exist_ok=True)
    files = {
        "logs/a.txt": "a\n", "Catalogs/c.pdf": "b\n", "sub/logs/d.txt": "c\n",
        "My Docs/Plan File.md": "d\n", "changelogs.md": "e\n", "real/x/f.MD": "x\n",
        "dupA/Plan.md": "one\n", "dupB/plan.md": "two\n", "server.pem": "k\n",
        ".git/config": "g\n", "STATUS_日本.md": "s\n", "AGENTS.md": "a\n",
        "CLAUDE.md": "c\n",
    }
    for rel, text in files.items():
        (root / rel).write_text(text, encoding="utf-8")
    (root / "INDEX.md").write_text(
        "# Index\n"
        "- [Plan](My%20Docs/Plan%20File.md)\n"
        "- [Plan again](<My Docs/Plan File.md>)\n"
        "- [Titled](changelogs.md \"Title\")\n"
        "- [Notebook](onenote:foo)\n"
        "- [Bad](missing.md)\n"
        "- `v1.1.0` and `nope.md`\n",
        encoding="utf-8")


class GlobExclusionTests(unittest.TestCase):
    """DS#1: '**/X/**' missed the top level in Python and substring-matched in PowerShell."""

    def test_python_segment_aware_exclude(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            build_fixture(root)
            out = run_py(str(PY_AUDIT), "--root", str(root), "--exclude", "**/logs/**").stdout
            self.assertRegex(section(out, "Summary"), r"Excluded:\s+2 ")
            per_folder = section(out, "Per-folder counts")
            self.assertIn("./Catalogs", per_folder)
            self.assertNotIn("./logs", per_folder)

    def test_glob_semantics_table(self) -> None:
        sys.path.insert(0, str(SCRIPTS))
        try:
            import importlib
            audit = importlib.import_module("audit_folder")
        finally:
            sys.path.pop(0)
        cases = [
            ("**/logs/**", "logs/a.txt", True), ("**/logs/**", "sub/logs/d.txt", True),
            ("**/logs/**", "Catalogs/c.pdf", False), ("**/logs/**", "changelogs.md", False),
            ("tmp/**", "tmp/x/y", True), ("tmp/**", "a/tmp/x", False),
            ("tmp", "a/tmp/x", True), ("tmp", "tmpx/a", False),
            ("*.log", "a/b/c.LOG", True), ("*.log", "a/log", False),
            (".git/**", ".git/config", True), ("**/__pycache__/**", "__pycache__/a.pyc", True),
            ("chrome-profile*", "x/chrome-profile-2/Cookies", True), ("[ab].txt", "a.txt", True),
        ]
        for pat, path, expected in cases:
            with self.subTest(pattern=pat, path=path):
                self.assertEqual(audit.matches_any(path, [pat]), expected)


class IndexLinkTests(unittest.TestCase):
    """DS#11: %20, titles, URI schemes and version strings were false positives."""

    def test_links_are_parsed_like_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            build_fixture(root)
            out = run_py(str(PY_AUDIT), "--root", str(root), "--index-path", "INDEX.md").stdout
            idx = section(out, "Index link check")
            self.assertIn("Markdown links checked: 3", idx)
            self.assertIn("BROKEN MARKDOWN LINKS: 1", idx)
            self.assertIn("missing.md", idx)
            self.assertNotIn("Plan%20File", idx)
            self.assertNotIn("Title", idx)
            self.assertNotIn("onenote", idx)
            self.assertNotIn("v1.1.0", idx)
            self.assertIn("nope.md", idx)


class OutputEncodingTests(unittest.TestCase):
    """DS#3: a non-ASCII filename crashed the Python audit on a cp1252 stdout."""

    def test_cp1252_stdout_does_not_crash(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "STATUS_日本.md").write_text("x\n", encoding="utf-8")
            result = run_py(str(PY_AUDIT), "--root", str(root),
                            env_extra={"PYTHONIOENCODING": "cp1252"}, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Audit complete", result.stdout)


@unittest.skipIf(os.name == "nt" or (hasattr(os, "geteuid") and os.geteuid() == 0),
                 "needs a POSIX non-root user to create an unreadable directory")
class UnreadableDirectoryTests(unittest.TestCase):
    """DS#2: unreadable directories vanished from every count without a warning."""

    def test_unreadable_directory_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "ok").mkdir()
            (root / "ok/a.md").write_text("a\n", encoding="utf-8")
            locked = root / "locked"
            (locked / "deep").mkdir(parents=True)
            (locked / "deep/b.md").write_text("b\n", encoding="utf-8")
            locked.chmod(0)
            try:
                outputs = [run_py(str(PY_AUDIT), "--root", str(root)).stdout]
                if POWERSHELL:
                    outputs.append(run_ps("-Root", str(root)))
                for out in outputs:
                    self.assertIn("Directories not readable", out)
                    self.assertIn("./locked", out)
                    self.assertIn("Coverage gap: 1 director", out)
            finally:
                locked.chmod(0o755)


class ReparsePointTests(unittest.TestCase):
    """DS#6: only junctions/symlinks may be skipped, never ordinary folders."""

    @unittest.skipIf(os.name == "nt", "POSIX symlink fixture")
    def test_directory_symlink_is_reported_and_not_walked(self) -> None:
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as outside:
            root = Path(temp)
            (Path(outside) / "external.md").write_text("x\n", encoding="utf-8")
            (root / "real").mkdir()
            (root / "real/inside.md").write_text("y\n", encoding="utf-8")
            os.symlink(outside, root / "linked", target_is_directory=True)
            outputs = [run_py(str(PY_AUDIT), "--root", str(root)).stdout]
            if POWERSHELL:
                outputs.append(run_ps("-Root", str(root)))
            for out in outputs:
                self.assertRegex(section(out, "Summary"), r"Files \(all\):\s+1\b")
                self.assertIn("./linked", section(out, "Reparse points"))

    @unittest.skipUnless(os.name == "nt", "Windows junction fixture")
    def test_windows_junction_is_skipped_but_plain_folders_are_walked(self) -> None:
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as outside:
            root = Path(temp)
            (Path(outside) / "external.md").write_text("x\n", encoding="utf-8")
            (root / "real").mkdir()
            (root / "real/inside.md").write_text("y\n", encoding="utf-8")
            subprocess.run(["cmd", "/c", "mklink", "/J", str(root / "junction"), outside],
                           check=True, capture_output=True)
            outputs = [run_py(str(PY_AUDIT), "--root", str(root)).stdout]
            if POWERSHELL:
                outputs.append(run_ps("-Root", str(root)))
            for out in outputs:
                self.assertRegex(section(out, "Summary"), r"Files \(all\):\s+1\b")
                self.assertIn("junction", section(out, "Reparse points"))


@unittest.skipUnless(POWERSHELL, "PowerShell is required for full-report parity")
class FullReportParityTests(unittest.TestCase):
    """DS#8: the two helpers must print the same report, apart from the
    Windows-only placeholder section and the flag spelling."""

    def test_reports_match_line_for_line(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            build_fixture(root)
            py = run_py(str(PY_AUDIT), "--root", str(root), "--exclude", "**/logs/**",
                        "--exclude", ".git", "--index-path", "INDEX.md", "--hash-files").stdout
            ps = run_ps("-Root", str(root), "-Exclude", "**/logs/**,.git",
                        "-IndexPath", "INDEX.md", "-HashFiles")

            def normalize(text: str) -> list[str]:
                text = text.replace("\\", "/").replace("--exclude", "-Exclude")
                text = text.replace(str(root).replace("\\", "/"), "<ROOT>")
                drop = ("Generated ", "Read-only audit of ")
                lines = [ln.rstrip() for ln in text.splitlines() if not ln.startswith(drop)]
                out, skip = [], False
                for ln in lines:
                    if ln.startswith("== OneDrive / cloud placeholders"):
                        skip = True
                        continue
                    if skip and ln.startswith("== "):
                        skip = False
                    if not skip:
                        out.append(ln)
                return [ln for ln in out if ln]

            self.assertEqual(normalize(py), normalize(ps))


class VerifyMoveTests(unittest.TestCase):
    """DS#4, DS#5, DS#12."""

    def test_excel_bom_csv_and_map_relative_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "src").mkdir()
            (root / "src/a.md").write_text("a\n", encoding="utf-8")
            (root / "moves.csv").write_bytes(b"\xef\xbb\xbfsource,target\nsrc/a.md,dst/a.md\n")
            result = subprocess.run([sys.executable, str(VERIFY), "preflight", "--map",
                                     str(root / "moves.csv")], capture_output=True, text=True, encoding="utf-8", errors="replace",
                                    cwd=tempfile.gettempdir())
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertIn("pairs:                    1", result.stdout)
            self.assertIn("missing sources:          0", result.stdout)

    def test_case_only_target_collision_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "src").mkdir()
            for name in ("a.md", "b.md"):
                (root / "src" / name).write_text(name, encoding="utf-8")
            with open(root / "moves.csv", "w", newline="", encoding="utf-8") as fh:
                writer = csv.writer(fh)
                writer.writerow(["source", "target"])
                writer.writerow([root / "src/a.md", root / "dst/Plan.md"])
                writer.writerow([root / "src/b.md", root / "dst/plan.md"])
            result = subprocess.run([sys.executable, str(VERIFY), "preflight", "--map",
                                     str(root / "moves.csv")], capture_output=True, text=True, encoding="utf-8", errors="replace")
            self.assertEqual(result.returncode, 1)
            self.assertIn("target collisions:        1", result.stdout)

    def test_copy_is_not_a_move(self) -> None:
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as audit:
            root = Path(temp)
            (root / "src").mkdir()
            (root / "src/a.md").write_text("a\n", encoding="utf-8")
            moves = root / "moves.json"
            moves.write_text(json.dumps([{"source": "src/a.md", "target": "dst/a.md"}]),
                             encoding="utf-8")
            baseline = Path(audit) / "baseline.json"
            subprocess.run([sys.executable, str(VERIFY), "baseline", "--map", str(moves),
                            "--out", str(baseline)], check=True, capture_output=True)
            (root / "dst").mkdir()
            shutil.copy2(root / "src/a.md", root / "dst/a.md")

            copied = subprocess.run([sys.executable, str(VERIFY), "verify", "--baseline",
                                     str(baseline)], capture_output=True, text=True, encoding="utf-8", errors="replace")
            self.assertEqual(copied.returncode, 1)
            self.assertIn("STILL AT SOURCE", copied.stdout)

            allowed = subprocess.run([sys.executable, str(VERIFY), "verify", "--baseline",
                                      str(baseline), "--allow-source-present"],
                                     capture_output=True, text=True, encoding="utf-8", errors="replace")
            self.assertEqual(allowed.returncode, 0, allowed.stdout)

            (root / "src/a.md").unlink()
            moved = subprocess.run([sys.executable, str(VERIFY), "verify", "--baseline",
                                    str(baseline)], capture_output=True, text=True, encoding="utf-8", errors="replace")
            self.assertEqual(moved.returncode, 0, moved.stdout)


class SecretHintTests(unittest.TestCase):
    """DS#19: key containers were not flagged."""

    def test_key_files_are_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name in ("server.pem", "id_ed25519", "vault.kdbx", ".git-credentials", "notes.md"):
                (root / name).write_text("x\n", encoding="utf-8")
            out = run_py(str(PY_AUDIT), "--root", str(root)).stdout
            creds = section(out, "Possible credential-bearing files")
            self.assertIn("4 file(s)", creds)
            self.assertNotIn("notes.md", creds)


if __name__ == "__main__":
    unittest.main()
