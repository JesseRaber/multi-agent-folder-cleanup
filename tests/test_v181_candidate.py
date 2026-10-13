"""v1.8.1 candidate (R268 work routing, R269 backup pending copies, R270 split tables, R271 quick-context size)."""

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


if __name__ == "__main__":
    unittest.main()
