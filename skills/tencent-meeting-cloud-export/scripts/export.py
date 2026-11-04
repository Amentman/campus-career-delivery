"""Tencent Meeting web archive. Run browser phases inside browser-use's Python REPL.

Set TMEET_EXPORT_PHASE to inventory, transcripts, videos, or finalize.
For phases after inventory, set TMEET_EXPORT_STATE_DIR to the printed state_dir.
"""

import argparse
import csv
import json
import os
import re
import shutil
import subprocess
import time
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = 'https://meeting.tencent.com'
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36'
STATE_ROOT = Path(os.environ.get('TMEET_EXPORT_STATE_ROOT', str(Path.home() / '.codex' / 'tencent-meeting-export-state')))


def safe(value):
    value = re.sub(r'[\\/:*?"<>|\x00-\x1f]', '_', str(value or '未命名会议'))
    return re.sub(r'\s+', ' ', value).strip(' ._')[:70] or '未命名会议'


def private_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = path.with_name(path.name + '.tmp')
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as output:
        json.dump(value, output, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def activate_tencent_tab():
    if 'js' not in globals():
        raise RuntimeError('This phase must run inside browser-use')
    if 'meeting.tencent.com' in page_info().get('url', ''):
        return
    choices = [tab for tab in list_tabs() if 'meeting.tencent.com/' in tab.get('url', '')]
    if not choices:
        raise RuntimeError('No logged-in Tencent Meeting tab is available in Chrome; open the website in Chrome first')
    choices.sort(key=lambda tab: '/user-center/' not in tab.get('url', ''))
    switch_tab(choices[0]['targetId'])


def account_uid():
    cookies = cdp('Network.getCookies', urls=[BASE_URL]).get('cookies', [])
    uid = next((item['value'] for item in cookies if item['name'] == 'app_uid'), '')
    if not uid:
        raise RuntimeError('Tencent Meeting web login is missing')
    expected = os.environ.get('TMEET_EXPORT_EXPECT_UID')
    if expected and uid != expected:
        raise RuntimeError(f'Web account mismatch: expected {expected}, current {uid}')
    return uid


def inventory():
    activate_tencent_tab()
    uid = account_uid()
    goto_url(BASE_URL + '/user-center/meeting-record')
    wait_for_load()
    api_url = None
    for _ in range(5):
        api_url = js("performance.getEntriesByType('resource').map(x=>x.name).find(x=>x.includes('/meetlog/dashboard/my-record-list'))||null")
        if api_url:
            break
        wait_for_load()
    if not api_url or '/user-center/meeting-record' not in page_info().get('url', ''):
        raise RuntimeError('The logged-in My Record page did not load')
    rows = []
    total = None
    for page in range(1, 1001):
        body = {'begin_time': '0', 'end_time': '0', 'meeting_code': '', 'page_index': page,
                'page_size': 30, 'aggregationFastRecording': 0, 'cover_image_type': 'meetlog_list_webp',
                'record_type_v4': 'fast_record|cloud_record|user_upload|realtime_transcription|voice_record',
                'sort_by': 'uni_record_id', 'record_scene': 1}
        code = "(async()=>{let r=await fetch(URL,{method:'POST',credentials:'include',headers:{'content-type':'application/json'},body:BODY});return await r.json()})()"
        live_url = urllib.parse.urlsplit(api_url)
        query = urllib.parse.parse_qsl(live_url.query, keep_blank_values=True)
        query = [(key, str(int(time.time() * 1000)) if key == 'c_timestamp' else value) for key, value in query]
        fresh_url = urllib.parse.urlunsplit((live_url.scheme, live_url.netloc, live_url.path, urllib.parse.urlencode(query), live_url.fragment))
        response = js(code.replace('URL', json.dumps(fresh_url)).replace('BODY', json.dumps(json.dumps(body))))
        if response.get('code') != 0:
            raise RuntimeError(f'inventory page {page}: source code {response.get("code")}')
        total = int(response['data']['page_info']['count'])
        batch = response['data'].get('records', [])
        rows.extend(batch)
        if len(rows) >= total:
            break
        if not batch:
            raise RuntimeError('inventory pagination stopped early')
    if len(rows) != total or len({x['record_id'] for x in rows}) != total:
        raise RuntimeError('inventory total or uniqueness mismatch')
    owner = next((x.get('recorder_username') for x in rows if x.get('recorder_uid') == uid and x.get('recorder_username')), '')
    label = safe(owner or uid[-8:])
    day = datetime.now().strftime('%Y-%m-%d')
    dest_root = Path(os.environ.get('TMEET_EXPORT_DESKTOP', str(Path.home() / 'Desktop'))).expanduser()
    dest = Path(os.environ.get('TMEET_EXPORT_DEST', str(dest_root / f'腾讯会议云录制归档_{label}_{uid[-8:]}_{day}'))).expanduser().resolve()
    state = Path(os.environ.get('TMEET_EXPORT_STATE_DIR', str(STATE_ROOT / uid / day))).expanduser().resolve()
    state.mkdir(parents=True, exist_ok=True, mode=0o700)
    marker = state / 'run.json'
    if marker.exists():
        previous = json.loads(marker.read_text())
        if previous['uid'] != uid or Path(previous['dest']) != dest:
            raise RuntimeError('Existing export state belongs to another account or destination')
    if dest.exists() and not marker.exists():
        raise RuntimeError(f'Destination already exists without matching export state: {dest}')
    dest.mkdir(parents=True, exist_ok=True, mode=0o700)
    private_json(marker, {'uid': uid, 'label': label, 'dest': str(dest), 'day': day, 'source_count': total})
    private_json(state / 'inventory.json', rows)
    print(json.dumps({'account': label, 'uid': uid, 'source_count': total,
                      'types': dict(Counter(x.get('record_type') for x in rows)),
                      'dest': str(dest), 'state_dir': str(state)}, ensure_ascii=False), flush=True)


def load_state(browser_phase=True):
    value = os.environ.get('TMEET_EXPORT_STATE_DIR')
    if not value:
        raise RuntimeError('Set TMEET_EXPORT_STATE_DIR from the inventory output')
    state = Path(value).expanduser().resolve()
    run = json.loads((state / 'run.json').read_text())
    rows = json.loads((state / 'inventory.json').read_text())
    dest = Path(run['dest']).resolve()
    if len(rows) != run['source_count']:
        raise RuntimeError('Inventory count differs from the account marker')
    if browser_phase:
        activate_tencent_tab()
        if account_uid() != run['uid']:
            raise RuntimeError('Browser account changed since inventory; stop before downloading')
    return state, run, rows, dest


def saved_files_present(result, dest):
    files = result.get('files', []) if 'files' in result else [result]
    if not files or any(not item.get('relative_path') for item in files):
        return False
    for item in files:
        path = (dest / item['relative_path']).resolve()
        if not path.is_relative_to(dest) or not path.is_file() or path.stat().st_size != item.get('bytes'):
            return False
        if path.suffix.lower() == '.mp4':
            try:
                if duration(path) <= 0:
                    return False
            except RuntimeError:
                return False
    return True


def folder_for(dest, row):
    stamp = datetime.fromtimestamp(int(row['start_time']) / 1000).strftime('%Y-%m-%d_%H-%M')
    title = re.sub(r'^转写[_－-]', '', row.get('title', ''))
    return dest / f'{stamp}_{safe(title)}_{str(row["meeting_info"]["meeting_id"])[-8:]}'


def minutes_template(rows):
    ordered = sorted(rows, key=lambda x: x['record_type'] != 'realtime_transcription')
    for row in ordered[:8]:
        path = row.get('jump_path', '')
        if not path.startswith('/'):
            continue
        goto_url(BASE_URL + path)
        wait_for_load()
        for _ in range(3):
            template = js("performance.getEntriesByType('resource').map(x=>x.name).find(x=>x.includes('/minutes/detail')&&x.includes('start_pid=0'))||null")
            if template:
                query = urllib.parse.parse_qs(urllib.parse.urlsplit(template).query)
                if query.get('id', [''])[0] != row['record_id'] or query.get('recording_id', [''])[0] != str(int(row['uni_record_id']) + 1):
                    raise RuntimeError('Transcript recording ID mapping changed; inspect the live detail request')
                return template
            wait_for_load()
    raise RuntimeError('No transcript detail API appeared; inspect the current website before retrying')


def minutes_page(row, template, cursor=None):
    params = {'template': template, 'id': row['record_id'], 'mid': row['meeting_info']['meeting_id'],
              'rid': str(int(row['uni_record_id']) + 1), 'cursor': cursor}
    script = """(async()=>{let p=PARAMS;let u=new URL(p.template);
      u.searchParams.set('id',p.id);u.searchParams.set('meeting_id',p.mid);
      u.searchParams.set('recording_id',p.rid);u.searchParams.set('limit','500');
      u.searchParams.set('c_timestamp',String(Date.now()));
      if(p.cursor===null){u.searchParams.set('start_pid','0');u.searchParams.delete('pid')}
      else{u.searchParams.delete('start_pid');u.searchParams.set('pid',p.cursor);u.searchParams.set('fview','0')}
      return await (await fetch(u,{credentials:'include'})).json()})()"""
    return js(script.replace('PARAMS', json.dumps(params)))


def hms(milliseconds):
    seconds = max(0, int(milliseconds or 0) // 1000)
    return f'{seconds // 3600:02d}:{seconds // 60 % 60:02d}:{seconds % 60:02d}'


def export_transcripts():
    state, run, rows, dest = load_state()
    result_path = state / 'transcripts.json'
    results = json.loads(result_path.read_text()) if result_path.exists() else {}
    template = minutes_template(rows)
    for index, row in enumerate(rows, 1):
        if row['record_type'] not in ('cloud_record', 'realtime_transcription'):
            continue
        if account_uid() != run['uid']:
            raise RuntimeError('Browser account changed during transcript export')
        rid = row['record_id']
        prior = results.get(rid, {})
        if prior.get('status') in ('empty', 'denied') or (prior.get('status') == 'saved' and saved_files_present(prior, dest)):
            continue
        for attempt in range(3):
            try:
                paragraphs = {}
                cursor = None
                terminal = None
                for _ in range(30):
                    response = minutes_page(row, template, cursor)
                    code = response.get('code')
                    if code in (30002, 4049, 500249, 403):
                        # 30002 is an empty minutes result; 4049 explicitly means
                        # "录制转写不存在" for cloud recordings without a transcript.
                        terminal = {'status': 'empty' if code in (30002, 4049) else 'denied', 'code': code}
                        break
                    if code != 0:
                        raise RuntimeError(f'source code {code}')
                    batch = response.get('minutes', {}).get('paragraphs', [])
                    for item in batch:
                        paragraphs[item['pid']] = item
                    if not response.get('more'):
                        break
                    last = batch[-1]['pid'] if batch else None
                    if last is None or last == cursor:
                        raise RuntimeError('Transcript pagination made no progress')
                    cursor = last
                else:
                    raise RuntimeError('Transcript pagination exceeded 30 pages')
                if terminal:
                    results[rid] = {'status': terminal['status'], 'code': terminal['code']}
                    break
                lines = []
                chars = 0
                for para in sorted(paragraphs.values(), key=lambda x: int(x['pid'])):
                    content = ''.join(str(word.get('text', '')) for sentence in para.get('sentences', []) for word in sentence.get('words', []))
                    if content:
                        speaker = (para.get('speaker') or {}).get('user_name') or '未知发言人'
                        lines.append(f'[{hms(para.get("start_time"))}] {speaker}：{content}')
                        chars += len(content)
                if not lines:
                    results[rid] = {'status': 'empty', 'code': 0}
                    break
                folder = folder_for(dest, row)
                folder.mkdir(parents=True, exist_ok=True, mode=0o700)
                source_label = '视频' if row['record_type'] == 'cloud_record' else '独立转写'
                target = folder / f'逐字稿_{source_label}_{rid}.txt'
                header = f'会议：{row.get("title", "")}\n时间：{datetime.fromtimestamp(int(row["start_time"]) / 1000):%Y-%m-%d %H:%M:%S}\n记录ID：{rid}\n来源：{source_label}\n\n'
                tmp = target.with_name(target.name + '.tmp')
                fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
                with os.fdopen(fd, 'w', encoding='utf-8') as output:
                    output.write(header + '\n'.join(lines) + '\n')
                os.replace(tmp, target)
                results[rid] = {'status': 'saved', 'relative_path': str(target.relative_to(dest)),
                                'bytes': target.stat().st_size, 'paragraphs': len(paragraphs), 'chars': chars}
                break
            except Exception as exc:
                if attempt == 2:
                    results[rid] = {'status': 'error', 'reason': f'{type(exc).__name__}: {str(exc)[:200]}'}
                else:
                    time.sleep(attempt + 1)
        private_json(result_path, results)
        if index % 10 == 0 or index == len(rows):
            print('transcripts', index, '/', len(rows), dict(Counter(x['status'] for x in results.values())), flush=True)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


opener = urllib.request.build_opener(NoRedirect)


def cookie_for(url):
    parsed = urllib.parse.urlsplit(url)
    host = parsed.hostname or ''
    if parsed.scheme != 'https' or not (host == 'meeting.tencent.com' or host.endswith('.meeting.tencent.com')):
        raise RuntimeError('Unexpected download host; inspect before sending account cookies')
    cookies = cdp('Network.getCookies', urls=[url]).get('cookies', [])
    header = '; '.join(x['name'] + '=' + x['value'] for x in cookies)
    if not header:
        raise RuntimeError('Missing browser download cookies')
    return header


def source_size(url, cookie):
    request = urllib.request.Request(url, headers={'User-Agent': USER_AGENT, 'Referer': BASE_URL + '/',
                                                   'Cookie': cookie, 'Range': 'bytes=0-0'})
    with opener.open(request, timeout=30) as response:
        match = re.fullmatch(r'bytes 0-0/(\d+)', response.headers.get('Content-Range', ''))
        if response.status != 206 or not match:
            raise RuntimeError('Cannot determine source size')
        return int(match.group(1))


def duration(path):
    result = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                             '-of', 'default=noprint_wrappers=1:nokey=1', str(path)], capture_output=True, text=True)
    if result.returncode or not result.stdout.strip():
        raise RuntimeError(f'ffprobe could not read {path.name}')
    return round(float(result.stdout.strip()), 2)


