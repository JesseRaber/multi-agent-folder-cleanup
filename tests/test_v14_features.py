#!/usr/bin/env python3
"""Regression tests for the v1.4.0 efficiency and multi-agent checks.

Each fixture element reproduces a condition observed in a real shared portfolio
on 2026-10-01: an AGENTS.md over Codex's 32 KiB budget, a proposed AGENTS.md
inside Incoming/, stale skill copies, an Info-ZIP temp file left by an
interrupted write, a pip --target install inside a synced folder, session logs
missing from a session index, scratch working copies, and path lengths measured
on a mount prefix instead of the real Windows path.
"""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import yaml

REPO = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO / "skills/multi-agent-folder-cleanup"
SCRIPTS = SKILL_ROOT / "scripts"
PY_AUDIT = SCRIPTS / "audit_folder.py"
PS_AUDIT = SCRIPTS / "audit_folder.ps1"
VERIFY = SCRIPTS / "verify_move.py"
POWERSHELL = shutil.which("pwsh") or shutil.which("powershell.exe")

SESSION_A = "2026-09-29_074727_codex_adoption_1ce08906-3ae0-41ab-8998-a26a875af4db.md"
SESSION_B = "2026-09-29_163532_codex_retest_6d526760-cf4c-4d48-9ec5-61f35e915bae.md"
SESSION_C = "2026-09-30_000521_codex_review_dba59a7d-fba3-4264-8db5-58043b45b646.md"
DEEP = ("deep/folder/with/a/very/long/enough/name/to/cross/the/configured/"
        "threshold/for/this/regression/test/file.md")
HOST_ROOT = r"C:\Users\Someone\OneDrive - Example Co\AI Project Folders\Demo"


