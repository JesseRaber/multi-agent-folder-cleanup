"""Read-only hygiene findings must retain coverage and avoid false all-clears."""
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / 'skills/multi-agent-folder-cleanup/scripts'
PS = os.environ.get('AUDIT_TEST_POWERSHELL') or shutil.which('pwsh') or shutil.which('powershell.exe')
SID = '51515151-5151-4151-8151-515151515151'


class Hygiene(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'project'
        self.root.mkdir()
        (self.root/'AI_CONTEXT/SESSIONS').mkdir(parents=True)
        self.name = f'2026-10-23_120000_codex_test_{SID}.md'
        (self.root/'AI_CONTEXT/SESSIONS'/self.name).write_text(
            f'Session ID: {SID}\nStart time: 2026-10-23T12:00:00-04:00\n', encoding='utf-8')
        (self.root/'AI_CONTEXT/SESSION_INDEX.md').write_text('# Index\n', encoding='utf-8')

    def run_helpers(self):
        commands = [[sys.executable,str(SCRIPTS/'audit_folder.py'),'--root',str(self.root),'--orient']]
        if PS:
            commands.append([PS,'-NoProfile','-ExecutionPolicy','Bypass','-File',str(SCRIPTS/'audit_folder.ps1'),'-Root',str(self.root),'-Orient'])
        for cmd in commands:
            with self.subTest(engine=cmd[0]):
                result=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',timeout=40)
                self.assertEqual(result.returncode,0,result.stderr)
                yield result.stdout

    def pile(self, rel, size):
        p=self.root/rel; p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('wb') as f: f.truncate(size)

    def test_generated_state_counted_and_decimal_boundary(self):
        self.pile('Incoming/large/node_modules/package/blob',100_000_001)
        self.pile('Incoming/exact/blob',100_000_000)
        for text in self.run_helpers():
            self.assertIn('Incoming/scratch piles over 100 MB: 1',text)
            self.assertIn('100000001 bytes; 1 files',text)
            self.assertIn('pile scan coverage gaps: 0',text)
            self.assertIn('session logs without index row: 1',text)

    def test_uuid_row_matches_and_prose_does_not(self):
        index=self.root/'AI_CONTEXT/SESSION_INDEX.md'
        index.write_text(f'Mention in prose: {SID}\n',encoding='utf-8')
        for text in self.run_helpers(): self.assertIn('session logs without index row: 1',text)
        index.write_text(f'| Start | Session ID | Status | Link |\n| x | {SID} | closed | another-name.md |\n',encoding='utf-8')
        for text in self.run_helpers(): self.assertIn('session logs without index row: 0',text)

    def test_missing_index_is_unavailable(self):
        (self.root/'AI_CONTEXT/SESSION_INDEX.md').unlink()
        for text in self.run_helpers(): self.assertIn('session logs without index row: unavailable',text)

    def test_nonstandard_log_can_match_header_uuid(self):
        (self.root/'AI_CONTEXT/SESSIONS'/self.name).rename(self.root/'AI_CONTEXT/SESSIONS/legacy.md')
        (self.root/'AI_CONTEXT/SESSION_INDEX.md').write_text(f'| {SID} |\n',encoding='utf-8')
        for text in self.run_helpers(): self.assertIn('session logs without index row: 0',text)

    def test_scan_is_read_only(self):
        before={str(p.relative_to(self.root)):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        list(self.run_helpers())
        after={str(p.relative_to(self.root)):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(before,after)

    @unittest.skipUnless(os.name!='nt','Windows symlink creation requires privileges; junction coverage is in existing suite')
    def test_external_link_not_counted(self):
        outside=Path(self.tmp.name)/'outside';outside.mkdir()
        with (outside/'blob').open('wb') as f:f.truncate(100_000_001)
        (self.root/'Incoming').mkdir()
        (self.root/'Incoming/link').symlink_to(outside,target_is_directory=True)
        for text in self.run_helpers():
            self.assertIn('Incoming/scratch piles over 100 MB: 0',text)
            self.assertIn('link skipped',text)
