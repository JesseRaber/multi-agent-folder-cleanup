#!/usr/bin/env python3
"""v1.7.1: align the skill with Project Rules 4.0.0 (register R227-R233, R235)."""

from __future__ import annotations

import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / "skills/multi-agent-folder-cleanup"
PY = SKILL / "scripts/audit_folder.py"
PS = SKILL / "scripts/audit_folder.ps1"
VR = SKILL / "scripts/verify_records.py"
RULES = SKILL / "references/project-rules"
OLD = time.time() - 3 * 86400

S1 = "11111111-1111-4111-8111-111111111111"   # open, active
S2 = "22222222-2222-4222-8222-222222222222"   # close entry in its log, recently touched
S3 = "33333333-3333-4333-8333-333333333333"   # index row Completed, recently touched
S4 = "44444444-4444-4444-8444-444444444444"   # index row in progress, idle (old files)
S5 = "55555555-5555-4555-8555-555555555555"   # log old, but a scratch FILE changed recently
S6 = "66666666-6666-4666-8666-666666666666"   # log old, scratch folder empty (folder time only)


def powershell():
    return os.environ.get("AUDIT_TEST_POWERSHELL") or shutil.which("pwsh") or shutil.which("powershell.exe")


def run_py(root, *args):
    r = subprocess.run([sys.executable, str(PY), "--root", str(root), *args],
                       capture_output=True, text=True, encoding="utf-8", stdin=subprocess.DEVNULL)
    assert r.returncode == 0, r.stderr
    return r.stdout


def run_ps(root, *args):
    exe = powershell()
    cmd = [exe, "-NoProfile"]
    if Path(exe).name.lower().startswith("powershell"):
        cmd += ["-ExecutionPolicy", "Bypass"]
    r = subprocess.run(cmd + ["-File", str(PS), "-Root", str(root), *args],
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       stdin=subprocess.DEVNULL)
    assert r.returncode == 0, r.stderr
    return r.stdout


def norm(text):
    out = []
    for line in text.lstrip("\ufeff").replace("\\", "/").splitlines():
        if line.startswith(("Generated ", "Helper: ", "Read-only work-mode check of ")):
            continue
        out.append(re.sub(r"\d{4}-\d\d-\d\dT\d\d:\d\d[+-]\d\d:\d\d", "<t>", line.rstrip()))
    return out


def w(root, rel, text, mtime=None):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8", newline="\n")
    if mtime:
        os.utime(p, (mtime, mtime))


def log(sid, slug, header, extra=""):
    return (f"Session ID: {sid}\nStarted: 2026-10-09T10:00:00-04:00\nTool/runtime: {header}\n\n"
            f"T001 | 2026-10-09T10:01:00-04:00 | work\nWork/result: did it\n{extra}")


