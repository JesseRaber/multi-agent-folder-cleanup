"""Regression checks for the approved R157–R167 helper changes."""

from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "skills/multi-agent-folder-cleanup/scripts"
PY = SCRIPTS / "audit_folder.py"
PS = SCRIPTS / "audit_folder.ps1"
POWERSHELL = shutil.which("pwsh") or shutil.which("powershell.exe")
UUID = "11111111-1111-4111-8111-111111111111"


def run_helper(root, *flags, powershell=False):
    if powershell:
        command = [POWERSHELL, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(PS),
                   "-Root", str(root), *flags]
    else:
        command = [sys.executable, str(PY), "--root", str(root), *flags]
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
    if result.returncode:
        raise AssertionError(result.stderr or result.stdout)
    return result.stdout


class CandidateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def helper_outputs(self, py_flags, ps_flags):
        yield run_helper(self.root, *py_flags)
        if POWERSHELL:
            yield run_helper(self.root, *ps_flags, powershell=True)

    def test_filename_start_preserves_wall_time_without_offset(self):
        sessions = self.root / "AI_CONTEXT/SESSIONS"
        sessions.mkdir(parents=True)
        name = f"2026-10-06_224940_codex_x_{UUID}.md"
        (sessions / name).write_text(f"Session ID: {UUID}\nTool/runtime: codex\n", encoding="utf-8")
        for output in self.helper_outputs(("--session-index", "--orient"), ("-SessionIndex", "-Orient")):
            self.assertIn("2026-10-06T22:49 (filename; offset unknown)", output)
            self.assertNotRegex(output, r"2026-10-06T22:49[+-]\d\d:\d\d")
            self.assertIn("files changed since 2026-10-06T22:49 (filename; offset unknown)", output)

    def test_brief_portfolio_has_all_twelve_children(self):
        for index in range(12):
            (self.root / f"project-{index:02d}").mkdir()
        for output in self.helper_outputs(("--portfolio", "--brief"), ("-Portfolio", "-Brief")):
            matrix = output.split("Portfolio root matrix (immediate children; advisory)", 1)[1]
            for index in range(12):
                self.assertIn(f"project-{index:02d} |", matrix)

    def test_nonstandard_slugs_and_id_report_three(self):
        sessions = self.root / "AI_CONTEXT/SESSIONS"
        sessions.mkdir(parents=True)
        names = [f"2026-10-06_224940_claude-cowork_x_{UUID}.md",
                 "2026-10-06_224941_Antigravity_x_22222222-2222-4222-8222-222222222222.md",
                 "2026-10-06_224942_codex_x_01K7ABCDEF0123456789ABCDEFG.md"]
        for name in names:
            (sessions / name).write_text("# session\n", encoding="utf-8")
        for output in self.helper_outputs(("--session-index",), ("-SessionIndex",)):
            self.assertIn("nonstandard session filenames: 3", output)
            for name in names:
                self.assertIn(name, output)

    def test_orient_identifies_own_script_and_version(self):
        for output, path in [(run_helper(self.root, "--orient"), PY),
                             *(([(run_helper(self.root, "-Orient", powershell=True), PS)] if POWERSHELL else []))]:
            self.assertIn(str(path), output)
            self.assertIn("1.7.0", output.split("== Orient ==", 1)[0])

    def test_pruned_state_does_not_claim_provider_sync(self):
        (self.root / "node_modules").mkdir()
        for output in self.helper_outputs(("--prune-noise",), ("-PruneNoise",)):
            self.assertIn("Generated state, not evidence. Provider sync/index state not checked.", output)
            self.assertNotIn("Still synced and indexed by cloud providers", output)
