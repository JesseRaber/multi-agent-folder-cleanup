"""v1.5.3 regressions for R094/R096/R123/R124/R126."""
from pathlib import Path
import contextlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zipfile

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "skills/multi-agent-folder-cleanup/scripts"
PY = SCRIPTS / "audit_folder.py"
PS = SCRIPTS / "audit_folder.ps1"
VERIFY = SCRIPTS / "verify_move.py"
POWERSHELL = shutil.which("pwsh") or shutil.which("powershell.exe")


def run_audits(root, *flags):
    py = subprocess.run([sys.executable, str(PY), "--root", str(root), *flags],
                        capture_output=True, text=True, encoding="utf-8")
    outputs = [("python", py)]
    if POWERSHELL:
        mapping = {"--inspect-zip": "-InspectZip", "--hash-files": "-HashFiles",
                   "--orient": "-Orient", "--session-index": "-SessionIndex",
                   "--active-minutes": "-ActiveMinutes"}
        ps_flags = [mapping.get(x, x) for x in flags]
        pw = subprocess.run([POWERSHELL, "-NoProfile", "-ExecutionPolicy", "Bypass",
                             "-File", str(PS), "-Root", str(root), *ps_flags],
                            capture_output=True, text=True, encoding="utf-8")
        outputs.append(("powershell", pw))
    return outputs


class V153CandidateTests(unittest.TestCase):
    def test_verify_move_warns_without_root_and_accepts_root_on_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.txt").write_text("x", encoding="utf-8")
            move_map = root / "moves.json"
            move_map.write_text(json.dumps([{"source": "a.txt", "target": "b.txt"}]), encoding="utf-8")
            unguarded = subprocess.run([sys.executable, str(VERIFY), "review", "--map", str(move_map)],
                                       capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(unguarded.returncode, 0, unguarded.stderr)
            self.assertIn("paths are not confined", unguarded.stderr)
            guarded = subprocess.run([sys.executable, str(VERIFY), "review", "--map", str(move_map),
                                      "--root", str(root)], capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(guarded.returncode, 0, guarded.stderr)
            self.assertNotIn("paths are not confined", guarded.stderr)

    def test_zip_traversal_names_only_are_listed_as_unsafe(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with zipfile.ZipFile(root / "evil.zip", "w") as zf:
                for name in ("safe/report.md", "inside/../escape.txt", "inside/../escape2.txt",
                             "/absolute.txt", "C:/drive.txt"):
                    zf.writestr(zipfile.ZipInfo(name), b"x")
            for name, result in run_audits(root, "--inspect-zip"):
                with self.subTest(helper=name):
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn("INVALID/UNSAFE NAMES: 4", result.stdout)
                    unsafe = result.stdout.split("INVALID/UNSAFE NAMES: 4", 1)[1].split("== Path length", 1)[0]
                    self.assertNotIn("safe/report.md", unsafe)
                    for bad in ("inside/../escape.txt", "inside/../escape2.txt", "/absolute.txt", "C:/drive.txt"):
                        self.assertIn(bad, unsafe)

    def test_credential_guard_is_separate_from_unreadable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "credentials.md").write_text("secret fixture", encoding="utf-8")
            (root / "ordinary.md").write_text("ordinary", encoding="utf-8")
            for name, result in run_audits(root, "--hash-files"):
                with self.subTest(helper=name):
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn("Not hashed by design (credential guard)", result.stdout)
                    guarded = result.stdout.split("Not hashed by design (credential guard)", 1)[1].split("== Identical content", 1)[0]
                    self.assertIn("credentials.md", guarded)
                    self.assertNotIn("Resolve before any Execute", guarded)

    @unittest.skipIf(sys.platform == "win32", "POSIX symlink fixture")
    def test_credential_and_link_land_in_different_sections(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ordinary.md").write_text("ordinary", encoding="utf-8")
            (root / "credentials.md").write_text("secret fixture", encoding="utf-8")
            try:
                (root / "linked.md").symlink_to(root / "ordinary.md")
            except OSError as exc:
                self.skipTest(f"symlink unavailable: {exc}")
            for name, result in run_audits(root, "--hash-files"):
                with self.subTest(helper=name):
                    self.assertEqual(result.returncode, 0, result.stderr)
                    guarded = result.stdout.split("Not hashed by design (credential guard)", 1)[1].split("== LINKED PATH", 1)[0]
                    linked = result.stdout.split("LINKED PATH - not followed or hashed", 1)[1].split("== Identical content", 1)[0]
                    self.assertIn("credentials.md", guarded)
                    self.assertNotIn("linked.md", guarded)
                    self.assertIn("linked.md", linked)
                    self.assertIn("READ BLOCKED", linked)

    @unittest.skipUnless(sys.platform == "win32", "Windows placeholder classification")
    def test_cloud_placeholder_keeps_execute_blocking_advice(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("audit_folder_fixture", PY)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            item = root / "offline.md"
            item.write_text("fixture", encoding="utf-8")
            module.AUDIT_ROOT = str(root.resolve())
            output = io.StringIO()
            with mock.patch.object(module, "_cloud_only", side_effect=lambda path: Path(path) == item), \
                    mock.patch.object(sys, "argv", [str(PY), "--root", str(root), "--hash-files"]), \
                    contextlib.redirect_stdout(output):
                self.assertEqual(module.content_read_block_reason(str(item)), "unreadable")
                self.assertFalse(module.content_read_allowed(str(item)))
                module.main()
            report = output.getvalue()
            unreadable = report.split("UNREADABLE - could not hash", 1)[1].split("== Identical content", 1)[0]
            self.assertIn("offline.md", unreadable)
            self.assertIn("Resolve before any Execute pass", unreadable)
            if "Not hashed by design (credential guard)" in report:
                guarded = report.split("Not hashed by design (credential guard)", 1)[1].split("==", 1)[0]
                self.assertNotIn("offline.md", guarded)

    def test_header_variants_outcome_and_distinct_writer_pairing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sessions = root / "AI_CONTEXT/SESSIONS"
            sessions.mkdir(parents=True)
            sid = "11111111-1111-4111-8111-111111111111"
            log = sessions / f"2026-10-05_210000_codex_fixture_{sid}.md"
            log.write_text("Session ID: " + sid + "\nStart Time: 2026-10-05T21:00:00-04:00\n"
                           "Tool/runtime: Codex\nT001 | 2026-10-05T21:01:00-04:00 | fragment\n"
                           "Outcome: verified outcome\n", encoding="utf-8")
            (root / "AI_CONTEXT/scratch" / sid).mkdir(parents=True)
            (root / "AI_CONTEXT/scratch/unpaired").mkdir()
            for name, result in run_audits(root, "--orient", "--session-index", "--active-minutes", "100000"):
                with self.subTest(helper=name):
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn("1 distinct sessions, 1 unpaired scratch folders", result.stdout)
                    self.assertIn("verified outcome", result.stdout)
                    self.assertNotIn("| fragment |", result.stdout)


if __name__ == "__main__":
    unittest.main()
