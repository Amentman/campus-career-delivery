#!/usr/bin/env python3
"""Search and append to the private shared job pool through the user's lark-cli."""
import argparse
import hashlib
import json
import os
import re
import subprocess
import time
import unicodedata
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

TEAM_CONFIG = Path.home() / '.config/jihui-skills/team.json'
LEGACY_CONFIG = Path.home() / '.codex/campus-job-matching.local.json'
TRACKING = {'from', 'source', 'ref', 'refer', 'referrer', 'shareid', 'sharecode', 'campussharecode', 'scene', 'spm', 'channel', 'channelid', 'trackingid', 'securityid', 'ka', 'lid', 'pk', 'sessionid', 'share_token', 'sharepageid', 'sourcetoken', 'locale'}


def load_config():
    """Load member settings without contacting Feishu or creating any files."""
    explicit = os.environ.get('JIHUI_SKILLS_CONFIG')
    if explicit:
        path = Path(explicit).expanduser()
    elif TEAM_CONFIG.exists():
        path = TEAM_CONFIG
    elif LEGACY_CONFIG.exists():
        path = LEGACY_CONFIG
    else:
        path = TEAM_CONFIG
    setup = ('先复制团队配置样例到 ~/.config/jihui-skills/team.json，填写当前成员身份与 shared_pool；'
             '自选路径用 JIHUI_SKILLS_CONFIG 指定。配置步骤见 references/runtime-config.md。')
    try:
        config = json.loads(path.read_text(encoding='utf-8-sig'))
    except FileNotFoundError:
        raise ValueError('找不到团队配置。' + setup) from None
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise ValueError('团队配置不是可读的 JSON 文件。' + setup) from None
    if not isinstance(config, dict):
        raise ValueError('团队配置根节点必须是对象。' + setup)
    if 'version' in config and (type(config['version']) is not int or config['version'] != 1):
        raise ValueError('不支持的团队配置 version；当前支持 version=1。')
    if not str(config.get('expected_user_open_id') or '').strip():
        raise ValueError('团队配置缺少 expected_user_open_id；绑定当前成员本人账号。' + setup)
    if config.get('version') == 1 and not str(config.get('expected_profile') or '').strip():
        raise ValueError('团队配置缺少 expected_profile；填写当前成员的 lark-cli profile。' + setup)
    route = config.get('shared_pool')
    if not isinstance(route, dict):
        raise ValueError('shared_pool 未配置；本轮尚未查询共享池。' + setup)
    route = dict(route)
    # Legacy configurations described a personal pool owned by the same user.
    if 'version' not in config and not route.get('owner_open_id'):
        route['owner_open_id'] = config['expected_user_open_id']
    required = ('base_token', 'job_table_id', 'company_table_id', 'wiki_node_token', 'owner_open_id')
    missing = [key for key in required if not isinstance(route.get(key), str) or not route[key].strip()]
    if missing:
        raise ValueError('shared_pool 缺少配置字段：' + ', '.join(missing) + '。' + setup)
    config['shared_pool'] = route
    return config


def verify_pool_access(config):
    """Check caller identity separately from the configured shared pool owner.

    Actual record/field reads follow this check and prove the caller's access;
    ownership never implies access for another team member.
    """
    result = subprocess.run(['lark-cli', 'auth', 'status', '--json', '--verify'],
                            capture_output=True, text=True, check=True)
    auth = json.loads(result.stdout)
    user = auth.get('identities', {}).get('user', {})
    if not user.get('verified') or user.get('openId') != config['expected_user_open_id']:
        raise RuntimeError('Unexpected or unverified current member identity; check expected_user_open_id')
    profile = config.get('expected_profile')
    actual_profiles = {str(value) for value in (
        auth.get('appId'), auth.get('profile'), auth.get('profileId'),
        user.get('appId'), user.get('profile'), user.get('profileId')) if isinstance(value, str)}
    if profile and profile not in actual_profiles:
        raise RuntimeError('Current member profile differs or is unavailable; check expected_profile')
    route = config['shared_pool']
    meta = cli(['wiki', '+node-get', '--node-token', route['wiki_node_token']])
    if meta.get('obj_token') != route['base_token']:
        raise RuntimeError('Shared pool target differs from configured base_token')
    if meta.get('owner') != route['owner_open_id']:
        raise RuntimeError('Shared pool owner differs from configured owner_open_id')
    return meta

