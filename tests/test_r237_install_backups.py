#!/usr/bin/env python3
"""R237: install guidance keeps host backups out of scanned skill folders."""

from pathlib import Path
import unittest

REPO = Path(__file__).resolve().parents[1]
PKG = REPO / "packaging"
WORK = REPO / "skills/multi-agent-folder-cleanup/references/work-mode.md"


class InstallBackupGuidance(unittest.TestCase):
    def test_install_guides(self):
        for name in ("INSTALL-universal.md", "INSTALL-codex-chatgpt.md", "INSTALL-claude-code.md"):
            text = PKG.joinpath(name).read_text(encoding="utf-8")
            with self.subTest(name):
                self.assertIn("## Updating an existing install", text)
                self.assertIn("**outside** every folder the host", text)
                self.assertIn("SKILL.backup-not-loaded.md", text)
                self.assertIn("exactly one whose `name:` is `multi-agent-folder-cleanup`", text)
                self.assertIn("not proof the host loads them", text)

    def test_copilot_guide(self):
        text = PKG.joinpath("INSTALL-microsoft-copilot.md").read_text(encoding="utf-8")
        self.assertIn("exactly one `multi-agent-folder-cleanup` skill", text)

    def test_work_mode_release_row(self):
        row = [l for l in WORK.read_text(encoding="utf-8").splitlines()
               if l.startswith("| Candidate or release package")]
        self.assertEqual(len(row), 1)
        self.assertIn("outside every folder the host scans for skills", row[0])
        self.assertIn("exactly one `SKILL.md`", row[0])
        self.assertIn("not proof the host loads them", row[0])


if __name__ == "__main__":
    unittest.main()