def transfer_range(url, start, end, path, total, cookie):
    length = end - start + 1
    offset = path.stat().st_size if path.exists() else 0
    if offset > length:
        raise RuntimeError('Segment exceeds its source range')
    if offset < length:
        headers = {'User-Agent': USER_AGENT, 'Referer': BASE_URL + '/', 'Cookie': cookie,
                   'Range': f'bytes={start + offset}-{end}'}
        with opener.open(urllib.request.Request(url, headers=headers), timeout=90) as response:
            match = re.fullmatch(r'bytes (\d+)-(\d+)/(\d+)', response.headers.get('Content-Range', ''))
            if response.status != 206 or not match or (int(match.group(1)), int(match.group(2)), int(match.group(3))) != (start + offset, end, total):
                raise RuntimeError('Invalid segment range')
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
            with os.fdopen(fd, 'ab') as output:
                while chunk := response.read(1 << 20):
                    output.write(chunk)
    if path.stat().st_size != length:
        raise RuntimeError('Incomplete segment')


def download_file(url, target, expected, cookie):
    if expected <= 0:
        raise RuntimeError('Source file is empty')
    if target.exists():
        if target.stat().st_size != expected:
            raise RuntimeError('Existing file size differs from source')
        return expected, duration(target)
    part = target.with_name(target.name + '.part')
    offset = part.stat().st_size if part.exists() else 0
    if offset > expected:
        raise RuntimeError('Partial file exceeds source size')
    remaining = expected - offset
    if remaining > (16 << 20):
        count = min(8, max(2, (remaining + (4 << 20) - 1) // (4 << 20)))
        span = (remaining + count - 1) // count
        segments = []
        for index in range(count):
            start = offset + index * span
            end = min(expected - 1, start + span - 1)
            if start <= end:
                segments.append((start, end, target.with_name(f'{target.name}.range-{start}-{end}')))
        with ThreadPoolExecutor(max_workers=len(segments)) as pool:
            futures = [pool.submit(transfer_range, url, start, end, path, expected, cookie) for start, end, path in segments]
            for future in as_completed(futures):
                future.result()
        fd = os.open(part, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        with os.fdopen(fd, 'ab') as output:
            for _, _, path in segments:
                with path.open('rb') as source:
                    shutil.copyfileobj(source, output, length=1 << 20)
    elif offset < expected:
        headers = {'User-Agent': USER_AGENT, 'Referer': BASE_URL + '/', 'Cookie': cookie,
                   'Range': f'bytes={offset}-'}
        with opener.open(urllib.request.Request(url, headers=headers), timeout=90) as response:
            match = re.fullmatch(r'bytes (\d+)-(\d+)/(\d+)', response.headers.get('Content-Range', ''))
            if response.status != 206 or not match or (int(match.group(1)), int(match.group(3))) != (offset, expected):
                raise RuntimeError('Invalid download range')
            fd = os.open(part, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
            with os.fdopen(fd, 'ab') as output:
                while chunk := response.read(1 << 20):
                    output.write(chunk)
    if part.stat().st_size != expected:
        raise RuntimeError('Incomplete download')
    seconds = duration(part)
    os.replace(part, target)
    for path in target.parent.glob(target.name + '.range-*'):
        path.unlink()
    return expected, seconds


def video_links(row):
    script = """(async()=>{let u=new URL('/wemeet-cloudrecording-webapi/v1/download/meeting',location.origin);
      u.searchParams.set('id',ID);u.searchParams.set('source','owner');
      u.searchParams.set('need_multi_stream','1');u.searchParams.set('from_share','1');
      u.searchParams.set('enter_from','share');return await (await fetch(u,{credentials:'include'})).json()})()"""
    return js(script.replace('ID', json.dumps(row['uni_record_id'])))


def export_videos():
    state, run, rows, dest = load_state()
    result_path = state / 'videos.json'
    results = json.loads(result_path.read_text()) if result_path.exists() else {}
    videos = [row for row in rows if row['record_type'] in ('cloud_record', 'user_upload')]
    remaining_bytes = sum(int(row.get('size') or 0) for row in videos if results.get(row['record_id'], {}).get('status') != 'saved')
    if shutil.disk_usage(dest).free < remaining_bytes * 1.1:
        raise RuntimeError('Insufficient free space for the remaining source videos')
    for index, row in enumerate(videos, 1):
        if account_uid() != run['uid']:
            raise RuntimeError('Browser account changed during video export')
        rid = row['record_id']
        prior = results.get(rid, {})
        if prior.get('status') == 'denied' or (prior.get('status') == 'saved' and saved_files_present(prior, dest)):
            continue
        if row.get('allow_download') is False:
            results[rid] = {'status': 'denied', 'reason': 'Source disabled download'}
            private_json(result_path, results)
            continue
        for attempt in range(3):
            try:
                response = video_links(row)
                if response.get('code') in (403, 40304, 500249):
                    results[rid] = {'status': 'denied', 'code': response['code'],
                                    'reason': response.get('message') or 'Source denied download'}
                    break
                if response.get('code') != 0:
                    raise RuntimeError(f'source code {response.get("code")}')
                links = response.get('links') or []
                if not links or any(link.get('res_type') != 0 or not link.get('link') for link in links):
                    raise RuntimeError('Unsupported or missing source links')
                folder = folder_for(dest, row)
                folder.mkdir(parents=True, exist_ok=True, mode=0o700)
                files = []
                for number, link in enumerate(links, 1):
                    variants = [('视频', link['link'])]
                    for stream in link.get('multi_stream_recordings') or []:
                        if stream.get('link'):
                            label = {1: '共享屏幕', 2: '说话人'}.get(stream.get('stream_type'), '多流' + str(stream.get('stream_type')))
                            variants.append((label, stream['link']))
                    for variant_number, (label, url) in enumerate(variants, 1):
                        cookie = cookie_for(url)
                        size = source_size(url, cookie)
                        target = folder / f'{label}_{number}_{variant_number}_{rid}.mp4'
                        file_bytes, seconds = download_file(url, target, size, cookie)
                        files.append({'relative_path': str(target.relative_to(dest)), 'bytes': file_bytes,
                                      'duration_seconds': seconds})
                results[rid] = {'status': 'saved', 'files': files, 'bytes': sum(item['bytes'] for item in files)}
                break
            except Exception as exc:
                if attempt == 2:
                    results[rid] = {'status': 'error', 'reason': f'{type(exc).__name__}: {str(exc)[:200]}'}
                else:
                    time.sleep(attempt + 1)
        private_json(result_path, results)
        print('videos', index, '/', len(videos), row.get('title', ''), results[rid]['status'], flush=True)


def excel_safe(value):
    value = str(value or '')
    return "'" + value if value.startswith(('=', '+', '-', '@')) else value


def finalize():
    state, run, rows, dest = load_state(browser_phase=False)
    videos = json.loads((state / 'videos.json').read_text()) if (state / 'videos.json').exists() else {}
    transcripts = json.loads((state / 'transcripts.json').read_text()) if (state / 'transcripts.json').exists() else {}
    issues = []
    manifest = []
    file_count = 0
    byte_count = 0
    for row in rows:
        rid = row['record_id']
        if row['record_type'] not in ('cloud_record', 'user_upload', 'realtime_transcription'):
            issues.append(f'unsupported source type {row["record_type"]}: {rid}')
        video = videos.get(rid, {}) if row['record_type'] in ('cloud_record', 'user_upload') else {}
        transcript = transcripts.get(rid, {})
        if row['record_type'] in ('cloud_record', 'user_upload') and video.get('status') not in ('saved', 'denied'):
            issues.append(f'video {rid}: {video.get("status", "unprocessed")}')
        if row['record_type'] in ('cloud_record', 'realtime_transcription') and transcript.get('status') not in ('saved', 'empty', 'denied'):
            issues.append(f'transcript {rid}: {transcript.get("status", "unprocessed")}')
        if video.get('status') == 'saved' and not video.get('files'):
            issues.append(f'video {rid}: saved without files')
        if transcript.get('status') == 'saved' and not transcript.get('relative_path'):
            issues.append(f'transcript {rid}: saved without a file')
        paths = [item['relative_path'] for item in video.get('files', [])] + ([transcript['relative_path']] if transcript.get('relative_path') else [])
        for item in video.get('files', []) + ([transcript] if transcript.get('relative_path') else []):
            path = (dest / item['relative_path']).resolve()
            if not path.is_relative_to(dest) or not path.is_file() or path.stat().st_size != item['bytes']:
                issues.append(f'file validation failed: {item["relative_path"]}')
                continue
            if path.suffix.lower() == '.mp4' and (item.get('duration_seconds', 0) <= 0 or duration(path) <= 0):
                issues.append(f'video validation failed: {item["relative_path"]}')
            file_count += 1
            byte_count += item['bytes']
        manifest.append({
            '类型': '视频' if row['record_type'] == 'cloud_record' else '用户上传视频' if row['record_type'] == 'user_upload' else '独立转写' if row['record_type'] == 'realtime_transcription' else row['record_type'],
            '会议题目': excel_safe(row.get('title')),
            '开始时间': datetime.fromtimestamp(int(row['start_time']) / 1000).strftime('%Y-%m-%d %H:%M:%S'),
            '记录ID': rid,
            '来源链接': BASE_URL + row.get('jump_path', ''),
            '视频状态': video.get('status', ''),
            '逐字稿状态': transcript.get('status', ''),
            '本地相对路径': '\n'.join(paths),
            '说明': excel_safe(video.get('reason') or transcript.get('reason') or video.get('code') or transcript.get('code')),
        })
    partials = list(dest.rglob('*.part')) + list(dest.rglob('*.range-*'))
    if partials:
        issues.append(f'{len(partials)} incomplete transfer files remain')
    csv_path = dest / '归档清单.csv'
    with csv_path.open('w', encoding='utf-8-sig', newline='') as output:
        writer = csv.DictWriter(output, fieldnames=manifest[0] if manifest else ['记录ID'])
        writer.writeheader()
        writer.writerows(manifest)
    csv_path.chmod(0o600)
    video_counts = Counter(videos.get(row['record_id'], {}).get('status', 'unprocessed') for row in rows if row['record_type'] in ('cloud_record', 'user_upload'))
    transcript_counts = Counter(transcripts.get(row['record_id'], {}).get('status', 'unprocessed') for row in rows if row['record_type'] in ('cloud_record', 'realtime_transcription'))
    readme = (f'# 腾讯会议云录制归档\n\n账号：{run["label"]}（UID 末八位 {run["uid"][-8:]}）\n'
              f'导出核验：{datetime.now():%Y-%m-%d %H:%M}\n来源列表：{len(rows)} 条\n'
              f'视频状态：{dict(video_counts)}\n逐字稿状态：{dict(transcript_counts)}\n'
              f'文件数：{file_count}；总字节：{byte_count}\n\n'
              '同一会议的独立转写与视频详情文字可能不同，分别保存。来源为空或无权限的条目见归档清单。\n')
    readme_path = dest / 'README.md'
    readme_path.write_text(readme, encoding='utf-8')
    readme_path.chmod(0o600)
    summary = {'account': run['label'], 'source_count': len(rows), 'video_status': dict(video_counts),
               'transcript_status': dict(transcript_counts), 'verified_files': file_count,
               'bytes': byte_count, 'dest': str(dest), 'issues': issues}
    private_json(state / 'summary.json', summary)
    print(json.dumps(summary, ensure_ascii=False), flush=True)
    if issues:
        raise SystemExit(1)


def main():
    phase = os.environ.get('TMEET_EXPORT_PHASE', '')
    if phase == 'inventory':
        inventory()
    elif phase == 'transcripts':
        export_transcripts()
    elif phase == 'videos':
        export_videos()
    elif phase == 'finalize':
        finalize()
    else:
        raise SystemExit('Set TMEET_EXPORT_PHASE to inventory, transcripts, videos, or finalize')


def inspect_resume_state(state_dir):
    """Inspect explicit local state only; never write or contact a browser.

    This checks whether a saved run is internally consistent enough to resume.
    It does not validate the logged-in web account or media playback.
    """
    state = Path(state_dir).expanduser().resolve()
    issues = []
    report = {'status': 'blocked', 'source_count': 0, 'checked_saved_files': 0,
              'browser_checked': False, 'media_playback_checked': False, 'issues': issues}
    try:
        run = json.loads((state / 'run.json').read_text(encoding='utf-8'))
        rows = json.loads((state / 'inventory.json').read_text(encoding='utf-8'))
        if not isinstance(run, dict) or not isinstance(rows, list):
            raise ValueError('State files must contain an object and an inventory array')
        if not run.get('uid') or not isinstance(run.get('dest'), str):
            raise ValueError('Account marker or destination is missing')
        dest_path = Path(run['dest']).expanduser()
        if not dest_path.is_absolute():
            raise ValueError('Archive destination must be absolute')
        dest = dest_path.resolve()
        if not dest.is_dir():
            issues.append('Archive destination is unavailable')
        report['source_count'] = len(rows)
        if type(run.get('source_count')) is not int or len(rows) != run['source_count']:
            issues.append('Inventory count differs from the account marker')
        if any(not isinstance(row, dict) or not row.get('record_id') for row in rows):
            raise ValueError('Inventory has missing record identifiers')
        ids = {row['record_id'] for row in rows}
        if len(ids) != len(rows):
            issues.append('Inventory has duplicate record identifiers')
        for filename in ('videos.json', 'transcripts.json'):
            if not (state / filename).exists():
                continue
            progress = json.loads((state / filename).read_text(encoding='utf-8'))
            if not isinstance(progress, dict):
                raise ValueError('Progress file must be an object')
            if set(progress) - ids:
                issues.append('Progress contains records outside the inventory')
            for entry in progress.values():
                if not isinstance(entry, dict):
                    raise ValueError('Progress entries must be objects')
                if entry.get('status') != 'saved':
                    continue
                files = entry.get('files', [entry])
                if not isinstance(files, list) or not files:
                    issues.append('Saved entry has no file evidence')
                    continue
                for item in files:
                    if not isinstance(item, dict) or not isinstance(item.get('relative_path'), str):
                        issues.append('Saved file metadata is incomplete')
                        continue
                    path = (dest / item['relative_path']).resolve()
                    if (not path.is_relative_to(dest) or not path.is_file()
                            or type(item.get('bytes')) is not int or item['bytes'] < 1
                            or path.stat().st_size != item['bytes']):
                        issues.append('Saved file is missing, outside the archive, or has a different size')
                    else:
                        report['checked_saved_files'] += 1
    except (OSError, UnicodeError, ValueError, TypeError, KeyError):
        issues.append('Cannot read consistent run.json, inventory.json and progress files; restore the matching state before resuming')
    report['issues'] = list(dict.fromkeys(issues))
    if not report['issues']:
        report['status'] = 'ready_for_browser_resume'
    return report


def cli(argv=None):
    parser = argparse.ArgumentParser(
        description='Tencent Meeting archive helper. Download phases require the authorized browser-use runtime.',
        epilog='--check-state is read-only and offline. It does not prove web login, download permissions, media playback or export completion. '
               'Browser phases may activate Chrome; use only when the current task permits that route.')
    parser.add_argument('--check-state', type=Path, metavar='STATE_DIR',
                        help='inspect an explicitly selected local run for safe resumption; no browser access or writes')
    args = parser.parse_args(argv)
    if args.check_state is not None:
        report = inspect_resume_state(args.check_state)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if not report['issues'] else 2
    main()
    return 0


if __name__ == '__main__':
    raise SystemExit(cli())
