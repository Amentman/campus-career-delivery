"""Synthetic mode/channel regressions. Never reads real recruitment accounts."""
import hashlib
import json
import unittest

import test_job_gate as fixture


class SearchModeTests(unittest.TestCase):
    setUp = fixture.JobGateTests.setUp
    audit = fixture.JobGateTests.audit
    status = fixture.JobGateTests.status

    def refresh_review(self):
        self.job['final_review']['source_hashes']['profile'] = hashlib.sha256(
            json.dumps(self.profile, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        self.job['final_review']['source_hashes']['jd_text'] = hashlib.sha256(self.job['jd_text'].encode()).hexdigest()

    def mode(self, mode):
        self.profile['search_mode'] = mode
        conditions = self.job['final_review']['hard_conditions']
        if mode == 'experienced':
            self.job['jd_text'] = '上海全职审计助理；会计相关专业硕士；负责整理审计底稿；必须掌握Excel；有内控测试经验优先。要求至少1年相关正式工作经验。'
            self.profile.pop('graduation_date')
            self.profile['experience'] = {'verified_work_months': 24, 'relevant_work_months': 18,
                                          'internship_months': 12}
            conditions.pop('graduation')
            self.job['checks'].pop('graduation')
            self.job['experience_requirement'] = {'min_months': 12, 'basis': 'relevant_work', 'priority': 'mandatory'}
            keys = ['experience', 'seniority', 'salary']
        else:
            self.job['jd_text'] = '上海审计实习；在校会计相关专业硕士；负责整理审计底稿；必须掌握Excel；有内控测试经验优先。每周至少3天，持续3个月，最晚2026年12月1日到岗。'
            self.profile.pop('graduation_date')
            self.profile['employment_types'] = ['internship']
            self.profile['student_status'] = 'enrolled'
            self.profile['internship_availability'] = {'days_per_week': 4, 'months': 6, 'start_date': '2026-11-01'}
            self.job['employment_type'] = 'internship'
            self.job['internship_requirement'] = {'days_per_week': 3, 'months': 3, 'student_only': True,
                                                 'latest_start_date': '2026-12-01'}
            conditions.pop('graduation')
            self.job['checks'].pop('graduation')
            keys = ['student_status', 'schedule']
        for key in keys:
            self.job['checks'][key] = {'status': 'pass', 'quote': '合成模式条件原文', 'source_url': self.job['url']}
            conditions[key] = {'status': 'pass', 'reason': '合成条件与本人来源已独立核对'}
        self.refresh_review()

    def chat(self):
        self.job.update(source_platform='boss', link_type='recruiter_platform')
        self.job['application'].update(route='chat', status='chat_available', entry_method='visible_control',
                                       control_enabled=True, recruiter_id='synthetic-recruiter',
                                       text='合成J1详情与招聘者，沟通控件可见且启用；未发送消息。')
        self.job['application'].pop('clicked')

    def test_experienced_does_not_require_graduation_year(self):
        self.mode('experienced')
        self.assertEqual(self.status(), 'ready')

    def test_unknown_mode_cannot_silently_disable_checks(self):
        self.mode('experienced')
        self.profile['search_mode'] = 'other'
        self.refresh_review()
        self.assertEqual(self.status(), 'pending')

    def test_experienced_missing_work_timeline_is_pending(self):
        self.mode('experienced')
        self.profile.pop('experience')
        self.refresh_review()
        self.assertEqual(self.status(), 'pending')

    def test_internship_months_cannot_fill_formal_work_gap(self):
        self.mode('experienced')
        self.profile['experience'].update(verified_work_months=6, relevant_work_months=6, internship_months=60)
        self.refresh_review()
        self.assertEqual(self.status(), 'rejected')

    def test_relevant_experience_not_total_years_is_used(self):
        self.mode('experienced')
        self.profile['experience'].update(verified_work_months=60, relevant_work_months=6)
        self.refresh_review()
        self.assertEqual(self.status(), 'rejected')

    def test_preferred_experience_gap_is_not_mandatory(self):
        self.mode('experienced')
        self.job['experience_requirement'].update(min_months=60, priority='preferred')
        self.assertEqual(self.status(), 'ready')

    def test_unknown_experience_requirement_is_pending(self):
        self.mode('experienced')
        self.job['experience_requirement']['priority'] = 'unknown'
        self.assertEqual(self.status(), 'pending')

    def test_relevant_months_cannot_exceed_verified_total(self):
        self.mode('experienced')
        self.profile['experience']['relevant_work_months'] = 36
        self.refresh_review()
        self.assertEqual(self.status(), 'pending')

    def test_hard_salary_floor_rejects_wholly_lower_range(self):
        self.mode('experienced')
        self.profile['salary_constraint'] = {'min': 20000, 'period': 'month', 'currency': 'CNY', 'hard': True}
        self.job['salary_range'] = {'min': 12000, 'max': 18000, 'period': 'month', 'currency': 'CNY'}
        self.refresh_review()
        self.assertEqual(self.status(), 'rejected')

    def test_hard_salary_with_unpublished_range_is_pending(self):
        self.mode('experienced')
        self.profile['salary_constraint'] = {'min': 20000, 'period': 'month', 'currency': 'CNY', 'hard': True}
        self.refresh_review()
        self.assertEqual(self.status(), 'pending')

    def test_different_salary_period_cannot_be_compared_as_equal(self):
        self.mode('experienced')
        self.profile['salary_constraint'] = {'min': 20000, 'period': 'month', 'currency': 'CNY', 'hard': True}
        self.job['salary_range'] = {'min': 200000, 'max': 300000, 'period': 'year', 'currency': 'CNY'}
        self.refresh_review()
        self.assertEqual(self.status(), 'pending')

    def test_internship_checks_schedule_instead_of_cohort(self):
        self.mode('internship')
        self.assertEqual(self.status(), 'ready')

    def test_internship_cannot_ignore_short_availability(self):
        self.mode('internship')
        self.profile['internship_availability']['days_per_week'] = 2
        self.refresh_review()
        self.assertEqual(self.status(), 'rejected')

    def test_graduated_candidate_cannot_take_student_only_internship(self):
        self.mode('internship')
        self.profile['student_status'] = 'graduated'
        self.refresh_review()
        self.assertEqual(self.status(), 'rejected')

    def test_experienced_mode_does_not_mix_internships(self):
        self.mode('experienced')
        self.job['employment_type'] = 'internship'
        self.profile['employment_types'].append('internship')
        self.refresh_review()
        self.assertEqual(self.status(), 'rejected')

    def test_boss_can_verify_visible_chat_control_without_sending(self):
        self.mode('experienced')
        self.chat()
        self.assertEqual(self.status(), 'ready')
        gate = self.audit()['ready_jobs'][0]['quality_gate']
        self.assertEqual(gate['search_mode'], 'experienced')
        self.assertEqual(gate['application_route'], 'chat')
        self.assertFalse(gate['delivery_verified'])

    def test_boss_homepage_login_cannot_replace_current_job_context(self):
        self.mode('experienced')
        self.chat()
        self.job['application']['context'] = 'homepage'
        self.assertEqual(self.status(), 'pending')

    def test_disabled_chat_button_is_not_available(self):
        self.mode('experienced')
        self.chat()
        self.job['application']['control_enabled'] = False
        self.assertEqual(self.status(), 'pending')

    def test_chat_requires_identified_recruiter(self):
        self.mode('experienced')
        self.chat()
        self.job['application'].pop('recruiter_id')
        self.assertEqual(self.status(), 'pending')

    def test_contacted_or_resume_sent_cannot_be_entry_status(self):
        self.mode('experienced')
        self.chat()
        for state in ['contacted', 'resume_sent', 'replied', 'submitted']:
            with self.subTest(state=state):
                self.job['application']['status'] = state
                self.assertEqual(self.status(), 'pending')

    def test_social_mode_still_obeys_explicit_graduation_window(self):
        self.mode('experienced')
        self.job['graduation_window'] = {'start': '2027-01', 'end': '2027-12'}
        self.assertEqual(self.status(), 'pending')

    def test_boss_route_must_be_explicit(self):
        self.mode('experienced')
        self.job['source_platform'] = 'boss'
        self.assertEqual(self.status(), 'pending')

    def test_zero_internship_availability_is_not_a_ready_profile(self):
        self.mode('internship')
        self.profile['internship_availability'].update(days_per_week=0, months=0)
        self.job['internship_requirement'].update(days_per_week=0, months=0)
        self.refresh_review()
        self.assertEqual(self.status(), 'pending')

    def test_scoped_boss_login_still_requires_identified_recruiter(self):
        self.mode('experienced')
        self.chat()
        self.job['application'].update(status='login_required', entry_method='direct_url', opened=True,
                                       final_url='https://a.example/login?return=J1')
        self.job['application'].pop('recruiter_id')
        self.assertEqual(self.status(), 'pending')
