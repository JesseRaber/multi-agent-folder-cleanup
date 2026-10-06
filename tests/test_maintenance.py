"""Safety/correctness regressions reproduced against the v1.4.0 baseline."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / 'skills/multi-agent-folder-cleanup/scripts'
PS = shutil.which('pwsh') or shutil.which('powershell.exe')

def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def run(script, *args):
    if script.endswith('.ps1') and not PS:
        raise unittest.SkipTest('PowerShell is not available')
    cmd = ([PS, '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File']
           if script.endswith('.ps1') else [sys.executable])
    return subprocess.run(cmd + [str(SCRIPTS / script), *map(str, args)],
                          capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=45)

class MaintenanceTests(unittest.TestCase):
    def test_secret_content_never_opened(self):
        audit = load('audit_folder')
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ('Cookies', '.env', 'credentials.md'):
                path = root / name
                path.write_bytes(b'PK\x03\x04synthetic-only')
                with mock.patch('builtins.open', side_effect=AssertionError('content read')):
                    self.assertIsNone(audit.orphan_reason(str(path), path.stat().st_size))
                    self.assertFalse(audit.pointer_candidate(str(path), path.stat().st_size))
                    with self.assertRaises(OSError):
                        audit.sha256(str(path))

    def test_secret_hashes_and_index_contents_not_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ('credentials.md', 'ordinary.md'):
                (root / name).write_text('[synthetic](DO_NOT_DISCLOSE.md)', encoding='utf-8')
            for script, flags in [('audit_folder.py', ['--root', tmp, '--hash-files', '--index-path', 'credentials.md']),
                                  ('audit_folder.ps1', ['-Root', tmp, '-HashFiles', '-IndexPath', 'credentials.md'])]:
                with self.subTest(script=script):
                    result = run(script, *flags)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertNotIn('DO_NOT_DISCLOSE', result.stdout)
                    self.assertNotIn('(2 copies)', result.stdout)
                    self.assertIn('READ BLOCKED', result.stdout)

    def test_balanced_links_and_root_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'docs').mkdir()
            (root / 'docs/a(b(c)).md').write_text('ok')
            (root / 'only-root.md').write_text('ok')
            (root / 'docs/index.md').write_text(
                '[nested](a(b(c)).md)\n[angle](<a(b(c)).md>)\n'
                '[escaped](a\\(b\\(c\\)\\).md "title")\n[root](only-root.md)\n', encoding='utf-8')
            for script, flag in [('audit_folder.py', '--root'), ('audit_folder.ps1', '-Root')]:
                result = run(script, flag, tmp, '--index-path' if flag == '--root' else '-IndexPath', 'docs/index.md')
                with self.subTest(script=script):
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertNotIn('BROKEN MARKDOWN', result.stdout)
                    self.assertIn('ROOT-FALLBACK REFERENCES: 1', result.stdout)

    def test_brief_caps_journals_and_pointer_stubs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for i in range(12):
                (root / ('journal-%02d.md' % i)).write_text('See [target](target.md)\n')
            (root / 'target.md').write_text('ordinary')
            for script, flags in [('audit_folder.py', ['--root', tmp, '--brief', '--journal-threshold-kb', '0', '--detect-pointers']),
                                  ('audit_folder.ps1', ['-Root', tmp, '-Brief', '-JournalThresholdKB', '0', '-DetectPointers'])]:
                result = run(script, *flags)
                with self.subTest(script=script):
                    self.assertEqual(result.returncode, 0, result.stderr)
                    for section in ('Large journals', 'Possible pointer stubs'):
                        body = re.search(r'(?ms)^== ' + section + r'.*?==\n(.*?)(?=^== |\Z)', result.stdout).group(1)
                        self.assertEqual(len(re.findall(r'journal-\d+', body)), 10, body)
                        self.assertIn('2 more', body)

    def test_root_relative_link_does_not_resolve_against_document_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'docs').mkdir()
            (root / 'docs/only-doc.md').write_text('fixture')
            (root / 'docs/index.md').write_text('[root](/only-doc.md)')
            for script, flags in [('audit_folder.py', ['--root', tmp, '--index-path', 'docs/index.md']),
                                  ('audit_folder.ps1', ['-Root', tmp, '-IndexPath', 'docs/index.md'])]:
                result = run(script, *flags)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('BROKEN MARKDOWN LINKS: 1', result.stdout)

    def test_placeholder_baseline_refuses_before_read(self):
        verify = load('verify_move')
        with mock.patch.object(verify, 'is_placeholder', return_value=True), mock.patch('builtins.open', side_effect=AssertionError('read')):
            with self.assertRaises(OSError):
                verify.sha256('synthetic-placeholder')

    def test_linked_parent_rejected_in_preflight_and_baseline(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'real').mkdir()
            (root / 'real/source.txt').write_text('synthetic fixture')
            link = root / 'link'
            if os.name == 'nt':
                env = dict(os.environ, FIXTURE_LINK=str(link), FIXTURE_REAL=str(root / 'real'))
                subprocess.run([PS, '-NoProfile', '-Command',
                    'New-Item -ItemType Junction -Path $env:FIXTURE_LINK -Target $env:FIXTURE_REAL | Out-Null'], env=env, check=True, capture_output=True)
            else:
                link.symlink_to(root / 'real', target_is_directory=True)
            plan = root / 'map.json'
            plan.write_text(json.dumps([{'source': str(link / 'source.txt'), 'target': str(root / 'dest/file.txt')}]))
            for command in ('preflight', 'baseline'):
                args = ['--map', plan]
                if command == 'baseline':
                    args += ['--out', root / 'evidence/baseline.json']
                result = run('verify_move.py', command, *args)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertFalse((root / 'evidence/baseline.json').exists())
            self.assertEqual((root / 'real/source.txt').read_text(), 'synthetic fixture')

    def test_cloud_attribute_classification(self):
        from types import SimpleNamespace
        audit, verify = load('audit_folder'), load('verify_move')
        for attrs, expected in [(0x20, False), (0x40000, False), (0x40400, True),
                                (0x1000, True), (0x400000, True), (0x400, False)]:
            with self.subTest(attrs=attrs), mock.patch.object(audit.os, 'lstat', return_value=SimpleNamespace(st_file_attributes=attrs)):
                self.assertEqual(audit._cloud_only('fixture'), expected)
            with mock.patch.object(verify.os, 'stat', return_value=SimpleNamespace(st_file_attributes=attrs)):
                self.assertEqual(verify.is_placeholder('fixture'), expected)

    def test_outside_root_manifest_does_not_hash_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'root'
            root.mkdir()
            (Path(tmp) / 'outside.txt').write_text('synthetic outside')
            (root / 'manifest.csv').write_text('path,sha256\n../outside.txt,' + '0' * 64 + '\n')
            for script, flags in [('audit_folder.py', ['--root', root, '--expected-upload-manifest', 'manifest.csv']),
                                  ('audit_folder.ps1', ['-Root', root, '-ExpectedUploadManifest', 'manifest.csv'])]:
                result = run(script, *flags)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('HASH UNCHECKED', result.stdout)
                self.assertNotIn('HASH MISMATCH', result.stdout)

    def test_incomplete_staging_cannot_verify_and_preserves_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'src').mkdir()
            (root / 'stage').mkdir()
            pairs = []
            for name in ('AGENTS.md', 'notes.txt'):
                (root / 'src' / name).write_text('fixture-' + name)
                pairs.append({'source': str(root / 'src' / name), 'target': str(root / 'dst' / name)})
            plan, receipt, baseline = root / 'map.json', root / 'receipt.json', root / 'baseline.json'
            plan.write_text(json.dumps(pairs))
            self.assertEqual(run('verify_move.py', 'review', '--map', plan, '--approval-out', receipt).returncode, 0)
            self.assertEqual(run('verify_move.py', 'baseline', '--map', plan, '--approval', receipt, '--out', baseline).returncode, 0)
            shutil.copy2(root / 'src/AGENTS.md', root / 'stage/AGENTS.md')
            result = run('verify_move.py', 'verify', '--baseline', baseline, '--approval', receipt, '--stage', root / 'stage')
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertIn('missing 1', result.stdout)
            self.assertEqual((root / 'src/AGENTS.md').read_bytes(), (root / 'stage/AGENTS.md').read_bytes())
            self.assertTrue((root / 'src/notes.txt').is_file())

    @unittest.skipUnless(os.name == 'nt', 'Windows sharing violation fixture')
    def test_windows_locked_source_rejected_without_mutation(self):
        import ctypes
        from ctypes import wintypes
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'src/file.txt'
            source.parent.mkdir()
            source.write_text('locked fixture')
            plan = root / 'map.json'
            plan.write_text(json.dumps([{'source': str(source), 'target': str(root / 'dst/file.txt')}]))
            kernel = ctypes.WinDLL('kernel32', use_last_error=True)
            create = kernel.CreateFileW
            create.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
            create.restype = wintypes.HANDLE
            kernel.CloseHandle.argtypes = [wintypes.HANDLE]
            handle = create(str(source), 0x80000000, 0, None, 3, 0, None)
            self.assertNotEqual(handle, ctypes.c_void_p(-1).value)
            try:
                result = run('verify_move.py', 'preflight', '--map', plan)
                self.assertEqual(result.returncode, 1, result.stdout)
                self.assertIn('Windows error 32', result.stdout)
            finally:
                kernel.CloseHandle(handle)
            self.assertEqual(source.read_text(), 'locked fixture')
            self.assertEqual(run('verify_move.py', 'preflight', '--map', plan).returncode, 0)

if __name__ == '__main__':
    unittest.main()