def run_py(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    env = dict(os.environ, NO_COLOR="1")
    return subprocess.run([sys.executable, str(PY_AUDIT), *args], capture_output=True,
                          text=True, encoding="utf-8", errors="replace", env=env,
                          stdin=subprocess.DEVNULL, check=check)


def run_ps(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    cmd = [POWERSHELL, "-NoProfile"]
    if Path(POWERSHELL).name.lower().startswith("powershell"):
        cmd += ["-ExecutionPolicy", "Bypass"]
    return subprocess.run(cmd + ["-File", str(PS_AUDIT), *args], capture_output=True,
                          text=True, encoding="utf-8", errors="replace",
                          stdin=subprocess.DEVNULL, check=check)


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


def write(root: Path, rel: str, data: str | bytes) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, bytes):
        path.write_bytes(data)
    else:
        path.write_text(data, encoding="utf-8")


def build_fixture(root: Path) -> None:
    write(root, "AGENTS.md", "# Rules\n" + ("x" * 79 + "\n") * 420)  # 33,608 bytes
    write(root, "AI_CONTEXT/PROJECT_QUICK_CONTEXT.md", "# Quick context\n" + ("q" * 99 + "\n") * 90)
    write(root, "AI_CONTEXT/SESSION_INDEX.md",
          "# Sessions\n"
          f"| [a](SESSIONS/{SESSION_A}) |\n"
          "| 6d526760-cf4c-4d48-9ec5-61f35e915bae | listed by id only |\n")
    for name in (SESSION_A, SESSION_B, SESSION_C):
        write(root, f"AI_CONTEXT/SESSIONS/{name}", "# Session\n")
    write(root, "AI_CONTEXT/scratch/abc/PROJECT_INDEX.md", "# working copy\n")
    write(root, "Incoming/Rules v2 (Proposed)/AGENTS.md", "# Proposed rules\n")
    write(root, "docs/README.md", "# Docs\n")
    write(root, "Skill Copies/A/demo-skill/SKILL.md",
          "---\nname: demo-skill\nmetadata:\n  version: \"1.0.0\"\n---\n# Demo\n")
    write(root, "Skill Copies/B/demo-skill/SKILL.md", "---\nname: demo-skill\n---\n# Old demo\n")
    write(root, "pkg/demo-skill.skill", b"PK\x03\x04skill-bytes")
    write(root, "AI_CONTEXT/ziAB12cd", b"PK\x03\x04interrupted-zip")
    write(root, "blob", b"PK\x03\x04no-extension-archive")
    write(root, "~$report.docx", b"lock")
    write(root, "downloads/file.crdownload", b"partial")
    for d in ("anyio-4.1.dist-info", "numpy-2.0.dist-info", "torch-2.5.dist-info"):
        write(root, f"tools/.audio-tools/{d}/METADATA", "Name: x\n")
    write(root, "tools/.audio-tools/torch/__init__.py", "")
    write(root, "tools/.audio-tools/torch/__pycache__/a.cpython-312.pyc", b"\x00")
    write(root, "src/__pycache__/m.cpython-312.pyc", b"\x00")
    write(root, "lib/__pycache__/n.cpython-312.pyc", b"\x00")
    write(root, ".git/config", "[core]\n")
    write(root, DEEP, "deep\n")
    write(root, "INDEX.md", "# Index\n- [Docs](docs/README.md)\n- [Gone](gone.md)\n")


COMMON = ["--hash-files", "--suggest-excludes", "--index-path", "INDEX.md",
          "--entrypoint", "AGENTS.md", "--entrypoint", "AI_CONTEXT/PROJECT_QUICK_CONTEXT.md",
          "--entrypoint", "AI_CONTEXT/MISSING.md",
          "--index-coverage", "AI_CONTEXT/SESSION_INDEX.md=AI_CONTEXT/SESSIONS",
          "--host-root", HOST_ROOT, "--path-threshold", "165"]

PS_COMMON = ["-HashFiles", "-SuggestExcludes", "-IndexPath", "INDEX.md",
             "-EntryPoint", "AGENTS.md,AI_CONTEXT/PROJECT_QUICK_CONTEXT.md,AI_CONTEXT/MISSING.md",
             "-IndexCoverage", "AI_CONTEXT/SESSION_INDEX.md=AI_CONTEXT/SESSIONS",
             "-HostRoot", HOST_ROOT, "-PathThreshold", "165"]


def normalize(text: str, root: Path) -> list[str]:
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


class V14PythonFeatureTests(unittest.TestCase):
    maxDiff = None

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name) / "Demo"
        self.root.mkdir()
        build_fixture(self.root)
        self.out = run_py("--root", str(self.root), *COMMON).stdout

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_oversized_and_misplaced_instruction_files(self) -> None:
        instr = section(self.out, "Instruction files found")
        self.assertIn("OVER 32 KiB", instr)
        self.assertIn("./AGENTS.md", instr)
        self.assertIn("LIVE-LOADING NAME IN NON-GOVERNING LOCATION: ./Incoming/Rules v2 (Proposed)/AGENTS.md", instr)
        self.assertIn("README / startup files: 1", instr)

    def test_startup_read_set_and_entrypoints(self) -> None:
        read = section(self.out, "Startup read set (budget 40 KB)")
        self.assertIn("AGENTS.md", read)
        self.assertIn("AI_CONTEXT/PROJECT_QUICK_CONTEXT.md", read)
        self.assertIn("OVER BUDGET", read)
        self.assertEqual(read.count("AGENTS.md"), 1)  # root file listed once
        self.assertIn("MISSING  AI_CONTEXT/MISSING.md", section(self.out, "Expected entrypoints"))

    def test_index_coverage_finds_unlisted_session(self) -> None:
        cov = section(self.out, "Index coverage")
        self.assertIn("Files directly in AI_CONTEXT/SESSIONS: 3", cov)
        self.assertIn("NOT MENTIONED: 1", cov)
        self.assertIn(SESSION_C, cov)
        self.assertNotIn(SESSION_B, cov)  # matched by its UUID

    def test_embedded_skill_copies_and_versions(self) -> None:
        skills = section(self.out, "Embedded skill copies")
        self.assertIn("demo-skill  1.0.0  ./Skill Copies/A/demo-skill/SKILL.md", skills)
        self.assertIn("demo-skill  (no version)  ./Skill Copies/B/demo-skill/SKILL.md", skills)
        self.assertIn("3 copies of demo-skill (versions: (no version), (packaged), 1.0.0)", skills)

    def test_orphaned_temporary_files(self) -> None:
        orphans = section(self.out, "Possible orphaned temporary files")
        self.assertIn("Info-ZIP temp name", orphans)
        self.assertIn("archive data without extension", orphans)
        self.assertIn("Office lock/temp", orphans)
        self.assertIn("temporary extension", orphans)
        self.assertNotIn("demo-skill.skill", orphans)

    def test_suggestions_collapse_and_find_environments(self) -> None:
        sug = section(self.out, "Suggested exclusions")
        self.assertEqual(sug.count("__pycache__"), 1)
        self.assertIn("'**/__pycache__/**'", sug)
        self.assertIn("'tools/.audio-tools/**'  [Python environment]", sug)
        self.assertIn("'.git/**'", sug)

    def test_path_length_uses_host_root_and_relative_paths(self) -> None:
        longp = section(self.out, "Path length risks")
        self.assertIn(f"Measured against: {HOST_ROOT}", longp)
        rel = DEEP
        self.assertIn(f"{len(HOST_ROOT) + 1 + len(rel)}  ./{rel}", longp)
        self.assertNotIn(str(self.root), longp)

    def test_scratch_claims_are_counted_not_listed(self) -> None:
        claims = section(self.out, "Claims requiring verification")
        self.assertNotIn("scratch/abc/PROJECT_INDEX.md", claims)
        self.assertIn("1 more under scratch/ folders not listed", claims)

    def test_findings_at_a_glance(self) -> None:
        glance = section(self.out, "Findings at a glance")
        expected = {
            "Broken index links / indexes:": "1",
            "Files missing from indexes:": "1",
            "Missing entrypoints:": "1",
            "AGENTS.md over 32 KiB:": "1",
            "Misplaced live-loading names:": "1",
            "Possible orphaned temp files:": "4",
            "Path length risks:": "1",
        }
        for label, value in expected.items():
            with self.subTest(label=label):
                self.assertRegex(glance, rf"{label}\s+{value}\b")
        self.assertRegex(glance, r"Embedded skill copies:\s+3 \(1 name")
        self.assertRegex(glance, r"Startup read set:\s+\d+\.\d KB OVER BUDGET")

    def test_brief_caps_lists(self) -> None:
        for i in range(30):
            write(self.root, f"many/f{i:02d}/dup.md", f"{i}\n")
        brief = run_py("--root", str(self.root), "--brief", "--hash-files").stdout
        full = run_py("--root", str(self.root), "--hash-files").stdout
        self.assertIn("== Per-folder counts (top 10) ==", brief)
        dup = section(brief, "Duplicate names across folders")
        self.assertIn("... and 27 more", dup)  # 30 copies, 3 shown
        self.assertLess(len(brief), len(full))

    def test_out_writes_full_report_and_prints_summary(self) -> None:
        dest = Path(self._tmp.name) / "report.txt"
        res = run_py("--root", str(self.root), *COMMON, "--out", str(dest))
        self.assertTrue(dest.is_file())
        full = dest.read_text(encoding="utf-8")
        self.assertIn("== Duplicate names across folders ==", full)
        self.assertNotIn("== Duplicate names across folders ==", res.stdout)
        self.assertIn("== Summary ==", res.stdout)
        self.assertIn("== Findings at a glance ==", res.stdout)
        self.assertIn(f"Full report: {dest}", res.stdout)
        again = run_py("--root", str(self.root), "--out", str(dest), check=False)
        self.assertNotEqual(again.returncode, 0)
        inside = run_py("--root", str(self.root), "--out", str(self.root / "r.txt"), check=False)
        self.assertNotEqual(inside.returncode, 0)
        self.assertFalse((self.root / "r.txt").exists())

    def test_prune_noise_lists_and_discloses(self) -> None:
        out = run_py("--root", str(self.root), "--prune-noise").stdout
        pruned = section(out, "Pruned generated state")
        self.assertIn("./.git", pruned)
        self.assertIn("Python environment (4 subfolders) ./tools/.audio-tools", " ".join(pruned.split()))
        self.assertNotIn("./tools/.audio-tools/torch", pruned)
        self.assertIn("./src/__pycache__", pruned)
        self.assertRegex(section(out, "Summary"), r"Pruned folders:\s+\d+")
        self.assertIn("pruned as generated state", out)
        # Real folders named like noise are still walked.
        write(self.root, "logs/note.md", "kept\n")
        out = run_py("--root", str(self.root), "--prune-noise").stdout
        self.assertNotIn("./logs", section(out, "Pruned generated state"))

    @unittest.skipIf(os.name == "nt", "coarse Windows clock makes a zero-length budget unreliable")
    def test_max_seconds_discloses_unvisited_directories(self) -> None:
        out = run_py("--root", str(self.root), "--max-seconds", "0.000000001").stdout
        self.assertIn("WALK INCOMPLETE", section(out, "Summary"))
        self.assertIn("queued directories were never visited", out)


