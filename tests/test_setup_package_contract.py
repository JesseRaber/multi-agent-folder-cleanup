"""Setup must ship usable, canonical rules resources in each supported layout."""
from pathlib import Path, PurePosixPath
import importlib.util
import re
import tempfile
import unittest
import zipfile
import posixpath

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("setup_builder", REPO / "packaging/build_packages.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

class SetupPackageContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = builder.source_files()
        cls.packages = builder.build_packages(cls.sources)

    def test_canonical_rules_resources_survive_all_supported_layouts(self):
        resources = ("ADOPTION.md", "AGENTS.proposed.md", "SECTION_0_PASTE_IN.txt")
        for flavor, (items, _) in self.packages.items():
            if flavor in ("gemini-apps-only", "opal-only"):
                continue
            for resource in resources:
                with self.subTest(flavor=flavor, resource=resource):
                    found = [data for name, data in items.items() if name.endswith("project-rules/" + resource)]
                    self.assertEqual(found, [self.sources["references/project-rules/" + resource]])

    def test_adoption_relative_links_resolve_inside_each_rules_package(self):
        for flavor, (items, _) in self.packages.items():
            for name, data in items.items():
                if not name.endswith("project-rules/ADOPTION.md"):
                    continue
                for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", data.decode("utf-8")):
                    target = target.split("#", 1)[0]
                    if not target or "://" in target:
                        continue
                    resolved = posixpath.normpath(str(PurePosixPath(name).parent / target))
                    with self.subTest(flavor=flavor, target=target):
                        self.assertIn(resolved, items)

    def test_new_setup_resources_roundtrip_zip_without_extras(self):
        with tempfile.TemporaryDirectory() as tmp:
            for flavor, (items, folders) in self.packages.items():
                archive = Path(tmp) / (flavor + ".zip")
                builder.write_zip(archive, items, folders)
                with zipfile.ZipFile(archive) as z:
                    with self.subTest(flavor=flavor):
                        self.assertIsNone(z.testzip())
                        files = {n: z.read(n) for n in z.namelist() if not n.endswith("/")}
                        self.assertEqual(files, items)
