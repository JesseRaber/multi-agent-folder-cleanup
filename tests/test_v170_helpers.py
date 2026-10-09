"""Stage 2 of v1.7.0: helper checks in audit_folder.py and audit_folder.ps1.

Register rows R030, R155/R201/R212 (--pending), R161, R165/R166, R168, R189/R209,
R206, R207, R208, R211, R213, R214, R215. Every check is report-only.
"""

import hashlib
import os
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
TEMPLATE = REPO / "skills/multi-agent-folder-cleanup/references/project-rules/AGENTS.proposed.md"
ZIP_TIME = 1767243600  # identical modified time, as left by archive extraction
FIXED_TIME = 1767330000


def powershell():
    requested = os.environ.get("AUDIT_TEST_POWERSHELL")
    return shutil.which(requested) if requested else (shutil.which("pwsh") or shutil.which("powershell.exe"))


def w(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, bytes):
        path.write_bytes(data)
    else:
        path.write_text(data, encoding="utf-8", newline="\n")


def build(base):
    a = base / "port" / "projA"
    w(a / "AGENTS.md", TEMPLATE.read_text(encoding="utf-8"))
    w(a / "AI_CONTEXT/README_FIRST.md", "Read [quick](PROJECT_QUICK_CONTEXT.md) then `PROJECT_INDEX.md`.\n")
    w(a / "AI_CONTEXT/PROJECT_QUICK_CONTEXT.md", "# QC\nstate\n")
    w(a / "PROJECT_INDEX.md", "# Index\n- docs/plan.md\n")
    w(a / "docs/plan.md", "plan\n")
    w(a / "docs/plan (1).md", "plan copy\n")
    w(a / "docs/orphan (1).md", "x\n")
    w(a / "docs/plan-DESKTOP7.md", "p\n")
    w(a / "docs/README-v2.md", "not a conflict copy: lowercase suffix\n")
    w(a / "AI_CONTEXT/research.pdf", b"binary")
    w(a / "AI_CONTEXT/report.md", "loose\n")
    w(a / "tool/.gitignore", "x\n")
    w(a / "tool/README.md", "tool\n")
    w(a / "History/skillcopy/SKILL.md", "---\nname: x\n---\n")
    w(a / "AI_CONTEXT/scratch/s1/pkg/SKILL.md", "---\nname: y\n---\n")
    digest = hashlib.sha256((a / "PROJECT_INDEX.md").read_bytes()).hexdigest()
    s1 = a / "AI_CONTEXT/scratch/s1"
    w(s1 / "PENDING_PROJECT_INDEX.md",
      f"Status: PENDING\nTarget: PROJECT_INDEX.md\nBase: {digest}\nEdit: append\nNew: - docs/new-file-row.md\n")
    w(s1 / "pending-index.md", "Target: PROJECT_INDEX.md\nNew: - docs/plan.md\n")
    w(s1 / "PENDING_QC.md", "Status: PENDING\nTarget: PROJECT_INDEX.md\nBase: " + "0" * 64
      + "\nNew: - docs/never-added-row.md\n")
    w(s1 / "PENDING_ANCHOR.md", "Status: PENDING\nTarget: PROJECT_INDEX.md\nInsert after: - docs/plan.md\n"
      "New:\n```\n- docs/fenced-new-row.md\n```\n")
    w(s1 / "PENDING_DONE.md", "Status: APPLIED abcd1234 by x/T001\nTarget: PROJECT_INDEX.md\n")
    w(s1 / "PENDING_GONE.md", "Status: PENDING\nTarget: missing/file.md\n")
    w(s1 / "PENDING_V1_SHARED.json",
      '{"status":"PENDING","target":"PROJECT_INDEX.md","edits":'
      '[{"insert_after":"- docs/plan.md","new_line":"- docs/json-added-row.md"}]}')
    w(s1 / "spending-notes.md", "not a pending file\n")
    w(a / "Incoming/2026-10-08_muse_x/_PROVENANCE.md", "Tool: muse\nPENDING index row for docs/plan-DESKTOP7.md\n")
    w(a / "AI_CONTEXT/PROJECT_ACTIVITY_JOURNAL.md", "# J\n" + "a" * 120000)
    w(a / "AI_CONTEXT/SESSIONS/2026-10-08_100000_muse_x_11111111-1111-4111-8111-111111111111.md",
      "# Session 1\nT001 | 2026-10-08T10:00-04:00 | x\nWork/result: wrote docs/plan.md\n")
    for i in range(12):
        f = a / f"zipped/f{i:02d}.md"
        w(f, "z\n")
        os.utime(f, (ZIP_TIME, ZIP_TIME))
    w(base / "port/projB/Handoffs/2026-10-08_handoff.md", "Status: current\nTo: projA and others\n")
    w(base / "port/projB/AGENTS.md", "# Rules\nVersion: 3.2.0\n\n## 1. Authority\n\n- one\n")
    w(base / "port/projC/AGENTS.md", "# Wrapper\nAdopts [rules](AI_CONTEXT/PROJECT_RULES_3.2.0.md).\n")
    w(base / "port/projC/AI_CONTEXT/PROJECT_RULES_3.2.0.md", "Version: 3.2.0\n## 1. A\n- x\n")
    w(base / "port/projA - Copy/README.md", "copy\n")
    # Whole-second, identical times outside zipped/: ordering then depends only on
    # the ordinal path tie-break, which both helpers share.
    for f in base.rglob("*"):
        if f.is_file() and "zipped" not in f.parts:
            os.utime(f, (FIXED_TIME, FIXED_TIME))
    return a


