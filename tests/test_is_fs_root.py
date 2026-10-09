"""Offline boundary coverage for verify_move.is_fs_root."""

import importlib.util
import os
from pathlib import Path
import unittest


MODULE = Path(__file__).parents[1] / "skills/multi-agent-folder-cleanup/scripts/verify_move.py"
spec = importlib.util.spec_from_file_location("verify_move", MODULE)
verify_move = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(verify_move)


class IsFsRootTests(unittest.TestCase):
    def test_filesystem_root_is_recognized(self):
        root = os.path.abspath(os.path.sep)
        self.assertTrue(verify_move.is_fs_root(root))

    def test_non_root_and_empty_paths_are_rejected(self):
        self.assertFalse(verify_move.is_fs_root(os.path.join(os.path.abspath(os.path.sep), "child")))
        self.assertFalse(verify_move.is_fs_root(""))
        self.assertFalse(verify_move.is_fs_root(None))

    def test_pathlike_input_is_not_treated_as_a_root_string(self):
        self.assertFalse(verify_move.is_fs_root(Path(os.path.abspath(os.path.sep))))


if __name__ == "__main__":
    unittest.main()
