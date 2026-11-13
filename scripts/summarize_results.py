"""Validate independent result records and collect measured values without rescanning."""
import hashlib
from datetime import datetime
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / 'results'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def main():
    sonar = RESULTS / 'sonarqube'
    assert read(sonar / 'execution.json')['exit_code'] == 0
    measures = {m['metric']: float(m['value']) for m in read(sonar / 'measures.json')['component']['measures']}
    issues = read(sonar / 'issues.json')
    assert len(issues) == sum(measures[k] for k in ('code_smells', 'bugs', 'vulnerabilities'))
    assert len({issue['key'] for issue in issues}) == len(issues)
    summary = {'generated_at': datetime.now().astimezone().isoformat(timespec='seconds'),
               'scope': 'representative reproduction, not full paper replication',
               'sonarqube': {'measures': measures, 'issues': len(issues),
                             'gate': read(sonar / 'quality-gate.json')['projectStatus'],
                             'execution': read(sonar / 'execution.json')}, 'reynard': {}}

    for case in ('register-ser', 'register-no-ser', 'patterns-ser', 'patterns-no-ser'):
        directory = RESULTS / 'reynard' / case
        reports = list(directory.glob('TEST-*.xml'))
        assert len(reports) == 1, (case, reports)
        suite = ET.parse(reports[0]).getroot()
        tests = int(suite.get('tests'))
        assert tests == len(suite.findall('testcase'))
        assert all(int(suite.get(k)) == 0 for k in ('failures', 'errors', 'skipped'))
        space = read(next(directory.rglob('search_space.json')))
        assert tests == space['total_run'] == space['cases_run'] + 1
        generator = read(next(directory.rglob('DynamicExplorationGenerator.json')))
        generator_stats = generator['stats']
        assert space['complete_space_size'] == (1 + generator_stats['failure_modes']) ** generator_stats['fault_injection_points']
        for name in ('failures.json', 'StatusPropagationOracle.json', 'FaultsWithoutCauseOracle.json'):
            assert read(next(directory.rglob(name))) == [], (case, name)
        timing = read(next(directory.rglob('timing.json')))
        assert timing['stats']['Per test']['count'] == tests
        summary['reynard'][case] = {'tests': tests, 'fault_cases': space['cases_run'],
            'failures': 0, 'errors': 0, 'skipped': 0,
            'suite_seconds': float(suite.get('time')),
            'test_phase_seconds': timing['stats']['Total test time']['average']['s'],
            'search_space': space, 'generator_stats': generator_stats,
            'failure_modes': generator['details']['failure_modes']}

    on = summary['reynard']['patterns-ser']['tests']
    off = summary['reynard']['patterns-no-ser']['tests']
    summary['reynard_patterns_reduction_percent'] = 100 * (off - on) / off

    fetruth = RESULTS / 'fetruth'
    result = read(fetruth / 'execution.json')
    assert result['exit_code'] == 0
    records = read(fetruth / 'jsoup-features.json')['RECORDS']
    assert len(records) == result['candidate_methods']
    assert hashlib.sha256((fetruth / 'jsoup-features.json').read_bytes()).hexdigest() == result['feature_sha256']
    recommendations = (fetruth / 'jsoup.txt').read_text(encoding='utf-8').splitlines()[1:]
    recommendations = [row.split('\t') for row in recommendations if row.strip()]
    assert len(recommendations) == result['recommendations']
    candidates = {row['source_class_name'] + '::' + row['method_signature']:
                  row['target_class_list'].split(', ') for row in records}
    for kind, method, target in recommendations:
        assert kind == 'Move Method' and target.strip() in candidates[method.strip()]
    assert read(RESULTS / 'fetruth-weights.json')['download_verified']
    summary['fetruth'] = result
    paper = read(RESULTS / 'fetruth-paper/comparison.json')
    assert paper['exit_code'] == 0 and paper['exact_match']
    assert paper['expected_recommendations'] == paper['observed_recommendations'] == paper['matching_recommendations']
    summary['fetruth_paper_replay'] = paper
    summary['fetruth_version_diagnostics'] = read(RESULTS / 'fetruth-model-diagnostics.json')
    (RESULTS / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Verified SonarQube issue totals, 4 Reynard suites, and feTruth source-to-recommendation evidence.')


if __name__ == '__main__':
    main()