def run_py(root, *flags, script=PY):
    r = subprocess.run([sys.executable, str(script), "--root", str(root), *flags],
                       capture_output=True, text=True, encoding="utf-8")
    if r.returncode:
        raise AssertionError(r.stderr or r.stdout)
    return r.stdout


def run_ps(root, *flags):
    r = subprocess.run([powershell(), "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(PS),
                        "-Root", str(root), *flags], capture_output=True, text=True, encoding="utf-8")
    if r.returncode:
        raise AssertionError(r.stderr or r.stdout)
    return r.stdout


def section(text, name):
    start = text.index(f"== {name} ==")
    end = text.find("\n== ", start + 1)
    return text[start:end if end >= 0 else len(text)]


def norm(text):
    return [line.rstrip().replace("\\", "/") for line in text.splitlines()
            if line.strip() and not line.startswith(("Generated ", "Read-only ", "Helper: "))]


class HelperChecks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.root = build(self.base)

    def tearDown(self):
        self.tmp.cleanup()

    def snapshot(self):
        return sorted((str(p), p.stat().st_mtime_ns, p.stat().st_size)
                      for p in self.base.rglob("*") if p.is_file())

    def test_pending_classification(self):
        before = self.snapshot()
        out = section(run_py(self.root, "--pending"), "Pending files (report only)")
        expect = {
            "PENDING_PROJECT_INDEX.md": "Pending (base matches)",
            "PENDING_ANCHOR.md": "Pending (anchor matches)",
            "PENDING_V1_SHARED.json": "Pending (anchor matches)",
            "PENDING_QC.md": "Conflicted (base differs, text absent)",
            "PENDING_DONE.md": "Applied (recorded)",
            "PENDING_GONE.md": "Unverifiable (target not found)",
            "pending-index.md": "Applied (not marked)",
        }
        for name, state in expect.items():
            line = next(l for l in out.splitlines() if name in l)
            self.assertTrue(line.strip().startswith(state), line)
        self.assertNotIn("spending-notes.md", out)
        self.assertIn("pending files: 7, edit blocks: 7 (no Status: line: 1; Status: not first line: 0)", out)
        self.assertIn("[no Status: line]", next(l for l in out.splitlines() if "pending-index.md" in l))
        self.assertIn("Incoming/2026-10-08_muse_x/_PROVENANCE.md (1 PENDING mentions)", out)
        self.assertIn("sequential-writer declaration found", out)
        self.assertEqual(before, self.snapshot(), "--pending must not write")

    def test_pending_real_world_shapes(self):
        """Shapes seen in the portfolio on 2026-10-08: sections, headings, prose labels."""
        s2 = self.root / "AI_CONTEXT/scratch/22222222-2222-4222-8222-222222222222"
        idx = (self.root / "PROJECT_INDEX.md").read_text(encoding="utf-8")
        digest = hashlib.sha256(idx.encode("utf-8")).hexdigest().upper()
        w(self.root / "AI_CONTEXT/SESSION_INDEX.md",
          "| Started | ID |\n|---|---|\n| 2026-10-05 | 22222222-2222-4222-8222-222222222222 (reworded row) |\n")
        w(s2 / "PENDING_SHARED_EDITS.md",
          "# Pending Shared Edits\n\n## SESSION_INDEX.md\nStatus: PENDING\nTarget: \\AI_CONTEXT/SESSION_INDEX.md\\\n"
          "Complete base SHA-256: " + "A" * 64 + "\nExact new Markdown row:\n| 2026-10-05 | original wording of the row |\n\n"
          "## PROJECT_INDEX.md\nStatus: PENDING\nTarget: \\PROJECT_INDEX.md\\\nComplete base SHA-256: " + digest + "\n"
          "Exact new Markdown row:\n| [Report](Audits/report.md) | Evidence |\n")
        w(s2 / "PENDING_NAVIGATION_EDITS.md",
          "# Pending navigation edits\n\nSession/turn: x / T001\n\n## Edit A\n\nStatus: PENDING\n"
          "Target: `PROJECT_INDEX.md`\nBase: SHA-256 " + "b" * 64 + "\n"
          "Edit: insert immediately after the row beginning `- docs/plan.md`:\n\n```\n- docs/plan.md\n```\n")
        w(s2 / "PENDING_PROSE.md", "PENDING (staging): in AI_CONTEXT/SESSION_INDEX.md, set last activity.\n")
        out = run_py(self.root, "--pending")
        line = lambda part: next(l for l in out.splitlines() if part in l)
        self.assertIn("Superseded (likely: source session ID in target)", line("PENDING_SHARED_EDITS.md [1/2]"))
        self.assertIn("-> AI_CONTEXT/SESSION_INDEX.md", line("PENDING_SHARED_EDITS.md [1/2]"))
        self.assertIn("[Status: not first line]", line("PENDING_SHARED_EDITS.md [1/2]"))
        self.assertIn("Pending (base matches)", line("PENDING_SHARED_EDITS.md [2/2]"))
        self.assertIn("Applied (not marked)", line("PENDING_NAVIGATION_EDITS.md"))
        self.assertIn("Unverifiable (no Target)", line("PENDING_PROSE.md"))
        self.assertIn("[Status: not first line]", line("PENDING_PROSE.md"))
        if powershell():
            self.assertEqual(norm(run_py(self.root, "--pending")), norm(run_ps(self.root, "-Pending")))

    def test_orient_new_checks(self):
        out = run_py(self.root, "--orient", "--since", "2020-01-01T00:00")
        self.assertIn("coordination: sequential-writer declaration found (AGENTS.md)", out)
        self.assertIn("declared read order (AI_CONTEXT/README_FIRST.md", out)
        self.assertIn("AI_CONTEXT/PROJECT_QUICK_CONTEXT.md  0 KB", out)
        self.assertIn("    PROJECT_INDEX.md  0 KB", out)
        unattributed = out.split("changed files no session log or _PROVENANCE.md names:")[1].split("\n  ")[0]
        self.assertNotIn("docs/plan.md\n", unattributed)          # named by the session log
        self.assertNotIn("docs/plan-DESKTOP7.md", unattributed)   # named by _PROVENANCE.md
        self.assertIn("identical modified times: 12 files at", out)
        self.assertIn("under zipped/ (typical of archive extraction", out)
        self.assertIn("sync conflict copies: 3 (original missing: 1)", out)
        self.assertIn("ORIGINAL MISSING docs/orphan (1).md", out)
        self.assertIn("-HOST copy original present docs/plan-DESKTOP7.md", out)
        self.assertNotIn("README-v2.md", out.split("sync conflict copies")[1].split("case-only")[0])
        self.assertIn("handoffs from sibling projects: not read (outside this root)", out)
        self.assertIn("sequential-writer declaration    yes", out)

    def test_orient_without_declaration(self):
        (self.root / "AGENTS.md").write_text("# Rules\nVersion: 3.2.0\n", encoding="utf-8")
        out = run_py(self.root, "--orient")
        self.assertIn("coordination: no sequential-writer declaration; stage PENDING edits", out)

    @unittest.skipUnless(os.path.normcase("A") == "A", "case-only names need a case-sensitive filesystem")
    def test_case_only_collisions(self):
        w(self.root / "docs/Notes.md", "a\n")
        w(self.root / "docs/notes.md", "b\n")
        out = run_py(self.root, "--orient")
        self.assertIn("case-only name collisions: 1", out)
        self.assertIn("docs/Notes.md | docs/notes.md", out)

    def test_full_audit_new_section(self):
        out = run_py(self.root)
        sec = section(out, "Sync copies, unpacked packages and continuity folders")
        self.assertIn("unpacked skill trees under scratch/backup/history/incoming: 2", sec)
        self.assertIn("repository-shaped folders without .git: 1\n    tool", sec)
        self.assertIn("AI_CONTEXT/ files that are not continuity records: 2", sec)
        self.assertIn("non-text file         6  AI_CONTEXT/research.pdf", sec)
        self.assertIn("loose file            6  AI_CONTEXT/report.md", sec)
        self.assertNotIn("README_FIRST.md", sec)
        journals = section(out, "Large journals (threshold 100 KB)")
        self.assertIn("retired legacy journal, 117 KB", journals)
        self.assertIn("superseded by SESSIONS/ logs (rules 3.x)", journals)
        inst = section(out, "Instruction files found")
        self.assertIn("OVER 16 KB, warning", inst)
        glance = section(out, "Findings at a glance")
        for row in ("AGENTS.md over 16 KB (warning):  1", "Large journals:                  0",
                    "Retired journals (no rotation):  1", "Sync conflict copies:            3"):
            self.assertIn(row, glance)
        life = section(out, "Handoff and pending-update lifecycle warnings")
        self.assertIn("pending shared-update artifacts: 7 (without a Status: first line: 1)", life)

    def test_live_journal_still_flagged(self):
        (self.root / "AGENTS.md").write_text("# Rules\n", encoding="utf-8")
        out = section(run_py(self.root), "Large journals (threshold 100 KB)")
        self.assertIn("Rotation is a proposal only", out)
        self.assertNotIn("retired legacy journal", out)

    def test_portfolio_matrix(self):
        out = section(run_py(self.base / "port", "--portfolio"), "Portfolio root matrix (immediate children; advisory)")
        rows = {l.split(" | ")[0].strip(): l.split(" | ") for l in out.splitlines() if " | root-level | " in l}
        self.assertEqual(rows["projA"][6:11], ["7 (1 no Status)", "3.3.0", "yes", "match", "yes"])
        self.assertEqual(rows["projB"][7:9] + [rows["projB"][10]], ["3.2.0", "no", "no"])
        self.assertRegex(rows["projB"][9], r"^differs \(\d+ lines\)$")
        self.assertEqual(rows["projC"][7], "3.2.0 (by reference)")
        self.assertIn("possible replicas under this root: projA ~ projA - Copy", out)
        self.assertIn("projB/Handoffs/2026-10-08_handoff.md -> projA", out)
        self.assertIn("replica declaration: none (PORTFOLIO.md)", out)
        self.assertIn("bundled template 3.3.0", out)

    def test_portfolio_without_bundled_template(self):
        # Gemini Apps and Opal packages omit references/project-rules/.
        alt = self.base / "pkg/scripts"
        alt.mkdir(parents=True)
        shutil.copy2(PY, alt / "audit_folder.py")
        out = run_py(self.base / "port", "--portfolio", script=alt / "audit_folder.py")
        self.assertIn("| unknown (no template bundled) |", out)
        self.assertNotIn("differs (", out)

    @unittest.skipUnless(powershell(), "PowerShell is required for parity")
    def test_powershell_parity(self):
        runs = [
            (["--orient", "--pending", "--since", "2020-01-01T00:00"], ["-Orient", "-Pending", "-Since", "2020-01-01T00:00"], self.root),
            (["--pending", "--brief"], ["-Pending", "-Brief"], self.root),
        ]
        for py_flags, ps_flags, root in runs:
            self.assertEqual(norm(run_py(root, *py_flags)), norm(run_ps(root, *ps_flags)), py_flags)
        full_py, full_ps = run_py(self.root), run_ps(self.root)
        for name in ("Sync copies, unpacked packages and continuity folders", "Large journals (threshold 100 KB)",
                     "Instruction files found", "Findings at a glance", "Handoff and pending-update lifecycle warnings"):
            a, b = norm(section(full_py, name)), norm(section(full_ps, name))
            self.assertEqual([x.replace("./", "") for x in a], [x.replace("./", "") for x in b], name)
        port = self.base / "port"
        name = "Portfolio root matrix (immediate children; advisory)"
        self.assertEqual(norm(section(run_py(port, "--portfolio"), name)),
                         norm(section(run_ps(port, "-Portfolio"), name)))


if __name__ == "__main__":
    unittest.main()
