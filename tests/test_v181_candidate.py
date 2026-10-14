"""v1.8.1 candidate (R268 work routing, R269 backup pending copies, R270 split tables, R271 quick-context size,
R274 helper fixes from the Gemini audit of v1.8.0)."""

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
VR = SCRIPTS / "verify_records.py"
POWERSHELL = shutil.which("pwsh") or shutil.which("powershell.exe")
UUID = "55555555-5555-4555-8555-555555555555"
PORTFOLIO = "Portfolio root matrix (immediate children; advisory)"
LIFECYCLE = "Handoff and pending-update lifecycle warnings"


def run(root, *flags, powershell=False):
    if powershell:
        cmd = [POWERSHELL, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(PS), "-Root", str(root), *flags]
    else:
        cmd = [sys.executable, str(PY), "--root", str(root), *flags]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if r.returncode:
        raise AssertionError(r.stderr or r.stdout)
    return r.stdout


def section(out, name):
    lines, on = [], False
    for line in out.splitlines():
        if line.startswith("== "):
            on = line.strip("= ").strip() == name
            continue
        if on:
            lines.append(line)
    return "\n".join(lines)


def rows(out):
    return {l.split(" | ")[0].strip(): l.split(" | ") for l in out.splitlines() if " | root-level | " in l}


