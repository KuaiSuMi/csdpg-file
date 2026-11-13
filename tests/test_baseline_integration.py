import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'integration'))
from maturity_baselines import BaselineCollector
from kg_builder import BuildPipeline, BuildSettings
from kg_builder.graph.model import KGNode
from kg_builder.graph.serialization import dict_to_graph, graph_to_dict


@pytest.fixture
def fetruth(tmp_path):
    features = {'RECORDS': [dict(id=1, project_name='demo', source_class_name='demo.Order',
                                method_signature='submit(int):void', target_class_list='demo.Payment')]}
    raw = json.dumps(features).encode()
    (tmp_path / 'features.json').write_bytes(raw)
    (tmp_path / 'recommendations.tsv').write_text(
        'Refactoring Type\tSource Method\tTarget Class\nMove Method\tdemo.Order::submit(int):void\tdemo.Payment\n')
    (tmp_path / 'summary.json').write_text(json.dumps(dict(
        exit_code=0, candidate_methods=1, candidate_pairs=1, recommendations=1,
        threshold=0.95, workflow='author-source-workflow', model_sha256='fixed',
        feature_sha256=hashlib.sha256(raw).hexdigest())))
    return tmp_path


def test_fetruth_candidate_retains_signature_and_evidence(fetruth):
    result = BaselineCollector('fetruth', fetruth, namespace='test').collect()
    assert result.metrics == dict(status='ok', observations=2, subjects=2, findings=1)
    candidate = next(n for n in result.nodes if n.name == 'Feature Envy')
    assert candidate.attributes['status'] == 'candidate'
    assert candidate.attributes['method_signature'] == 'submit(int):void'
    assert len(candidate.provenance) == 3


@pytest.mark.parametrize('damage', ['coverage', 'target', 'features'])
def test_fetruth_rejects_inconsistent_evidence(fetruth, damage):
    if damage == 'coverage':
        p = fetruth / 'summary.json'
        data = json.loads(p.read_text()); data['candidate_pairs'] = 2
        p.write_text(json.dumps(data))
    elif damage == 'target':
        p = fetruth / 'recommendations.tsv'
        p.write_text(p.read_text().replace('demo.Payment', 'demo.Missing'))
    else:
        (fetruth / 'features.json').write_text('{"RECORDS": []}')
    result = BaselineCollector('fetruth', fetruth, namespace='test').collect()
    assert result.metrics['status'] == 'error' and not result.nodes


def kivi_files(directory, failed=False):
    raw = 'Full statespace search for:\nerrors: %d\n12 states, stored\npan: elapsed time 0.1 seconds\n' % failed
    (directory / 'process-2.stdout.txt').write_text(raw)
    (directory / 'processes.json').write_text(json.dumps([
        dict(command=['./pan', '-m100000'], exit_code=0, stdout='process-2.stdout.txt')]))
    log = 'Working on the intents: pod_always_schedulable \n'
    if failed:
        log += '[Scheduler - no_feasible_node] No feasible node!\n'
    (directory / 'kivi.log').write_text(log)
    (directory / 'model-input.json').write_text(json.dumps({'setup': {'nodes': [{}], 'd': [{}]}}))
    result = dict(status='fail' if failed else 'pass', spin_errors=int(failed), stored_states=12.0,
                  intent='pod_always_schedulable', scope='fixed-topology-model',
                  native_stdout='process-2.stdout.txt', tool_commit='fixed', input_source='document',
                  subject='k8s:test/default/Deployment/api')
    (directory / 'result.json').write_text(json.dumps(result))
    return directory


def test_kivi_model_failure_is_not_collection_error(tmp_path):
    result = BaselineCollector('kivi', kivi_files(tmp_path, True), namespace='test').collect()
    assert result.metrics['status'] == 'ok' and result.metrics['findings'] == 1
    assert all(p.source_type == 'document' for n in result.nodes for p in n.provenance)


@pytest.mark.parametrize('damage', ['process', 'incomplete', 'forged-pass', 'empty-model'])
def test_kivi_rejects_invalid_verification(tmp_path, damage):
    kivi_files(tmp_path, damage == 'forged-pass')
    if damage == 'process':
        p = tmp_path / 'processes.json'; data = json.loads(p.read_text())
        data[0]['exit_code'] = 1; p.write_text(json.dumps(data))
    elif damage == 'incomplete':
        p = tmp_path / 'process-2.stdout.txt'; p.write_text(p.read_text() + 'Warning: Search not completed')
    elif damage == 'forged-pass':
        p = tmp_path / 'result.json'; data = json.loads(p.read_text())
        data['status'] = 'pass'; p.write_text(json.dumps(data))
    else:
        (tmp_path / 'model-input.json').write_text('{"setup":{"nodes":[],"d":[]}}')
    result = BaselineCollector('kivi', tmp_path, namespace='test').collect()
    assert result.metrics['status'] == 'error' and not result.nodes