def text(value):
    if value is None:
        return ''
    if isinstance(value, list):
        return '、'.join(filter(None, (text(v) for v in value)))
    if isinstance(value, dict):
        return text(value.get('text') or value.get('name') or value.get('title') or value.get('url') or '')
    return str(value).strip()

def values(value):
    if isinstance(value, list):
        return [text(v) for v in value if text(v)]
    return [s.strip() for s in re.split(r'[、,，;；\n/]', text(value)) if s.strip()]

def normalized(value):
    return re.sub(r'\s+', '', unicodedata.normalize('NFKC', text(value))).casefold()

def clean_company(value):
    value = text(value)
    value = re.sub(r'\[([^\]]+)\]\(https?://[^)]+\)', r'\1', value)
    return re.sub(r'[（(](?:简历编号|只能投一个)[^）)]*[）)]', '', value).strip()

def company_tokens(value):
    value = unicodedata.normalize('NFKC',clean_company(value))
    aliases = [a for a in re.findall(r'\(([^)]+)\)',value) if not re.search(r'集团|公司|合伙|有限|分行|分局|分院',a)]
    tokens = [re.sub(r'\([^)]*\)', '',value), *aliases]
    result = set()
    for token in tokens:
        for part in re.split(r'[、,|×]',token):
            part = normalized(part)
            part = re.sub(r'(?:股份有限公司|有限责任公司|集团有限公司|有限公司|集团股份公司|集团)$','',part)
            if part and part not in {'中国','北京','上海','香港','未知','待确认'}:
                result.add(part)
    return result

def same_company(a,b):
    pa,pb = company_primary(a),company_primary(b)
    return bool(pa and pb and (pa == pb or pa in company_tokens(b) or pb in company_tokens(a)))

def company_primary(name):
    name = re.sub(r'\([^)]*\)','',unicodedata.normalize('NFKC',clean_company(name)))
    return re.sub(r'(?:股份有限公司|有限责任公司|集团有限公司|有限公司|集团股份公司|集团)$','',normalized(name))

def index_company(row, indices):
    exact, primary, aliases = indices
    name, rid = row['公司名称'], row['record_id']
    exact.setdefault(normalized(name),rid)
    primary.setdefault(company_primary(name),set()).add(rid)
    for token in company_tokens(name):
        aliases.setdefault(token,set()).add(rid)

def company_index(companies):
    indices = ({},{},{})
    for row in companies:
        index_company(row,indices)
    return indices

def resolve_company(name, indices):
    exact, primary, aliases = indices
    if normalized(name) in exact:
        return exact[normalized(name)]
    matches = primary.get(company_primary(name),set())
    if len(matches) == 1:
        return next(iter(matches))
    matches = set(aliases.get(company_primary(name),set()))
    for token in company_tokens(name):
        matches.update(primary.get(token,set()))
    return next(iter(matches)) if len(matches) == 1 else None