class V181Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="v181-"))
        self.port = self.tmp / "port"
        for name, version in (("new", "4.0.0"), ("future", "10.0.0"), ("old", "3.0.0")):
            p = self.port / name
            (p / "AI_CONTEXT").mkdir(parents=True)
            (p / "AGENTS.md").write_text(f"# Project rules\n\nVersion: {version} - test.\n", encoding="utf-8")
        scratch = self.port / "new" / "AI_CONTEXT" / "scratch" / UUID
        (scratch / "before").mkdir(parents=True)
        (scratch / "before-T004").mkdir()
        live = "Status: PENDING\nTarget: AI_CONTEXT/SESSION_INDEX.md\nOld: a\nNew: b\n"
        (scratch / "PENDING_SESSION_INDEX.md").write_text(live, encoding="utf-8")
        (scratch / "before" / "PENDING_x.pre-T001.md").write_text(live, encoding="utf-8")
        (scratch / "before-T004" / "1837aef3_PENDING_SESSION_INDEX.md").write_text(live, encoding="utf-8")
        (self.port / "new" / "AI_CONTEXT" / "PROJECT_QUICK_CONTEXT.md").write_text("x" * 13000, encoding="utf-8")
        (self.port / "old" / "AI_CONTEXT" / "PROJECT_QUICK_CONTEXT.md").write_text("small\n", encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_r268_work_routing_numeric(self):
        r = rows(section(run(self.port, "--portfolio"), PORTFOLIO))
        self.assertEqual(r["new"][8], "yes")
        self.assertEqual(r["future"][8], "yes")  # 10.0.0 must not sort below 4.0.0
        self.assertEqual(r["old"][8], "no")

    def test_r269_backup_copies_not_counted(self):
        out = run(self.port, "--portfolio")
        self.assertTrue(rows(section(out, PORTFOLIO))["new"][6].startswith("1 "))
        life = section(out, LIFECYCLE)
        self.assertIn("pending shared-update artifacts: 1 ", life)
        # "<id>_PENDING_*" names never matched the pending pattern; only PENDING_* backups did.
        self.assertIn("pre-edit backup copies with pending names, not counted: 1", life)

    def test_r271_quick_context_over_limit(self):
        out = section(run(self.port, "--portfolio"), PORTFOLIO)
        self.assertIn("quick context over 12 KB: 1 (rewrite to current state; move history out)", out)
        self.assertIn("    new: 13000 bytes", out)

    @unittest.skipUnless(POWERSHELL, "PowerShell not available")
    def test_powershell_parity(self):
        for name in (PORTFOLIO, LIFECYCLE):
            py = section(run(self.port, "--portfolio"), name).replace("\\", "/")
            ps = section(run(self.port, "-Portfolio", powershell=True), name).replace("\\", "/")
            self.assertEqual(py, ps, name)

    def test_r270_split_table_named(self):
        f = self.tmp / "idx.md"
        f.write_bytes(b"# Index\n\n| A | B |\n|---|---|\n| 1 | 2 |\n\nnote inside\n| 3 | 4 |\n")
        r = subprocess.run([sys.executable, str(VR), str(f)], capture_output=True, text=True, encoding="utf-8")
        self.assertIn("table split: rows continue the table that ended at line 5", r.stdout)


class R274Tests(unittest.TestCase):
    """Gemini Argon audit of 673223c (2026-10-13), register R274 a-e."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="r274-"))
        self.root = self.tmp / "proj"
        (self.root / "AI_CONTEXT" / "SESSIONS").mkdir(parents=True)
        (self.root / "AGENTS.md").write_text("# Project rules\n\nVersion: 4.0.0 - test.\n", encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_a_verify_records_link_with_parentheses(self):
        (self.root / "doc (1).md").write_text("x\n", encoding="utf-8")
        (self.root / "na(me).md").write_text("x\n", encoding="utf-8")
        (self.root / "plain.md").write_text("x\n", encoding="utf-8")
        f = self.root / "idx.md"
        # a: percent-encoded space with balanced parens; b: angle form; c: escaped parens; e: the one real miss.
        f.write_text("[a](doc%20(1).md) [b](<doc (1).md>) [c](na\\(me\\).md) [d](plain.md) [e](missing%20(2).md)\n",
                     encoding="utf-8")
        r = subprocess.run([sys.executable, str(VR), str(f)], capture_output=True, text=True, encoding="utf-8")
        self.assertNotIn("doc%20(1", r.stdout + r.stderr)
        self.assertIn("link target not found: missing%20(2).md", r.stdout)
        self.assertEqual(r.stdout.count("link target not found"), 1, r.stdout)

    def _bold_log(self):
        log = self.root / "AI_CONTEXT" / "SESSIONS" / f"2026-10-13_101500_claude_bold_{UUID}.md"
        log.write_text("# Session log\n\n- **Session ID:** " + UUID + "\n- **Started:** 2026-10-13 10:15 -04:00\n"
                       "- **Tool/runtime:** claude\n\n## T001\n- **Outcome:** did a thing that is long enough\n",
                       encoding="utf-8")

    def test_c_bold_header_labels_parse(self):
        self._bold_log()
        out = run(self.root, "--session-index")
        self.assertNotIn("without a header block", out)
        self.assertNotIn("(filename; offset unknown)", out)

    def test_d_pending_json_keys_case_insensitive(self):
        scratch = self.root / "AI_CONTEXT" / "scratch" / UUID
        scratch.mkdir(parents=True)
        body = ('{"Status": "PENDING", "Target": "AI_CONTEXT/SESSION_INDEX.md", "Base": "abcd1234",'
                ' "Edits": [{"Old": "anchor text long enough here", "New": "replacement text long enough"}]}')
        (scratch / "PENDING_upper.json").write_text(body, encoding="utf-8")
        (scratch / "PENDING_lower.json").write_text(body.lower().replace('"pending"', '"PENDING"'), encoding="utf-8")
        out = section(run(self.root, "--pending"), "Pending files (report only)")
        self.assertIn("pending files: 2, edit blocks: 2 (no Status: line: 0;", out)
        upper = [l for l in out.splitlines() if "PENDING_upper.json" in l]
        lower = [l for l in out.splitlines() if "PENDING_lower.json" in l]
        self.assertEqual(upper[0].split()[0:2], lower[0].split()[0:2], out)  # same state label

    def test_e_out_inside_root_rejected_case_insensitively(self):
        target = self.root / "report.txt"
        cmd = [sys.executable, str(PY), "--root", str(self.root), "--orient", "--out", str(target)]
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("--out must be outside the audited root", r.stderr)
        if sys.platform == "win32":  # casing differs only in the drive letter and folder
            swapped = str(target).swapcase()
            r = subprocess.run([sys.executable, str(PY), "--root", str(self.root), "--orient", "--out", swapped],
                               capture_output=True, text=True, encoding="utf-8")
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("--out must be outside the audited root", r.stderr)

    def test_b_orient_out_prints_header_python(self):
        self._bold_log()
        out = run(self.root, "--orient", "--out", str(self.tmp / "py.txt"))
        self.assertIn("Read-only work-mode check of", out)
        self.assertIn("Helper: ", out)
        self.assertIn("(audit_folder.py ", out)
        self.assertIn("Generated ", out)
        self.assertIn("== Findings at a glance ==", out)

    @unittest.skipUnless(POWERSHELL, "PowerShell not available")
    def test_b_orient_out_header_parity_powershell(self):
        self._bold_log()
        py = run(self.root, "--orient", "--out", str(self.tmp / "py.txt"))
        ps = run(self.root, "-Orient", "-Out", str(self.tmp / "ps.txt"), powershell=True)
        for needle in ("Read-only work-mode check of", "Helper: ", "Generated ", "== Findings at a glance =="):
            self.assertIn(needle, ps, needle)
        # Same line set before the glance section apart from the helper file name and timestamp.
        def head(text):
            keep = []
            for ln in text.splitlines():
                if ln.startswith("== "):
                    break
                if ln.startswith(("Helper:", "Generated")):
                    ln = ln.split(" ")[0]
                keep.append(ln.rstrip().replace("\\", "/"))
            return keep
        self.assertEqual(head(py), head(ps))

    @unittest.skipUnless(POWERSHELL, "PowerShell not available")
    def test_c_bold_header_labels_parity_powershell(self):
        self._bold_log()
        ps = run(self.root, "-SessionIndex", powershell=True)
        self.assertNotIn("without a header block", ps)
        self.assertNotIn("(filename; offset unknown)", ps)


if __name__ == "__main__":
    unittest.main()
