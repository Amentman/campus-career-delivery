"""Record the complete public Skill files and prompt snapshots for a release."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP = {'.git', 'node_modules', '__pycache__', '.venv', '.DS_Store'}


def release_files(directory):
    return [p for p in directory.rglob('*') if p.is_file() and not any(part in SKIP for part in p.relative_to(directory).parts) and not p.name.endswith(('.pyc', '.local.json'))]


def build():
    skills = sorted(p.name for p in (ROOT / 'skills').iterdir() if (p / 'SKILL.md').is_file())
    target = ROOT / 'docs/SYNC_MANIFEST.json'
    data = json.loads(target.read_text()) if target.exists() else {}
    data.update({'version': '0.5.0', 'synced_at': datetime.now(timezone.utc).isoformat(), 'skill_count': len(skills), 'skills': skills,
        'files_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(release_files(ROOT / 'skills'))},
        'prompt_sha256': {str(p.relative_to(ROOT / 'prompts')): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(release_files(ROOT / 'prompts'))}})
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'skills': len(skills), 'skill_files': len(data['files_sha256']), 'prompt_files': len(data['prompt_sha256'])}))


if __name__ == '__main__':
    build()
