#!/usr/bin/env python3
"""Observable parity checks for the Python and PowerShell audit helpers."""

from __future__ import annotations

import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
PY_AUDIT = REPO / "skills/multi-agent-folder-cleanup/scripts/audit_folder.py"
PS_AUDIT = REPO / "skills/multi-agent-folder-cleanup/scripts/audit_folder.ps1"


def section(text: str, name: str) -> str:
    match = re.search(
        rf"(?ms)^== {re.escape(name)} ==\s*(.*?)(?=^== |\Z)", text
    )
    if not match:
        raise AssertionError(f"missing section {name!r}\n{text}")
    return match.group(1)


class AuditParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not shutil.which("pwsh"):
            raise unittest.SkipTest("pwsh is required for cross-language parity")

    def test_shared_fixture_has_matching_observable_results(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "docs").mkdir()
            (root / "archive").mkdir()
            shared = b"same bytes\n"
            (root / "docs/plan.md").write_bytes(shared)
            (root / "archive/plan.md").write_bytes(shared)
            claim = root / "archive/RELEASE_NOTES_v1.1.0.md"
            claim.write_text("release candidate\n", encoding="utf-8")
            (root / ".gitignore").write_text("cache/\n", encoding="utf-8")
            (root / "INDEX.md").write_text(
                "# Index\n- [Plan](docs/plan.md)\n", encoding="utf-8"
            )

            env = dict(os.environ)
            env["NO_COLOR"] = "1"
            py = subprocess.run(
                [sys.executable, str(PY_AUDIT), "--root", str(root),
                 "--index-path", "INDEX.md", "--hash-files"],
                check=True, capture_output=True, text=True, env=env,
            ).stdout
            ps = subprocess.run(
                ["pwsh", "-NoProfile", "-File", str(PS_AUDIT),
                 "-Root", str(root), "-IndexPath", "INDEX.md", "-HashFiles"],
                check=True, capture_output=True, text=True, env=env,
            ).stdout

            # PowerShell emits native separators while Python normalizes to
            # forward slashes. Paths are otherwise the same observable value.
            py = py.replace("\\", "/")
            ps = ps.replace("\\", "/")

            for output in (py, ps):
                summary = section(output, "Summary")
                self.assertRegex(summary, r"Files \(all\):\s+5\b")
                self.assertIn(".gitignore", section(output, "Extensions"))
                claims = section(
                    output,
                    "Claims requiring verification (open these - never trust the name)",
                )
                self.assertIn("RELEASE_NOTES_v1.1.0.md", claims)
                self.assertRegex(claims, rf"\s{claim.stat().st_size}\s+.*RELEASE_NOTES_v1\.1\.0\.md")
                hashes = section(output, "Identical content groups (SHA-256)")
                self.assertIn("docs/plan.md", hashes)
                self.assertIn("archive/plan.md", hashes)

            py_extensions = {
                line.strip() for line in section(py, "Extensions").splitlines() if line.strip()
            }
            ps_extensions = {
                line.strip() for line in section(ps, "Extensions").splitlines() if line.strip()
            }
            self.assertEqual(py_extensions, ps_extensions)


if __name__ == "__main__":
    unittest.main()
