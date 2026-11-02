import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "skills" / "campus-job-matching"

class CampusJobMatchingContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        cls.references = "\n".join(p.read_text(encoding="utf-8") for p in (ROOT / "references").glob("*.md"))

    def test_search_modes_respect_student_intent(self):
        for mode in ("campus", "internship", "experienced"):
            self.assertIn(mode, self.skill)
        self.assertIn("方向来自学生本次意向", self.skill)
        self.assertIn("不内置产运白名单", self.skill)

    def test_pool_does_not_replace_eligibility_or_resume_review(self):
        for term in ("共享岗位池", "最新简历", "完整JD", "final_review", "ready", "pending", "blocked"):
            self.assertIn(term, self.skill + self.references)
        for script in ("shared_pool.py", "validate_jobs.py", "enforce_company_cap.py"):
            self.assertTrue((ROOT / "scripts" / script).is_file(), script)

    def test_company_cap_includes_history(self):
        for term in ("同一学生 × 同一公司最多 3 个岗位", "累计已有", "历史已超额保留不动"):
            self.assertIn(term, self.skill)

    def test_public_pool_requires_current_user_authorization(self):
        self.assertNotIn("用户已授权维护此共享池", self.skill)
        self.assertIn("已有明确授权覆盖共享池维护", self.skill)
        self.assertIn("不自动发起沟通、投递、改权限或开启定时任务", self.skill)

if __name__ == "__main__":
    unittest.main()
