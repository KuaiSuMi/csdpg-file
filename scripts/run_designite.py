"""Analyze jsoup and a parameter-count boundary control with the built Designite jar."""
import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--java', default='java')
    parser.add_argument('--source', type=Path, help='Analyze this project instead of the reference/control cases')
    args = parser.parse_args()
    if args.source is not None and not args.source.is_dir():
        parser.error('--source must be an existing directory')
    jar = ROOT / 'baselines/sources/designite-java/target/DesigniteJava.jar'
    stamp = datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    out = ROOT / 'results/designite' / stamp
    out.mkdir(parents=True)
    summary = {'date': datetime.now(timezone.utc).isoformat(), 'jar_sha256': hashlib.sha256(jar.read_bytes()).hexdigest(), 'cases': {}}
    cases = [('project', args.source.resolve())] if args.source else [
        ('jsoup', ROOT / 'baselines/sources/jsoup/src/main/java'), ('control', ROOT / 'baselines/fixtures/designite')]
    for name, source in cases:
        dest = out / name
        dest.mkdir()  # The tool requires an existing empty directory and clears its contents.
        started = time.monotonic()
        with (out / (name + '.log')).open('w', encoding='utf-8') as log:
            subprocess.run([args.java, '-Dfile.encoding=UTF-8', '-jar', str(jar),
                            '-i', str(source), '-o', str(dest)], check=True,
                           stdout=log, stderr=subprocess.STDOUT)
        data = {}
        for filename in ('designCodeSmells.csv', 'implementationCodeSmells.csv', 'typeMetrics.csv', 'methodMetrics.csv'):
            with (dest / filename).open(encoding='utf-8-sig', newline='') as handle:
                data[filename] = list(csv.DictReader(handle))
        if not data['typeMetrics.csv']:
            raise RuntimeError(f'No Java types were analyzed: {source}')
        if name == 'control':
            detected = {r['Method Name'] for r in data['implementationCodeSmells.csv'] if r['Code Smell'] == 'Long Parameter List'}
            assert detected == {'five'}, detected
        summary['cases'][name] = {'elapsed_seconds': time.monotonic() - started,
            'rows': {k: len(v) for k, v in data.items()},
            'smells': {k: dict(Counter(r['Code Smell'] for r in v)) for k, v in data.items() if 'Smells' in k}}
    (out / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(out)
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
