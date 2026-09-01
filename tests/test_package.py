#!/usr/bin/env python3
"""Repository-level checks not covered by host-specific validators."""

from __future__ import annotations

import json
from pathlib import Path
import re
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/multi-agent-folder-cleanup/SKILL.md"


class PackageTests(unittest.TestCase):
    def test_versions_agree(self) -> None:
        text = SKILL.read_text(encoding="utf-8")
        frontmatter = yaml.safe_load(text.split("---", 2)[1])
        expected = frontmatter["metadata"]["version"]
        manifests = [
            ROOT / ".codex-plugin/plugin.json",
            ROOT / ".claude-plugin/plugin.json",
        ]
        for path in manifests:
            with self.subTest(path=path):
                self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["version"], expected)
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertRegex(readme, rf"`{re.escape(expected)}`")
        self.assertTrue((ROOT / f"packaging/RELEASE_NOTES_v{expected}.md").is_file())

    def test_skill_links_resolve(self) -> None:
        text = SKILL.read_text(encoding="utf-8")
        for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", text):
            if "://" not in target:
                with self.subTest(target=target):
                    self.assertTrue((SKILL.parent / target).is_file())

    def test_openai_default_prompt_names_skill(self) -> None:
        data = yaml.safe_load(
            (SKILL.parent / "agents/openai.yaml").read_text(encoding="utf-8")
        )
        self.assertIn("$multi-agent-folder-cleanup", data["interface"]["default_prompt"])


if __name__ == "__main__":
    unittest.main()
