"""Build the pinned legacy runtime and run the author cinema-1 corpus locally."""
from datetime import datetime
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    patch = ROOT / 'baselines/filibuster-startup.patch'
    apply = ['git', '-C', str(ROOT / 'baselines/sources/filibuster'), 'apply', '--unidiff-zero']
    if subprocess.run(apply + ['--reverse', '--check', str(patch)], capture_output=True).returncode:
        subprocess.run(apply + ['--check', str(patch)], check=True)
        subprocess.run(apply + [str(patch)], check=True)
    out = ROOT / 'results/filibuster' / datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    out.mkdir(parents=True)
    with (out / 'build.log').open('w', encoding='utf-8') as log:
        subprocess.run(['docker', 'build', '-t', 'maturity-filibuster:20261021',
                        str(ROOT / 'baselines/filibuster')], check=True, stdout=log, stderr=subprocess.STDOUT)
    with (out / 'run.log').open('w', encoding='utf-8') as log:
        subprocess.run(['docker', 'run', '--rm', '--memory', '2g', '--cpus', '2',
                        '--mount', f'type=bind,source={ROOT},target=/workspace,readonly',
                        '--mount', f'type=bind,source={out},target=/out',
                        'maturity-filibuster:20261021', 'python', '/workspace/scripts/filibuster_container_run.py'],
                       check=True, stdout=log, stderr=subprocess.STDOUT)
    summary = json.loads((out / 'summary.json').read_text(encoding='utf-8'))
    print(out)
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
