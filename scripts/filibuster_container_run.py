"""Run author cinema-1 services and CLI with the documented startup-log patch."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import requests

ROOT = Path('/workspace')
SOURCE = ROOT / 'baselines/sources/filibuster'
CORPUS = ROOT / 'baselines/sources/filibuster-corpus/cinema-1'
OUT = Path('/out')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    processes, logs = [], []
    summary = {'date': datetime.now(timezone.utc).isoformat(), 'case': 'cinema-1',
               'deployment': 'four original Flask service processes in one isolated Linux container',
               'cases': {}}
    env = dict(os.environ, PYTHONPATH=str(SOURCE), NO_PROXY='*', no_proxy='*')
    try:
        for service in ('movies', 'showtimes', 'bookings', 'users'):
            log = (OUT / (service + '.log')).open('w')
            logs.append(log)
            processes.append(subprocess.Popen([sys.executable, '-m', service + '.app'],
                cwd=CORPUS / 'services' / service, env=env, stdout=log, stderr=subprocess.STDOUT))
        session = requests.Session()
        session.trust_env = False
        deadline = time.monotonic() + 60
        for port in (5000, 5001, 5002, 5003):
            while True:
                if any(p.poll() is not None for p in processes):
                    raise RuntimeError('A service exited; inspect service logs.')
                try:
                    if session.get(f'http://127.0.0.1:{port}/health-check', timeout=2).status_code == 200:
                        break
                except requests.RequestException:
                    pass
                if time.monotonic() > deadline:
                    raise RuntimeError('Service readiness timed out')
                time.sleep(.5)
        baseline = session.get('http://127.0.0.1:5000/users/chris_rivers/bookings', timeout=15)
        summary['healthy_response'] = {'status': baseline.status_code, 'body': baseline.json()}
        assert baseline.status_code == 200
        functional = f'python {CORPUS}/functional/test_user_bookings.py'
        command = [sys.executable, '-c', 'from filibuster_cli import test; test()',
                   '--functional-test', functional]
        for name, flags in [('dynamic', []), ('no-dynamic', ['--disable-dynamic-reduction'])]:
            start = time.monotonic()
            with (OUT / (name + '.log')).open('w') as log:
                result = subprocess.run(command + flags, cwd=OUT, env=env,
                                        stdout=log, stderr=subprocess.STDOUT, timeout=600)
            result.check_returncode()
            content = (OUT / (name + '.log')).read_text()
            ran = int(re.search(r'Number of test executions ran: (\d+)', content)[1])
            pruned = int(re.search(r'Test executions pruned with only dynamic pruning: (\d+)', content)[1])
            assert ran > 1, 'No fault executions recorded'
            summary['cases'][name] = {'exit_code': result.returncode, 'executions': ran,
                                      'pruned': pruned, 'wall_seconds': time.monotonic() - start}
        # Deliberately stricter than the author's contract: demonstrates counterexample handling.
        strict = OUT / 'strict_control.py'
        strict.write_text("import requests\nr = requests.get('http://127.0.0.1:5000/users/chris_rivers/bookings', timeout=15)\nassert r.status_code == 200, r.status_code\n")
        strict_cmd = command[:-1] + [f'python {strict}']
        for name, flags in [('strict-control', []), ('strict-replay', ['--counterexample-file', str(OUT / 'counterexample.json')])]:
            with (OUT / (name + '.log')).open('w') as log:
                result = subprocess.run(strict_cmd + flags, cwd=OUT, env=env,
                                        stdout=log, stderr=subprocess.STDOUT, timeout=120)
            assert result.returncode == 1, f'{name}: expected counterexample exit 1, got {result.returncode}'
            assert (OUT / 'counterexample.json').exists()
            summary['cases'][name] = {'exit_code': result.returncode, 'expected_failure': True}
        (OUT / 'summary.json').write_text(json.dumps(summary, indent=2))
        subprocess.run([sys.executable, '-m', 'pip', 'freeze'], check=True,
                       stdout=(OUT / 'environment.txt').open('w'))
        print(json.dumps(summary, indent=2))
    finally:
        for p in processes:
            p.terminate()
        for p in processes:
            p.wait(timeout=10)
        for log in logs:
            log.close()


if __name__ == '__main__':
    main()
