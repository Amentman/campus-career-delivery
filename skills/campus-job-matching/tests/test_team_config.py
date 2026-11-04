"""First-use configuration tests. All routes and identities are synthetic."""
import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import shared_pool as pool


class TeamConfigTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.config = {
            'version': 1, 'expected_user_open_id': 'member-identity',
            'expected_profile': 'member-profile',
            'shared_pool': {'base_token': 'synthetic-base', 'job_table_id': 'jobs',
                            'company_table_id': 'companies', 'wiki_node_token': 'pool-node',
                            'owner_open_id': 'shared-owner'},
        }
        self.path = self.root / 'team.json'
        self.path.write_text(json.dumps(self.config))
        self.auth = {'appId': 'member-profile', 'identities': {
            'user': {'openId': 'member-identity', 'verified': True}}}

    def test_explicit_environment_path_wins(self):
        with patch.dict(os.environ, {'JIHUI_SKILLS_CONFIG': str(self.path)}):
            self.assertEqual(pool.load_config()['shared_pool']['owner_open_id'], 'shared-owner')

    def test_missing_explicit_path_does_not_fall_back_or_call_cli(self):
        with patch.dict(os.environ, {'JIHUI_SKILLS_CONFIG': str(self.root / 'absent.json')}), \
                patch.object(pool.subprocess, 'run') as run:
            with self.assertRaisesRegex(ValueError, 'JIHUI_SKILLS_CONFIG|team.json'):
                pool.load_config()
            run.assert_not_called()

    def test_missing_pool_is_configuration_gap_not_empty_jobs(self):
        self.path.write_text(json.dumps({k: v for k, v in self.config.items() if k != 'shared_pool'}))
        with patch.dict(os.environ, {'JIHUI_SKILLS_CONFIG': str(self.path)}):
            with self.assertRaisesRegex(ValueError, 'shared_pool'):
                pool.load_config()

    def test_current_config_does_not_fall_back_when_malformed(self):
        self.path.write_text('{not json')
        with patch.dict(os.environ, {'JIHUI_SKILLS_CONFIG': str(self.path)}):
            with self.assertRaisesRegex(ValueError, 'JSON'):
                pool.load_config()

    def test_legacy_path_is_supported_when_team_path_absent(self):
        legacy = dict(self.config)
        legacy.pop('version')
        legacy['shared_pool'] = dict(legacy['shared_pool'])
        legacy['shared_pool'].pop('owner_open_id')
        self.path.write_text(json.dumps(legacy))
        with patch.dict(os.environ, {'JIHUI_SKILLS_CONFIG': ''}), \
                patch.object(pool, 'TEAM_CONFIG', self.root / 'missing-team.json', create=True), \
                patch.object(pool, 'LEGACY_CONFIG', self.path, create=True):
            self.assertEqual(pool.load_config()['shared_pool']['owner_open_id'], 'member-identity')

    def test_shared_owner_may_differ_from_current_member(self):
        meta = {'obj_token': 'synthetic-base', 'owner': 'shared-owner'}
        response = type('Result', (), {'stdout': json.dumps(self.auth)})()
        with patch.object(pool.subprocess, 'run', return_value=response), \
                patch.object(pool, 'cli', return_value=meta):
            self.assertEqual(pool.verify_pool_access(self.config), meta)

    def test_wrong_owner_stops_access(self):
        response = type('Result', (), {'stdout': json.dumps(self.auth)})()
        with patch.object(pool.subprocess, 'run', return_value=response), \
                patch.object(pool, 'cli', return_value={'obj_token': 'synthetic-base', 'owner': 'other-owner'}):
            with self.assertRaisesRegex(RuntimeError, 'owner'):
                pool.verify_pool_access(self.config)

    def test_wrong_current_member_or_profile_stops_before_pool_read(self):
        for change in ('member', 'profile', 'unverified'):
            auth = json.loads(json.dumps(self.auth))
            if change == 'member': auth['identities']['user']['openId'] = 'other-member'
            if change == 'profile': auth['appId'] = 'other-profile'
            if change == 'unverified': auth['identities']['user']['verified'] = False
            response = type('Result', (), {'stdout': json.dumps(auth)})()
            with self.subTest(change=change), patch.object(pool.subprocess, 'run', return_value=response), \
                    patch.object(pool, 'cli') as cli:
                with self.assertRaises(RuntimeError): pool.verify_pool_access(self.config)
                cli.assert_not_called()

    def test_snapshot_missing_config_has_actionable_json_error(self):
        out = io.StringIO()
        with patch.dict(os.environ, {'JIHUI_SKILLS_CONFIG': str(self.root / 'absent.json')}), \
                patch.object(pool.subprocess, 'run') as run, contextlib.redirect_stdout(out):
            code = pool.main(['snapshot', '--output', str(self.root / 'snapshot.json')])
        self.assertEqual(code, 2)
        error = json.loads(out.getvalue())
        self.assertFalse(error['pool_checked'])
        self.assertIn('team.json', error['error'])
        self.assertFalse((self.root / 'snapshot.json').exists())
        run.assert_not_called()

    def test_snapshot_shared_member_reads_both_tables(self):
        tables = []
        response = type('Result', (), {'stdout': json.dumps(self.auth)})()

        def fake_cli(args):
            if args[:2] == ['wiki', '+node-get']:
                return {'obj_token': 'synthetic-base', 'owner': 'shared-owner'}
            table = args[args.index('--table-id') + 1]
            tables.append(table)
            return {'fields': [], 'data': [], 'record_id_list': [], 'has_more': False, 'rev': 1}

        target = self.root / 'snapshot.json'
        with patch.dict(os.environ, {'JIHUI_SKILLS_CONFIG': str(self.path)}), \
                patch.object(pool.subprocess, 'run', return_value=response), \
                patch.object(pool, 'cli', side_effect=fake_cli), contextlib.redirect_stdout(io.StringIO()):
            code = pool.main(['snapshot', '--output', str(target)])
        self.assertEqual(code, 0)
        self.assertEqual(set(tables), {'companies', 'jobs'})
        self.assertTrue(json.loads(target.read_text())['complete'])

    def test_denied_record_access_does_not_write_empty_snapshot(self):
        target = self.root / 'snapshot.json'
        with patch.dict(os.environ, {'JIHUI_SKILLS_CONFIG': str(self.path)}), \
                patch.object(pool, 'verify_pool_access', return_value={}), \
                patch.object(pool, 'read_all', side_effect=RuntimeError('Access denied')), \
                contextlib.redirect_stdout(io.StringIO()):
            code = pool.main(['snapshot', '--output', str(target)])
        self.assertEqual(code, 2)
        self.assertFalse(target.exists())


if __name__ == '__main__':
    unittest.main()
