"""Synthetic interview evidence only; no accounts or live meetings."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


class TranscriptTests(unittest.TestCase):
    def module(self):
        path = ROOT / 'scripts/transcript.py'
        self.assertTrue(path.is_file(), 'missing transcript intake and source coverage implementation')
        spec = importlib.util.spec_from_file_location('transcript', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def evidence(self):
        return self.module().normalize('[00:00:01] 面试官：请介绍项目。\n[00:00:05] 学生：我做了核对。\n[00:00:10] 面试官：为什么这样做？结果呢？\n[00:00:15] 学生：发现了差异。', 'local', True)

    def inventory(self, doc):
        return {'transcript_sha256': doc['sha256'], 'scope': 'full',
                'roles': {'面试官': 'interviewer', '学生': 'candidate'},
                'audits': [{'turn_id': 'T0001', 'question_ids': ['Q01']},
                           {'turn_id': 'T0002', 'question_ids': [], 'reason': '学生回答'},
                           {'turn_id': 'T0003', 'question_ids': ['Q02', 'Q03']},
                           {'turn_id': 'T0004', 'question_ids': [], 'reason': '学生回答'}],
                'questions': [{'id': 'Q01', 'turn_id': 'T0001', 'quote': '请介绍项目。', 'review_id': 'Q01'},
                              {'id': 'Q02', 'turn_id': 'T0003', 'quote': '为什么这样做？', 'review_id': 'Q02'},
                              {'id': 'Q03', 'turn_id': 'T0003', 'quote': '结果呢？', 'review_id': 'Q03'}],
                'input_review': {'confirmed': True, 'limitations': []}}

    def test_timed_speakers_and_multiline_content_are_preserved(self):
        m = self.module()
        doc = m.normalize('面试官 00:00:01\n请介绍项目\n学生 00:00:04\n我做了核对\n也整理了差异。', 'feishu', True)
        self.assertEqual(['面试官', '学生'], [t['speaker'] for t in doc['turns']])
        self.assertEqual('我做了核对\n也整理了差异。', doc['turns'][1]['text'])
        self.assertEqual(4000, doc['turns'][1]['timestamp_ms'])

    def test_summary_and_unknown_source_are_not_complete(self):
        m = self.module()
        doc = m.normalize('AI 摘要：讨论了项目。', 'local', False)
        self.assertIn('transport_unverified', doc['issues'])
        self.assertIn('speaker_unresolved', doc['issues'])
        self.assertIn('empty_transcript', m.normalize('', 'local', True)['issues'])

    def test_three_questions_cannot_pass_with_one_review_card(self):
        m = self.module(); doc = self.evidence(); inv = self.inventory(doc)
        errors = m.validate_coverage(doc, inv, '### Q01｜介绍项目\n**来源问题：** Q01')
        self.assertTrue(any('Q02' in e for e in errors), errors)
        self.assertTrue(any('Q03' in e for e in errors), errors)

    def test_all_questions_and_followups_can_be_grouped_explicitly(self):
        m = self.module(); doc = self.evidence(); inv = self.inventory(doc)
        inv['questions'][2]['review_id'] = 'Q02'
        text = '### Q01｜项目\n**来源问题：** Q01\n### Q02｜判断与结果\n**来源问题：** Q02、Q03'
        self.assertEqual([], m.validate_coverage(doc, inv, text))

    def test_unindexed_interviewer_turn_and_stale_input_fail(self):
        m = self.module(); doc = self.evidence(); inv = self.inventory(doc)
        inv['audits'] = inv['audits'][:2]
        inv['transcript_sha256'] = 'stale'
        errors = m.validate_coverage(doc, inv, '')
        self.assertTrue(any('T0003' in e for e in errors), errors)
        self.assertTrue(any('指纹' in e for e in errors), errors)

    def test_question_from_another_turn_cannot_hide_a_missing_question(self):
        m = self.module(); doc = self.evidence(); inv = self.inventory(doc)
        inv['questions'] = inv['questions'][:1]
        inv['audits'][2]['question_ids'] = ['Q01']
        errors = m.validate_coverage(doc, inv, '### Q01｜项目\n**来源问题：** Q01')
        self.assertTrue(any('T0003' in e and '其他段落' in e for e in errors), errors)

    def test_second_question_in_same_turn_cannot_be_silently_dropped(self):
        m = self.module(); doc = self.evidence(); inv = self.inventory(doc)
        inv['questions'] = inv['questions'][:2]
        inv['audits'][2]['question_ids'] = ['Q02']
        review='### Q01｜项目\n**来源问题：** Q01\n### Q02｜原因\n**来源问题：** Q02'
        errors=m.validate_coverage(doc,inv,review)
        self.assertTrue(any('T0003' in e and '未覆盖' in e for e in errors),errors)

    def test_colons_in_timed_multiline_answers_are_not_new_speakers(self):
        m = self.module()
        doc=m.normalize('[00:00:01] 面试官：请介绍项目。\n[00:00:05] 学生：我做了核对。\n目标：找到差异\n方法：逐项比较', 'local', True)
        self.assertEqual(2,len(doc['turns']))
        self.assertIn('目标：找到差异',doc['turns'][1]['text'])

    def test_partial_unknown_turn_is_preserved_without_personal_attribution(self):
        m = self.module(); doc = self.evidence(); inv = self.inventory(doc)
        doc['turns'].append({'id':'T0005','speaker':'未知发言人','timestamp_ms':None,'text':'听不清'})
        doc['issues'].append('speaker_unresolved')
        inv['scope']='partial';inv['input_review']['limitations']=['尾段角色不明，仅复盘前四段']
        inv['input_review']['resolutions']={'speaker_unresolved':'T0005保留待确认'}
        inv['audits'].append({'turn_id':'T0005','question_ids':[],'unresolved_reason':'尾段角色不明'})
        review='\n'.join(f'### Q0{i}｜问题\n**来源问题：** Q0{i}' for i in range(1,4))
        self.assertEqual([],m.validate_coverage(doc,inv,review))

    def test_partial_scope_needs_explicit_exclusions_and_cannot_be_full(self):
        m = self.module(); doc = self.evidence(); inv = self.inventory(doc)
        inv['scope'] = 'partial'
        for q in inv['questions'][1:]:
            q.pop('review_id'); q.update(disposition='out_of_scope', reason='用户仅要求 Q01')
        self.assertEqual([], m.validate_coverage(doc, inv, '### Q01｜项目\n**来源问题：** Q01'))
        inv['scope'] = 'full'
        self.assertTrue(any('范围外' in e for e in m.validate_coverage(doc, inv, '')))

    def test_fabricated_quote_unknown_role_and_duplicate_ids_fail(self):
        m = self.module(); doc = self.evidence(); inv = self.inventory(doc)
        inv['questions'][0]['quote'] = '我独立上线了整个系统'
        inv['roles']['面试官'] = 'unknown'
        inv['questions'].append(dict(inv['questions'][0]))
        errors = m.validate_coverage(doc, inv, '')
        self.assertTrue(any('原文' in e for e in errors), errors)
        self.assertTrue(any('角色' in e for e in errors), errors)
        self.assertTrue(any('重复' in e for e in errors), errors)

    def test_missing_tail_and_single_speaker_require_resolution(self):
        m = self.module()
        doc = m.normalize('[00:00:01] 面试官：请介绍项目。', 'local', True, duration_ms=600000)
        self.assertIn('single_speaker', doc['issues'])
        self.assertIn('tail_gap', doc['issues'])

    def test_tencent_import_refuses_unfinished_pagination(self):
        m = self.module()
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)/'capture.json'
            p.write_text(json.dumps({'source': 'tencent', 'transport_complete': False, 'turns': []}))
            with self.assertRaises(ValueError): m.read_tencent(p)

    def test_feishu_wrapper_reads_actual_file_and_rejects_summary(self):
        m = self.module()
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp); cli = folder/'fake-cli'
            program = '''#!/usr/bin/env python3
import json,sys
from pathlib import Path
out=Path(sys.argv[sys.argv.index('--output-dir')+1]); out.mkdir(exist_ok=True)
p=out/'transcript.txt';p.write_text('[00:00:01] 面试官：请介绍项目。\\n[00:00:03] 学生：我做了核对。')
print(json.dumps({'data':{'minutes':[{'minute_token':'synthetic','artifacts':{'transcript_file':str(p)}}]}}))
'''
            cli.write_text(program); cli.chmod(0o700)
            doc = m.read_feishu('https://sample.feishu.cn/minutes/synthetic?from=share', folder/'out', str(cli))
            self.assertEqual('请介绍项目。', doc['turns'][0]['text'])
            self.assertEqual([], doc['issues'])
            cli.write_text(program.replace("{'transcript_file':str(p)}", "{'summary':'只有摘要'}"))
            with self.assertRaisesRegex(ValueError, 'transcript_file'):
                m.read_feishu('https://sample.feishu.cn/minutes/synthetic', folder/'out', str(cli))

    def test_prepare_generates_unconfirmed_audit_for_every_turn(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp); source = folder/'original.txt'
            source.write_text('[00:00:01] 面试官：请介绍项目。\n[00:00:05] 学生：我做了核对。')
            result = subprocess.run([sys.executable, str(ROOT/'scripts/transcript.py'), 'prepare',
                                     '--source','local','--input',str(source),'--out-dir',str(folder/'out'),'--complete'], capture_output=True, text=True)
            self.assertEqual(0,result.returncode,result.stdout)
            draft=folder/'out/question_inventory.draft.json'
            self.assertTrue(draft.is_file(), 'prepare must provide a source-bound audit draft')
            inv=json.loads(draft.read_text())
            self.assertFalse(inv['input_review']['confirmed'])
            self.assertEqual(['T0001','T0002'], [a['turn_id'] for a in inv['audits']])


if __name__ == '__main__': unittest.main()
