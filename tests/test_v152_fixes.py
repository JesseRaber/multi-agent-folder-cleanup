#!/usr/bin/env python3
"""v1.5.2 verify_move.py fixes: --root confinement (R094), filesystem-root
baseline guard (R105), case-only renames (R106), macOS case folding (R107)
and Windows long-path probe form (R108)."""
from __future__ import annotations
import importlib.util, os, subprocess, sys, tempfile, unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / "skills/multi-agent-folder-cleanup/scripts/verify_move.py"


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True,
                          text=True, encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL)


def load():
    spec = importlib.util.spec_from_file_location("verify_move_v152", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def case_insensitive(folder: Path) -> bool:
    probe = folder / "CaseProbe.tmp"
    probe.write_text("x")
    try:
        return (folder / "caseprobe.tmp").exists()
    finally:
        probe.unlink()


class RootConfinementTests(unittest.TestCase):
    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.base = Path(self._t.name).resolve()
        self.proj = self.base / "proj"
        (self.proj / "a").mkdir(parents=True)
        (self.proj / "a/x.md").write_text("x\n")
        (self.base / "outside").mkdir()
        (self.base / "outside/y.md").write_text("y\n")
        self.plans = self.base / "plans"
        self.plans.mkdir()

    def tearDown(self):
        self._t.cleanup()

    def map(self, text):
        m = self.plans / "moves.csv"
        m.write_text(text)
        return m

    def test_inside_root_passes(self):
        m = self.map(f"source,target\n{self.proj/'a/x.md'},{self.proj/'b/x.md'}\n")
        r = run("preflight", "--map", m, "--root", self.proj)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("OUTSIDE ROOT", r.stdout)

    def test_outside_source_refused(self):
        m = self.map(f"source,target\n{self.base/'outside/y.md'},{self.proj/'b/y.md'}\n")
        r = run("preflight", "--map", m, "--root", self.proj)
        self.assertEqual(r.returncode, 1)
        self.assertIn("OUTSIDE ROOT", r.stdout)

    def test_outside_target_refused_by_baseline(self):
        m = self.map(f"source,target\n{self.proj/'a/x.md'},{self.base/'outside/x.md'}\n")
        r = run("baseline", "--map", m, "--root", self.proj, "--out", self.plans / "b.json")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("OUTSIDE ROOT", r.stderr)
        self.assertFalse((self.plans / "b.json").exists())

    def test_sibling_named_like_root_is_outside(self):
        (self.base / "proj-old").mkdir()
        (self.base / "proj-old/z.md").write_text("z\n")
        m = self.map(f"source,target\n{self.base/'proj-old/z.md'},{self.proj/'z.md'}\n")
        self.assertIn("OUTSIDE ROOT", run("preflight", "--map", m, "--root", self.proj).stdout)

    def test_baseline_inside_root_refused(self):
        m = self.map(f"source,target\n{self.proj/'a/x.md'},{self.proj/'b/x.md'}\n")
        r = run("baseline", "--map", m, "--root", self.proj, "--out", self.proj / "notes/b.json")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("Refusing to write the baseline", r.stderr)

    def test_verify_refuses_baseline_outside_root(self):
        m = self.map(f"source,target\n{self.proj/'a/x.md'},{self.proj/'b/x.md'}\n")
        b = self.plans / "b.json"
        self.assertEqual(run("baseline", "--map", m, "--out", b).returncode, 0)
        r = run("verify", "--baseline", b, "--root", self.base / "outside")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("OUTSIDE ROOT", r.stderr)

    def test_without_root_behaves_as_before(self):
        m = self.map(f"source,target\n{self.base/'outside/y.md'},{self.proj/'b/y.md'}\n")
        r = run("preflight", "--map", m)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


class FilesystemRootBaselineTests(unittest.TestCase):
    def test_baseline_allowed_when_common_root_is_filesystem_root(self):
        mod = load()
        with tempfile.TemporaryDirectory() as t:
            base = Path(t).resolve()
            src = base / "s/x.md"
            src.parent.mkdir()
            src.write_text("x\n")
            out = base / "plans/b.json"
            out.parent.mkdir()
            anchor = os.path.abspath(os.sep)
            fake = {str(src): anchor}
            # Force the plan's common source/target roots to the filesystem root,
            # as a map spanning /home and /mnt would produce.
            with mock.patch.object(mod, "common_parent", lambda paths: fake.get(str(paths[0]), anchor)):
                args = mock.Mock(map=str(base / "m.csv"), approval=None, out=str(out), root=None)
                (base / "m.csv").write_text(f"source,target\n{src},{base/'t/x.md'}\n")
                self.assertEqual(mod.cmd_baseline(args), 0)
            self.assertTrue(out.exists())

    def test_baseline_still_refused_inside_a_pair_folder(self):
        mod = load()
        with tempfile.TemporaryDirectory() as t:
            base = Path(t).resolve()
            src = base / "s/x.md"
            src.parent.mkdir()
            src.write_text("x\n")
            (base / "m.csv").write_text(f"source,target\n{src},{base/'t/x.md'}\n")
            anchor = os.path.abspath(os.sep)
            with mock.patch.object(mod, "common_parent", lambda paths: anchor):
                args = mock.Mock(map=str(base / "m.csv"), approval=None,
                                 out=str(base / "s/b.json"), root=None)
                with self.assertRaises(SystemExit) as cm:
                    mod.cmd_baseline(args)
            self.assertIn("Refusing to write the baseline", str(cm.exception.code))


class CaseOnlyRenameTests(unittest.TestCase):
    def test_case_only_rename_not_target_exists(self):
        with tempfile.TemporaryDirectory() as t:
            base = Path(t).resolve()
            if not case_insensitive(base):
                self.skipTest("needs a case-insensitive volume (Windows/macOS)")
            (base / "readme.md").write_text("r\n")
            m = base.parent / f"{base.name}-moves.csv"
            m.write_text(f"source,target\n{base/'readme.md'},{base/'README.md'}\n")
            try:
                r = run("preflight", "--map", m)
            finally:
                m.unlink()
            self.assertNotIn("TARGET EXISTS", r.stdout)

    def test_real_existing_target_still_reported(self):
        with tempfile.TemporaryDirectory() as t:
            base = Path(t).resolve()
            (base / "a.md").write_text("a\n")
            (base / "b.md").write_text("b\n")
            m = base / "moves.csv"
            m.write_text("source,target\na.md,b.md\n")
            r = run("preflight", "--map", m)
            self.assertIn("TARGET EXISTS", r.stdout)

    def test_same_file_exemption_logic(self):
        mod = load()
        with mock.patch.object(mod, "same_file", return_value=True):
            s, t = "/p/readme.md", "/p/README.md"
            self.assertTrue(s != t and s.lower() == t.lower() and mod.same_file(s, t))


class FoldAndLongPathTests(unittest.TestCase):
    def test_fold_lowercases_on_macos_only(self):
        mod = load()
        with mock.patch.object(mod.sys, "platform", "darwin"):
            self.assertEqual(mod.fold("/Users/Me/Proj"), mod.os.path.normcase("/Users/Me/Proj").lower())
        if os.name != "nt":
            with mock.patch.object(mod.sys, "platform", "linux"):
                self.assertEqual(mod.fold("/Home/Me"), "/Home/Me")

    def test_is_within_case_insensitive_on_macos(self):
        mod = load()
        with mock.patch.object(mod.sys, "platform", "darwin"):
            self.assertTrue(mod.is_within("/Users/me/PROJ/a.md", "/Users/me/proj"))
            self.assertFalse(mod.is_within("/Users/me/proj-old/a.md", "/Users/me/proj"))

    def test_win_long_path(self):
        mod = load()
        short = "C:\\p\\a.md"
        self.assertEqual(mod.win_long_path(short), short)
        long_local = "C:\\" + "d\\" * 130 + "a.md"
        self.assertEqual(mod.win_long_path(long_local), "\\\\?\\" + long_local)
        long_unc = "\\\\server\\share\\" + "d\\" * 130 + "a.md"
        self.assertEqual(mod.win_long_path(long_unc), "\\\\?\\UNC\\" + long_unc[2:])
        prefixed = "\\\\?\\" + long_local
        self.assertEqual(mod.win_long_path(prefixed), prefixed)

    def test_version(self):
        self.assertIn("1.7.2", run("--version").stdout)


if __name__ == "__main__":
    unittest.main()
