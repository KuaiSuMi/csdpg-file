"""Audit a real isolated kind workload before and after deployment configuration changes."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
CLUSTER = 'maturity-baselines'
CONTEXT = 'kind-' + CLUSTER


def target_summary(report):
    targets = [r for r in report['Results'] if r['Name'] == 'audit-demo'
               and r['Namespace'] == 'maturity-audit' and r['Kind'] == 'Deployment']
    assert len(targets) == 1
    checks = []
    def visit(value):
        if isinstance(value, dict):
            if {'ID', 'Success', 'Severity'} <= value.keys():
                checks.append(value)
            else:
                for child in value.values():
                    visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)
    visit(targets[0])
    successes = sum(c['Success'] for c in checks)
    warnings = sum(not c['Success'] and c['Severity'] == 'warning' for c in checks)
    dangers = sum(not c['Success'] and c['Severity'] != 'warning' for c in checks)
    denominator = successes * 2 + warnings + dangers * 2
    assert denominator > 0
    return {'score': successes * 200 // denominator, 'successes': successes,
            'warnings': warnings, 'dangers': dangers,
            'failed_checks': [c['ID'] for c in checks if not c['Success']]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--polaris', default='polaris')
    parser.add_argument('--kind', default='kind')
    args = parser.parse_args()
    out = ROOT / 'results/polaris' / datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    out.mkdir(parents=True)
    kubeconfig = ROOT / '.runtime/tools/maturity-kubeconfig'
    env = dict(os.environ, KUBECONFIG=str(kubeconfig))
    # Never use the user's current Kubernetes context.
    kubectl = ['kubectl', '--kubeconfig', str(kubeconfig), '--context', CONTEXT]
    log = (out / 'commands.log').open('w', encoding='utf-8')

    def run(command, *, capture=False):
        log.write(subprocess.list2cmdline([str(x) for x in command]) + '\n')
        log.flush()
        result = subprocess.run(command, env=env, check=True, encoding='utf-8',
                                stdout=subprocess.PIPE if capture else log, stderr=log)
        return result.stdout

    # Docker's containerd store may keep an incomplete multi-platform index.
    # Export just the locally available platform before importing into kind.
    archive = ROOT / '.runtime/tools/node-amd64.tar'
    run(['docker', 'save', '--platform', 'linux/amd64', '-o', str(archive), 'node:22-alpine'])
    run([args.kind, 'load', 'image-archive', str(archive), '--name', CLUSTER])
    # Apply is idempotent and confined to the dedicated namespace and cluster.
    namespace = {'apiVersion': 'v1', 'kind': 'Namespace', 'metadata': {'name': 'maturity-audit'}}
    ns_file = out / 'namespace.json'
    ns_file.write_text(json.dumps(namespace), encoding='utf-8')
    run(kubectl + ['apply', '-f', str(ns_file)])
    summary = {'date': datetime.now(timezone.utc).isoformat(), 'context': CONTEXT, 'cases': {}}
    for phase in ('before', 'after'):
        run(kubectl + ['apply', '-f', str(ROOT / f'baselines/polaris/{phase}.yaml')])
        run(kubectl + ['-n', 'maturity-audit', 'rollout', 'status', 'deployment/audit-demo', '--timeout=180s'])
        resources = run(kubectl + ['-n', 'maturity-audit', 'get', 'deployment,pods', '-o', 'json'], capture=True)
        (out / f'{phase}-resources.json').write_text(resources, encoding='utf-8')
        body = run(kubectl + ['-n', 'maturity-audit', 'exec', 'deployment/audit-demo', '--', 'node', '-e',
                   "fetch('http://127.0.0.1:8080/').then(async r=>{console.log(r.status,await r.text());if(r.status!==200)process.exit(1)})"], capture=True)
        assert body.strip() == '200 ok', body
        run([args.polaris, 'audit', '--context', CONTEXT, '--namespace', 'maturity-audit',
             '--format', 'json', '--output-file', str(out / f'{phase}.json')])
        report = json.loads((out / f'{phase}.json').read_text(encoding='utf-8'))
        assert report['SourceType'] == 'ClusterNamespace', report['SourceType']
        scoped = target_summary(report)
        summary['cases'][phase] = {'score': scoped['score'], 'target': scoped,
                                    'raw_overall_score': report['Score'], 'source_type': report['SourceType'],
                                    'cluster_info': report['ClusterInfo'], 'http': body.strip()}
    assert summary['cases']['after']['score'] > summary['cases']['before']['score']
    (out / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    log.close()
    print(out)
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
