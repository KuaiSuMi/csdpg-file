"""Run an unchanged business oracle before/after a recommendation fallback repair."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
CLASS = 'dev.reynard.junit.integration.micro.MaturityContractIT'


@contextmanager
def installed_test(target, fixture):
    data = fixture.read_bytes()
    created = not target.exists()
    if not created and target.read_bytes() != data:
        raise RuntimeError(f"Refusing to overwrite a different test: {target}")
    if created:
        target.write_bytes(data)
    try:
        yield
    finally:
        if created and target.read_bytes() == data:
            target.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--java-home', type=Path, default=ROOT / '.runtime/jdk17/jdk-17.0.20.1+1')
    parser.add_argument('--maven', default='C:/Users/YuRui/Tools/apache-maven-3.9.16/bin/mvn.cmd')
    args = parser.parse_args()
    source = ROOT / 'baselines/sources/reynard'
    target = source / ('library/src/test/java/' + CLASS.replace('.', '/') + '.java')
    fixture = ROOT / 'baselines/fixtures/reynard/MaturityContractIT.java'
    output = ROOT / 'results/reynard-contract' / datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    output.mkdir(parents=True)
    env = dict(os.environ, JAVA_HOME=str(args.java_home.resolve()),
               PATH=str(args.java_home.resolve() / 'bin') + os.pathsep + os.environ['PATH'],
               PROXY_IMAGE='fit-proxy:latest', CONTROLLER_IMAGE='fit-controller:latest',
               DOCKER_API_VERSION='1.44', USE_SER='true')
    summary = {'date': datetime.now(timezone.utc).isoformat(),
               'scenario': 'optional-recommendation', 'cases': {}}
    with installed_test(target, fixture):
        for phase in ('before', 'after'):
            dest = output / phase
            dest.mkdir()
            phase_env = dict(env, MATURITY_REPAIR=str(phase == 'after').lower(),
                             MATURITY_OBSERVATIONS=str(dest / 'observations'),
                             OUTPUT_DIR=str(dest), OUTPUT_TAG=phase)
            report = source / f'library/target/surefire-reports/TEST-{CLASS}.xml'
            report.unlink(missing_ok=True)
            with (dest / 'maven.log').open('w', encoding='utf-8') as log:
                result = subprocess.run([args.maven, '-B', '-ntp', 'test',
                                         f'-Dtest={CLASS}', '-Dsurefire.failIfNoSpecifiedTests=false',
                                         '-Dapi.version=1.44'], cwd=source, env=phase_env,
                                        stdout=log, stderr=subprocess.STDOUT)
            if not report.exists():
                raise RuntimeError(f'No JUnit report; inspect {dest / "maven.log"}')
            shutil.copyfile(report, dest / 'junit.xml')
            suite = ET.parse(dest / 'junit.xml').getroot()
            counts = {k: int(suite.attrib[k]) for k in ('tests', 'failures', 'errors', 'skipped')}
            observations = [json.loads(p.read_text(encoding='utf-8'))
                            for p in sorted((dest / 'observations').glob('*.json'))]
            assert counts['errors'] == counts['skipped'] == 0, counts
            assert counts['tests'] == len(observations) and len(observations) > 1, counts
            assert all(x['injection_verified'] for x in observations)
            healthy = [x for x in observations if x['fault_count'] == 0]
            assert len(healthy) == 1 and healthy[0]['passed'], healthy
            failed = sum(not x['passed'] for x in observations)
            assert failed == counts['failures'], counts
            if phase == 'before':
                assert result.returncode != 0 and failed > 0, counts
            else:
                assert result.returncode == 0 and failed == 0, counts
            summary['cases'][phase] = dict(counts, exit_code=result.returncode,
                                           healthy_passed=True, fault_executions=len(observations) - 1)
            print(phase, summary['cases'][phase], flush=True)
        assert summary['cases']['before']['tests'] == summary['cases']['after']['tests']
        (output / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
        print(output)



if __name__ == '__main__':
    main()