class V14VersionTests(unittest.TestCase):
    def test_script_versions_match_skill(self) -> None:
        text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        version = yaml.safe_load(text.split("---", 2)[1])["metadata"]["version"]
        self.assertEqual(run_py("--version").stdout.strip(), f"audit_folder.py {version}")
        out = subprocess.run([sys.executable, str(VERIFY), "--version"], capture_output=True,
                             text=True, check=True).stdout.strip()
        self.assertEqual(out, f"verify_move.py {version}")
        ps_text = PS_AUDIT.read_text(encoding="utf-8")
        self.assertIn(f"$ScriptVersion = '{version}'", ps_text)
        if POWERSHELL:
            self.assertEqual(run_ps("-Version").stdout.strip(), f"audit_folder.ps1 {version}")


@unittest.skipUnless(POWERSHELL, "PowerShell is required for v1.4 report parity")
class V14ParityTests(unittest.TestCase):
    maxDiff = None

    def _compare(self, py_args: list[str], ps_args: list[str]) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "Demo"
            root.mkdir()
            build_fixture(root)
            py = run_py("--root", str(root), *py_args).stdout
            ps = run_ps("-Root", str(root), *ps_args).stdout
            self.assertEqual(normalize(py, root), normalize(ps, root))

    def test_all_new_checks_match(self) -> None:
        self._compare(COMMON, PS_COMMON)

    def test_brief_and_prune_match(self) -> None:
        self._compare(["--brief", "--prune-noise", "--hash-files"],
                      ["-Brief", "-PruneNoise", "-HashFiles"])

    def test_out_summary_matches(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "Demo"
            root.mkdir()
            build_fixture(root)
            py_dest, ps_dest = Path(temp) / "py.txt", Path(temp) / "ps.txt"
            py = run_py("--root", str(root), *COMMON, "--out", str(py_dest)).stdout
            ps = run_ps("-Root", str(root), *PS_COMMON, "-Out", str(ps_dest)).stdout
            strip = lambda t: [ln for ln in normalize(t, root) if not ln.startswith("Full report:")]
            self.assertEqual(strip(py), strip(ps))
            self.assertEqual(normalize(py_dest.read_text(encoding="utf-8"), root),
                             normalize(ps_dest.read_text(encoding="utf-8"), root))


if __name__ == "__main__":
    unittest.main()
