#!/usr/bin/env python3
"""v1.5 work-mode helpers: --orient and --session-index (read-only)."""

from __future__ import annotations

import os
import importlib.util
from unittest import mock
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

REPO = Path(__file__).resolve().parents[1]
PY = REPO / "skills/multi-agent-folder-cleanup/scripts/audit_folder.py"
PS = REPO / "skills/multi-agent-folder-cleanup/scripts/audit_folder.ps1"
OLD = time.time() - 3 * 86400


def build(root: Path) -> None:
    def w(rel, text, mtime=None):
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8", newline="\n")
        if mtime:
            os.utime(p, (mtime, mtime))
    w("AGENTS.md", "# rules\n")
    w("PROJECT_INDEX.md", "# Index\n- [docs](docs/)\n- old.md\n")
    w("AI_CONTEXT/PROJECT_QUICK_CONTEXT.md", "q\n" * 8000)
    w("AI_CONTEXT/SESSIONS/2026-10-01_090000_codex_first-task_11111111-1111-4111-8111-111111111111.md",
      "- Session ID: 11111111-1111-4111-8111-111111111111\n- Started: 2026-10-01T09:00:00-04:00\n"
      "- Tool/runtime: Codex (gpt)\n\n## T001 — 2026-10-01T09:00:00-04:00 — First task done\n", OLD)
    w("AI_CONTEXT/SESSIONS/2026-10-02_100000_claude_second_22222222-2222-4222-8222-222222222222.md",
      "- Session ID: 22222222-2222-4222-8222-222222222222\n- Started: 2026-10-02T10:00:00-04:00\n"
      "- Tool/runtime: Claude\n\n## T001 — 2026-10-02T10:00:00-04:00 — Start\n"
      "T002 | 2026-10-02T11:30:00.1234567-04:00 | Shipped draft\n")
    w("AI_CONTEXT/SESSIONS/notes.md", "x\n")
    w("AI_CONTEXT/SESSION_INDEX.md",
      "| x | [Session](SESSIONS/2026-10-01_090000_codex_first-task_11111111-1111-4111-8111-111111111111.md) |\n"
      "| y | [Session](SESSIONS/gone_33333333-3333-4333-8333-333333333333.md) |\n")
    w("AI_CONTEXT/scratch/abc/n.txt", "s\n")
    w("docs/new report.md", "new\n")
    w("old.md", "o\n", OLD - 30 * 86400)
    w(".env", "SECRET=1\n")
    w("node_modules/x.js", "x\n")


def run_py(root, *args):
    return subprocess.run([sys.executable, str(PY), "--root", str(root), *args],
                          capture_output=True, text=True, encoding="utf-8")


def snapshot(root: Path):
    return sorted((str(p.relative_to(root)), p.stat().st_mtime_ns, p.stat().st_size)
                  for p in root.rglob("*") if p.is_file())


class WorkModeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        build(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def test_session_index_reports_missing_rows_stale_links_and_nonstandard(self):
        r = run_py(self.root, "--session-index")
        self.assertEqual(r.returncode, 0, r.stderr)
        out = r.stdout
        self.assertIn("session logs: 2", out)
        self.assertIn("sessions missing from index: 1", out)
        self.assertIn("| 22222222-2222-4222-8222-222222222222 | Claude | second | (fill in) | (fill in) |", out)
        self.assertNotIn("11111111-1111-4111-8111-111111111111 | Codex", out)
        self.assertIn("index links to missing session logs: 1", out)
        self.assertIn("SESSIONS/gone_33333333", out)
        self.assertIn("notes.md (no session UUID", out)

    def test_orient_reports_activity_changes_and_unindexed(self):
        r = run_py(self.root, "--orient")
        self.assertEqual(r.returncode, 0, r.stderr)
        out = r.stdout
        self.assertIn("possibly active writers (changed in last 30 min): 1 distinct sessions, 1 unpaired scratch folders", out)
        self.assertIn("start of latest session 22222222", out)
        self.assertIn("docs/new report.md", out)
        self.assertNotIn("  old.md", out)
        self.assertNotIn("node_modules", out.split("generated-state")[0])
        self.assertIn("changed files the index never names: 2", out)  # docs/new report.md and .env name
        self.assertIn("OVER 12 KB: replace stale lines", out)
        self.assertIn("quick context over size          yes", out)

    def test_session_id_excludes_self_and_moves_baseline(self):
        out = run_py(self.root, "--orient", "--session-id", "2222").stdout
        self.assertIn("0 distinct sessions, 1 unpaired scratch folders", out)
        self.assertIn("start of latest session 11111111", out)

    def test_never_reads_credential_names_or_writes(self):
        before = snapshot(self.root)
        out = run_py(self.root, "--orient", "--session-index").stdout
        self.assertNotIn("SECRET=1", out)
        self.assertEqual(before, snapshot(self.root))

    def test_since_validation_and_out(self):
        bad = run_py(self.root, "--orient", "--since", "yesterday")
        self.assertNotEqual(bad.returncode, 0)
        with tempfile.TemporaryDirectory() as o:
            target = Path(o) / "r.txt"
            r = run_py(self.root, "--orient", "--session-index", "--out", str(target))
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("Findings at a glance", r.stdout)
            self.assertIn("== Orient ==", target.read_text(encoding="utf-8"))

    def assert_work_parity(self, *flags):
        py = run_py(self.root, *flags)
        self.assertEqual(py.returncode, 0, py.stderr)
        ps = shutil.which("pwsh") or shutil.which("powershell.exe")
        if ps:
            mapping = {"--session-index": "-SessionIndex", "--orient": "-Orient",
                       "--sessions-dir": "-SessionsDir", "--session-index-file": "-SessionIndexFile"}
            pw = subprocess.run([ps, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(PS),
                                 "-Root", str(self.root), *[mapping.get(f, f) for f in flags]],
                                capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(pw.returncode, 0, pw.stderr)
            norm = lambda text: [line.rstrip() for line in text.splitlines()
                                 if not line.startswith(("Generated ", "Read-only work-mode"))]
            self.assertEqual(norm(py.stdout), norm(pw.stdout), pw.stderr)
        return py.stdout

    def test_duplicate_ids_do_not_propose_ambiguous_rows_or_baselines(self):
        sessions = self.root / "AI_CONTEXT/SESSIONS"
        source = next(sessions.glob("*22222222*.md"))
        (sessions / "duplicate.md").write_bytes(source.read_bytes())
        out = self.assert_work_parity("--session-index", "--orient")
        self.assertIn("duplicate session IDs: 1", out)
        self.assertNotIn("| 22222222-2222-4222-8222-222222222222 |", out)
        self.assertIn("start of latest session 11111111", out)
        self.assertTrue(source.exists())
        self.assertTrue((sessions / "duplicate.md").exists())

    def test_oversized_log_is_not_reported_as_latest_complete_record(self):
        source = next((self.root / "AI_CONTEXT/SESSIONS").glob("*22222222*.md"))
        source.write_text(source.read_text(encoding="utf-8") + "x" * (1048576 + 1), encoding="utf-8")
        before = snapshot(self.root)
        out = self.assert_work_parity("--session-index")
        self.assertIn("read incomplete (over 1048576 characters)", out)
        self.assertIn("session logs not parsed (blocked, unreadable or incomplete): 1", out)
        self.assertNotIn("Shipped draft |", out)
        self.assertEqual(before, snapshot(self.root))

    def test_unreadable_index_cannot_be_reported_as_missing_rows(self):
        index = self.root / "AI_CONTEXT/SESSION_INDEX.md"
        index.write_text("x" * (1048576 + 1), encoding="utf-8")
        out = self.assert_work_parity("--session-index")
        self.assertIn("n/a (index not inspected)", out)
        self.assertNotIn("Proposed rows", out)
        self.assertNotIn("index links to missing session logs: 0", out)

    def test_naive_recorded_times_stay_unknown_and_mtime_is_labeled(self):
        source = next((self.root / "AI_CONTEXT/SESSIONS").glob("*22222222*.md"))
        text = source.read_text(encoding="utf-8").replace("-04:00", "")
        source.write_text(text, encoding="utf-8")
        out = self.assert_work_parity("--session-index", "--orient")
        self.assertIn("[filename; no offset]", out)
        self.assertIn("(file mtime; not recorded activity)", out)
        self.assertIn("start of latest session 22222222", out)
        self.assertRegex(out, r"2026-10-01T\d{2}:\d{2}[+-]\d{2}:\d{2}")

    def test_absent_and_guard_blocked_folder_have_distinct_states(self):
        absent = self.assert_work_parity("--session-index", "--sessions-dir", "absent")
        self.assertIn("sessions folder NOT FOUND (coverage unavailable)", absent)
        blocked = self.assert_work_parity("--session-index", "--sessions-dir", ".env")
        self.assertIn("sessions folder UNAVAILABLE (read blocked)", blocked)
        self.assertNotIn("SECRET=1", blocked)
        self.assertNotIn("sessions missing from index: 0", blocked)

    def test_permission_errors_remain_unavailable_not_absent(self):
        spec = importlib.util.spec_from_file_location("work_audit_permission_test", PY)
        helper = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = helper
        spec.loader.exec_module(helper)
        with mock.patch.object(helper.os, "stat", side_effect=PermissionError("denied")):
            self.assertEqual(helper.work_path_state(str(self.root)), "UNAVAILABLE")
        with mock.patch.object(helper.os, "listdir", side_effect=PermissionError("denied")):
            _, sessions, _, blocked = helper.load_sessions(str(self.root), "AI_CONTEXT/SESSIONS")
            self.assertIsNone(sessions)
            self.assertEqual(blocked, ["UNAVAILABLE (listing failed)"])

    def test_powershell_parity(self):
        ps = shutil.which("pwsh") or shutil.which("powershell.exe")
        if not ps:
            self.skipTest("PowerShell is required for cross-language parity")
        for pa, sa in [(["--orient", "--session-index"], ["-Orient", "-SessionIndex"]),
                       (["--orient", "--session-id", "2222", "--brief"], ["-Orient", "-SessionId", "2222", "-Brief"])]:
            py = run_py(self.root, *pa)
            pw = subprocess.run([ps, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(PS),
                                 "-Root", str(self.root), *sa], capture_output=True, text=True, encoding="utf-8")
            norm = lambda t: [l.rstrip() for l in t.splitlines()
                              if not l.startswith(("Generated ", "Read-only work-mode"))]
            self.assertEqual(norm(py.stdout), norm(pw.stdout), pw.stderr)

    def test_quick_context_structure_warning(self):
        qc = self.root / "AI_CONTEXT/PROJECT_QUICK_CONTEXT.md"
        qc.write_text("# Quick\n2026-10-01 updated\n2026-10-03 updated\n2026-10-02 updated\n", encoding="utf-8")
        out = run_py(self.root, "--orient").stdout
        self.assertIn("quick context header structure: 3 update-like lines", out)
        self.assertIn("dates out of descending order", out)

    def test_lifecycle_and_credential_tiers(self):
        (self.root / "certifi").mkdir()
        (self.root / "certifi/cacert.pem").write_text("public bundle fixture", encoding="utf-8")
        (self.root / "server.pem").write_text("ambiguous fixture", encoding="utf-8")
        (self.root / "HANDOFF.md").write_text("Status: current", encoding="utf-8")
        (self.root / "NEXT_REVIEW_PROMPT.md").write_text("Status: current", encoding="utf-8")
        p = self.root / "AI_CONTEXT/scratch/x/PENDING_SHARED_UPDATES.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("Status: Superseded\n", encoding="utf-8")
        (self.root / "release-candidate.zip").write_bytes(b"fixture")
        out = run_py(self.root, "--brief").stdout
        self.assertIn("recognizable public CA bundle: 1", out)
        self.assertIn("ambiguous cryptographic material: 1", out)
        self.assertIn("handoff/next-prompt files outside non-governing areas: 2", out)
        self.assertIn("Superseded", out)
        self.assertIn("candidate/release/superseded ZIPs requiring channel review: 1", out)

    def test_portfolio_health_states(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "empty").mkdir()
            (root / "unmanaged").mkdir()
            (root / "unmanaged/work.txt").write_text("x", encoding="utf-8")
            (root / "managed").mkdir()
            (root / "managed/AGENTS.md").write_text("rules", encoding="utf-8")
            out = run_py(root, "--portfolio", "--brief").stdout
            self.assertIn("empty | root-level | empty | 0", out)
            self.assertIn("unmanaged | root-level | unmanaged | 1", out)
            self.assertIn("managed | root-level | managed | 1", out)

    def test_work_guidance_covers_new_lifecycles(self):
        text = (REPO / "skills/multi-agent-folder-cleanup/references/work-mode.md").read_text(encoding="utf-8")
        for phrase in ("same task is active", "one explicitly current handoff per subject",
                       "Pending**, **Applied**, **Superseded**, **Conflicted** or **Unverifiable",
                       "same-version candidate", "exactly one authoritative project-wide tracker",
                       "do not create a substitute roadmap", "newly discovered future work"):
            self.assertIn(phrase, text)

    def test_optional_rules_carry_single_tracker_requirement(self):
        text = (REPO / "skills/multi-agent-folder-cleanup/references/project-rules/AGENTS.proposed.md").read_text(encoding="utf-8")
        for phrase in ("exactly one authoritative project-wide tracker",
                       "Do not create a competing roadmap", "one exact pending tracker insertion",
                       "Delegated helpers return proposed rows"):
            self.assertIn(phrase, text)

    def test_v151_decision_invariants_are_routed_to_relevant_modes(self):
        refs = REPO / "skills/multi-agent-folder-cleanup/references"
        preconditions = (refs / "preconditions.md").read_text(encoding="utf-8")
        connector = (refs / "connector-audit.md").read_text(encoding="utf-8")
        audit = (refs / "audit-mode.md").read_text(encoding="utf-8")
        work = (refs / "work-mode.md").read_text(encoding="utf-8")

        # Ambiguous connector roots stop only root-dependent work and retain identity evidence.
        self.assertIn("multiple same-name candidate roots", preconditions)
        self.assertIn("stable identifier", preconditions)
        self.assertIn("stop the affected inspection or mutation", connector)

        # File properties never become authority evidence for a canonical root.
        connector_lower = connector.lower()
        for prohibited_basis in ("filename", "newest modified time", "search rank", "matching bytes/hashes"):
            self.assertIn(prohibited_basis, connector_lower)
        self.assertIn("owner direction or applicable adopted authority/navigation", connector)

        # Audit and Work modes receive only their relevant additions.
        self.assertIn("`Documented`, `Observed`, `Inferred` or `Unknown`", audit)
        self.assertIn("What would verify it", audit)
        self.assertIn("Before creating an important standalone file", work)
        self.assertIn("bounded pre-write check", work)


if __name__ == "__main__":
    unittest.main()