def canonical_url(value):
    raw = text(value)
    md = re.search(r'\]\((https?://[^\s]+)\)', raw)
    if md:
        raw = md.group(1)
    else:
        found = re.search(r'https?://[^\s<>"\]]+', raw)
        raw = found.group(0) if found else raw
    try:
        p = urlsplit(raw)
    except ValueError:
        return ''
    if p.scheme not in ('http', 'https') or not p.hostname or p.username or p.password:
        return ''
    if re.search(r'/(?:resume|candidate|candidateHome|profile|personal|myresume|cv)(?:/|$)',p.path+'#'+p.fragment,re.I):
        return ''
    def private_key(key):
        return key.lower().startswith(('candidate','resume','applyinfo','applicant','access_token','refresh_token','useremail','userphone'))
    all_queries = parse_qsl(p.query) + (parse_qsl(p.fragment.split('?',1)[1]) if '?' in p.fragment else [])
    if any(private_key(k) for k,v in all_queries) and not (re.search(r'/(?:job|position|job_detail)/[^/?#]+',p.path+'#'+p.fragment,re.I) or any(k.lower() in {'jobid','jobunionid','positionid','job_id'} for k,v in all_queries)):
        return ''
    def clean(query):
        return urlencode(sorted((k,v) for k,v in parse_qsl(query, keep_blank_values=True) if not private_key(k) and not k.lower().startswith('utm_') and k.lower() not in TRACKING))
    fragment = p.fragment
    path = p.path
    if p.hostname.endswith('mokahr.com'):
        tenant = re.match(r'/(?:m/)?((?:campus-recruitment|social-recruitment|recruitment)/[^/]+/[^/]+)',path)
        jobid = re.search(r'/job/([^/?#]+)',fragment)
        if tenant and jobid:
            path = '/' + tenant.group(1)
            fragment = '/job/' + jobid.group(1)
    if '?' in fragment:
        route, query = fragment.split('?', 1)
        fragment = route + ('?' + clean(query) if clean(query) else '')
    if fragment and not fragment.startswith('/'):
        fragment = ''
    return urlunsplit(('https', p.netloc.lower(), path.rstrip('/') or '/', clean(p.query), fragment))

def normalize_job(row, company_lookup=None):
    company_lookup = company_lookup or {}
    def pick(*names):
        return next((row[n] for n in names if row.get(n) not in (None, '', [])), '')
    company = pick('company', '公司', '公司名称', '企业名称', '企业', '公司/机构')
    if isinstance(company, list) and company and isinstance(company[0], dict) and 'id' in company[0]:
        company = '、'.join(company_lookup.get(v['id'], '') for v in company)
    title = text(pick('title', 'job_title', 'job_name', '投递岗位', '岗位名称', '职位名称', '职位', '岗位'))
    url = ''
    url_kind = row.get('url_kind') or 'detail_or_announcement'
    for field in ['url', 'application_url', 'job_url', 'detail_url', 'apply_url', '岗位直达链接', '专岗详情链接', '投递链接', '投递链接（放最终岗位页面‼️不要放offer先生或者过渡页）', '申请链接', '岗位链接', '网申链接', '链接', '校招官网链接', '招聘首页']:
        url = canonical_url(row.get(field))
        if url:
            if field in ('校招官网链接','招聘首页'):
                url_kind = 'portal'
            break
    mode = text(pick('search_mode', 'mode'))
    kind = text(pick('job_type', 'employment_type', '岗位类型', '招聘类型', '用工类型'))
    batch = values(pick('batch', '招聘批次'))
    if mode not in ('campus', 'internship', 'experienced'):
        mode = 'internship' if '实习' in kind or '实习' in title else 'experienced' if '社招' in kind else 'campus' if '校招' in kind or any(s in text(batch) for s in ['秋招', '春招', '提前批', '补录']) else ''
    jd = text(pick('jd_text', 'jd', '完整JD', '职位描述', '岗位职责', '岗位描述', '岗位jd', 'JD', '岗位JD', '职位说明'))
    if not jd:
        note = text(row.get('备注'))
        match = re.search(r'(?:完整JD|JD原文)[：:]\s*\n?(.*)', note, re.S|re.I)
        if match:
            jd = re.split(r'\n\s*(?:本人申请前确认|集团校招原始公告|简历依据|学生|匹配依据|匹配证据|申请边界|入口核验|个人条件|建议投递)[：:：\s]',match.group(1),maxsplit=1)[0].strip()
    result = {
        'company': clean_company(company), 'title': title, 'url': url, 'url_kind':url_kind,
        'cities': values(pick('cities', 'city', '工作城市', '城市', '工作地点', '地点')),
        'mode': mode, 'job_type': kind, 'batch': batch,
        'jd': jd,
        'requirements': text(pick('requirements', '岗位要求', '任职要求')),
        'degree': values(pick('degree', '学历要求')),
        'major': text(pick('major', '专业要求')),
        'graduation_requirement': text(pick('graduation_requirement', '毕业时间要求', '毕业要求')),
        'graduation_years': values(pick('graduation_years', '适合届次', '届别')),
        'category': text(pick('category', '岗位大类', '岗位分类')),
        'deadline': text(pick('deadline', '截止时间', '投递截止日期', '投递截止时间')),
        'platform_id': text(pick('platform_id', 'job_id', '平台岗位ID')),
        'recruitment_status': text(pick('recruitment_status', '在招状态')),
        'record_id': row.get('record_id', ''),
        'pool_key':text(pick('pool_key','唯一键')),
        'source': row.get('source', {}), 'sources': row.get('sources', []),
    }
    note = text(row.get('备注'))
    if note.startswith('共享岗位回收；批次 '):
        saved = dict(re.findall(r'^(原始[^：\n]+)：([^\n]*)',note,re.M))
        match = re.search(r'^模式：(campus|internship|experienced)；',note,re.M)
        if match:
            result['mode'] = match.group(1)
        for label,field in [('原始城市','cities'),('原始招聘批次','batch'),('原始学历要求','degree'),('原始届别','graduation_years')]:
            if saved.get(label):
                result[field] = values(saved[label])
        if saved.get('原始岗位分类'):
            result['category'] = saved['原始岗位分类']
        if saved.get('原始截止时间'):
            result['deadline'] = saved['原始截止时间']
        if '入口类型：招聘首页' in note:
            result['url_kind'] = 'portal'
    return result

