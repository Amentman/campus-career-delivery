import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'team_setup.py'


class TeamSetupTests(unittest.TestCase):
    def run_tool(self, *args):
        self.assertTrue(SCRIPT.is_file(), 'Team setup entrypoint is not distributed')
        result = subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True)
        self.assertNotIn('Traceback', result.stderr)
        return result, json.loads(result.stdout)

    def test_missing_config_is_an_actionable_error(self):
        with tempfile.TemporaryDirectory() as temp:
            result, data = self.run_tool('doctor', '--config', Path(temp) / 'missing.json', '--skill', 'campus-job-matching')
            self.assertEqual(2, result.returncode)
            self.assertFalse(data['ready'])
            self.assertIn('init', data['next_step'])

    def test_team_profile_does_not_transfer_the_authors_identity(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            profile = root / 'team.json'
            profile.write_text(json.dumps({'version': 1, 'expected_user_open_id': 'author-example', 'expected_profile': 'author-profile', 'shared_pool': {'owner_open_id': 'team-owner-example'}, 'workspace': {'student_root': 'authors-local-directory'}}))
            result, _ = self.run_tool('init', '--team-profile', profile, '--output', root / 'member.json', '--student-root', root / 'students')
            self.assertEqual(0, result.returncode)
            saved = json.loads((root / 'member.json').read_text())
            self.assertEqual('', saved['expected_user_open_id'])
            self.assertEqual('', saved['expected_profile'])
            self.assertEqual('team-owner-example', saved['shared_pool']['owner_open_id'])
            self.assertEqual(str(root / 'students'), saved['workspace']['student_root'])

    def test_team_profile_does_not_transfer_the_authors_sharing_authorization(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            profile, target = root / 'team.json', root / 'member.json'
            profile.write_text(json.dumps({'version': 1, 'role_prep_delivery': {'authorization_confirmed': True, 'link_share_entity': 'anyone_readable'}, 'shared_pool': {'owner_open_id': 'team-owner-example'}}))
            original_profile = profile.read_bytes()
            result, _ = self.run_tool('init', '--team-profile', profile, '--output', target)
            self.assertEqual(0, result.returncode)
            saved = json.loads(target.read_text())
            preference = saved.get('role_prep_delivery', {})
            self.assertFalse(preference.get('authorization_confirmed', False))
            self.assertEqual('preserve', preference.get('link_share_entity', 'preserve'))
            self.assertEqual('team-owner-example', saved['shared_pool']['owner_open_id'])
            self.assertEqual(original_profile, profile.read_bytes())
            target.write_bytes(original_profile)
            result, _ = self.run_tool('init', '--team-profile', profile, '--output', target)
            self.assertEqual(2, result.returncode)
            self.assertEqual(original_profile, target.read_bytes())

    def test_init_rejects_credentials_and_does_not_overwrite_existing_member_config(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            profile = root / 'team.json'
            profile.write_text(json.dumps({'version': 1, 'access_token': 'private-example-value'}))
            result, data = self.run_tool('init', '--team-profile', profile, '--output', root / 'member.json')
            self.assertEqual(2, result.returncode)
            self.assertNotIn('private-example-value', json.dumps(data))
            self.assertFalse((root / 'member.json').exists())
            profile.write_text('{"version":1}')
            target = root / 'member.json'
            target.write_text('preserve me')
            result, _ = self.run_tool('init', '--team-profile', profile, '--output', target)
            self.assertEqual(2, result.returncode)
            self.assertEqual('preserve me', target.read_text())

    def test_dry_run_and_single_skill_install_are_independent(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / 'skills'
            result, data = self.run_tool('install', '--dest', target, '--skill', 'campus-job-matching')
            self.assertEqual(0, result.returncode)
            self.assertFalse(target.exists())
            self.assertEqual(['campus-job-matching'], data['skills'])
            result, _ = self.run_tool('install', '--dest', target, '--skill', 'campus-job-matching', '--apply')
            self.assertEqual(0, result.returncode)
            self.assertTrue((target / 'campus-job-matching' / 'SKILL.md').is_file())
            self.assertTrue((target / 'campus-job-matching' / 'references' / 'team-setup.md').is_file())
            self.assertFalse((target / 'student-role-interview-prep').exists())

    def test_install_is_idempotent_and_preserves_member_changes(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / 'skills'
            arguments = ('install', '--dest', target, '--skill', 'campus-job-matching', '--apply')
            first, _ = self.run_tool(*arguments)
            second, _ = self.run_tool(*arguments)
            self.assertEqual((0, 0), (first.returncode, second.returncode))
            member_file = target / 'campus-job-matching' / 'SKILL.md'
            member_file.write_text(member_file.read_text() + '\nMember modification\n')
            result, data = self.run_tool(*arguments, '--update')
            self.assertEqual(2, result.returncode)
            self.assertTrue(data['conflicts'])
            self.assertIn('Member modification', member_file.read_text())

    def test_install_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as temp:
            result, _ = self.run_tool('install', '--dest', temp, '--skill', '../../outside', '--apply')
            self.assertEqual(2, result.returncode)

    def test_legacy_alias_install_includes_its_required_main_skill(self):
        with tempfile.TemporaryDirectory() as temp:
            result, data = self.run_tool('install', '--dest', temp, '--skill', 'campus-recommend')
            self.assertEqual(0, result.returncode)
            self.assertEqual(['campus-job-matching', 'campus-recommend'], data['skills'])

    def test_install_does_not_follow_a_members_symlink_outside_the_target(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target, outside = root / 'skills', root / 'outside'
            target.mkdir()
            outside.mkdir()
            (target / 'campus-job-matching').symlink_to(outside, target_is_directory=True)
            result, _ = self.run_tool('install', '--dest', target, '--skill', 'campus-job-matching', '--apply')
            self.assertEqual(2, result.returncode)
            self.assertEqual([], list(outside.iterdir()))

    def test_local_only_work_does_not_require_a_feishu_configuration(self):
        with tempfile.TemporaryDirectory() as temp:
            result, data = self.run_tool('doctor', '--config', Path(temp) / 'absent.json', '--skill', 'auditing-candidate-resumes')
            self.assertEqual(0, result.returncode)
            self.assertTrue(data['ready'])

    def test_unknown_skill_is_not_reported_ready(self):
        with tempfile.TemporaryDirectory() as temp:
            config = Path(temp) / 'config.json'
            config.write_text(json.dumps({'version': 1, 'expected_user_open_id': 'member-example', 'feishu': {'students_root_url': 'configured-root-example'}}))
            result, data = self.run_tool('doctor', '--config', config, '--skill', 'unknown-skill-example')
            self.assertEqual(2, result.returncode)
            self.assertFalse(data['ready'])

    def test_feishu_task_without_cli_is_not_reported_ready(self):
        with tempfile.TemporaryDirectory() as temp:
            config = Path(temp) / 'config.json'
            config.write_text(json.dumps({'expected_user_open_id': 'member-example', 'feishu': {'students_root_url': 'root-example'}, 'shared_pool': {'enabled': False}}))
            spec = importlib.util.spec_from_file_location('setup_under_test', SCRIPT)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            args = type('Arguments', (), {'skill': 'campus-job-matching', 'config': config, 'target_url': None, 'live': False})()
            with patch.object(module.shutil, 'which', return_value=None):
                report = module.doctor(args)
            self.assertFalse(report['ready'])
            self.assertIn('tool:lark-cli', report['missing'])

    def test_ready_config_requires_member_identity_and_pool_resource_fields(self):
        with tempfile.TemporaryDirectory() as temp:
            config = Path(temp) / 'config.json'
            config.write_text(json.dumps({'version': 1, 'feishu': {'students_root_url': 'configured-root-example'}, 'shared_pool': {'enabled': True}}))
            result, data = self.run_tool('doctor', '--config', config, '--skill', 'campus-job-matching')
            self.assertEqual(2, result.returncode)
            self.assertIn('expected_user_open_id', data['missing'])
            self.assertIn('shared_pool.base_token', data['missing'])
            self.assertFalse(data['ready'])

    def test_pool_doctor_requires_every_field_used_by_the_live_pool_script(self):
        with tempfile.TemporaryDirectory() as temp:
            config = Path(temp) / 'config.json'
            config.write_text(json.dumps({'version': 1, 'expected_user_open_id': 'member-example', 'feishu': {'students_root_url': 'root-example'}, 'shared_pool': {'base_token': 'base-example', 'job_table_id': 'jobs-example', 'company_table_id': 'companies-example'}}))
            result, data = self.run_tool('doctor', '--config', config, '--skill', 'campus-job-matching')
            self.assertEqual(2, result.returncode)
            for key in ['expected_profile', 'shared_pool.wiki_node_token', 'shared_pool.owner_open_id']:
                self.assertIn(key, data['missing'])

    def test_each_workflow_only_requires_its_own_resource_group(self):
        cases = {
            'job-content-publisher': {'feishu': {'content_base_url': 'content-example'}},
            'personal-todo-control': {'feishu': {'todo_url': 'todo-example'}},
            'multi-source-todo-control': {'feishu': {'service_base_url': 'service-example'}},
            'job-sales-advisor': {'workspace': {'knowledge_root': 'knowledge-example'}},
        }
        with tempfile.TemporaryDirectory() as temp:
            for skill, resource in cases.items():
                with self.subTest(skill=skill):
                    config = Path(temp) / (skill + '.json')
                    config.write_text(json.dumps({'version': 1, 'expected_user_open_id': 'member-example', 'expected_profile': 'profile-example', **resource}))
                    result, data = self.run_tool('doctor', '--config', config, '--skill', skill)
                    self.assertEqual(0, result.returncode, data)

    def test_live_profile_mismatch_is_not_reported_ready(self):
        with tempfile.TemporaryDirectory() as temp:
            config = Path(temp) / 'config.json'
            config.write_text(json.dumps({'expected_user_open_id': 'member-example', 'expected_profile': 'configured-profile', 'feishu': {'students_root_url': 'root-example'}, 'shared_pool': {'enabled': False}}))
            spec = importlib.util.spec_from_file_location('setup_profile_test', SCRIPT)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            args = type('Arguments', (), {'skill': 'campus-job-matching', 'config': config, 'target_url': None, 'live': True})()
            with patch.object(module, 'authenticated_member', return_value=('member-example', 'different-profile')):
                with self.assertRaisesRegex(ValueError, 'profile'):
                    module.doctor(args)


if __name__ == '__main__':
    unittest.main()
