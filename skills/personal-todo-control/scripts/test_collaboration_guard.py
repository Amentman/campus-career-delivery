import unittest
from collaboration_guard import validate_patch,active_records,carry_forward,PROTECTED
class GuardTests(unittest.TestCase):
    def test_manual_values_including_clears_rejected(self):
        for field in PROTECTED:
            for value in (None,'',False,'人工值'):
                with self.subTest(field=field,value=value), self.assertRaises(ValueError): validate_patch({field:value})
    def test_system_patch_preserves_manual_snapshot(self):
        before={'负责人':None,'状态':'受阻','完成':True,'备注':'人工备注','计划日期':'2026-10-25','优先级':'P2'}
        after=before|validate_patch({'系统建议':'新证据待确认','结转次数':2})
        self.assertEqual(before,{k:after[k] for k in before})
    def test_stable_id_immutable(self):
        with self.assertRaises(ValueError): validate_patch({'任务编号':'T999'})
    def test_execution_layout_patch_does_not_assign_or_close(self):
        before={'负责人':None,'完成':False,'备注':'人工保留','状态':['待认领']}
        patch=validate_patch({'执行分区':'1. 你亲自做｜上午优先','执行顺序':1})
        after=before|patch
        self.assertEqual({k:after[k] for k in before},before)
        self.assertEqual(after['执行顺序'],1)
        with self.assertRaises(ValueError):validate_patch(patch|{'负责人':[{'id':'person'}]})
    def test_closed_excluded_and_reopen_allowed(self):
        rows=[{'任务编号':'T001','完成':True},{'任务编号':'T002','完成':False}]
        self.assertEqual([r['任务编号'] for r in active_records(rows)],['T002'])
        rows[0]['完成']=False;self.assertEqual(len(active_records(rows)),2)
    def test_duplicates_stop_merge(self):
        with self.assertRaises(ValueError): active_records([{'任务编号':'T001','完成':False}]*2)
    def test_unknown_rejected(self):
        with self.assertRaises(ValueError): validate_patch({'未知字段':1})
    def test_carry_excludes_historical_checked_and_preserves_manual(self):
        row={'任务编号':'T001','完成':False,'负责人':[{'id':'person'}],'状态':['受阻'],'备注':'人工备注','计划日期':'2026-10-25','优先级':['P2']}
        self.assertEqual(carry_forward([row]),[row])
        self.assertEqual(carry_forward([row],{'T001'}),[])
        self.assertEqual(row['备注'],'人工备注')
    def test_late_historical_completion_hidden_without_checkbox_write(self):
        row={'任务编号':'T001','完成':False,'继承状态':['历史已完成']}
        self.assertEqual(active_records([row]),[])
        self.assertFalse(row['完成'])
if __name__=='__main__': unittest.main()