def identity_keys(job):
    url = canonical_url(job.get('url'))
    if not url:
        return set()
    p = urlsplit(url)
    host = p.hostname.removeprefix('www.')
    queries = {k.lower():v for k,v in parse_qsl(p.query)}
    if host == 'zhaopin.meituan.com' and queries.get('jobunionid'):
        return {'posting:meituan:' + queries['jobunionid']}
    if host.endswith('mokahr.com'):
        tenant = re.match(r'/(?:campus-recruitment|social-recruitment|recruitment)/([^/]+)/([^/]+)',p.path)
        jobid = re.search(r'/job/([^/?#]+)',p.fragment)
        if tenant and jobid:
            return {'posting:moka:' + ':'.join((*tenant.groups(),jobid.group(1)))}
    if host.endswith('zhipin.com'):
        jobid = re.search(r'/job_detail/([^/.]+)',p.path)
        if jobid:
            return {'posting:boss:' + jobid.group(1)}
    if host.endswith('jobs.feishu.cn'):
        jobid = re.search(r'/(campus|experienced|internship)/position/(\d+)',p.path)
        if jobid:
            return {'posting:' + host + ':' + ':'.join(jobid.groups())}
    if host in ('jobs.bytedance.com','jobs.pupuapi.com'):
        jobid = re.search(r'/(campus|experienced)/position/(?:detail/)?(\d+)',p.path)
        if jobid:
            return {'posting:' + host + ':' + ':'.join(jobid.groups())}
    route = p.path + '#' + p.fragment
    # Detail IDs are scoped to host and tenant/category path, never globally.
    detail = re.search(r'/(?:job_detail|position|positions|job|jobs/detail|zpdetail|position-detail|jobdetail)/([^?#]+)', route, re.I)
    reserved = {'application','apply','search','list','jobs','position','positions','index','detail','all','home','graduate','campus','social','internship'}
    detail_id = bool(detail and any(s.lower() not in reserved for s in detail.group(1).strip('/').split('/')))
    id_queries = [(k.lower(), v) for k,v in parse_qsl(p.query) if k.lower() in {'jobid','jobunionid','positionid','requisitionid','jid','j','job_id','position_id'}]
    specific = bool(detail_id or id_queries or (re.search(r'/detail',p.path,re.I) and dict(parse_qsl(p.query)).get('id')))
    if p.hostname in ('mp.weixin.qq.com',) or '/article/' in p.path or '/notice/' in p.path or '/announcement/' in p.path:
        specific = False
    if specific:
        return {'url:' + url}
    # A shared announcement/list cannot identify a single role.
    parts = [url, normalized(job.get('company')), normalized(job.get('title')),
             '|'.join(sorted(normalized(v) for v in job.get('cities', []))),
             normalized(job.get('mode')), '|'.join(sorted(normalized(v) for v in job.get('batch', [])))]
    return {'announcement:' + json.dumps(parts, ensure_ascii=False)}

