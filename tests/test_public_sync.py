import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/sync_public.py'


class PublicSyncTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SCRIPT.is_file(), 'The public-source sync tool is missing')
        spec = importlib.util.spec_from_file_location('team_public_sync', SCRIPT)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'live'
        self.repo = self.root / 'repo'
        self.state = self.root / 'state'
        self.source.mkdir()
        (self.repo / 'skills/example').mkdir(parents=True)
        self.config = {'sources': {'example': str(self.source)}, 'replacements': []}

    def write(self, relative, value, *, public=False):
        target = (self.repo / 'skills/example' if public else self.source) / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(value)
        return target

    def test_new_source_change_preserves_public_team_instructions(self):
        self.write('SKILL.md', '# Example\n\nOld task rule\n')
        self.write('SKILL.md', '# Example\n\nTeam setup instructions\n\nOld task rule\n', public=True)
        self.module.capture(self.config, self.state)
        self.write('SKILL.md', '# Example\n\nUpdated task rule\n')
        plan = self.module.plan(self.config, self.repo, self.state)
        self.assertFalse(plan['conflicts'])
        content = plan['writes']['skills/example/SKILL.md']
        self.assertIn('Team setup instructions', content)
        self.assertIn('Updated task rule', content)

    def test_conflicting_source_and_public_edits_are_not_overwritten(self):
        self.write('SKILL.md', 'original\n')
        target = self.write('SKILL.md', 'public change\n', public=True)
        self.module.capture(self.config, self.state)
        self.write('SKILL.md', 'source change\n')
        plan = self.module.plan(self.config, self.repo, self.state)
        self.assertTrue(plan['conflicts'])
        self.assertEqual('public change\n', target.read_text())

    def test_a_public_prefix_on_the_same_line_is_a_real_conflict(self):
        self.write('SKILL.md', 'use canvas\n')
        self.write('SKILL.md', 'never use canvas\n', public=True)
        self.module.capture(self.config, self.state)
        self.write('SKILL.md', 'use images\n')
        result = self.module.plan(self.config, self.repo, self.state)
        self.assertTrue(result['conflicts'])

    def test_private_values_are_removed_before_merge_and_new_secrets_block_release(self):
        self.config['replacements'] = [{'from': 'author-private-node-example', 'to': 'configured-node'}]
        self.write('SKILL.md', 'route author-private-node-example\n')
        self.write('SKILL.md', 'route configured-node\n', public=True)
        self.module.capture(self.config, self.state)
        self.write('SKILL.md', 'route author-private-node-example\nnew rule\n')
        plan = self.module.plan(self.config, self.repo, self.state)
        self.assertFalse(plan['conflicts'])
        self.assertNotIn('author-private-node-example', plan['writes']['skills/example/SKILL.md'])
        self.write('references/private.md', 'access_token=' + 'secret-value-example')
        plan = self.module.plan(self.config, self.repo, self.state)
        self.assertTrue(plan['conflicts'])
        self.assertNotIn('secret-value-example', json.dumps(plan['conflicts']))

    def test_missing_or_removed_source_does_not_delete_public_resources(self):
        self.write('SKILL.md', 'original\n')
        target = self.write('SKILL.md', 'public\n', public=True)
        self.module.capture(self.config, self.state)
        (self.source / 'SKILL.md').unlink()
        plan = self.module.plan(self.config, self.repo, self.state)
        self.assertTrue(plan['conflicts'])
        self.assertEqual('public\n', target.read_text())

    def test_preview_never_writes_and_baseline_is_required(self):
        self.write('SKILL.md', 'content\n')
        plan = self.module.plan(self.config, self.repo, self.state)
        self.assertTrue(plan['conflicts'])
        self.assertFalse((self.state / 'baseline').exists())

    def test_source_edits_after_planning_are_not_marked_published(self):
        self.write('SKILL.md', 'first\n')
        self.write('SKILL.md', 'first\n', public=True)
        self.module.capture(self.config, self.state)
        self.write('SKILL.md', 'second\n')
        planned = self.module.plan(self.config, self.repo, self.state)
        self.assertIn('source_sha256', planned)
        self.write('SKILL.md', 'third, not yet reviewed\n')
        with self.assertRaises(ValueError):
            self.module.capture(self.config, self.state, expected=planned['source_sha256'])
        self.assertEqual('first\n', (self.state / 'baseline/example/SKILL.md').read_text())


if __name__ == '__main__':
    unittest.main()
