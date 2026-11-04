"""Reject plans whose job, company and compensation evidence do not connect."""

import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from validate_delivery import _validate_standard_plan_readback


def sample_row(**changes):
    row = {
        "route_key": "gtm",
        "company": "示例科技",
        "role": "海外产品营销实习生",
        "city": "深圳",
        "recruitment_type": "在校实习",
        "sample_status": "current_sample",
        "fit": "出海市场研究可迁移，仍需补充产品上市案例",
        "salary_type": "company_disclosed",
        "salary_text": "200—250元/天，未披露转正年包",
        "benefits_text": "餐补已披露；奖金、加班及外派安排未披露",
        "source_url": "https://jobs.example.com/marketing-intern",
        "access_date": "2026-11-03",
    }
    row.update(changes)
    return row


def card(row):
    return "\n".join(
        str(row[key]) for key in (
            "company", "role", "city", "recruitment_type", "fit",
            "salary_text", "benefits_text", "source_url", "access_date",
        )
    )


def plan(rows=None):
    rows = [sample_row()] if rows is None else rows
    text = """# 方向优先级
GTM；分析用户与渠道；出海研究；海外产品营销实习生。
个人目标20—30万元，不是公开岗位报价。核验日2026-11-03。
# 行业与公司选择
当前岗位样本：示例科技。长期研究池：另一科技。
# 补强项目
## 项目一：上市案例
达到最小可演示状态再进入简历。
# 简历版本
GTM定向简历。
# 正式投递
按项目证据投递。
"""
    entries = copy.deepcopy(rows)
    for row in entries:
        row["evidence_excerpt"] = card(row)
        text += "\n" + row["evidence_excerpt"] + "\n"
    payload = {
        "standard_plan_checks": {
            "direction_count_observed": 1,
            "salary_reference_date": "2026-11-03",
            "route_coverage": {"gtm": {
                "label": "GTM",
                "daily_work_markers": ["分析用户与渠道"],
                "fit_markers": ["出海研究"],
                "role_markers": ["海外产品营销实习生"],
                "salary_markers": ["20—30万元"],
                "company_markers": ["示例科技", "另一科技"],
            }},
            "company_pool": {"current_samples_separated_from_research_pool": True},
        },
        "opportunity_checks": {"rows": entries},
    }
    career = {"required_route_keys": ["gtm"], "expected_project_count": 1}
    return text, payload, career


class OpportunityContractTests(unittest.TestCase):
    def errors(self, data):
        text, payload, career = data
        return _validate_standard_plan_readback(payload, career, text)

    def test_accepts_connected_company_role_salary_and_benefits(self):
        self.assertEqual(self.errors(plan()), [])

    def test_accepts_shared_access_date_and_linked_source_footnote(self):
        text, payload, career = plan()
        row = payload["opportunity_checks"]["rows"][0]
        original = row["evidence_excerpt"]
        excerpt = original.replace(row["source_url"], "[S1]").replace(row["access_date"], "")
        text = text.replace(original, excerpt) + "\n[S1] " + row["source_url"]
        row["evidence_excerpt"] = excerpt
        row["source_marker"] = "[S1]"
        self.assertEqual(self.errors((text, payload, career)), [])

    def test_rejects_keyword_complete_plan_without_opportunity_rows(self):
        data = plan([])
        self.assertTrue(self.errors(data))

    def test_rejects_personal_target_used_as_company_salary(self):
        self.assertTrue(self.errors(plan([sample_row(salary_text="目标20—30万元")])))

    def test_rejects_missing_role_benefits_source_or_date(self):
        for field in ("role", "benefits_text", "source_url", "access_date", "fit"):
            with self.subTest(field=field):
                self.assertTrue(self.errors(plan([sample_row(**{field: ""})])))

    def test_rejects_fields_scattered_outside_the_claimed_job_excerpt(self):
        text, payload, career = plan()
        payload["opportunity_checks"]["rows"][0]["evidence_excerpt"] = "示例科技\n海外产品营销实习生"
        self.assertTrue(self.errors((text, payload, career)))

    def test_rejects_invented_readback_excerpt(self):
        text, payload, career = plan()
        payload["opportunity_checks"]["rows"][0]["evidence_excerpt"] += "\n这句话未写入正文"
        self.assertTrue(self.errors((text, payload, career)))

    def test_rejects_undisclosed_pay_as_completed_salary_research(self):
        self.assertTrue(self.errors(plan([sample_row(salary_type="undisclosed", salary_text="未披露")])))

    def test_accepts_unknown_company_pay_when_comparable_evidence_is_present(self):
        rows = [
            sample_row(salary_type="undisclosed", salary_text="未披露"),
            sample_row(company="参考科技", salary_type="comparable_sample",
                       salary_route_key="gtm", comparability_note="深圳同类产品营销在校实习薪资样本",
                       source_url="https://jobs.example.com/comparable-intern"),
        ]
        text, payload, career = plan(rows)
        note = rows[1]["comparability_note"]
        payload["opportunity_checks"]["rows"][1]["evidence_excerpt"] += "\n" + note
        text += "\n" + payload["opportunity_checks"]["rows"][1]["evidence_excerpt"]
        self.assertEqual(self.errors((text, payload, career)), [])

    def test_rejects_cross_route_comparable_salary(self):
        row = sample_row(salary_type="comparable_sample", salary_route_key="development",
                         comparability_note="研发工程师薪资，不能代表GTM")
        data = plan([row])
        self.assertTrue(self.errors(data))

    def test_rejects_comparable_salary_without_a_stated_basis(self):
        self.assertTrue(self.errors(plan([sample_row(salary_type="comparable_sample", salary_route_key="gtm")])))

    def test_rejects_labeled_salary_without_a_number_and_unit(self):
        self.assertTrue(self.errors(plan([sample_row(salary_text="薪资有竞争力")])))

    def test_requires_each_retained_route_to_have_an_opportunity(self):
        text, payload, career = plan()
        career["required_route_keys"].append("development")
        payload["standard_plan_checks"]["direction_count_observed"] = 2
        payload["standard_plan_checks"]["route_coverage"]["development"] = copy.deepcopy(
            payload["standard_plan_checks"]["route_coverage"]["gtm"]
        )
        self.assertTrue(self.errors((text, payload, career)))


if __name__ == "__main__":
    unittest.main()