def build_plan(jobs, existing):
    index = {}
    for raw in existing:
        j = raw if 'url' in raw and 'title' in raw else normalize_job(raw)
        for key in identity_keys(j):
            index.setdefault(key, []).append(j)
        if j.get('pool_key','').startswith('shared:'):
            index.setdefault('saved:' + j['pool_key'],[]).append(j)
    groups, incomplete, conflicts, already, duplicates = {}, [], [], 0, 0
    for raw in jobs:
        j = normalize_job(raw)
        keys = identity_keys(j)
        if not keys or not j.get('title') or not j.get('company'):
            incomplete.append(j)
            continue
        key = min(keys)
        digest = hashlib.sha256(key.encode()).hexdigest()
        existing_matches = index.get('saved:shared:' + digest,index.get(key))
        if existing_matches:
            if all(not same_company(e.get('company'),j['company']) for e in existing_matches):
                conflicts.append({'reason':'same posting has conflicting company', 'existing':existing_matches, 'incoming':j})
            else:
                already += 1
            continue
        if key in groups:
            group = groups[key]
            if not same_company(group['company'],j['company']):
                group['_conflict'] = True
                conflicts.append({'reason':'same posting has conflicting company', 'existing':group.copy(), 'incoming':j})
            else:
                duplicates += 1
                group['sources'].extend(j.get('sources') or [j.get('source', {})])
                for f in ['jd','requirements','degree','major','graduation_requirement','graduation_years','category','deadline']:
                    if not group.get(f) and j.get(f):
                        group[f] = j[f]
                group['cities'] = list(dict.fromkeys(group.get('cities', []) + j.get('cities', [])))
        else:
            groups[key] = {**j, 'pool_key':'shared:' + digest, 'sources':j.get('sources') or [j.get('source', {})]}
    additions = [{k:v for k,v in j.items() if k != '_conflict'} for j in groups.values() if not j.get('_conflict')]
    return {'additions':additions, 'conflicts':conflicts, 'incomplete':incomplete,
            'stats':{'source_rows':len(jobs), 'already_in_pool':already, 'within_sources_duplicates':duplicates, 'additions':len(additions), 'conflicts':len(conflicts), 'incomplete':len(incomplete)}}

def job_fields(job, company_record_id, batch):
    j = {**job,'url':canonical_url(job.get('url'))}
    if not j['url']:
        raise ValueError('No public job URL; personal/invalid links must stay outside the pool')
    key = j.get('pool_key') or 'shared:' + hashlib.sha256(min(identity_keys(j)).encode()).hexdigest()
    kind = '实习' if j.get('mode') == 'internship' else '全职' if j.get('mode') in ('campus','experienced') else '待确认'
    notes = [f'共享岗位回收；批次 {batch}；历史收录不等于当前在招或适合新学生。', f'模式：{j.get("mode") or "待确认"}；需重新核验岗位、资格和申请入口。']
    if j.get('url_kind') == 'portal':
        notes.append('入口类型：招聘首页；本岗位详情待定位。')
    # Only common job facts are allowed; never copy student remarks or fit scores.
    for label, field in [('原始城市','cities'), ('原始岗位分类','category'), ('原始招聘批次','batch'), ('原始学历要求','degree'), ('原始届别','graduation_years'), ('原始截止时间','deadline')]:
        if j.get(field):
            notes.append(label + '：' + text(j[field]))
    result = {'公司':[{'id':company_record_id}], '岗位名称':j['title'], '岗位直达链接':j['url'],
              '数据来源':j['url'], '唯一键':key, '审核状态':'需复核', '在招状态':'待核验',
              '岗位类型':kind, '备注':'\n'.join(notes)}
    if j.get('recruitment_status') in ('已截止','已下架'):
        result['在招状态'] = j['recruitment_status']
    for src, dst in [('jd','职位描述'),('requirements','岗位要求'),('major','专业要求'),('graduation_requirement','毕业时间要求'),('platform_id','平台岗位ID')]:
        if j.get(src):
            result[dst] = j[src]
    return result

