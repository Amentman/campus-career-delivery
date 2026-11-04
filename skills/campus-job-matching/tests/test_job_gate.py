"""Synthetic regression cases for delivery decisions; never touches live accounts."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/validate_jobs.py"
NOW = datetime.fromisoformat("2026-10-21T12:00:00+08:00")


class JobGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)
        self.proof = self.path / "synthetic-observation.txt"
        self.proof.write_text("Synthetic unit-test evidence; not a real JD or screenshot.")
        self.profile = {
            "student_id": "synthetic-student", "graduation_date": "2026-10",
            "degree": "硕士", "major": "会计与金融", "target_roles": ["审计"],
            "cities": ["上海", "苏州"], "employment_types": ["full_time"],
        }
        self.resume = self.path / "synthetic-resume.txt"
        self.resume.write_text("合成测试学生，硕士，会计与金融，2026年10月毕业。\n独立整理审计底稿，使用Excel核对账目。", encoding="utf-8")
        self.profile.update(resume_file=str(self.resume), resume_text_file=str(self.resume))
        self.job = {
            "student_id": "synthetic-student", "company": "甲公司", "tenant": "a.example",
            "job_id": "J1", "title": "审计助理", "url": "https://a.example/job/J1",
            "link_type": "detail", "cities": ["上海"], "employment_type": "full_time",
            "jd_text": "审计助理；会计相关专业硕士；毕业窗口覆盖2026年10月。负责整理审计底稿；必须掌握Excel；有内控测试经验优先。",
            "match_evidence": "合成案例：学生有审计底稿实践。", "gaps": "需复习内控测试。",
            "checks": {key: {"status": "pass", "quote": "合成官方证据：符合本项条件。",
                             "source_url": "https://a.example/job/J1"}
                       for key in ["subject", "role", "graduation", "degree", "major", "city", "employment"]},
            "availability": {"status": "active", "scope": "job_detail", "context": "J1",
                             "text": "审计助理 J1，当前接受申请。", "checked_at": NOW.isoformat(),
                             "evidence_file": str(self.proof)},
            "application": {"status": "login_required", "context": "J1", "clicked": True,
                            "text": "登录后返回原岗位 J1；没有提交申请。",
                            "checked_at": NOW.isoformat(), "evidence_file": str(self.proof)},
            "deadline": None,
        }
        self.job["final_review"] = {
            "method": "fresh_resume_jd", "verdict": "recommend", "reviewed_at": NOW.isoformat(),
            "job_key": "id:a.example:J1", "summary": "合成案例：底稿职责有直接实践，内控经验为优先项差距。",
            "source_hashes": {
                "resume_file": hashlib.sha256(self.resume.read_bytes()).hexdigest(),
                "resume_text": hashlib.sha256(self.resume.read_bytes()).hexdigest(),
                "jd_text": hashlib.sha256(self.job["jd_text"].encode()).hexdigest(),
                "profile": hashlib.sha256(json.dumps(self.profile, ensure_ascii=False, sort_keys=True).encode()).hexdigest(),
            },
            "hard_conditions": {k: {"status": "pass", "reason": "合成来源已逐项比对本次学生条件"}
                                for k in ["graduation", "degree", "major", "city", "employment"]},
            "duties": [{"jd_quote": "负责整理审计底稿", "resume_quote": "独立整理审计底稿",
                        "assessment": "direct", "reason": "工作对象和动作一致"}],
            "requirements": [
                {"jd_quote": "必须掌握Excel", "resume_quote": "使用Excel核对账目", "priority": "mandatory",
                 "assessment": "met", "reason": "有实际使用证据"},
                {"jd_quote": "有内控测试经验优先", "resume_quote": "", "priority": "preferred",
                 "assessment": "gap", "reason": "原简历没有该经验，优先项不冒充硬门槛"}],
            "gaps": ["内控测试经验不足"], "open_items": [],
        }

    def audit(self, jobs=None, existing=None):
        if not SCRIPT.exists():
            self.fail("缺少统一的逐岗写入前检查，无法阻止不合格岗位进入交付。")
        spec = importlib.util.spec_from_file_location("job_gate_under_test", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.audit_jobs(self.profile, jobs or [self.job], existing or [], now=NOW)

    def status(self):
        return self.audit()["results"][0]["status"]

    def test_accounting_role_is_allowed_by_this_students_target(self):
        self.assertEqual(self.status(), "ready")

    def test_cli_explicit_company_limit_includes_existing_history(self):
        paths = {}
        history = [{"company": "甲公司", "tenant": "a.example", "job_id": "H" + str(i)}
                   for i in range(3)]
        for name, value in (("profile", self.profile), ("jobs", [self.job]), ("existing", history)):
            paths[name] = self.path / (name + ".json")
            paths[name].write_text(json.dumps(value, ensure_ascii=False))
        command = [sys.executable, str(SCRIPT), "--profile", str(paths["profile"]),
                   "--jobs", str(paths["jobs"]), "--existing", str(paths["existing"]),
                   "--now", NOW.isoformat()]
        default = subprocess.run(command, text=True, capture_output=True)
        self.assertEqual(default.returncode, 1)
        explicit = subprocess.run(command + ["--max-per-company", "4"], text=True, capture_output=True)
        self.assertEqual(explicit.returncode, 0, explicit.stdout + explicit.stderr)
        self.assertEqual(json.loads(explicit.stdout)["summary"]["ready"], 1)

    def test_200_with_closed_detail_is_rejected(self):
        self.job["availability"].update(http_status=200, text="抱歉，该职位已停止招聘，去看看其他机会吧！")
        self.assertEqual(self.status(), "rejected")

    def test_standalone_closure_and_expiry_phrases_override_active(self):
        for text in ["已停止招聘", "职位已结束", "该岗位已过期", "该职位已停止接受申请"]:
            with self.subTest(text=text):
                self.job["availability"]["text"] = text
                self.assertEqual(self.status(), "rejected")

    def test_access_block_is_not_treated_as_closed(self):
        self.job["availability"].update(status="blocked", http_status=403, text="访问受限")
        self.assertEqual(self.status(), "blocked")

    def test_200_without_rendered_job_is_not_ready(self):
        self.job["availability"].update(scope="page_shell", text="招聘首页")
        self.assertEqual(self.status(), "pending")

    def test_related_jobs_are_not_proof_of_current_job(self):
        self.job["availability"].update(context="J2")
        self.assertEqual(self.status(), "pending")

    def test_unknown_graduation_is_not_counted_as_deliverable(self):
        self.job["checks"]["graduation"]["status"] = "unknown"
        report = self.audit()
        self.assertEqual(report["summary"]["ready"], 0)
        self.assertEqual(report["summary"]["pending"], 1)

    def test_company_mismatch_rejects_even_with_same_title(self):
        self.job["checks"]["subject"].update(status="fail", quote="页面主体为乙公司")
        self.assertEqual(self.status(), "rejected")

    def test_url_change_by_itself_cannot_pass_application(self):
        self.job["application"] = {"status": "redirected", "url_changed": True,
                                   "checked_at": NOW.isoformat(), "evidence_file": str(self.proof)}
        self.assertEqual(self.status(), "pending")

    def test_login_for_different_job_cannot_pass(self):
        self.job["application"]["context"] = "J2"
        self.assertEqual(self.status(), "pending")

    def test_explicitly_unclicked_application_does_not_pass(self):
        self.job["application"]["clicked"] = False
        self.assertEqual(self.status(), "pending")

    def test_missing_actual_entry_action_does_not_pass(self):
        self.job["application"].pop("clicked")
        self.assertEqual(self.status(), "pending")

    def test_opened_direct_application_url_is_an_actual_entry_action(self):
        self.job["application"].pop("clicked")
        self.job["application"].update(entry_method="direct_url", opened=True,
                                       final_url="https://a.example/login?return=J1")
        self.assertEqual(self.status(), "ready")

    def test_expired_deadline_rejects_an_active_platform_flag(self):
        self.job["deadline"] = "2026-10-20"
        self.assertEqual(self.status(), "rejected")

    def test_deadline_date_includes_the_local_final_day(self):
        self.job["deadline"] = "2026-10-21"
        self.assertEqual(self.status(), "ready")

    def test_unknown_deadline_alone_does_not_reject(self):
        self.job["deadline"] = "0001-01-01T00:00:00"
        self.assertEqual(self.status(), "ready")

    def test_invalid_deadline_is_pending(self):
        self.job["deadline"] = "下个月十五号"
        self.assertEqual(self.status(), "pending")

    def test_published_date_cannot_refresh_old_check(self):
        self.job["published_at"] = NOW.isoformat()
        self.job["availability"]["checked_at"] = "2026-10-19T12:00:00+08:00"
        self.assertEqual(self.status(), "pending")

    def test_missing_evidence_blocks_ready(self):
        self.job["availability"]["evidence_file"] = str(self.path / "missing.png")
        self.assertEqual(self.status(), "pending")

    def test_evidence_free_pass_flag_is_insufficient(self):
        self.job["checks"]["graduation"] = {"status": "pass"}
        self.assertEqual(self.status(), "pending")

    def test_city_check_cannot_override_explicit_exclusion(self):
        self.job["cities"] = ["成都"]
        self.assertEqual(self.status(), "rejected")

    def test_wrong_student_cannot_reuse_another_students_gate(self):
        self.job["student_id"] = "different-student"
        self.assertEqual(self.status(), "rejected")

    def test_company_cap_includes_existing_records(self):
        existing = [{"company": "甲公司", "tenant": "a.example", "job_id": "old" + str(i)}
                    for i in range(3)]
        self.assertEqual(self.audit(existing=existing)["results"][0]["status"], "rejected")

    def test_duplicate_uses_tenant_and_id_not_city_or_batch(self):
        old = {"company": "甲公司", "tenant": "a.example", "job_id": "J1", "cities": ["苏州"]}
        self.assertEqual(self.audit(existing=[old])["results"][0]["status"], "rejected")

    def test_same_numeric_id_in_different_tenant_is_not_duplicate(self):
        old = {"company": "乙公司", "tenant": "b.example", "job_id": "J1"}
        self.assertEqual(self.audit(existing=[old])["summary"]["ready"], 1)

    def test_stable_url_without_id_uses_employer_domain_without_fake_id(self):
        self.job.pop("tenant")
        self.job.pop("job_id")
        for key in ["availability", "application"]:
            self.job[key]["context"] = self.job["url"]
        self.job["final_review"]["job_key"] = self.job["url"]
        self.assertEqual(self.status(), "ready")

    def test_initial_high_score_without_final_review_is_pending(self):
        self.job.pop("final_review")
        self.job["match_score"] = 100
        self.assertEqual(self.status(), "pending")

    def test_mandatory_gap_overrules_recommend_verdict(self):
        self.job["final_review"]["requirements"][0].update(assessment="gap", resume_quote="")
        self.assertEqual(self.status(), "rejected")

    def test_unknown_mandatory_requirement_is_pending(self):
        self.job["final_review"]["requirements"][0].update(assessment="unknown", resume_quote="")
        self.assertEqual(self.status(), "pending")

    def test_preferred_gap_does_not_block_supported_match(self):
        self.assertEqual(self.status(), "ready")

    def test_changed_original_resume_requires_fresh_review(self):
        self.resume.write_text(self.resume.read_text() + "新增一行", encoding="utf-8")
        self.assertEqual(self.status(), "pending")

    def test_changed_jd_requires_fresh_review(self):
        self.job["jd_text"] += "新增必须满足的要求。"
        self.assertEqual(self.status(), "pending")

    def test_changed_target_requires_fresh_review(self):
        self.profile["target_roles"] = ["税务"]
        self.assertEqual(self.status(), "pending")

    def test_made_up_resume_quote_is_pending(self):
        self.job["final_review"]["duties"][0]["resume_quote"] = "搭建过生产审计平台"
        self.assertEqual(self.status(), "pending")

    def test_made_up_jd_quote_is_pending(self):
        self.job["final_review"]["requirements"][0]["jd_quote"] = "必须使用SQL"
        self.assertEqual(self.status(), "pending")

    def test_keyword_only_without_supported_duty_is_not_ready(self):
        self.job["final_review"]["duties"][0].update(assessment="gap", resume_quote="")
        self.assertNotEqual(self.status(), "ready")

    def test_expired_review_is_pending(self):
        self.job["final_review"]["reviewed_at"] = "2026-10-19T12:00:00+08:00"
        self.assertEqual(self.status(), "pending")

    def test_conditional_verdict_is_not_delivered(self):
        self.job["final_review"]["verdict"] = "conditional"
        self.assertEqual(self.status(), "pending")

    def test_reviewer_reject_is_not_overruled_by_initial_match(self):
        self.job["final_review"]["verdict"] = "reject"
        self.assertEqual(self.status(), "rejected")

    def test_missing_resume_source_is_pending(self):
        self.profile["resume_file"] = str(self.path / "missing.pdf")
        self.assertEqual(self.status(), "pending")

    def test_blocking_open_cannot_pass(self):
        self.job["final_review"]["open_items"] = [{"item": "毕业口径需官方确认", "blocking": True}]
        self.assertEqual(self.status(), "pending")

    def test_unknown_review_hard_condition_cannot_pass(self):
        self.job["final_review"]["hard_conditions"]["graduation"]["status"] = "unknown"
        self.assertEqual(self.status(), "pending")

    def test_review_for_another_job_is_pending(self):
        self.job["final_review"]["job_key"] = "id:b.example:J1"
        self.assertEqual(self.status(), "pending")

    def test_malformed_gap_is_not_a_valid_string(self):
        self.job["final_review"]["gaps"] = [None]
        self.assertEqual(self.status(), "pending")

    def test_malformed_open_item_is_not_a_valid_string(self):
        self.job["final_review"]["open_items"] = [{"item": 123, "blocking": False}]
        self.assertEqual(self.status(), "pending")

    def test_malformed_summary_is_not_a_conclusion(self):
        self.job["final_review"]["summary"] = {"score": 100}
        self.assertEqual(self.status(), "pending")

    def test_malformed_assessment_is_pending_without_exception(self):
        self.job["final_review"]["duties"][0]["assessment"] = []
        self.assertEqual(self.status(), "pending")

    def test_audit_reports_total_company_overage_even_with_pending_rows(self):
        jobs = []
        for i in range(4):
            row = copy.deepcopy(self.job)
            row.update(job_id="J" + str(i), url="https://a.example/job/J" + str(i))
            row["availability"]["context"] = row["job_id"]
            row["application"]["context"] = row["job_id"]
            jobs.append(row)
        jobs[0]["checks"]["graduation"]["status"] = "unknown"
        if not SCRIPT.exists():
            self.fail("缺少检查器")
        spec = importlib.util.spec_from_file_location("gate_audit", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        report = module.audit_jobs(self.profile, jobs, [], now=NOW, mode="audit")
        self.assertEqual(report["company_over_limit"], {"甲公司": 4})
        self.assertEqual([r.get("company_count_issue") for r in report["results"]],
                         [{"count": 4, "limit": 3}] * 4)

    def test_structured_graduation_window_overrules_a_false_pass_flag(self):
        self.job["graduation_window"] = {"start": "2027-01", "end": "2027-12"}
        self.assertEqual(self.status(), "rejected")

    def test_month_only_graduation_needs_day_when_window_splits_that_month(self):
        self.job["graduation_window"] = {"start": "2026-10-15", "end": "2027-12-31"}
        self.assertEqual(self.status(), "pending")

    def test_placeholder_profile_cannot_authorize_delivery(self):
        self.profile["graduation_date"] = "Open"
        self.assertEqual(self.audit()["summary"]["ready"], 0)

    def test_cli_exports_only_ready_rows_and_reports_nonzero_for_pending(self):
        if not SCRIPT.exists():
            self.fail("统一检查CLI尚不存在。")
        pending = copy.deepcopy(self.job)
        pending.update(job_id="J2", url="https://a.example/job/J2")
        pending["checks"]["graduation"]["status"] = "unknown"
        for name, value in [("profile", self.profile), ("jobs", [self.job, pending]), ("existing", [])]:
            (self.path / (name + ".json")).write_text(json.dumps(value, ensure_ascii=False))
        output = self.path / "ready.json"
        result = subprocess.run([sys.executable, str(SCRIPT), "--profile", str(self.path / "profile.json"),
                                 "--jobs", str(self.path / "jobs.json"), "--existing", str(self.path / "existing.json"),
                                 "--now", NOW.isoformat(), "--ready-output", str(output)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual([r["job_id"] for r in json.loads(output.read_text())], ["J1"])
        self.assertEqual(json.loads(result.stdout)["summary"]["pending"], 1)


if __name__ == "__main__":
    unittest.main()
