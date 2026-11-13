"""Verify original answers survive rendering; all evidence is synthetic."""
import importlib.util
from pathlib import Path
import unittest
import tempfile,json,subprocess,sys

ROOT=Path(__file__).resolve().parents[1]

def module():
 spec=importlib.util.spec_from_file_location('transcript',ROOT/'scripts/transcript.py')
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def fixture():
 m=module();doc=m.normalize('[00:00:01] 面试官：你做了什么？\n[00:00:02] 学生：我先核对两份记录。\n[00:00:03] 面试官：后来呢？\n[00:00:04] 学生：有一项没对上。\n我又查了原始记录。','local',True)
 inv={'roles':{'面试官':'interviewer','学生':'candidate'},'questions':[{'id':'Q001','turn_id':'T0001','review_id':'Q01'},{'id':'Q002','turn_id':'T0003','review_id':'Q01'}],'exchanges':{'Q01':[['T0001','T0004']]}}
 chunks=[f'> [{t["id"]}] 位置｜{t["speaker"]}\n'+ '\n'.join('> '+s for s in t['text'].splitlines()) for t in doc['turns']]
 review='### Q01｜项目\n**原始问答：**\n\n'+'\n\n'.join(chunks)+'\n\n**点评：** 需要补出处理依据。'
 return m,doc,inv,review

class OriginalExchangeTests(unittest.TestCase):
 def test_exact_questions_answers_and_followup_pass(self):
  m,d,i,r=fixture();self.assertEqual([],m.validate_original_exchanges(d,i,r))
 def test_summary_rewrite_or_dropped_answer_cannot_pass(self):
  m,d,i,r=fixture()
  for changed in [r.replace('我先核对两份记录。','候选人介绍了核对过程。'),r.replace('> 我又查了原始记录。',''),r.replace('> [T0004] 位置｜学生\n> 有一项没对上。\n> 我又查了原始记录。','')]:
   with self.subTest(changed=changed):self.assertTrue(m.validate_original_exchanges(d,i,changed))
 def test_reordered_turns_and_wrong_ranges_fail(self):
  m,d,i,r=fixture();r=r.replace('[T0001]','[TEMP]').replace('[T0002]','[T0001]').replace('[TEMP]','[T0002]')
  self.assertTrue(m.validate_original_exchanges(d,i,r))
  i['exchanges']['Q01']=[['T0003','T0001']]
  self.assertTrue(m.validate_original_exchanges(d,i,r))
 def test_missing_original_evidence_fails_even_with_question_mapping(self):
  m,d,i,r=fixture();i.pop('exchanges')
  self.assertTrue(m.validate_original_exchanges(d,i,r))
 def test_cli_checks_original_text_in_addition_to_question_ids(self):
  m,d,i,r=fixture()
  i.update(transcript_sha256=d['sha256'],scope='full',input_review={'confirmed':True,'limitations':[]},audits=[{'turn_id':t['id'],'question_ids':['Q001'] if n==0 else (['Q002'] if n==2 else []),'reason':'合成回答'} for n,t in enumerate(d['turns'])])
  i['questions'][0]['quote']='你做了什么？';i['questions'][1]['quote']='后来呢？'
  r=r.replace('**原始问答：**','**来源问题：** Q001、Q002\n**原始问答：**')
  with tempfile.TemporaryDirectory() as temp:
   p=Path(temp);(p/'source.json').write_text(json.dumps(d));(p/'inventory.json').write_text(json.dumps(i))
   for text,code in [(r,0),(r.replace('我先核对两份记录。','概述了核对工作。'),1)]:
    (p/'review.md').write_text(text)
    result=subprocess.run([sys.executable,str(ROOT/'scripts/transcript.py'),'check','--transcript',str(p/'source.json'),'--inventory',str(p/'inventory.json'),'--review',str(p/'review.md')],capture_output=True,text=True)
    self.assertEqual(code,result.returncode,result.stdout)
 def test_unanswered_question_keeps_original_prompt_and_explicit_reason(self):
  m,d,i,r=fixture();i['questions']=i['questions'][:1];i['exchanges']={'Q01':[['T0001','T0001']]}
  r='### Q01｜项目\n**原始问答：**\n> [T0001] 位置｜面试官\n> 你做了什么？\n'
  self.assertTrue(m.validate_original_exchanges(d,i,r))
  i['questions'][0]['no_answer_reason']='本题未得到候选人回答，按原记录保留。'
  self.assertEqual([],m.validate_original_exchanges(d,i,r))
 def test_contact_masking_keeps_the_rest_of_the_answer_exact(self):
  m,d,i,r=fixture();d['turns'][1]['text']='联系邮箱是test@example.com，我先核对两份记录。'
  r=r.replace('我先核对两份记录。','联系邮箱是[邮箱已隐去]，我先核对两份记录。')
  self.assertEqual([],m.validate_original_exchanges(d,i,r))

if __name__=='__main__':unittest.main()