def project_facts(job, fields, schema):
    """Only use existing option values; original values remain in job_fields notes."""
    fields = dict(fields)
    mapping = {'城市':job.get('cities',[]), '岗位大类':[job.get('category','')],
               '学历要求':job.get('degree',[]), '适合届次':job.get('graduation_years',[]),
               '招聘批次':job.get('batch',[])}
    for field in schema:
        name = field['name']
        if name not in mapping:
            continue
        options = {o['name'] for o in field.get('options',[])}
        found = list(dict.fromkeys(v for v in mapping[name] if v in options))
        if found:
            fields[name] = found if field.get('multiple') else found[0]
    return fields

def search_jobs(jobs, profile):
    wanted_cities = {normalized(v) for v in profile.get('cities', [])}
    directions = [normalized(v) for v in profile.get('directions', profile.get('target_roles', []))]
    excluded = {normalized(v) for v in profile.get('excluded_companies',[])}
    mode = profile.get('search_mode', '')
    found = []
    for raw in jobs:
        j = raw if 'url' in raw and 'title' in raw else normalize_job(raw)
        if normalized(j.get('company')) in excluded:
            continue
        if any(s in j.get('recruitment_status','') for s in ['已截止','已下架']):
            continue
        cities = {normalized(v) for v in j.get('cities', [])} - {'待确认','全国多地','不限'}
        if wanted_cities and cities and not wanted_cities.intersection(cities):
            continue
        if mode and j.get('mode') and j['mode'] != mode:
            continue
        haystack = normalized(j.get('title','') + ' ' + j.get('category','') + ' ' + j.get('jd',''))
        score = sum(d in haystack for d in directions)
        if directions and not score:
            continue
        found.append({**j, 'pool_score':score + int(bool(wanted_cities.intersection(cities))), 'requires_revalidation':True})
    return sorted(found, key=lambda j:-j['pool_score'])

def decode_page(data):
    rows, ids, fields = data.get('data', []), data.get('record_id_list', []), data.get('fields', [])
    if len(rows) != len(ids) or any(len(r) != len(fields) for r in rows):
        raise ValueError('CLI row/field/record ID counts differ; snapshot incomplete')
    return [{'record_id':rid, **dict(zip(fields,row))} for rid,row in zip(ids,rows)]

def cli(args, cwd=None):
    p = subprocess.run(['lark-cli', *args, '--as','user'], capture_output=True, text=True, timeout=120, cwd=cwd)
    v = json.loads(p.stdout if p.returncode == 0 else p.stderr)
    if p.returncode or v.get('ok') is not True:
        raise RuntimeError(str(v.get('error',v)))
    return v['data']

def read_all(base, table):
    rows, offset, revision = [], 0, None
    while True:
        d = cli(['base','+record-list','--base-token',base,'--table-id',table,'--limit','200','--offset',str(offset),'--format','json'])
        if revision is None:
            revision = d.get('rev')
        if d.get('rev') != revision:
            raise ValueError('Table revision changed during pagination; retry the complete read')
        page = decode_page(d)
        rows.extend(page)
        if not d.get('has_more'):
            break
        if not page:
            raise ValueError('Empty page with has_more; refusing incomplete snapshot')
        offset += len(page)
    if len({r['record_id'] for r in rows}) != len(rows):
        raise ValueError('Repeated record IDs across pages; retry a stable snapshot')
    probe = cli(['base','+record-list','--base-token',base,'--table-id',table,'--limit','1','--offset','0','--format','json'])
    if probe.get('rev') != revision:
        raise ValueError('Table revision changed before snapshot completion; retry the complete read')
    return rows

def dump(path, obj):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')

