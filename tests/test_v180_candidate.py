"""v1.8.0 candidate (R252 token cuts, R255 recycle-path test): guidance routing and helper changes."""

from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / "skills/multi-agent-folder-cleanup"
REFS = SKILL / "references"
SCRIPTS = SKILL / "scripts"
PY = SCRIPTS / "audit_folder.py"
PS = SCRIPTS / "audit_folder.ps1"
POWERSHELL = shutil.which("pwsh") or shutil.which("powershell.exe")
UUID = "33333333-3333-4333-8333-333333333333"
UUID2 = "44444444-4444-4444-8444-444444444444"


def read(rel):
    return (SKILL / rel).read_text(encoding="utf-8")


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


class HelperTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.sessions = self.root / "AI_CONTEXT/SESSIONS"
        self.sessions.mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def outputs(self, py_flags, ps_flags):
        yield run_helper(self.root, *py_flags)
        if POWERSHELL:
            yield run_helper(self.root, *ps_flags, powershell=True)

    def test_r178_space_before_offset_is_a_recorded_start(self):
        (self.sessions / f"2026-10-06_224940_codex_x_{UUID}.md").write_text(
            f"Session ID: {UUID}\nStart time: 2026-10-06 22:49:40 -04:00\nTool/runtime: codex\n",
            encoding="utf-8")
        for out in self.outputs(("--session-index",), ("-SessionIndex",)):
            self.assertNotIn("(filename; offset unknown)", out)

    def test_r180_logs_without_header_are_listed(self):
        (self.sessions / f"2026-10-06_224940_codex_x_{UUID}.md").write_text("# session\n", encoding="utf-8")
        (self.sessions / f"2026-10-06_224941_codex_y_{UUID2}.md").write_text(
            f"Session ID: {UUID2}\nTool/runtime: codex\n", encoding="utf-8")
        for out in self.outputs(("--session-index",), ("-SessionIndex",)):
            self.assertIn("session logs without a header block (Session ID, Start, Tool/runtime): 1", out)
            self.assertIn(f"2026-10-06_224940_codex_x_{UUID}.md", out.split("without a header block", 1)[1])
            self.assertNotIn(f"_y_{UUID2}.md", out.split("without a header block", 1)[1])

    def test_r127_generated_line_carries_offset(self):
        for out in self.outputs(("--orient",), ("-Orient",)):
            line = next(l for l in out.splitlines() if l.startswith("Generated "))
            self.assertRegex(line, r"^Generated \d{4}-\d{2}-\d{2} \d{2}:\d{2} [+-]\d{2}:\d{2}$")


class GuidanceTests(unittest.TestCase):
    def setUp(self):
        self.skill = read("SKILL.md")
        self.work = read("references/work-mode.md")
        self.base = read("references/work-mode-baseline.md")

    def test_s1_work_routing(self):
        self.assertIn("work-mode-baseline.md", self.skill)
        self.assertIn("unless the root instruction file is Project Rules 4.0.0 or later", self.skill)
        self.assertIn("Otherwise also read [work-mode-baseline.md](work-mode-baseline.md)", self.work)
        # Steps Rules 4.0.0 already carries are read only without those rules.
        for phrase in ("Create your session-index row when you create the log",
                       "Before a full-file replacement, keep one byte-for-byte pre-edit copy",
                       "Maintain exactly one authoritative project-wide tracker"):
            self.assertNotIn(phrase, self.work)
            self.assertIn(phrase, self.base)

    def test_r193_quick_tasks_and_p13_one_close(self):
        self.assertIn("**Quick tasks.**", self.work)
        self.assertIn("Write one close entry when the owner ends the chat", self.work)
        self.assertIn("refresh the close line instead of reopening", self.work)

    def test_r181_arrival_line(self):
        self.assertIn("if no helper ran, say `helpers not run`", self.skill)

    def test_r255_recycle_path_test(self):
        moves = read("references/execute-moves.md")
        self.assertIn("### Deletion recycle-path test", moves)
        self.assertIn("If it does not appear, stop", moves)
        self.assertIn("A delete through a remote shell or device bridge without a passing test does not happen.", moves)
        self.assertIn("**Deletion recycle-path test**", self.skill)
        self.assertIn("a delete through a remote shell or device bridge without a passing test does not happen", self.skill)

    def test_r183_move_safety_sentence(self):
        self.assertIn("Use one filesystem environment end to end and literal paths throughout.", read("references/execute-moves.md"))

    def test_r134_navigation_guard(self):
        self.assertIn("do not add root `STATUS.md`, `AUTHORITY.md`, `HANDOFF.md` or `INDEX.md`", read("references/navigation-templates.md"))

    def test_r102_default_prompt_names_modes(self):
        y = read("agents/openai.yaml")
        self.assertIn("Work for ordinary saving", y)

    def test_r238_r240_on_demand_notes(self):
        tools = read("references/audit-tools.md")
        for needle in ("git --no-optional-locks status", "Input/output error", "C:\\Program Files\\PowerShell\\7\\pwsh.exe"):
            self.assertIn(needle, tools)

    def test_readme_faq_routes_grok_to_copilot_zip(self):
        readme = (REPO / "README.md").read_text(encoding="utf-8")
        faq = readme.split("### Which ZIP do I install?", 1)[1].split("###", 1)[0]
        self.assertIn("Grok uses the Microsoft Copilot agent-only ZIP", faq)
        self.assertNotRegex(faq, r"skill upload, ChatGPT or Codex standalone skills, Grok")

    def test_every_reference_is_reachable_from_skill(self):
        for name in ("work-mode-baseline.md", "execute-principles.md", "audit-edge-cases.md", "release-packages.md"):
            self.assertTrue((REFS / name).is_file(), name)
            self.assertIn(name, self.skill)


if __name__ == "__main__":
    unittest.main()
