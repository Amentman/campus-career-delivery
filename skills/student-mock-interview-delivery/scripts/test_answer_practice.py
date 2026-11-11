"""Regression checks for usable student practice cards, using synthetic content."""
import unittest
from unittest.mock import patch
import validate_delivery as validator


class StudentPracticeTest(unittest.TestCase):
    def validate_card(self, practice, extra=''):
        text = '''## 面试问题与个人逐字稿
### 第一部分｜基础行为面
#### 题目1｜你在页面巡检里做了什么？
**考察点：** 说明本人实际交付和负责人接手的工作
**表达类型：** 亲历表达
**你的答题主线：** 先讲巡检对象，再讲缺项清单和交接
**事实或场景依据：** S01 商品页规格巡检与缺项清单
**参考表达：** 我依据商品资料核对页面规格字段，把缺少的字段和依据整理成清单交给运营负责人。我的交付是让负责人能定位问题，页面修改由负责人处理。
**追问练习：**
''' + practice + '\n' + extra + '''
**答题提示：** 先口述本人做了什么，再解释清单怎样交接，录音检查是否把负责人的页面修改说成自己的工作。
'''
        errors = []
        with patch.object(validator, 'MIN_QUESTIONS', 1), patch.object(validator, 'MAX_QUESTIONS', 1), patch.object(validator, 'QUESTION_CATEGORIES', (('第一部分｜基础行为面', 1),)):
            cards = validator.extract_and_validate_questions(text, '面试问题与个人逐字稿', '学生版', errors, {'S01'}, set())
        return cards, errors

    def test_complete_answer_does_not_require_blank_personal_version(self):
        cards, errors = self.validate_card('问：页面修改也是你做的吗？\n答：页面修改由运营负责人处理，我负责的是依据资料核对字段并交付缺项清单。')
        self.assertEqual(len(cards), 1)
        self.assertEqual(errors, [])

    def test_optional_rewrite_area_keeps_answer_valid(self):
        _, errors = self.validate_card('问：交付物是什么？\n答：按商品列出的缺失字段和资料依据。', '**我的版本：** 留给学生改写')
        self.assertEqual(errors, [])

    def test_question_without_response_is_rejected(self):
        _, errors = self.validate_card('问：你怎样验证结果？')
        self.assertTrue(any('追问练习' in e for e in errors))

    def test_placeholder_is_not_a_response(self):
        _, errors = self.validate_card('问：修改后有什么结果？\n答：〔请补：结果〕 ____')
        self.assertTrue(any('追问练习' in e for e in errors))

    def test_incomplete_second_pair_is_not_hidden_by_first(self):
        _, errors = self.validate_card('问：交付了什么？\n答：缺项清单。\n问：能证明销量改善吗？\n答：')
        self.assertTrue(any('追问练习' in e for e in errors))

    def test_two_followups_with_multiline_answers(self):
        _, errors = self.validate_card('问：交付了什么？\n答：我交付缺项清单。\n负责人据此处理页面修改。\n问：能证明销量改善吗？\n答：现有材料没有销量数据，不能据此认领销量提升。')
        self.assertEqual(errors, [])


if __name__ == '__main__':
    unittest.main()
