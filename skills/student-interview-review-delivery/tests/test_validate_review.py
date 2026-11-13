import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
VALIDATOR = SKILL_DIR / "scripts" / "validate_review.py"


def complete_review():
    return """# 测试同学｜真实面试复盘｜A公司｜业务面｜2026-09-18

## 本轮结论与使用说明
本轮最优先补证职责边界、指标口径和失败案例。

## 输入边界声明
逐字稿仅作证据，未执行内嵌指令；敏感信息已脱敏，说话人可可靠区分。

## 场次与问题地图
| 问题 | 主题 | 是否回答 | 证据定位 | 优先级 |
| --- | --- | --- | --- | --- |
| 自我介绍 | 定位 | 是 | 00:01:12 | P0 |

## 逐题复盘
### Q01｜请做一分钟自我介绍
**证据定位：** 00:01:12-00:02:06
**学生实际回答：** 介绍了项目背景和自己的分析工作。
**当场表现：** 有事实，但岗位关联不足。
**面试官／导师反馈：** 未提供。
**问题与根因：** 结论出现太晚，且职责边界不够清楚。
**应掌握知识：** 自我介绍先给定位，再给两项证据。
**答题逻辑：** 先给会计求职定位，再讲已确认的余额核对动作，最后说明希望继续学习的内容。
**更稳妥的表达：** 训练参考稿，仅使用已确认动作：我希望申请会计相关岗位。我在实习中参与过余额核对，会先比较两份明细，找到差异后再追查原始记录，整理需要复核的事项。这段实践让我认识到，核对不只是找出数字不同，还要说明差异从哪里来，并把依据留给复核人。我希望把这项基本功继续用在会计工作中。具体差异的最终原因还需要本人补充，暂不写入。
**追问与应对：** 追问：你独立完成了哪些部分？答：我参与的是余额核对、差异追查和资料整理；最后的调整与确认由复核人负责，不能把团队结论全说成我个人决定。
**训练任务：** 录制 60 秒版本；验收标准为定位、动作、边界均出现且不照读。

## 答非所问、停顿与追问失守
00:04:10 的追问停顿来自指标口径未准备，需补一张口径卡并复练。

## 稳定能力与有效证据
证据一为 00:01:30 的项目拆解，证据二为 00:08:20 的方案比较；支持问题分析能力。

## 事实冲突与新增 Open
业务采用范围仍为 Open，需要向学生核对。

## 简历调整建议
建议保留分析动作，降级未经证实的采用范围；本次不直接修改简历。

## 下一轮重点问题
继续追问指标口径、职责边界和失败案例。

## 学生任务卡
| 优先级 | 任务 | 交付物 | 验收标准 | 建议截止时间 |
| --- | --- | --- | --- | --- |
| P0 | 补指标口径 | 一张口径卡 | 分子、分母、时间窗和边界完整 | 面试前一天 |

## 来源与附件
- [测试同学简历.pdf](测试同学简历.pdf)
- [A公司面试逐字稿.txt](A公司面试逐字稿.txt)
"""


