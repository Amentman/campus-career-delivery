"""Preview or apply reviewed local Skill changes without replacing team additions.

Source paths and replacement values belong in a private JSON config. Capture the
baseline only after the corresponding public release has been independently read
back. This tool never commits, pushes, deletes public files, or grants access.
"""
import argparse
import difflib
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

EXCLUDED = {'.git', 'node_modules', '__pycache__', '.DS_Store', '.env', 'state', 'logs'}
TEXT_SUFFIXES = {'.md', '.py', '.json', '.yaml', '.yml', '.txt', '.html', '.css', '.js', '.mjs', '.cjs', '.svg', '.toml', '.sh'}
PRIVATE_PATTERNS = [
    re.escape('/' + 'Users' + '/'), re.escape('/' + 'home' + '/'),
    r'\bou_[A-Za-z0-9]{16,}\b', r'\bcli_[A-Za-z0-9]{12,}\b',
    r'\b(?:tbl|rec)[A-Za-z0-9]{12,}\b',
    r'https://[^\s)]+(?:feishu\.cn|larksuite\.com)/(?:wiki|docx|docs|base|drive)/[^\s)]+',
    r'(?:access_token|refresh_token|app_secret|api_key|password)\s*[=:]\s*[\'\"]?[^\s\'\"<>]{5,}',
    r'sk-[A-Za-z0-9_-]{16,}', r'gh[pousr]_[A-Za-z0-9]{20,}', r'Bearer\s+[A-Za-z0-9._-]{20,}',
]


def files(root):
    return {str(p.relative_to(root)): p for p in root.rglob('*') if p.is_file() and not p.is_symlink() and not any(part in EXCLUDED for part in p.relative_to(root).parts) and not p.name.endswith(('.pyc', '.local.json'))}


def sanitize(content, config):
    for item in sorted(config.get('replacements', []), key=lambda x: len(x['from']), reverse=True):
        if item['from']:
            content = content.replace(item['from'], item['to'])
    return content


def private_reason(content):
    for number, pattern in enumerate(PRIVATE_PATTERNS):
        if re.search(pattern, content, re.IGNORECASE):
            return 'private-data pattern ' + str(number + 1)
    return None


def capture(config, state, expected=None):
    state = Path(state)
    staged = state / 'baseline.next'
    if staged.exists():
        shutil.rmtree(staged)
    observed = {}
    for name, source in config['sources'].items():
        source = Path(source)
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', name) or not (source / 'SKILL.md').is_file():
            raise ValueError('Source is missing or invalid: ' + name)
        for relative, path in files(source).items():
            destination = staged / name / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            content = path.read_bytes()
            destination.write_bytes(content)
            observed[name + '/' + relative] = hashlib.sha256(content).hexdigest()
    if expected is not None and observed != expected:
        shutil.rmtree(staged)
        raise ValueError('Source changed after the accepted plan; preserve the old baseline and plan the new changes separately.')
    baseline = state / 'baseline'
    previous = state / 'baseline.previous'
    if previous.exists():
        shutil.rmtree(previous)
    if baseline.exists():
        baseline.rename(previous)
    staged.rename(baseline)
    state.chmod(0o700)
    for path in baseline.rglob('*'):
        path.chmod(0o700 if path.is_dir() else 0o600)
    (state / 'captured.json').write_text(json.dumps({'captured_at': datetime.now(timezone.utc).isoformat(), 'sources': sorted(config['sources'])}, indent=2))