def read_created(base, table, ids):
    for delay in (0,1,2,4,8):
        if delay:
            time.sleep(delay)
        data = cli(['base','+record-get','--base-token',base,'--table-id',table,'--json',json.dumps({'record_id_list':ids}),'--format','json'])
        if not data.get('record_not_found'):
            return data
    raise RuntimeError('Created records are not yet visible; re-read before resuming, never re-create blindly')

def make_journal(path):
    journal = Path(path).resolve()
    journal.mkdir(parents=True,exist_ok=True)
    if any(journal.iterdir()):
        journal = journal / ('attempt-' + str(time.time_ns()))
        journal.mkdir()
    return journal

def append_plan(plan, route, journal_dir, *, execute=False):
    """Append-only import. Every run re-reads live identities before planning writes."""
    config = load_config()
    if route != config['shared_pool']:
        raise RuntimeError('Shared pool route changed; reload the plan before continuing')
    meta = verify_pool_access(config)
    journal = make_journal(journal_dir)
    dump(journal/'node-before.json',meta)
    permission = cli(['drive','permission.public','get','--token',route['base_token'],'--type','bitable'])
    dump(journal/'permission-before.json',permission)
    companies = read_all(route['base_token'],route['company_table_id'])
    lookup = {r['record_id']:text(r.get('公司名称')) for r in companies}
    rows = read_all(route['base_token'],route['job_table_id'])
    dump(journal/'jobs-before.json',rows)
    dump(journal/'companies-before.json',companies)
    live_plan = build_plan(plan['additions'],[normalize_job(r,lookup) for r in rows])
    dump(journal/'live-plan.json',live_plan)
    if not execute:
        print(json.dumps({'dry_run':True,**live_plan['stats']},ensure_ascii=False))
        return live_plan
    schema = cli(['base','+field-list','--base-token',route['base_token'],'--table-id',route['job_table_id'],'--limit','200'])['fields']
    company_schema = cli(['base','+field-list','--base-token',route['base_token'],'--table-id',route['company_table_id'],'--limit','200'])['fields']
    dump(journal/'job-fields.json',schema)
    dump(journal/'company-fields.json',company_schema)
    indices = company_index(companies)
    pending = {}
    for j in live_plan['additions']:
        if not resolve_company(j['company'],indices):
            key = normalized(j['company'])
            pending.setdefault(key,j)
    batch_name = journal.name
    def create(table, payload_rows, kind):
        created = []
        for start in range(0,len(payload_rows),100):
            batch = payload_rows[start:start+100]
            fields = list(dict.fromkeys(f for r in batch for f in r))
            request = {'fields':fields,'rows':[[r.get(f) for f in fields] for r in batch]}
            name = f'{kind}-{start:05d}'
            dump(journal/(name+'-request.json'),request)
            # Never retry uncertain creates here: resume by re-reading the full live pool.
            data = cli(['base','+record-batch-create','--base-token',route['base_token'],'--table-id',table,'--json','@'+name+'-request.json'],cwd=journal)
            dump(journal/(name+'-response.json'),data)
            ids = data.get('record_id_list',[])
            if len(ids) != len(batch):
                raise RuntimeError('Create result does not contain all record IDs; inspect saved response before resuming')
            readback = read_created(route['base_token'],table,ids)
            dump(journal/(name+'-readback.json'),readback)
            confirmed = decode_page(readback)
            if {r['record_id'] for r in confirmed} != set(ids):
                raise RuntimeError('Batch readback IDs differ')
            by_id = {r['record_id']:r for r in confirmed}
            for rid,expected in zip(ids,batch):
                for field,value in expected.items():
                    actual = by_id[rid].get(field)
                    # CLI renders URL text cells as Markdown and single selects as lists.
                    if field in ('岗位直达链接','数据来源','招聘官网'):
                        equal = canonical_url(actual) == canonical_url(value)
                    elif isinstance(actual,list) and isinstance(value,str):
                        equal = actual == [value]
                    else:
                        equal = actual == value
                    if not equal:
                        raise RuntimeError(f'Batch field readback differs: {rid} / {field}')
                created.append({'record_id':rid,**expected})
            dump(journal/(kind+'-created.json'),created)
            print(json.dumps({'kind':kind,'verified':len(created),'total':len(payload_rows)},ensure_ascii=False),flush=True)
        return created
    company_fields = {f['name']:f for f in company_schema}
    new_companies = []
    for j in pending.values():
        r = {'公司名称':j['company'],'数据来源':j['url'],'备注':f'共享岗位回收；批次 {batch_name}；公司信息待核验。'}
        if '待核验' in [o['name'] for o in company_fields.get('信息状态',{}).get('options',[])]:
            r['信息状态'] = ['待核验'] if company_fields['信息状态'].get('multiple') else '待核验'
        new_companies.append(r)
    for row in create(route['company_table_id'],new_companies,'companies'):
        index_company(row,indices)
    payloads=[]
    for j in live_plan['additions']:
        rid = resolve_company(j['company'],indices)
        if not rid:
            raise RuntimeError('Company association unresolved after company creation')
        payloads.append(project_facts(j,job_fields(j,rid,batch_name),schema))
    created = create(route['job_table_id'],payloads,'jobs')
    result = {'added':len(created),'company_additions':len(new_companies),'stats':live_plan['stats']}
    dump(journal/'result.json',result)
    return result

