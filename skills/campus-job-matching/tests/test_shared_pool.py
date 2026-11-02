import sys
import unittest
import tempfile
from unittest.mock import patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import shared_pool as pool


class SharedPoolTests(unittest.TestCase):
    def job(self, **kw):
        return dict(company='甲公司', title='产品运营', url='https://jobs.example.com/job/123', cities=['北京'], **kw)

    def test_tracking_removed_but_job_routes_preserved(self):
        self.assertEqual(pool.canonical_url('[投递](https://jobs.example.com/detail?jobId=123&utm_source=wx&batch=2027)'), 'https://jobs.example.com/detail?batch=2027&jobId=123')
        self.assertEqual(pool.canonical_url('https://app.mokahr.com/campus-recruitment/acme/123#/job/abc?from=wx'), 'https://app.mokahr.com/campus-recruitment/acme/123#/job/abc')

    def test_same_posting_across_students_is_one_with_all_private_provenance(self):
        a = {**self.job(), 'source': {'base': 'baseA', 'record_id': 'recA'}}
        b = {**self.job(), 'url': 'https://jobs.example.com/job/123?utm_campaign=wx', 'source': {'base': 'baseB', 'record_id': 'recB'}}
        plan = pool.build_plan([a, b], [])
        self.assertEqual(len(plan['additions']), 1)
        self.assertEqual(len(plan['additions'][0]['sources']), 2)

    def test_existing_main_pool_prevents_new_row_and_rerun_is_empty(self):
        plan = pool.build_plan([self.job()], [self.job()])
        self.assertEqual(plan['additions'], [])
        self.assertEqual(plan['stats']['already_in_pool'], 1)

    def test_known_platform_detail_routes_dedupe_despite_display_parameters(self):
        a = {**self.job(), 'url':'https://zhaopin.meituan.com/web/position/detail?jobUnionId=456&highlightType=campus'}
        b = {**self.job(), 'url':'https://zhaopin.meituan.com/m/position?jobUnionId=456'}
        self.assertEqual(len(pool.build_plan([a,b],[])['additions']),1)

    def test_shared_announcement_keeps_distinct_roles_and_cities(self):
        jobs = [dict(company='甲公司', title=t, cities=[c], url='https://mp.weixin.qq.com/s/ann') for t,c in [('财务岗','北京'),('审计岗','北京'),('财务岗','上海')]]
        self.assertEqual(len(pool.build_plan(jobs, [])['additions']), 3)

    def test_same_moka_id_in_other_tenant_stays_distinct(self):
        jobs = [{**self.job(), 'url': f'https://app.mokahr.com/campus-recruitment/{tenant}/100#/job/abc'} for tenant in ['alpha','beta']]
        self.assertEqual(len(pool.build_plan(jobs, [])['additions']), 2)

    def test_explicit_conflict_on_same_posting_is_held_for_review(self):
        jobs = [self.job(), {**self.job(), 'company':'乙公司'}]
        result = pool.build_plan(jobs, [])
        self.assertEqual(result['additions'], [])
        self.assertEqual(len(result['conflicts']), 1)

    def test_missing_identity_is_not_written(self):
        result = pool.build_plan([{'title':'运营岗','company':'甲公司','url':''}], [])
        self.assertEqual(result['additions'], [])
        self.assertEqual(len(result['incomplete']), 1)

    def test_existing_saved_pool_key_survives_display_metadata_loss(self):
        j = dict(company='甲公司',title='运营',cities=['纽约'],mode='campus',url='https://jobs.example.com/')
        first = pool.build_plan([j],[])['additions'][0]
        saved = {**first,'cities':[],'mode':'','pool_key':first['pool_key']}
        self.assertEqual(pool.build_plan([j],[saved])['additions'],[])

    def test_legal_suffix_and_explicit_parenthetic_alias_share_company(self):
        a = {**self.job(),'company':'九牧集团'}
        b = {**self.job(),'company':'JOMOO（九牧）'}
        self.assertEqual(pool.build_plan([b],[a])['stats']['already_in_pool'],1)

    def test_portal_fallback_is_marked_and_company_identifier_is_removed(self):
        j = pool.normalize_job({'公司':'中国银行（简历编号333377）','投递岗位':'管培生','校招官网链接':'https://jobs.example.com/'})
        self.assertEqual(j['company'],'中国银行')
        self.assertEqual(j['url_kind'],'portal')
        self.assertEqual(j['url'],'https://jobs.example.com/')

    def test_public_payload_excludes_student_state_and_does_not_refresh_verification(self):
        job = {**self.job(), 'jd':'负责业务运营', 'student':'张同学', 'notes':'学生手机号13800138000，已投递', 'status':'ready', 'checked_at':'2026-10-20T12:00:00+08:00', 'source':{'student':'张同学'}}
        fields = pool.job_fields(job, 'recCompany', 'pool-test')
        self.assertEqual(fields['审核状态'], '需复核')
        self.assertEqual(fields['在招状态'], '待核验')
        self.assertNotIn('最后核验时间', fields)
        payload = str(fields)
        self.assertNotIn('张同学', payload)
        self.assertNotIn('13800138000', payload)
        self.assertNotIn('已投递', payload)

    def test_chinese_rows_and_standard_ready_format_normalize(self):
        a = pool.normalize_job({'公司':'甲公司','投递岗位':'产品运营','工作城市':['北京'],'投递链接':'https://jobs.example.com/job/123','审核':'已选岗'})
        self.assertEqual(a['company'], '甲公司')
        self.assertEqual(a['cities'], ['北京'])
        self.assertEqual(a['url'], 'https://jobs.example.com/job/123')

    def test_live_student_schema_aliases_preserve_detail_and_dedicated_jd(self):
        j = pool.normalize_job({'公司':'甲公司','投递岗位':'运营','专岗详情链接':'https://jobs.example.com/job/1','校招官网链接':'https://jobs.example.com/','完整JD':'负责运营和数据分析'})
        self.assertEqual(j['url'],'https://jobs.example.com/job/1')
        self.assertEqual(j['jd'],'负责运营和数据分析')

    def test_explicit_full_jd_section_does_not_copy_fit_or_personal_followup(self):
        j = pool.normalize_job({'公司':'甲公司','投递岗位':'审计','投递链接':'https://jobs.example.com/job/1','备注':'简历依据：张同学的项目\n完整JD：\n职责：核查底稿。\n任职要求：会计专业。\n本人申请前确认：手机号13800138000'})
        self.assertIn('核查底稿',j['jd'])
        self.assertNotIn('张同学',j['jd'])
        self.assertNotIn('13800138000',j['jd'])

    def test_boss_pending_can_be_recovered_without_becoming_ready(self):
        job = {**self.job(), 'url':'https://www.zhipin.com/job_detail/abc.html', 'status':'blocked'}
        result = pool.build_plan([job], [])
        self.assertEqual(len(result['additions']), 1)
        self.assertEqual(pool.job_fields(result['additions'][0], 'rec1', 'test')['在招状态'], '待核验')

    def test_search_filters_known_wrong_city_mode_and_closed_but_keeps_unknown_marked(self):
        jobs = [
            {**self.job(), 'mode':'campus', 'recruitment_status':'待核验'},
            {**self.job(), 'url':'https://jobs.example.com/job/2', 'cities':['上海'], 'mode':'campus'},
            {**self.job(), 'url':'https://jobs.example.com/job/3', 'mode':'internship'},
            {**self.job(), 'url':'https://jobs.example.com/job/4', 'recruitment_status':'已截止'},
            {**self.job(), 'url':'https://jobs.example.com/job/5', 'cities':[], 'mode':''},
        ]
        results = pool.search_jobs(jobs, {'cities':['北京'], 'search_mode':'campus', 'directions':['运营']})
        self.assertEqual([r['url'] for r in results], ['https://jobs.example.com/job/123','https://jobs.example.com/job/5'])
        self.assertTrue(all(r['requires_revalidation'] for r in results))

    def test_decode_cli_requires_matching_ids_and_pagination_does_not_silently_truncate(self):
        page = {'fields':['公司','岗位名称'],'data':[['甲公司','运营']],'record_id_list':['rec1'],'has_more':True,'rev':1}
        self.assertEqual(pool.decode_page(page)[0]['record_id'], 'rec1')
        with self.assertRaises(ValueError):
            pool.decode_page({**page,'record_id_list':[]})

    def test_schema_projection_preserves_known_city_but_keeps_unknown_category_in_notes(self):
        schema=[{'name':'城市','type':'select','multiple':True,'options':[{'name':'北京'}]}, {'name':'岗位大类','type':'select','multiple':False,'options':[{'name':'运营'}]}]
        j={**self.job(),'category':'财务'}
        result=pool.project_facts(j,{},schema)
        self.assertEqual(result['城市'],['北京'])
        self.assertNotIn('岗位大类',result)

    def test_negative_historical_state_is_never_reopened(self):
        result=pool.job_fields({**self.job(),'recruitment_status':'已下架'},'rec1','test')
        self.assertEqual(result['在招状态'],'已下架')

    def test_real_profile_target_roles_and_company_exclusions_are_used(self):
        jobs=[self.job(),{**self.job(),'company':'乙公司','title':'Java开发','url':'https://jobs.example.com/job/2'}]
        found=pool.search_jobs(jobs,{'target_roles':['Java'],'excluded_companies':['甲公司']})
        self.assertEqual([j['company'] for j in found],['乙公司'])

    def test_generic_application_page_does_not_merge_separate_jobs(self):
        a={**self.job(),'url':'https://hr.example.com/internship/position/application'}
        b={**a,'title':'国际平台运营','cities':['武汉']}
        self.assertEqual(len(pool.build_plan([a,b],[])['additions']),2)

    def test_moka_mobile_and_receipt_become_same_public_detail_without_candidate_data(self):
        receipt='https://app.mokahr.com/m/campus-recruitment/acme/100#/job/abc/campus_apply/thanks?candidateId=private-id&candidateName=PrivateName&applyInfo%5BaimWorkCity%5D=secret'
        want='https://app.mokahr.com/campus-recruitment/acme/100#/job/abc'
        self.assertEqual(pool.canonical_url(receipt),want)
        additions=pool.build_plan([{**self.job(),'url':receipt},{**self.job(),'url':want}],[])['additions']
        self.assertEqual(len(additions),1)
        self.assertEqual(additions[0]['url'],want)
        self.assertEqual(pool.job_fields({**self.job(),'url':receipt},'rec1','test')['岗位直达链接'],want)

    def test_resume_profile_link_is_held_instead_of_shared(self):
        self.assertEqual(pool.canonical_url('https://jobs.example.com/resume/detail?resumeId=private-id'),'')

    def test_personal_application_dashboard_is_not_a_public_job(self):
        self.assertEqual(pool.canonical_url('https://app.mokahr.com/campus-recruitment/acme/100#/candidateHome/applications'),'')

    def test_snapshot_rejects_changing_revisions_between_pages(self):
        first={'fields':['岗位名称'],'data':[['运营']],'record_id_list':['rec1'],'has_more':True,'rev':1}
        second={'fields':['岗位名称'],'data':[['产品']],'record_id_list':['rec2'],'has_more':False,'rev':2}
        with patch.object(pool,'cli',side_effect=[first,second]):
            with self.assertRaises(ValueError):
                pool.read_all('base','table')

    def test_snapshot_recovers_common_facts_saved_in_public_notes(self):
        j=pool.normalize_job({'公司':'甲公司','岗位名称':'管培生','岗位直达链接':'https://jobs.example.com/job/1','城市':['北京'],'岗位类型':['全职'],'备注':'共享岗位回收；批次 x；历史收录不等于当前在招或适合新学生。\n模式：experienced；需重新核验岗位、资格和申请入口。\n原始城市：北京、纽约\n原始岗位分类：财务\n原始截止时间：2026-12-31'})
        self.assertEqual(j['mode'],'experienced')
        self.assertEqual(j['category'],'财务')
        self.assertEqual(j['cities'],['北京','纽约'])
        self.assertEqual(j['deadline'],'2026-12-31')

    def test_new_record_readback_waits_for_visibility_without_creating_again(self):
        missing={'fields':['公司名称'],'data':[[None]],'record_id_list':['rec1'],'record_not_found':['rec1'],'rev':2}
        visible={'fields':['公司名称'],'data':[['甲公司']],'record_id_list':['rec1'],'rev':2}
        with patch.object(pool,'cli',side_effect=[missing,visible]),patch.object(pool.time,'sleep'):
            self.assertEqual(pool.read_created('base','table',['rec1'])['data'],[['甲公司']])

    def test_legal_form_and_parent_group_are_not_company_aliases(self):
        self.assertFalse(pool.same_company('立信会计师事务所（特殊普通合伙）','天健会计师事务所（特殊普通合伙）'))
        self.assertFalse(pool.same_company('平安科技（平安集团）','陆控（平安集团）'))
        self.assertFalse(pool.same_company('甲科技（广州）','乙科技（广州）'))

    def test_company_lookup_prefers_full_primary_name_over_parent_alias(self):
        companies=[{'record_id':'recA','公司名称':'安克创新'},{'record_id':'recB','公司名称':'Anker'},{'record_id':'recC','公司名称':'立信会计师事务所'},{'record_id':'recD','公司名称':'中审众环会计师事务所（特殊普通合伙）'}]
        idx=pool.company_index(companies)
        self.assertEqual(pool.resolve_company('安克创新（Anker）',idx),'recA')
        self.assertEqual(pool.resolve_company('立信会计师事务所（特殊普通合伙）',idx),'recC')
        self.assertIsNone(pool.resolve_company('甲科技（广州）',pool.company_index([{'record_id':'recE','公司名称':'乙科技（广州）'}])))

    def test_resume_keeps_previous_attempt_journal_intact(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'journal';root.mkdir();(root/'jobs-00000-response.json').write_text('saved proof')
            attempt=pool.make_journal(root)
            self.assertNotEqual(attempt,root)
            self.assertEqual((root/'jobs-00000-response.json').read_text(),'saved proof')
            self.assertTrue(attempt.is_dir())

    def test_standard_ready_candidate_recovers_its_jd_and_mode(self):
        raw={**self.job(),'search_mode':'campus','jd_text':'负责电商运营和复盘','employment_type':'full_time','student_id':'private-student'}
        j=pool.build_plan([raw],[])['additions'][0]
        payload=pool.job_fields(j,'rec1','test')
        self.assertEqual(payload['职位描述'],'负责电商运营和复盘')
        self.assertEqual(payload['岗位类型'],'全职')
        self.assertNotIn('private-student',str(payload))


if __name__ == '__main__':
    unittest.main()