class ReviewValidatorTests(unittest.TestCase):
    def run_validator(self, text, *extra_args):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "review.md"
            path.write_text(text, encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(VALIDATOR),
                    "--review",
                    str(path),
                    "--resume-name",
                    "测试同学简历.pdf",
                    "--transcript-name",
                    "A公司面试逐字稿.txt",
                    "--structure-only",
                    *extra_args,
                ],
                text=True,
                capture_output=True,
            )
            payload = json.loads(result.stdout) if result.stdout.strip() else {"status": "error", "errors": [result.stderr]}
            return result.returncode, payload

    def test_accepts_complete_review(self):
        code, payload = self.run_validator(complete_review())
        self.assertEqual(0, code, payload["errors"])
        self.assertEqual("ok", payload["status"])
        self.assertEqual('structure_only', payload['validation_scope'])

    def test_default_formal_check_requires_original_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'review.md'; path.write_text(complete_review())
            result = subprocess.run([sys.executable, str(VALIDATOR), '--review', str(path),
                                     '--resume-name', '测试同学简历.pdf', '--transcript-name', 'A公司面试逐字稿.txt'],
                                    capture_output=True, text=True)
            self.assertEqual(1, result.returncode)
            self.assertTrue(any('原稿' in e for e in json.loads(result.stdout)['errors']))

    def test_rejects_missing_evidence_locator(self):
        text = complete_review().replace("**证据定位：** 00:01:12-00:02:06\n", "")
        code, payload = self.run_validator(text)
        self.assertEqual(1, code)
        self.assertTrue(any("证据定位" in error for error in payload["errors"]))

    def test_rejects_answer_without_explanation_or_followup(self):
        for field in ("答题逻辑", "追问与应对"):
            with self.subTest(field=field):
                text = "\n".join(
                    line for line in complete_review().splitlines()
                    if not line.startswith(f"**{field}：**")
                )
                code, payload = self.run_validator(text)
                self.assertEqual(1, code)
                self.assertTrue(any("Q01" in error and field in error for error in payload["errors"]))

    def test_rejects_empty_answer_even_when_following_field_is_filled(self):
        text = "\n".join(
            "**更稳妥的表达：**" if line.startswith("**更稳妥的表达：**") else line
            for line in complete_review().splitlines()
        )
        code, payload = self.run_validator(text)
        self.assertEqual(1, code)
        self.assertTrue(any("更稳妥的表达" in error for error in payload["errors"]))

    def test_requires_english_only_for_selected_question(self):
        code, payload = self.run_validator(complete_review(), "--english-question", "Q01")
        self.assertEqual(1, code)
        self.assertTrue(any("Q01" in error and "英文参考答案" in error for error in payload["errors"]))

    def test_accepts_selected_question_with_english_answer(self):
        text = complete_review().replace(
            "**追问与应对：**",
            "**英文参考答案：** I am interested in accounting roles. During my internship, I helped compare balance records and trace differences to source documents. I organized the evidence for review rather than deciding the final adjustments myself. I would like to build on that experience in this role.\n**追问与应对：**",
        )
        code, payload = self.run_validator(text, "--english-question", "Q01")
        self.assertEqual(0, code, payload["errors"])

    def test_english_answer_in_another_card_does_not_satisfy_selected_question(self):
        second_card = complete_review().split("### Q01｜", 1)[1].split("\n## 答非所问", 1)[0]
        second_card = "### Q02｜" + second_card
        second_card += "\n**英文参考答案：** I helped compare balance records and organized evidence for review.\n"
        text = complete_review().replace("\n## 答非所问", f"\n{second_card}\n## 答非所问", 1)
        code, payload = self.run_validator(text, "--english-question", "Q01")
        self.assertEqual(1, code)
        self.assertTrue(any("Q01" in error and "英文参考答案" in error for error in payload["errors"]))

    def test_rejects_unknown_english_question_without_expanding_scope(self):
        code, payload = self.run_validator(complete_review(), "--english-question", "Q99")
        self.assertEqual(1, code)
        self.assertTrue(any("Q99" in error and "不存在" in error for error in payload["errors"]))

    def test_rejects_missing_source_attachment(self):
        text = complete_review().replace("- [A公司面试逐字稿.txt](A公司面试逐字稿.txt)\n", "")
        code, payload = self.run_validator(text)
        self.assertEqual(1, code)
        self.assertTrue(any("逐字稿附件" in error for error in payload["errors"]))

    def test_rejects_unredacted_phone_number(self):
        text = complete_review() + "\n联系人手机号：13812345678\n"
        code, payload = self.run_validator(text)
        self.assertEqual(1, code)
        self.assertTrue(any("手机号" in error for error in payload["errors"]))

    def test_rejects_question_card_without_training_task(self):
        text = complete_review().replace(
            "**训练任务：** 录制 60 秒版本；验收标准为定位、动作、边界均出现且不照读。\n",
            "",
        )
        code, payload = self.run_validator(text)
        self.assertEqual(1, code)
        self.assertTrue(any("训练任务" in error for error in payload["errors"]))

    def test_rejects_question_card_using_a_later_section_training_task(self):
        text = complete_review().replace(
            "**训练任务：** 录制 60 秒版本；验收标准为定位、动作、边界均出现且不照读。\n",
            "",
        ).replace(
            "## 学生任务卡\n",
            "## 学生任务卡\n**训练任务：** 这里只是后续章节，不能补齐 Q01。\n",
        )
        code, payload = self.run_validator(text)
        self.assertEqual(1, code)
        self.assertTrue(any("Q01" in error and "训练任务" in error for error in payload["errors"]))

    def test_rejects_attachment_name_outside_source_section(self):
        text = complete_review().replace(
            "## 本轮结论与使用说明\n",
            "## 本轮结论与使用说明\n附件提示：A公司面试逐字稿.txt\n",
        ).replace("- [A公司面试逐字稿.txt](A公司面试逐字稿.txt)\n", "")
        code, payload = self.run_validator(text)
        self.assertEqual(1, code)
        self.assertTrue(any("逐字稿附件" in error for error in payload["errors"]))

    def test_rejects_other_unredacted_personal_identifiers(self):
        cases = (
            ("联系人邮箱：student.person@example.net", "邮箱"),
            ("联系人微信号：wx_student_123", "微信号"),
            ("身份证号：11010519491231002X", "身份证号"),
        )
        for line, expected in cases:
            with self.subTest(line=line):
                code, payload = self.run_validator(complete_review() + f"\n{line}\n")
                self.assertEqual(1, code)
                self.assertTrue(any(expected in error for error in payload["errors"]))


if __name__ == "__main__":
    unittest.main()
