"""Run the distributed test suites without editing source or release hashes."""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    suites = [('repository', [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'])]
    for skill in sorted((ROOT / 'skills').iterdir()):
        for relative in ['tests', 'scripts']:
            directory = skill / relative
            if directory.is_dir() and list(directory.glob('test_*.py')):
                suites.append((skill.name + '/' + relative, [sys.executable, '-m', 'unittest', 'discover', '-s', str(directory), '-v']))
        node = sorted((skill / 'scripts').glob('*.test.mjs'))
        if node:
            suites.append((skill.name + '/node', ['node', '--test', *map(str, node)]))
    report = []
    for name, command in suites:
        result = subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        counts = re.findall(r'Ran (\d+) tests?', result.stdout)
        node_counts = re.findall(r'(?:# |ℹ )tests (\d+)', result.stdout)
        total = int((counts or node_counts or ['0'])[-1])
        row = {'suite': name, 'tests': total, 'exit_code': result.returncode}
        report.append(row)
        print(json.dumps(row), flush=True)
        if result.returncode:
            print(result.stdout, flush=True)
    print(json.dumps({'test_total': sum(r['tests'] for r in report), 'suites': len(report), 'failed': [r['suite'] for r in report if r['exit_code']]}), flush=True)
    return int(any(row['exit_code'] for row in report))


if __name__ == '__main__':
    raise SystemExit(main())
