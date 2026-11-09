import contextlib
import io
from pathlib import Path
import runpy
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'claude-usage'


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.module = runpy.run_path(str(SCRIPT))
        self.g = self.module['main'].__globals__
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.g['HISTORY'] = str(Path(self.tmp.name) / 'history.csv')
        self.g['CONFIG'] = str(Path(self.tmp.name) / 'hosts')
        self.g['write_history']({
            ('2026-10-01', 'local'): (1, 100),
            ('2026-11-01', 'local'): (2, 200),
            ('2026-11-02', 'local'): (3, 300),
            ('2026-11-02', 'remote'): (4, 400),
        })

    def run_cli(self, args, rows, error=None):
        calls = []
        def query(mode, since, target):
            calls.append((mode, since, target))
            if mode == 'monthly':
                return [{'period': '2026-11', 'totalCost': 9, 'totalTokens': 900}], None
            return rows, error
        with patch.dict(self.g, run_ccusage=query, local_label=lambda: 'local'), \
             patch.object(sys, 'argv', [str(SCRIPT), *args]), \
             contextlib.redirect_stdout(io.StringIO()), \
             contextlib.redirect_stderr(io.StringIO()):
            self.g['main']()
        return calls

    def test_monthly_snapshot_keeps_daily_archive_and_unrelated_rows(self):
        rows = [{'period': '2026-11-01', 'totalCost': 5, 'totalTokens': 500},
                {'period': '2026-11-02', 'totalCost': 6, 'totalTokens': 600}]
        args = ['--monthly', '--snapshot', '--since', '20261101']
        calls = self.run_cli(args, rows)
        self.assertEqual(calls, [('daily', '20261101', None)])
        expected = {('2026-10-01', 'local'): (1, 100),
                    ('2026-11-01', 'local'): (5, 500),
                    ('2026-11-02', 'local'): (6, 600),
                    ('2026-11-02', 'remote'): (4, 400)}
        self.assertEqual(self.g['read_history'](), expected)
        self.run_cli(args, rows)
        self.assertEqual(self.g['read_history'](), expected)
        monthly = self.g['history_source']('20261101', True, merge_remote=False)
        self.assertEqual(monthly['local']['2026-11']['totalCost'], 11)

    def test_monthly_report_still_queries_monthly(self):
        calls = self.run_cli(['--monthly', '--since', '20261101'], [])
        self.assertEqual(calls, [('monthly', '20261101', None)])

    def test_failed_and_empty_snapshots_preserve_archive(self):
        before = self.g['read_history']()
        for error in ['timeout', None]:
            with self.subTest(error=error):
                self.run_cli(['--snapshot', '--since', '20261101'], [], error)
                self.assertEqual(self.g['read_history'](), before)


if __name__ == '__main__':
    unittest.main()