def merge(public, baseline, incoming):
    with tempfile.TemporaryDirectory(prefix='skill-public-merge-') as temp:
        paths = [Path(temp) / name for name in ['public', 'baseline', 'incoming']]
        for path, value in zip(paths, [public, baseline, incoming]):
            path.write_text(value, encoding='utf-8')
        result = subprocess.run(['git', 'merge-file', '--stdout', *map(str, paths)], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout
    # Git may flag a team-guide insertion next to a changed rule as one hunk.
    # Accept only uniquely identifiable, unchanged old text; ambiguous edits stay
    # conflicts. This never unions two competing versions of the same rule.
    old_lines, new_lines = baseline.splitlines(keepends=True), incoming.splitlines(keepends=True)
    updated = public.splitlines(keepends=True)
    changes = list(difflib.SequenceMatcher(None, old_lines, new_lines, autojunk=False).get_opcodes())
    for kind, start, end, new_start, new_end in reversed(changes):
        if kind == 'equal':
            continue
        previous = old_lines[start:end]
        replacement = new_lines[new_start:new_end]
        if previous:
            matches = [index for index in range(len(updated) - len(previous) + 1) if updated[index:index + len(previous)] == previous]
            if len(matches) != 1:
                return None
            index = matches[0]
            updated[index:index + len(previous)] = replacement
        else:
            before = old_lines[max(0, start - 3):start]
            after = old_lines[start:start + 3]
            anchor = before + after
            matches = [index for index in range(len(updated) - len(anchor) + 1) if updated[index:index + len(anchor)] == anchor]
            if not anchor or len(matches) != 1:
                return None
            index = matches[0]
            updated[index:index + len(anchor)] = before + replacement + after
    return ''.join(updated)


def plan(config, repo, state):
    repo, state = Path(repo), Path(state)
    result = {'writes': {}, 'conflicts': [], 'changed_skills': [], 'unchanged_sources': 0, 'source_sha256': {}}
    for name, location in config['sources'].items():
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', name):
            result['conflicts'].append({'skill': name, 'reason': 'invalid skill name'})
            continue
        source, baseline = Path(location), state / 'baseline' / name
        if not (source / 'SKILL.md').is_file() or not (baseline / 'SKILL.md').is_file():
            result['conflicts'].append({'skill': name, 'reason': 'source or accepted baseline missing; inspect, do not infer deletion'})
            continue
        current, old = files(source), files(baseline)
        for relative in sorted(set(current) | set(old)):
            target = repo / 'skills' / name / relative
            if relative not in current:
                result['conflicts'].append({'skill': name, 'file': relative, 'reason': 'source removed; review public callers before removing any resource'})
                continue
            raw = current[relative].read_bytes()
            result['source_sha256'][name + '/' + relative] = hashlib.sha256(raw).hexdigest()
            before = old[relative].read_bytes() if relative in old else None
            if before == raw:
                result['unchanged_sources'] += 1
                continue
            if current[relative].suffix not in TEXT_SUFFIXES and current[relative].name not in {'LICENSE', '.gitignore'}:
                result['conflicts'].append({'skill': name, 'file': relative, 'reason': 'changed non-text asset needs explicit review'})
                continue
            try:
                incoming = sanitize(raw.decode('utf-8'), config)
                base = sanitize(before.decode('utf-8'), config) if before is not None else ''
            except UnicodeError:
                result['conflicts'].append({'skill': name, 'file': relative, 'reason': 'non-UTF-8 input needs review'})
                continue
            if private_reason(incoming):
                result['conflicts'].append({'skill': name, 'file': relative, 'reason': private_reason(incoming)})
                continue
            public = target.read_text(encoding='utf-8') if target.is_file() else None
            if public == incoming:
                continue
            if public is None:
                updated = incoming
            elif before is None:
                updated = None
            else:
                updated = merge(public, base, incoming)
            if updated is None or private_reason(updated):
                result['conflicts'].append({'skill': name, 'file': relative, 'reason': 'source/public conflict or private content; both versions preserved'})
                continue
            if updated != public:
                result['writes']['skills/' + name + '/' + relative] = updated
                result['changed_skills'].append(name)
    result['changed_skills'] = sorted(set(result['changed_skills']))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['capture', 'plan'])
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--state', type=Path, required=True)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    try:
        config = json.loads(args.config.read_text(encoding='utf-8'))
        if args.command == 'capture':
            pending = args.state / 'pending-plan.json'
            if (args.state / 'baseline').exists() and not pending.is_file():
                raise ValueError('A successful applied plan is required before advancing an existing baseline.')
            expected = json.loads(pending.read_text())['source_sha256'] if pending.is_file() else None
            capture(config, args.state, expected=expected)
            if pending.exists():
                pending.unlink()
            output = {'captured': True, 'sources': len(config['sources']), 'note': 'Only mark a baseline accepted after public readback.'}
        else:
            output = plan(config, args.repo, args.state)
            if args.apply and not output['conflicts']:
                for relative, content in output['writes'].items():
                    target = args.repo / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(content, encoding='utf-8')
                args.state.mkdir(parents=True, exist_ok=True)
                pending = args.state / 'pending-plan.json'
                pending.write_text(json.dumps({'source_sha256': output['source_sha256']}, indent=2))
                pending.chmod(0o600)
            output = {**output, 'writes': sorted(output['writes']), 'applied': args.apply and not output['conflicts']}
            output.pop('source_sha256', None)
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 2 if output.get('conflicts') else 0
    except (OSError, ValueError, KeyError) as error:
        print(json.dumps({'error': type(error).__name__, 'next_step': 'Inspect the private source mapping and baseline locally; no public data was deleted.'}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