def build(root: Path, window_line="Active-writer window: 45 minutes\n"):
    w(root, "AGENTS.md", "# Rules\nVersion: 4.0.0\n\n## 13. Project scope\n\n```text\n"
      "Tool slugs in use: claude = Claude; cursor-grokbot = Cursor agent Grok Bot; grok = xAI Grok app\n"
      + window_line + "```\n")
    w(root, "PROJECT_INDEX.md", "# Index\n")
    sess = "AI_CONTEXT/SESSIONS/"
    w(root, sess + f"2026-10-09_100000_grok_a_{S1}.md", log(S1, "grok", "grok (xAI Grok app)"))
    w(root, sess + f"2026-10-09_100000_grok_b_{S2}.md",
      log(S2, "grok", "grok (Cursor agent Grok Bot)", "\nT002 | 2026-10-09T11:00:00-04:00 | Session close\n"))
    w(root, sess + f"2026-10-09_100000_claude_c_{S3}.md", log(S3, "claude", "claude (Claude app)"))
    w(root, sess + f"2026-10-09_100000_claude_d_{S4}.md", log(S4, "claude", "claude (Claude app)"), OLD)
    w(root, sess + f"2026-10-09_100000_cursor-grokbot_e_{S5}.md",
      log(S5, "cursor-grokbot", "cursor-grokbot (Cursor)"), OLD)
    w(root, sess + f"2026-10-09_100000_codex_f_{S6}.md", log(S6, "codex", "codex"), OLD)
    w(root, "AI_CONTEXT/SESSION_INDEX.md",
      "| Start | ID | Status |\n|---|---|---|\n"
      f"| x | {S3} | Completed |\n| x | {S4} | in progress |\n| x | {S1} | in progress |\n")
    w(root, f"AI_CONTEXT/scratch/{S5}/draft.md", "recent file\n")
    (root / f"AI_CONTEXT/scratch/{S6}").mkdir(parents=True, exist_ok=True)
    w(root, "Incoming/2026-10-09_grok_review/_PROVENANCE.md",
      "Tool: grok\n- PENDING index row: | Incoming/2026-10-09_grok_review/report.md | Review |\n"
      "- APPLIED 1a2b3c4d by abc/T002 (was PENDING) tracker row\n"
      "- PENDING tracker row: R999 review follow-up\n")
    w(root, "Incoming/2026-10-09_opal_x/_PROVENANCE.md", "- APPLIED 9f8e7d6c by abc/T003 index row\n")


class HelperTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        build(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def test_r229_closed_sessions_never_possibly_active(self):
        out = run_py(self.root, "--orient")
        self.assertIn("active-writer window: 45 min (AGENTS.md 'Active-writer window:' line)", out)
        self.assertIn("possibly active writers (changed in last 45 min): 2 distinct sessions, 0 unpaired scratch folders", out)
        active = out.split("possibly active writers")[1].split("closed sessions with recent")[0]
        self.assertIn(f"session {S1[:8]}", active)
        self.assertIn(f"session {S5[:8]}", active)          # scratch FILE time counts
        for sid in (S2, S3, S4, S6):
            self.assertNotIn(f"session {sid[:8]}", active)
        self.assertIn("closed sessions with recent file activity (not active writers): 2", out)
        self.assertIn("'in progress' index rows with no file activity in the window (not active writers): 1", out)
        self.assertIn("An owner handoff message also closes a session; this helper cannot see chat.", out)

    def test_r229_flag_overrides_section13_window_and_default(self):
        self.assertIn("active-writer window: 5 min (--active-minutes)", run_py(self.root, "--orient", "--active-minutes", "5"))
        build(self.root, window_line="")
        self.assertIn("active-writer window: 30 min (default; no 'Active-writer window:' line)",
                      run_py(self.root, "--orient"))

    def test_r228_slug_with_two_runtime_headers(self):
        out = run_py(self.root, "--session-index")
        self.assertIn("tool slugs used with more than one Tool/runtime header: 1", out)
        self.assertIn("grok: grok (cursor agent grok bot) | grok (xai grok app)", out)
        self.assertNotIn(f"cursor-grokbot_e_{S5}.md (nonstandard tool slug)", out)   # declared in section 13
        self.assertIn("slugs with several headers       1", out)

    def test_r232_provenance_pending_lines(self):
        out = run_py(self.root, "--pending")
        self.assertIn("_PROVENANCE.md files with PENDING rows: 1", out)
        self.assertIn("Incoming/2026-10-09_grok_review/_PROVENANCE.md (2 PENDING lines)", out)
        self.assertIn("- PENDING tracker row: R999 review follow-up", out)
        self.assertNotIn("was PENDING", out)
        self.assertNotIn("opal_x", out)
        orient = run_py(self.root, "--orient")
        self.assertIn("_PROVENANCE.md files with PENDING rows: 1 (list and apply state: --pending)", orient)
        self.assertIn("provenance PENDING files         1", orient)

    def test_powershell_parity(self):
        if not powershell():
            self.skipTest("PowerShell not available")
        for py_flags, ps_flags in ((["--orient"], ["-Orient"]),
                                   (["--session-index"], ["-SessionIndex"]),
                                   (["--pending"], ["-Pending"]),
                                   (["--orient", "--active-minutes", "5"], ["-Orient", "-ActiveMinutes", "5"])):
            with self.subTest(flags=py_flags):
                self.assertEqual(norm(run_py(self.root, *py_flags)), norm(run_ps(self.root, *ps_flags)))


class PortfolioTests(unittest.TestCase):
    def test_r231_core_match_and_section13(self):
        template = (RULES / "AGENTS.proposed.md").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            filled = re.sub(r"(?s)(## 13\..*?```text\n).*?```",
                            "\\1Project: P; root: R\nAdopted: 4.0.0 on 2026-10-09 by owner go; activation event: e1\n"
                            "Owner timezone: America/New_York\nTracker: TRACKER.md\nActive-writer window: 30 minutes\n```",
                            template)
            w(base, "filled/AGENTS.md", filled)
            w(base, "blank/AGENTS.md", template)
            w(base, "edited/AGENTS.md", template.replace("## 2. Start", "## 2. Start\n\nLocal extra line."))
            out = run_py(base, "--portfolio")
            rows = {l.split(" | ")[0].strip(): [c.strip() for c in l.split(" | ")]
                    for l in out.splitlines() if " | root-level | " in l}
            self.assertEqual(rows["filled"][7:12], ["4.0.0", "no", "match", "no", "yes"])
            self.assertEqual(rows["blank"][9], "match")
            self.assertRegex(rows["blank"][11], r"^no \(\d+ placeholders\)$")
            self.assertEqual(rows["edited"][9], "differs (1 lines)")
            self.assertIn("Core match compares sections 0-12", out)
            self.assertIn("Section 13 complete", out)
            if powershell():
                ps = run_ps(base, "-Portfolio")
                pick = lambda t: [l for l in norm(t) if " | root-level | " in l or "Core match compares" in l]
                self.assertEqual(pick(out), pick(ps))


class TemplateOptInTests(unittest.TestCase):
    def test_unfilled_template_never_opts_in(self):
        template = (RULES / "AGENTS.proposed.md").read_text(encoding="utf-8")
        self.assertNotRegex(template, r"(?m)^[ \t]*(?:[-*][ \t]*)?\**Sequential writers\**[ \t]*:")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            w(root, "AGENTS.md", template)
            out = run_py(root, "--orient")
            self.assertIn("coordination: no sequential-writer declaration", out)
            filled = template.replace(
                "<only if the owner says agents never work at the same time, replace this line with: "
                "Sequential writers: one owner; agents work one after another (owner, <date>); otherwise delete it>",
                "Sequential writers: one owner; agents work one after another (owner, 2026-10-09)")
            self.assertNotEqual(filled, template)
            w(root, "AGENTS.md", filled)
            self.assertIn("coordination: sequential-writer declaration found (AGENTS.md)", run_py(root, "--orient"))


class VerifyRecordsTests(unittest.TestCase):
    def run_vr(self, data):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "SESSION_INDEX.md"
            p.write_bytes(data)
            r = subprocess.run([sys.executable, str(VR), str(p), "--no-links"],
                               capture_output=True, text=True, encoding="utf-8")
            return r.returncode, r.stdout

    def test_r235_powershell51_append_is_flagged(self):
        head = b"| a | b |\n|---|---|\n| 1 | 2 |\n"
        code, out = self.run_vr(head + "| 3 | 4 |\r\n".encode("utf-16le"))
        self.assertEqual(code, 1, out)
        self.assertIn("NUL bytes (first at byte", out)
        self.assertIn("UTF-16LE text segment(s)", out)
        self.assertNotIn("UTF-16BE", out)

    def test_r235_misdecoded_line_break_residue(self):
        code, out = self.run_vr("| a | b |\n|---|---|\n| 1 | 2 |\u0a0d\u0d00\n".encode("utf-8"))
        self.assertEqual(code, 1, out)
        self.assertIn("mis-decoded UTF-16 line-break character(s)", out)
        self.assertIn("first on line 3", out)

    def test_r235_utf16_bom_file(self):
        code, out = self.run_vr("\ufeff| a |\n".encode("utf-16le"))
        self.assertIn("UTF-16 byte-order mark at byte 0", out)

    def test_clean_file_still_passes(self):
        code, out = self.run_vr("| a | b |\n|---|---|\n| 1 | 2 — ok |\n".encode("utf-8"))
        self.assertEqual(code, 0, out)


class GuidanceTests(unittest.TestCase):
    def setUp(self):
        self.work = (SKILL / "references/work-mode.md").read_text(encoding="utf-8")
        self.skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")

    def test_r227_read_only_keeps_the_log(self):
        for text in (self.work, self.skill):
            self.assertNotIn("prohibits all project writes, including continuity records", text)
            self.assertNotIn("make no project writes, including logs", text)
            self.assertIn("Read-only limits task files, not your session log", text)
        self.assertIn("unless the owner expressly prohibits all project writes", self.work)

    def test_r228_one_slug_per_runtime(self):
        self.assertIn("One slug per runtime: a different runtime never shares one", self.work)
        self.assertIn("`Tool slugs in use:`", self.work)

    def test_r230_version_neutral_rules_reference(self):
        self.assertNotRegex(self.work, r"Project Rules \d+\.\d+\.\d+ section")

    def test_r233_pre_edit_copy_only_before_full_replacement(self):
        self.assertIn("Before a full-file replacement, keep one byte-for-byte pre-edit copy of that file per session", self.work)
        self.assertIn("A pure append or a bounded in-place edit needs no copy; read-back is still mandatory.", self.work)

    def test_r232_apply_covers_provenance(self):
        self.assertIn("or lines marked PENDING in `Incoming/*/_PROVENANCE.md`", self.work)
        self.assertIn("`PENDING` → `APPLIED <after-sha8> by <session>/<turn>`", self.work)

    def test_r235_windows_write_mechanics(self):
        self.assertIn("Never use `>>` on a shared record", self.work)
        self.assertIn("never regex-replace across a shared file", self.work)
        self.assertIn("only the one line that carries your own session ID", self.work)


class RulesBundleTests(unittest.TestCase):
    def test_r231_bundled_rules_400(self):
        t = (RULES / "AGENTS.proposed.md").read_text(encoding="utf-8")
        self.assertRegex(t, r"(?m)^Version: 4\.0\.0 — reusable core, 2026-10-09\.$")
        self.assertNotIn("candidate", t.split("\n## 0.")[0])
        for n in range(14):
            self.assertRegex(t, rf"(?m)^## {n}\. ")
        paste = (RULES / "SECTION_0_PASTE_IN.txt").read_text(encoding="utf-8")
        section0 = t.split("\n## 0.", 1)[1].split("\n## 1.", 1)[0]
        body = [l for l in section0.splitlines()[1:] if l.strip()]
        self.assertEqual([l for l in paste.splitlines() if re.match(r"^(\d\.|   )", l)], body)
        self.assertIn("Full rules: AI Project Folders/<project>/AGENTS.md", paste)
        adoption = (RULES / "ADOPTION.md").read_text(encoding="utf-8")
        self.assertIn("SECTION_0_PASTE_IN.txt", adoption)
        self.assertIn("Replace `<project>`", adoption)
        for field in ("`Owner timezone:`", "`Tracker:`", "`Sequential writers:`", "`Active-writer window:`",
                      "`Tool slugs in use:`"):
            self.assertIn(field, adoption)


if __name__ == "__main__":
    unittest.main()
