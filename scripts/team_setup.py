"""Install complete skills and configure member-owned access to team resources.

No command writes to Feishu. Live checks only inspect the existing login.
"""
import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = Path.home() / '.config/jihui-skills/team.json'
SECRET_KEYS = {'access_token', 'refresh_token', 'tenant_access_token', 'user_access_token', 'app_secret', 'client_secret', 'api_key', 'password', 'cookie', 'cookies'}
LOCAL_SKILLS = {'auditing-candidate-resumes', 'building-resume-interview-stories', 'recording-processing', 'student-job-content', 'jihui-interview', 'pengyouquan-copywriting', 'xiaohongshu-image-renderer', 'tencent-meeting-cloud-export', 'job-sales-advisor', 'visual-document-delivery'}
DEPENDENCIES = {'campus-recommend': ['campus-job-matching'], 'job-content-publisher': ['xiaohongshu-image-renderer'], 'delivering-student-career-plans': ['visual-document-delivery']}


def emit(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))


def check_secrets(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if key.lower() in SECRET_KEYS:
                raise ValueError('Configuration must contain resource locations, not credentials: ' + key)
            check_secrets(item)
    elif isinstance(value, list):
        for item in value:
            check_secrets(item)


def read_config(path):
    if not path.is_file():
        raise ValueError('Configuration is missing. Run team_setup.py init with the private team profile.')
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (ValueError, UnicodeError):
        raise ValueError('Configuration must be a UTF-8 JSON object.') from None
    if not isinstance(data, dict):
        raise ValueError('Configuration must be a JSON object.')
    check_secrets(data)
    return data


def write_private(path, data, *, exclusive=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | (os.O_EXCL if exclusive else os.O_TRUNC)
    descriptor = os.open(path, flags, 0o600)
    with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    path.chmod(0o600)


def init_config(args):
    data = read_config(args.team_profile) if args.team_profile else read_config(ROOT / 'config/team.example.json')
    data = copy.deepcopy(data)
    data['version'] = 1
    data['expected_user_open_id'] = ''
    data['expected_profile'] = ''
    # Sharing consent belongs to each member, not to a team resource profile.
    data.pop('role_prep_delivery', None)
    # A team profile must not transfer another person's local directories.
    data['workspace'] = {'student_root': str(args.student_root or ''), 'knowledge_root': str(args.knowledge_root or ''), 'output_root': str(args.output_root or '')}
    write_private(args.output, data, exclusive=True)
    return {'created': True, 'config': str(args.output), 'next_step': 'Log in to your own lark-cli account, then run team_setup.py bind-user --config <member config>.'}


def authenticated_member():
    if not shutil.which('lark-cli'):
        raise ValueError('lark-cli is unavailable. Install it and log in to your own account first.')
    result = subprocess.run(['lark-cli', 'auth', 'status', '--verify', '--json'], capture_output=True, text=True, timeout=30)
    if result.returncode:
        raise ValueError('lark-cli could not verify the current login; inspect login locally.')
    try:
        data = json.loads(result.stdout)
        user = data['identities']['user']
        identity = user['openId']
    except (ValueError, KeyError, TypeError):
        raise ValueError('lark-cli did not return a verified user identity.') from None
    if not identity or user.get('verified') is not True:
        raise ValueError('The current user login is not verified.')
    return identity, data.get('profile') or data.get('appId') or ''


def bind_user(args):
    data = read_config(args.config)
    identity, profile = authenticated_member()
    if data.get('expected_user_open_id') and data['expected_user_open_id'] != identity:
        raise ValueError('The configured member and current login differ. Preserve this config and create a separate member config.')
    data['expected_user_open_id'] = identity
    data['expected_profile'] = profile
    write_private(args.config, data)
    return {'bound': True, 'config': str(args.config), 'identity_values_redacted': True, 'next_step': 'Run team_setup.py doctor --config <member config> --live.'}


def get(data, dotted):
    for key in dotted.split('.'):
        if not isinstance(data, dict):
            return None
        data = data.get(key)
    return data


def doctor(args):
    selected = args.skill or 'campus-job-matching'
    if not (ROOT / 'skills' / selected / 'SKILL.md').is_file() or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', selected):
        raise ValueError('Unknown skill. Use a skill name from docs/SKILL_CATALOG.md.')
    data = {} if not args.config.exists() and selected in LOCAL_SKILLS else read_config(args.config)
    missing = []
    if selected not in LOCAL_SKILLS:
        for key in ['expected_user_open_id', 'expected_profile']:
            if not get(data, key):
                missing.append(key)
        resource_groups = {
            'job-content-publisher': ['feishu.content_base_url'],
            'personal-todo-control': ['feishu.todo_url', 'feishu.service_base_url'],
            'multi-source-todo-control': ['feishu.service_base_url', 'feishu.students_root_url'],
        }
        resources = resource_groups.get(selected, ['feishu.students_root_url', 'wiki.students_parent_node_token'])
        if not (args.target_url or any(get(data, key) for key in resources)):
            missing.append(resources[0])
    if selected in {'campus-job-matching', 'campus-recommend'} and get(data, 'shared_pool.enabled') is not False:
        keys = ['shared_pool.base_token', 'shared_pool.job_table_id', 'shared_pool.company_table_id', 'shared_pool.wiki_node_token']
        if data.get('version') is not None:
            keys.append('shared_pool.owner_open_id')
        for key in keys:
            if not get(data, key):
                missing.append(key)
    if selected == 'job-sales-advisor' and not get(data, 'workspace.knowledge_root'):
        missing.append('workspace.knowledge_root')
    dependencies = {'python': True, 'lark-cli': bool(shutil.which('lark-cli'))}
    if selected not in LOCAL_SKILLS and not dependencies['lark-cli']:
        missing.append('tool:lark-cli')
    if selected == 'xiaohongshu-image-renderer':
        dependencies['node'] = bool(shutil.which('node'))
    live = 'not_requested'
    if args.live and not missing and selected not in LOCAL_SKILLS:
        identity, profile = authenticated_member()
        if identity != data.get('expected_user_open_id'):
            raise ValueError('The active user differs from the member configured for this workspace.')
        if profile != data.get('expected_profile'):
            raise ValueError('The active profile differs from the member configuration.')
        live = 'login_verified_only; target access and content must be read before the task'
    return {'ready': not missing, 'skill': selected, 'missing': missing, 'dependencies': dependencies, 'live': live, 'scope': 'Configuration and tool availability; not business or Feishu write acceptance.', 'next_step': 'Fill the listed resource fields or pass the explicit task target; bind-user sets only the current member identity.' if missing else 'Read the current target and permissions before performing the authorized task.'}


def source_files(directory):
    return {str(p.relative_to(directory)): p for p in directory.rglob('*') if p.is_file() and not any(x in {'__pycache__', 'node_modules', '.git'} for x in p.parts) and p.name != '.DS_Store' and not p.name.endswith(('.pyc', '.local.json'))}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def install(args):
    available = {p.name: p for p in (ROOT / 'skills').iterdir() if (p / 'SKILL.md').is_file()}
    names = sorted(set(args.skill or available))
    if not names or any(not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', name) or name not in available for name in names):
        raise ValueError('Unknown skill. Use a skill name from docs/SKILL_CATALOG.md.')
    names = sorted(set(names).union(*(DEPENDENCIES.get(name, []) for name in names)))
    destination = args.dest.expanduser().resolve()
    if destination == (ROOT / 'skills').resolve() or (ROOT / 'skills').resolve() in destination.parents:
        raise ValueError('The install destination must be separate from the release source.')
    receipt_path = destination / '.jihui-skills-install.json'
    receipt = json.loads(receipt_path.read_text()) if receipt_path.is_file() else {'version': 1, 'skills': {}}
    conflicts, writes, deletes, final_hashes = [], [], [], {}
    for name in names:
        member_directory = destination / name
        if member_directory.is_symlink():
            conflicts.append(name + ' (member-managed symlink)')
            continue
        current = source_files(available[name])
        old = receipt['skills'].get(name, {})
        final_hashes[name] = {rel: digest(path) for rel, path in current.items()}
        for rel, source in current.items():
            target = destination / name / rel
            if any(parent.is_symlink() for parent in target.parents if parent != destination) or target.is_symlink() or (target.exists() and not target.is_file()):
                conflicts.append(name + '/' + rel)
            elif target.is_file() and digest(target) != final_hashes[name][rel]:
                if not args.update or digest(target) != old.get(rel):
                    conflicts.append(name + '/' + rel)
                else:
                    writes.append((source, target))
            elif not target.exists():
                if rel in old:
                    conflicts.append(name + '/' + rel + ' (removed locally)')
                else:
                    writes.append((source, target))
        for rel, old_digest in old.items():
            if rel not in current:
                target = destination / name / rel
                if target.is_file() and digest(target) == old_digest and args.update:
                    deletes.append(target)
                elif target.exists():
                    conflicts.append(name + '/' + rel + ' (obsolete, locally changed)')
    if conflicts:
        return {'applied': False, 'skills': names, 'conflicts': conflicts, 'next_step': 'Preserve local edits and merge them explicitly; no files were changed.'}
    if args.apply:
        for source, target in writes:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        for target in deletes:
            target.unlink()
        receipt['skills'].update(final_hashes)
        write_private(receipt_path, receipt)
    return {'applied': args.apply, 'skills': names, 'conflicts': [], 'files_to_write': len(writes), 'managed_obsolete_files': len(deletes), 'next_step': 'Configure the private team profile and run doctor before the first Feishu task.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    init = sub.add_parser('init', help='Create a new private member configuration; never overwrite one')
    init.add_argument('--team-profile', type=Path)
    init.add_argument('--output', type=Path, default=Path(os.environ.get('JIHUI_SKILLS_CONFIG', str(DEFAULT_CONFIG))))
    for field in ['student-root', 'knowledge-root', 'output-root']:
        init.add_argument('--' + field, type=Path)
    bind = sub.add_parser('bind-user', help='Bind the current verified lark-cli user; no Feishu writes')
    check = sub.add_parser('doctor', help='Check configured inputs, without printing resource values')
    for command in [bind, check]:
        command.add_argument('--config', type=Path, default=Path(os.environ.get('JIHUI_SKILLS_CONFIG', str(DEFAULT_CONFIG))))
    check.add_argument('--skill')
    check.add_argument('--target-url')
    check.add_argument('--live', action='store_true')
    add = sub.add_parser('install', help='Preview a complete-skill install; --apply writes, --update preserves local edits')
    add.add_argument('--dest', type=Path, required=True)
    add.add_argument('--skill', action='append')
    add.add_argument('--apply', action='store_true')
    add.add_argument('--update', action='store_true')
    args = parser.parse_args()
    try:
        result = {'init': init_config, 'bind-user': bind_user, 'doctor': doctor, 'install': install}[args.command](args)
        emit(result)
        return 2 if result.get('conflicts') or result.get('ready') is False else 0
    except (ValueError, OSError, subprocess.TimeoutExpired) as error:
        message = str(error) if isinstance(error, ValueError) else 'Local operation failed; check the path, permissions, and tool availability.'
        emit({'ready': False, 'error': message, 'next_step': 'Run team_setup.py init for a new member config, or resolve the specific local error.'})
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
