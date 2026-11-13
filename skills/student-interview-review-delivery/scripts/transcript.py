"""Read transcript evidence and check source-to-question-to-review coverage (stdlib only)."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile
from urllib.parse import urlsplit

STAMP = r'\d{1,2}:\d{2}(?::\d{2})?(?:[.,]\d{1,3})?'


def milliseconds(value):
    bits = value.replace(',', '.').split(':')
    return int(sum(float(v) * 60**i for i, v in enumerate(reversed(bits))) * 1000)


def normalize(text, source, transport_complete=False, duration_ms=None):
    turns = []; metadata_lines = []; in_keywords = False
    patterns = [rf'^\[({STAMP})\]\s*([^：:\n]+)[：:]\s*(.*)$',
                rf'^([^\[\n]+?)\s+({STAMP})\s*[：:]?\s*(.*)$',
                rf'^\[([^\]]+)\]\s*\[({STAMP})\]\s*(.*)$']
    for line_no, line in enumerate(text.splitlines(), 1):
        if not line.strip(): continue
        if not turns:
            is_header = re.match(r'^(?:会议|时间|记录ID|录制文件ID|创建者|来源|Keywords)[：:]', line.strip())
            is_date_header = re.match(r'^\d{4}-\d{2}-\d{2}[^\n]*\|[^\n]*(?:min|\d+s|分钟|小时)', line.strip())
            if is_header or is_date_header:
                metadata_lines.append(line)
                in_keywords = line.strip().startswith('Keywords:')
                continue
            if in_keywords and not any(re.match(pattern, line.strip()) for pattern in patterns):
                metadata_lines.append(line); continue
        matched = False
        for index, pattern in enumerate(patterns):
            m = re.match(pattern, line.strip())
            if not m: continue
            stamp, speaker = (m[1], m[2]) if index == 0 else (m[2], m[1])
            turns.append({'id': f'T{len(turns)+1:04d}', 'speaker': speaker.strip(),
                          'timestamp_ms': milliseconds(stamp), 'text': m[3].strip(), 'line': line_no})
            matched = True; break
        if not matched:
            m = re.match(r'^([^：:\n]{1,40})[：:]\s*(.+)$', line.strip())
            timed = any(t['timestamp_ms'] is not None for t in turns)
            known_speaker = m and (m[1] in {t['speaker'] for t in turns} or re.fullmatch(r'学生|面试官|导师|说话人\s*\d+|interviewer|candidate', m[1], re.I))
            if m and (not timed or known_speaker) and m[1] not in ('AI 摘要', 'AI摘要', '摘要', '总结'):
                turns.append({'id': f'T{len(turns)+1:04d}', 'speaker': m[1], 'timestamp_ms': None, 'text': m[2], 'line': line_no})
            elif turns: turns[-1]['text'] = (turns[-1]['text'] + '\n' + line).strip()
            else: turns.append({'id': 'T0001', 'speaker': '未知发言人', 'timestamp_ms': None, 'text': line, 'line': line_no})
    document = make_document(turns, text.encode(), source, transport_complete, duration_ms)
    document['metadata_lines'] = metadata_lines
    return document


def make_document(turns, raw, source, complete, duration_ms=None):
    issues = []
    if not complete: issues.append('transport_unverified')
    if not turns or not any(t['text'].strip() for t in turns): issues.append('empty_transcript')
    speakers = {t['speaker'] for t in turns}
    if any(s in ('未知发言人', '', 'unknown') for s in speakers): issues.append('speaker_unresolved')
    if len(speakers) < 2: issues.append('single_speaker')
    times = [t['timestamp_ms'] for t in turns if t['timestamp_ms'] is not None]
    if len(times) != len(turns): issues.append('missing_timestamps')
    if times != sorted(times): issues.append('timestamp_order')
    # A tail gap is a review prompt, not proof of missing audio (silence is possible).
    if duration_ms and (not times or duration_ms - max(times) > max(60000, duration_ms*.1)): issues.append('tail_gap')
    return {'version': 1, 'source': source, 'sha256': hashlib.sha256(raw).hexdigest(),
            'transport_complete': complete, 'duration_ms': duration_ms, 'issues': issues, 'turns': turns}


def read_tencent(path):
    raw = Path(path).read_bytes(); data = json.loads(raw)
    if (data.get('source') != 'tencent' or data.get('transport_complete') is not True
            or not isinstance(data.get('page_count'), int) or data['page_count'] < 1):
        raise ValueError('Tencent pagination is not complete')
    turns = []
    for item in data['turns']:
        turns.append({**item, 'id': f'T{len(turns)+1:04d}'})
    doc = make_document(turns, raw, 'tencent', True, data.get('duration_ms'))
    doc['page_count'] = data.get('page_count'); doc['record_id'] = data.get('record_id')
    return doc


def read_feishu(url, output_dir, cli='lark-cli'):
    parsed = urlsplit(url)
    if parsed.scheme != 'https' or not any(parsed.hostname and parsed.hostname.endswith('.'+d) for d in ('feishu.cn', 'larksuite.com')):
        raise ValueError('Expected an authorized Feishu/Lark Minutes URL')
    parts = parsed.path.strip('/').split('/')
    if len(parts) != 2 or parts[0] != 'minutes' or not re.fullmatch(r'[A-Za-z0-9_-]+', parts[1]):
        raise ValueError('URL is not a Minutes resource; use the matching document/note route')
    Path(output_dir).mkdir(parents=True, exist_ok=True, mode=0o700)
    fetch_dir = Path(tempfile.mkdtemp(prefix='fetch-', dir=output_dir))
    result = subprocess.run([cli, 'minutes', '+detail', '--minute-tokens', parts[1], '--transcript',
                             '--as', 'user', '--output-dir', '.'], cwd=fetch_dir, capture_output=True, text=True, timeout=120)
    if result.returncode: raise ValueError('Minutes read failed; inspect CLI permission/login error locally')
    payload = json.loads(result.stdout)
    entries = payload.get('minutes', payload.get('data', {}).get('minutes', []))
    if len(entries) != 1 or entries[0].get('minute_token') != parts[1]: raise ValueError('Minutes target mismatch')
    filename = entries[0].get('artifacts', {}).get('transcript_file')
    if not filename: raise ValueError('No transcript_file; summary is not a transcript')
    path = (fetch_dir / filename).resolve()
    if not path.is_relative_to(fetch_dir.resolve()): raise ValueError('Transcript file outside requested output directory')
    raw = path.read_bytes()
    doc = normalize(raw.decode('utf-8-sig'), 'feishu', True)
    doc['sha256'] = hashlib.sha256(raw).hexdigest()
    return doc


def validate_coverage(doc, inventory, review):
    errors = []
    if inventory.get('transcript_sha256') != doc['sha256']: errors.append('逐字稿指纹不匹配，问题索引已过期')
    check = inventory.get('input_review', {})
    if check.get('confirmed') is not True: errors.append('输入完整性尚未人工核对')
    unresolved = [issue for issue in doc.get('issues', []) if not check.get('resolutions', {}).get(issue)]
    if unresolved: errors.append('输入异常尚无逐项解释：' + ', '.join(unresolved))
    if 'empty_transcript' in doc.get('issues', []): errors.append('逐字稿为空')
    if inventory.get('scope') not in ('full', 'partial'): errors.append('必须声明 full 或 partial 范围')
    if inventory.get('scope') == 'full' and (not doc.get('transport_complete') or check.get('limitations')):
        errors.append('输入未完整或仍有限制，不能标为整场 full')
    roles = inventory.get('roles', {})
    actual_roles = {roles.get(t['speaker']) for t in doc['turns']}
    if not {'interviewer', 'candidate'} <= actual_roles and not (inventory.get('scope') == 'partial' and check.get('limitations')): errors.append('未确认原稿中面试官与学生双方角色')
    turns = {t['id']: t for t in doc['turns']}
    audits = inventory.get('audits', [])
    audit_map = {a['turn_id']: a for a in audits}
    if len(audit_map) != len(audits): errors.append('原文段落核对重复')
    for turn_id in sorted(set(audit_map) - set(turns)): errors.append('核对记录引用不存在段落：' + turn_id)
    questions = inventory.get('questions', [])
    ids = [q['id'] for q in questions]
    question_turns = {q['id']:q.get('turn_id') for q in questions}
    if not questions: errors.append('没有已核对的实际问题，不能验收逐题复盘')
    if len(set(ids)) != len(ids): errors.append('问题编号重复')
    cards = re.findall(r'^###\s+(Q\d+)｜', review, re.M)
    if len(cards) != len(set(cards)): errors.append('复盘题卡编号重复')
    blocks = {m[1]: m[2] for m in re.finditer(r'^###\s+(Q\d+)｜([^\n]*\n.*?)(?=^###\s+Q\d+｜|^##\s|\Z)', review, re.M | re.S)}
    for turn_id, turn in turns.items():
        audit = audit_map.get(turn_id)
        if not audit: errors.append(f'{turn_id} 原文尚未核对'); continue
        role = roles.get(turn['speaker'])
        if role not in ('interviewer', 'candidate', 'mentor', 'observer'):
            if (inventory.get('scope') == 'partial' and check.get('limitations')
                    and audit.get('unresolved_reason') and not audit.get('question_ids')): continue
            errors.append(f'{turn_id} 说话人角色未确认'); continue
        qids = audit.get('question_ids', [])
        if not qids and not audit.get('reason'): errors.append(f'{turn_id} 无问题但未说明原因')
        if any(qid not in ids for qid in qids): errors.append(f'{turn_id} 引用了不存在的问题')
        if any(question_turns.get(qid) != turn_id for qid in qids): errors.append(f'{turn_id} 错用了其他段落的问题编号')
        remaining = turn['text']
        for q in questions:
            if q.get('turn_id') == turn_id and q.get('quote'):
                remaining = remaining.replace(q['quote'], '', 1)
        if role == 'interviewer' and re.search(r'[？?]|请(?:介绍|解释|说明)|为什么|怎么|如何|结果呢', remaining) and not audit.get('non_question_evidence'):
            errors.append(f'{turn_id} 原文仍有未覆盖的疑似问题；补索引或具体排除依据')
        if role == 'interviewer' and re.search(r'[？?]|请(?:介绍|解释|说明)|为什么|怎么|如何', turn['text']) and not qids and not audit.get('non_question_evidence'):
            errors.append(f'{turn_id} 疑似提问未入索引；需补问题或具体排除依据')
    for q in questions:
        qid = q['id']; turn = turns.get(q.get('turn_id'))
        if not re.fullmatch(r'Q\d+', qid): errors.append('问题编号格式错误：' + qid)
        if not turn or not q.get('quote') or q['quote'] not in turn['text']:
            errors.append(f'{qid} 提问原文或段落不匹配'); continue
        if qid not in audit_map.get(turn['id'], {}).get('question_ids', []): errors.append(f'{qid} 未关联原文核对记录')
        role = roles.get(turn['speaker'])
        disposition = q.get('disposition', 'reviewed')
        if disposition in ('excluded', 'out_of_scope'):
            if not q.get('reason'): errors.append(f'{qid} 排除须有具体原因')
            if disposition == 'out_of_scope' and inventory.get('scope') != 'partial': errors.append(f'{qid} 整场复盘不能将问题列为范围外')
            continue
        if role != 'interviewer': errors.append(f'{qid} 来源角色不是已确认面试官')
        rid = q.get('review_id')
        if rid not in blocks: errors.append(f'{qid} 漏题：缺少对应复盘题卡 {rid}')
        elif qid not in re.findall(r'Q\d+', re.search(r'^\*\*来源问题：\*\*(.*)$', blocks[rid], re.M)[1] if re.search(r'^\*\*来源问题：\*\*(.*)$', blocks[rid], re.M) else ''):
            errors.append(f'{qid} 未在 {rid} 的来源问题中出现')
    mapped = {q.get('review_id') for q in questions if q.get('disposition', 'reviewed') == 'reviewed'}
    for rid in set(cards) - mapped: errors.append(f'{rid} 题卡无原稿问题映射')
    return errors


def redact_contacts(text):
    text = re.sub(r'(?<!\d)1[3-9]\d{9}(?!\d)', '[手机号已隐去]', text)
    text = re.sub(r'(?<![A-Za-z0-9_.+-])[A-Za-z0-9][\w.+-]*@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+', '[邮箱已隐去]', text)
    return re.sub(r'(?<!\d)\d{17}[\dXx](?!\d)', '[证件号已隐去]', text)


def validate_original_exchanges(doc, inventory, review):
    """Compare displayed original exchanges with source turns, not summaries."""
    errors = []
    turns = doc['turns']; positions = {t['id']: i for i, t in enumerate(turns)}
    exchanges = inventory.get('exchanges', {})
    blocks = {m[1]: m[2] for m in re.finditer(r'^###\s+(Q\d+)｜([^\n]*\n.*?)(?=^###\s+Q\d+｜|^##\s|\Z)', review, re.M | re.S)}
    for rid, block in blocks.items():
        ranges = exchanges.get(rid)
        if not ranges:
            errors.append(f'{rid} 缺少原始问答范围 exchanges'); continue
        expected = []; previous = -1
        for bounds in ranges:
            if (not isinstance(bounds, list) or len(bounds) != 2
                    or any(tid not in positions for tid in bounds)):
                errors.append(f'{rid} 原始问答范围无效'); continue
            start, end = (positions[tid] for tid in bounds)
            if start > end or start <= previous:
                errors.append(f'{rid} 原始问答范围倒序或重复'); continue
            expected.extend(turns[start:end + 1]); previous = end
        expected_ids = [t['id'] for t in expected]
        questions = [q for q in inventory.get('questions', [])
                     if q.get('disposition', 'reviewed') == 'reviewed' and q.get('review_id') == rid]
        for q in questions:
            if q['turn_id'] not in expected_ids:
                errors.append(f'{rid} 原始问答缺少来源问题 {q["id"]}')
        unanswered = questions and all(q.get('no_answer_reason') for q in questions)
        if not unanswered and not any(inventory.get('roles', {}).get(t['speaker']) == 'candidate' for t in expected):
            errors.append(f'{rid} 原始问答未保留候选人发言')
        field = re.search(r'^\*\*原始问答：\*\*[^\S\n]*(.*?)(?=^\*\*[^*\n]+：\*\*|\Z)', block, re.M | re.S)
        raw = field[1] if field else ''
        found = list(re.finditer(r'^> \[(T\d+)\][^\n]*\n(.*?)(?=^> \[T\d+\]|\Z)', raw, re.M | re.S))
        if [m[1] for m in found] != expected_ids:
            errors.append(f'{rid} 原始问答段落缺失、倒序或重复')
        displayed = {m[1]: re.sub(r'^> ?', '', m[2], flags=re.M).strip() for m in found}
        for turn in expected:
            actual = re.sub(r'\s+', '', displayed.get(turn['id'], ''))
            original = re.sub(r'\s+', '', redact_contacts(turn['text']))
            if actual != original:
                errors.append(f'{rid} {turn["id"]} 原文不一致；摘要、删句或改写不能代替原答')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    ingest = sub.add_parser('prepare'); ingest.add_argument('--source', choices=['feishu', 'tencent', 'local'], required=True)
    ingest.add_argument('--input', required=True); ingest.add_argument('--out-dir', type=Path, required=True)
    ingest.add_argument('--complete', action='store_true', help='local export confirmed complete by source inspection')
    ingest.add_argument('--duration-ms', type=int)
    check = sub.add_parser('check'); check.add_argument('--transcript', type=Path, required=True)
    check.add_argument('--inventory', type=Path, required=True); check.add_argument('--review', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == 'prepare':
            args.out_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
            if args.source == 'feishu': doc = read_feishu(args.input, args.out_dir)
            elif args.source == 'tencent': doc = read_tencent(args.input)
            else: doc = normalize(Path(args.input).read_text(encoding='utf-8-sig'), 'local', args.complete, args.duration_ms)
            target = args.out_dir/'transcript.json'; target.write_text(json.dumps(doc, ensure_ascii=False, indent=2)); target.chmod(0o600)
            draft = {'transcript_sha256': doc['sha256'], 'scope':'full',
                     'roles':{t['speaker']:'unknown' for t in doc['turns']},
                     'audits':[{'turn_id':t['id'],'question_ids':[], 'reason':''} for t in doc['turns']],
                     'questions':[], 'input_review':{'confirmed':False,'limitations':[], 'resolutions':{}}}
            draft_path = args.out_dir/'question_inventory.draft.json'
            # Preserve an existing manual audit; never replace it on a retry.
            if not draft_path.exists():
                draft_path.write_text(json.dumps(draft, ensure_ascii=False, indent=2)); draft_path.chmod(0o600)
            print(json.dumps({'status':'prepared', 'turns':len(doc['turns']), 'issues':doc['issues'], 'file':str(target)}, ensure_ascii=False)); return 0
        doc = json.loads(args.transcript.read_text()); inventory = json.loads(args.inventory.read_text()); review = args.review.read_text()
        errors = validate_coverage(doc, inventory, review) + validate_original_exchanges(doc, inventory, review)
        print(json.dumps({'status':'invalid' if errors else 'coverage_checked', 'errors':errors}, ensure_ascii=False)); return int(bool(errors))
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        print(json.dumps({'status':'error', 'error':type(exc).__name__, 'message':'读取或结构检查失败；保留原件，核对当前来源与本地错误。'}, ensure_ascii=False)); return 2


if __name__ == '__main__': raise SystemExit(main())