def run(args):
    if args.command == 'append':
        config = load_config()
        result = append_plan(json.loads(Path(args.plan).read_text()),config['shared_pool'],args.journal,execute=args.execute)
        if args.execute:
            print(json.dumps(result,ensure_ascii=False))
        return 0
    if args.command == 'snapshot':
        config = load_config()
        route = config['shared_pool']
        verify_pool_access(config)
        companies = read_all(route['base_token'], route['company_table_id'])
        lookup = {r['record_id']:text(r.get('公司名称')) for r in companies}
        rows = read_all(route['base_token'], route['job_table_id'])
        jobs = [normalize_job(r,lookup) for r in rows]
        dump(args.output, {'complete':True,'read_at':datetime.now().astimezone().isoformat(),'route':route,'jobs':jobs})
        print(json.dumps({'complete':True,'pool_checked':True,'count':len(jobs),'output':args.output},ensure_ascii=False))
        return 0
    snapshot = json.loads(Path(args.snapshot).read_text())
    if snapshot.get('complete') is not True:
        raise ValueError('A complete pool snapshot is required')
    if args.command == 'search':
        profile = json.loads(Path(args.profile).read_text())
        result = search_jobs(snapshot['jobs'], profile)
        dump(args.output, {'pool_read_at':snapshot.get('read_at'),'count':len(result),'requires_revalidation':True,'jobs':result})
        print(json.dumps({'pool_candidates':len(result),'output':args.output},ensure_ascii=False))
    else:
        jobs = json.loads(Path(args.jobs).read_text())
        if isinstance(jobs,dict):
            jobs = jobs.get('jobs',jobs.get('ready', []))
        result = build_plan(jobs, snapshot['jobs'])
        dump(args.output,result)
        print(json.dumps(result['stats'],ensure_ascii=False))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    snapshot = sub.add_parser('snapshot', help='Read the complete live pool, without changing it')
    snapshot.add_argument('--output', required=True)
    search = sub.add_parser('search', help='Search a full pool snapshot; results still require live verification')
    search.add_argument('--snapshot', required=True)
    search.add_argument('--profile', required=True)
    search.add_argument('--output', required=True)
    plan = sub.add_parser('plan', help='Deduplicate common job facts against a complete pool snapshot')
    plan.add_argument('--jobs', required=True)
    plan.add_argument('--snapshot', required=True)
    plan.add_argument('--output', required=True)
    append = sub.add_parser('append', help='Append a reviewed plan; dry-run unless --execute is supplied')
    append.add_argument('--plan',required=True)
    append.add_argument('--journal',required=True)
    append.add_argument('--execute',action='store_true')
    args = parser.parse_args(argv)
    try:
        return run(args)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, subprocess.SubprocessError) as exc:
        print(json.dumps({'status':'blocked','error':str(exc),'pool_checked':False,
                          'next_step':'补齐并核对团队配置；或由当前任务明确允许不使用共享池后再外搜。'},ensure_ascii=False))
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
