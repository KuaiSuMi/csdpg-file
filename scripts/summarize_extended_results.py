"""Validate stored extension results without rerunning any benchmark."""
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

from run_polaris import target_summary

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def main():
    manifest = read(ROOT / 'baselines/extended-manifest.json')
    result = {'validated_at': datetime.now(timezone.utc).isoformat(),
              'previous_results': 'results/summary.json',
              'previous_experiment_date': '2026-10-14', 'new_experiment_date': '2026-10-21'}
    for name in ('designite', 'filibuster', 'polaris'):
        ref = manifest['repositories'][name]['result_file']
        path = ROOT / ref
        data = read(path)
        if name == 'designite':
            for case in ('jsoup', 'control'):
                for filename, expected in data['cases'][case]['rows'].items():
                    with (path.parent / case / filename).open(encoding='utf-8-sig', newline='') as handle:
                        rows = list(csv.DictReader(handle))
                    assert len(rows) == expected
            with (path.parent / 'control/implementationCodeSmells.csv').open(encoding='utf-8-sig') as handle:
                targets = {r['Method Name'] for r in csv.DictReader(handle) if r['Code Smell'] == 'Long Parameter List'}
            assert targets == {'five'}
            assert data['cases']['jsoup']['rows']['designCodeSmells.csv'] == 208
            assert data['cases']['jsoup']['rows']['implementationCodeSmells.csv'] == 271
        elif name == 'filibuster':
            for case in ('dynamic', 'no-dynamic'):
                log = (path.parent / (case + '.log')).read_text(encoding='utf-8')
                actual = int(re.search(r'Number of test executions ran: (\d+)', log)[1])
                assert actual == data['cases'][case]['executions'] == 11
                assert data['cases'][case]['exit_code'] == 0
            assert data['cases']['strict-control']['exit_code'] == 1
            assert data['cases']['strict-replay']['exit_code'] == 1
            replay = (path.parent / 'strict-replay.log').read_text(encoding='utf-8')
            assert 'Counterexample reproduced.' in replay
            counterexample = read(path.parent / 'counterexample.json')
            execution = json.loads(counterexample['TestExecution'])
            assert len(execution['failures']) > 0
            assert data['healthy_response']['status'] == 200
        else:
            for phase, expected in [('before', 53), ('after', 87)]:
                raw = read(path.parent / (phase + '.json'))
                assert raw['SourceType'] == 'ClusterNamespace'
                scoped = target_summary(raw)
                assert scoped == data['cases'][phase]['target']
                assert scoped['score'] == expected
                assert raw['Score'] == data['cases'][phase]['raw_overall_score']
                assert data['cases'][phase]['http'] == '200 ok'
                snapshot = read(path.parent / (phase + '-resources.json'))
                deployment = next(x for x in snapshot['items'] if x['kind'] == 'Deployment')
                assert deployment['status']['availableReplicas'] == 1
        result[name] = {'result_file': ref, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                        'validated': True, 'data': data}
    assert hashlib.sha256((ROOT / 'docs/原始项目要求.md').read_bytes()).hexdigest() == manifest['original_requirements_sha256']
    (ROOT / 'results/extended-summary.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Validated: Designite CSV/control, Filibuster runs/counterexample, Polaris live snapshots/scoped scores; original requirements unchanged.')


if __name__ == '__main__':
    main()
