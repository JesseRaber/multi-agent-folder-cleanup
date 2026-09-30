"""Observable v1.3 plan-review, identity and recovery regressions."""

import csv
import hashlib
import html
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

HELPER = Path(__file__).resolve().parents[1] / 'skills/multi-agent-folder-cleanup/scripts/verify_move.py'


class PlanBindingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'source'
        self.target = self.root / 'target'
        self.source.mkdir()
        self.target.mkdir()
        self.src = self.source / 'a.md'
        self.dst = self.target / 'a.md'
        self.src.write_text('original\n', encoding='utf-8')
        self.map = self.root / 'moves.csv'
        self.write_map([(self.src, self.dst)])
        self.receipt = self.root / 'proposal.json'
        self.baseline = self.root / 'baseline.json'

    def write_map(self, pairs):
        with self.map.open('w', encoding='utf-8-sig', newline='') as fh:
            writer = csv.writer(fh)
            writer.writerow(['source', 'target', 'reason'])
            for src, dst in pairs:
                writer.writerow([str(src), str(dst), 'a non-executable annotation'])

    def run_helper(self, *args):
        return subprocess.run([sys.executable, str(HELPER), *map(str, args)],
                              capture_output=True, text=True, encoding='utf-8',
                              errors='replace', stdin=subprocess.DEVNULL)

    def review(self):
        result = self.run_helper('review', '--map', self.map, '--approval-out', self.receipt)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def make_baseline(self):
        self.review()
        result = self.run_helper('baseline', '--map', self.map, '--approval', self.receipt,
                                 '--out', self.baseline)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_review_is_deterministic_and_displays_actual_bom_csv_pairs(self):
        self.write_map([(self.src, self.dst), (self.source/'b.md', self.target/'b.md')])
        first = self.review()
        second = self.run_helper('review', '--map', self.map)
        self.assertEqual(first.stdout, second.stdout)
        table = [line for line in first.stdout.splitlines() if line.startswith('| M')]
        self.assertEqual(len(table), 2)
        for number, (src, dst) in enumerate([(self.src, self.dst),
                                             (self.source/'b.md', self.target/'b.md')], 1):
            self.assertEqual(table[number-1],
                             f'| M{number:03d} | <code>{html.escape(str(src))}</code> | '
                             f'<code>{html.escape(str(dst))}</code> |')
        receipt = json.loads(self.receipt.read_text(encoding='utf-8'))
        self.assertEqual(receipt['row_count'], 2)
        self.assertEqual(receipt['map_sha256'], hashlib.sha256(self.map.read_bytes()).hexdigest())
        self.assertEqual(receipt['map_path'], str(self.map))

    def test_json_map_resolves_the_same_pairs_as_csv(self):
        self.review()
        identity = json.loads(self.receipt.read_text(encoding='utf-8'))
        json_map = self.root / 'moves.json'
        json_map.write_text(json.dumps({'pairs': [{'source': 'source/a.md', 'target': 'target/a.md'}]}),
                            encoding='utf-8-sig')
        receipt = self.root / 'json-proposal.json'
        result = self.run_helper('review', '--map', json_map, '--approval-out', receipt)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(receipt.read_text())['resolved_pairs_sha256'],
                         identity['resolved_pairs_sha256'])

    def test_markdown_delimiters_do_not_create_extra_rows_or_cells(self):
        # Paths need not exist to review; some characters are POSIX-only.
        self.write_map([(str(self.source/'pipe|`<x>.md') + '\nnext', self.dst)])
        result = self.review()
        row = next(line for line in result.stdout.splitlines() if line.startswith('| M'))
        self.assertEqual(row.count('|'), 4)
        self.assertIn('&#124;', row)
        self.assertIn('&lt;x&gt;', row)
        self.assertIn('&#10;', row)

    def test_edited_map_rejected_by_preflight_and_baseline(self):
        self.review()
        self.write_map([(self.src, self.target/'different.md')])
        for command in ('preflight', 'baseline'):
            args = [command, '--map', self.map, '--approval', self.receipt]
            if command == 'baseline':
                args += ['--out', self.baseline]
            result = self.run_helper(*args)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('APPROVAL MISMATCH', result.stderr)
        self.assertFalse(self.baseline.exists())
        self.assertTrue(self.src.exists())
        self.assertFalse(self.dst.exists())

    def test_non_path_byte_change_also_requires_review(self):
        self.review()
        self.map.write_bytes(self.map.read_bytes() + b'\n')
        result = self.run_helper('preflight', '--map', self.map, '--approval', self.receipt)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('APPROVAL MISMATCH', result.stderr)

    def test_relocated_relative_map_with_same_bytes_is_rejected(self):
        self.write_map([('source/a.md', 'target/a.md')])
        self.review()
        other = self.root / 'other'
        other.mkdir()
        relocated = other / 'moves.csv'
        relocated.write_bytes(self.map.read_bytes())
        self.assertEqual(hashlib.sha256(relocated.read_bytes()).digest(),
                         hashlib.sha256(self.map.read_bytes()).digest())
        result = self.run_helper('preflight', '--map', relocated, '--approval', self.receipt)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('APPROVAL MISMATCH', result.stderr)

    def test_changed_receipt_count_or_resolved_digest_is_rejected(self):
        self.review()
        original = json.loads(self.receipt.read_text())
        for field, value in [('row_count', 99), ('resolved_pairs_sha256', '0'*64)]:
            data = dict(original)
            data[field] = value
            self.receipt.write_text(json.dumps(data), encoding='utf-8')
            result = self.run_helper('preflight', '--map', self.map, '--approval', self.receipt)
            self.assertNotEqual(result.returncode, 0)

    def test_unchanged_sources_pass_final_pre_move_check(self):
        self.make_baseline()
        result = self.run_helper('preflight', '--map', self.map, '--approval', self.receipt,
                                 '--baseline', self.baseline)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(self.src.exists())
        self.assertFalse(self.dst.exists())

    def test_source_changed_after_staging_is_rejected_without_mutation(self):
        self.make_baseline()
        self.src.write_text('new contribution\n', encoding='utf-8')
        result = self.run_helper('preflight', '--map', self.map, '--approval', self.receipt,
                                 '--baseline', self.baseline)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('SOURCE CHANGED', result.stderr)
        self.assertEqual(self.src.read_text(), 'new contribution\n')
        self.assertFalse(self.dst.exists())

    def test_target_change_is_detected_and_neither_version_overwritten(self):
        self.make_baseline()
        stage = self.root / 'stage'
        stage.mkdir()
        staged = stage / 'a.md'
        shutil.copyfile(self.src, staged)
        shutil.move(self.src, self.dst)
        self.dst.write_text('newer target contribution\n', encoding='utf-8')
        result = self.run_helper('verify', '--baseline', self.baseline, '--approval', self.receipt)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('HASH MISMATCH', result.stdout)
        self.assertEqual(self.dst.read_text(), 'newer target contribution\n')
        self.assertEqual(staged.read_text(), 'original\n')

    def test_tampered_baseline_paths_rejected_even_if_file_hash_matches(self):
        self.make_baseline()
        shutil.copyfile(self.src, self.dst)
        data = json.loads(self.baseline.read_text())
        data['pairs'][0]['target'] = str(self.src)
        self.baseline.write_text(json.dumps(data), encoding='utf-8')
        result = self.run_helper('verify', '--baseline', self.baseline, '--approval', self.receipt)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('BASELINE PLAN MISMATCH', result.stderr)

    def test_receipt_and_baseline_never_overwrite_existing_evidence(self):
        self.make_baseline()
        for output, args in [
            (self.receipt, ['review', '--map', self.map, '--approval-out', self.receipt]),
            (self.baseline, ['baseline', '--map', self.map, '--approval', self.receipt,
                             '--out', self.baseline])]:
            before = output.read_bytes()
            result = self.run_helper(*args)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(output.read_bytes(), before)

    def test_pre_move_check_requires_receipt(self):
        self.make_baseline()
        result = self.run_helper('preflight', '--map', self.map, '--baseline', self.baseline)
        self.assertNotEqual(result.returncode, 0)

    def test_legacy_baseline_verifies_but_cannot_gain_approval_retroactively(self):
        self.make_baseline()
        data = json.loads(self.baseline.read_text())
        del data['map_identity']
        self.baseline.write_text(json.dumps(data), encoding='utf-8')
        shutil.move(self.src, self.dst)
        plain = self.run_helper('verify', '--baseline', self.baseline)
        self.assertEqual(plain.returncode, 0, plain.stdout + plain.stderr)
        bound = self.run_helper('verify', '--baseline', self.baseline, '--approval', self.receipt)
        self.assertNotEqual(bound.returncode, 0)
        self.assertIn('Legacy baseline', bound.stderr)


if __name__ == '__main__':
    unittest.main()