def test_real_pipeline_preserves_explicit_node(fetruth):
    existing = KGNode(id='source-order', type='Service', name='OrderService',
                      namespace='test', attributes={'existing': True})
    collector = BaselineCollector('fetruth', fetruth, namespace='test',
                                  bindings={'java:demo.Order': existing})
    report = BuildPipeline(BuildSettings(repo_path=fetruth, namespace='test', enrich=False)).run(
        collectors=[collector], write_outputs=False)
    assert not report.warnings and report.graph.get_node('source-order').attributes['existing']
    assert not existing.provenance
    assert dict_to_graph(graph_to_dict(report.graph)).stats() == report.graph.stats()


def test_binding_cannot_cross_project(fetruth):
    wrong = KGNode(id='wrong', type='Service', name='other', namespace='other-project')
    result = BaselineCollector('fetruth', fetruth, namespace='test',
                               bindings={'java:demo.Order': wrong}).collect()
    assert result.metrics['status'] == 'error' and not result.nodes


def test_missing_input_is_not_clean(tmp_path):
    result = BaselineCollector('fetruth', tmp_path, namespace='test').collect()
    assert result.metrics['status'] == 'error' and result.warnings


def test_cli_preserves_existing_metadata(fetruth):
    original = fetruth / 'base.kg.json'
    original.write_text(json.dumps({'nodes': [], 'edges': [], 'meta': {
        'baseline_runs': {'baseline-reynard': {'status': 'ok'}}, 'existing': True}}))
    output = fetruth / 'merged.kg.json'
    subprocess.run([sys.executable, str(ROOT / 'scripts/build_baseline_graph.py'),
                    '--fetruth', str(fetruth), '--base-graph', str(original),
                    '--namespace', 'test', '--output', str(output)], check=True, capture_output=True)
    meta = json.loads(output.read_text())['meta']
    assert meta['existing'] and set(meta['baseline_runs']) == {'baseline-fetruth', 'baseline-reynard'}


def test_missing_observation_is_not_repair():
    sys.path.insert(0, str(ROOT / 'scripts'))
    from compare_baseline_graphs import compare
    node = {'id': 'check', 'type': 'Metric', 'name': 'schedulability',
            'attributes': {'baseline': 'kivi', 'status': 'fail'}}
    assert compare({'nodes': [node]}, {'nodes': []})['counts'] == {'not-observed-after': 1}
    after = dict(node, attributes={'baseline': 'kivi', 'status': 'pass'})
    assert compare({'nodes': [node]}, {'nodes': [after]})['counts'] == {'check-passed-after': 1}

def runtime_files(tmp_path, *, healthy=True, verified=True, missing=False):
    (tmp_path / "junit.xml").write_text('<testsuite tests="2" failures="1" errors="0" skipped="0"/>')
    observations = tmp_path / "observations"
    observations.mkdir()
    for index in range(2):
        if missing and index:
            continue
        obs = dict(service="frontend", dependency="recommendations", scenario="optional-recommendation",
                   phase="before", trace_id=str(index), http_status=200 if index == 0 else 500,
                   body="[]", passed=healthy if index == 0 else False, fault_count=index,
                   injection_verified=verified, faultload={"faults": [] if index == 0 else [{"mode": "error"}]},
                   trace={"reports": [{"trace_id": str(index), "injected_fault": None if index == 0 else {"mode": "error"},
                                       "uid": {"stack": [{"destination": "frontend"}, {"destination": "recommendations"}]}}]})
        (observations / f"{index}.json").write_text(json.dumps(obs))
    return tmp_path


def test_runtime_failure_is_evidence_not_collection_error(tmp_path):
    result = BaselineCollector("reynard", runtime_files(tmp_path), namespace="test").collect()
    assert result.metrics == {"status": "ok", "observations": 2, "subjects": 2, "findings": 1}
    assert any(e.relation == "CALLS" for e in result.edges)


@pytest.mark.parametrize("options", [{"healthy": False}, {"verified": False}, {"missing": True}])
def test_runtime_does_not_accept_incomplete_evidence(tmp_path, options):
    result = BaselineCollector("reynard", runtime_files(tmp_path, **options), namespace="test").collect()
    assert result.metrics["status"] == "error" and not result.nodes




def test_runtime_checks_raw_injection_evidence(tmp_path):
    runtime_files(tmp_path)
    path = tmp_path / "observations/1.json"
    obs = json.loads(path.read_text())
    obs["trace"]["reports"][0]["injected_fault"] = None
    path.write_text(json.dumps(obs))
    result = BaselineCollector("reynard", tmp_path, namespace="test").collect()
    assert result.metrics["status"] == "error"


