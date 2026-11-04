"""Offline synthetic fixtures only; never connect to a real browser or account."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'export.py'
spec = importlib.util.spec_from_file_location('tmeet_export', SCRIPT)
export = importlib.util.module_from_spec(spec)
spec.loader.exec_module(export)


class OfflineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.dest = self.root / 'archive'
        self.dest.mkdir()
        self.state = self.root / 'state'
        self.state.mkdir()
        (self.state / 'run.json').write_text(json.dumps({
            'uid': 'synthetic-account', 'dest': str(self.dest), 'source_count': 1}))
        self.rows = [{'record_id': 'synthetic-record', 'record_type': 'realtime_transcription'}]
        self.save_inventory()

    def save_inventory(self):
        (self.state / 'inventory.json').write_text(json.dumps(self.rows))

    def test_help_is_offline_and_successful(self):
        result = subprocess.run([sys.executable, str(SCRIPT), '--help'], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn('--check-state', result.stdout)
        self.assertIn('browser', result.stdout.lower())

    def test_resume_inspection_does_not_write_or_use_browser(self):
        before = {p.name: p.read_bytes() for p in self.state.iterdir()}
        with patch.object(export, 'activate_tencent_tab', side_effect=AssertionError('browser accessed')):
            result = export.inspect_resume_state(self.state)
        self.assertEqual(result['source_count'], 1)
        self.assertEqual(result['issues'], [])
        self.assertEqual({p.name: p.read_bytes() for p in self.state.iterdir()}, before)
        self.assertNotIn('synthetic-account', str(result))
        self.assertNotIn('synthetic-record', str(result))

    def test_missing_state_does_not_create_directories(self):
        absent = self.root / 'missing'
        result = export.inspect_resume_state(absent)
        self.assertTrue(result['issues'])
        self.assertFalse(absent.exists())

    def test_inventory_count_or_duplicate_ids_prevents_resume(self):
        self.rows.append(dict(self.rows[0]))
        self.save_inventory()
        result = export.inspect_resume_state(self.state)
        self.assertTrue(result['issues'])

    def test_saved_file_outside_destination_is_not_trusted(self):
        outside = self.root / 'outside.txt'
        outside.write_text('synthetic')
        (self.state / 'transcripts.json').write_text(json.dumps({
            'synthetic-record': {'status': 'saved', 'relative_path': '../outside.txt', 'bytes': 9}}))
        result = export.inspect_resume_state(self.state)
        self.assertTrue(result['issues'])

    def test_saved_file_size_mismatch_prevents_resume(self):
        (self.dest / 'transcript.txt').write_text('synthetic')
        (self.state / 'transcripts.json').write_text(json.dumps({
            'synthetic-record': {'status': 'saved', 'relative_path': 'transcript.txt', 'bytes': 999}}))
        self.assertTrue(export.inspect_resume_state(self.state)['issues'])

    def test_browser_phase_without_injected_runtime_explains_dependency(self):
        with self.assertRaisesRegex(RuntimeError, 'browser-use'):
            export.activate_tencent_tab()


if __name__ == '__main__':
    unittest.main()
