"""One-click reruns using the existing Windows baseline environment."""
import argparse
from datetime import datetime
import json
import msvcrt
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
JAVA8 = Path('C:/Users/YuRui/Tools/jdk8')
JAVA17 = ROOT / '.runtime/jdk17/jdk-17.0.20.1+1'
MAVEN = Path('C:/Users/YuRui/Tools/apache-maven-3.9.16/bin/mvn.cmd')


def run(command, log, *, env=None):
    log.write('\n> ' + subprocess.list2cmdline([str(arg) for arg in command]) + '\n')
    log.flush()
    subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                   env=env, check=True)


def wait_ready(probe, description, timeout=300):
    print(f'Waiting for {description} (up to {timeout}s)...', flush=True)
    deadline = time.monotonic() + timeout
    while True:
        if probe():
            return
        if time.monotonic() >= deadline:
            raise RuntimeError(f'{description} did not become ready within {timeout}s.')
        time.sleep(3)


def docker_os():
    try:
        result = subprocess.run(['docker', 'info', '--format', '{{.OSType}}'],
                                capture_output=True, text=True, encoding='utf-8', timeout=10)
        return result.stdout.strip() if result.returncode == 0 else ''
    except subprocess.TimeoutExpired:
        return ''


def sonar_ready():
    try:
        with urllib.request.urlopen('http://127.0.0.1:19000/api/system/status', timeout=5) as response:
            return json.load(response)['status'] == 'UP'
    except (OSError, ValueError, KeyError):
        return False


def prepare(baseline, log):
    for command in ('docker', 'powershell') + (('git',) if baseline != 'sonarqube' else ()):
        if not shutil.which(command):
            raise RuntimeError(f'Missing command: {command}. See docs/复现步骤.md.')
    if baseline == 'sonarqube':
        required = [JAVA8 / 'bin/java.exe', MAVEN, ROOT / 'baselines/sources/jsoup/pom.xml']
    elif baseline == 'fetruth':
        required = [JAVA17 / 'bin/java.exe', ROOT / 'baselines/sources/jsoup/pom.xml',
                    ROOT / 'baselines/sources/feTruth/implementation/feTruth.py']
        required += [ROOT / '.runtime/fetruth/word2vec' / name for name in
                     ('new_model.bin.trainables.syn1neg.npy', 'new_model.bin.wv.vectors.npy')]
    else:
        required = [JAVA17 / 'bin/java.exe', MAVEN, ROOT / 'baselines/sources/reynard/pom.xml']
    for path in required:
        if not path.exists():
            raise RuntimeError(f'Missing {path}. See docs/复现步骤.md for first-time setup.')

    if not docker_os():
        print('Starting Docker Desktop...', flush=True)
        run(['powershell', '-NoProfile', '-Command',
             "Start-Process -FilePath (Join-Path $env:ProgramFiles 'Docker/Docker/Docker Desktop.exe') -WindowStyle Hidden -ErrorAction Stop"], log)
        wait_ready(docker_os, 'Docker Desktop')
    if docker_os() != 'linux':
        raise RuntimeError('Switch Docker Desktop to Linux containers, then run again.')

    if baseline in ('sonarqube', 'fetruth'):
        name = 'maturity-' + baseline
        inspection = subprocess.run(['docker', 'inspect', name], capture_output=True,
                                    text=True, encoding='utf-8')
        if inspection.returncode:
            raise RuntimeError(f'{name} is unavailable: {inspection.stderr.strip()} See docs/复现步骤.md.')
        container = json.loads(inspection.stdout)[0]
        if baseline == 'fetruth':
            mounts = [item for item in container['Mounts'] if item['Destination'] == '/workspace']
            if len(mounts) != 1 or Path(mounts[0]['Source']).resolve() != ROOT:
                raise RuntimeError('maturity-fetruth must mount this project at /workspace. See docs/复现步骤.md.')
        if not container['State']['Running']:
            print(f'Starting {name}...', flush=True)
            run(['docker', 'start', name], log)
        if baseline == 'sonarqube':
            wait_ready(sonar_ready, 'SonarQube')

    if baseline == 'reynard':
        # Concurrent builds reuse image tags and can collide in Docker's image store.
        patch = ROOT / 'baselines/reynard-sequential-start.patch'
        command = ['git', '-C', str(ROOT / 'baselines/sources/reynard'), 'apply']
        already_applied = subprocess.run(command + ['--reverse', '--check', str(patch)], capture_output=True)
        if already_applied.returncode:
            run(command + ['--check', str(patch)], log)
            run(command + [str(patch)], log)
        print('Container startup is sequential; fault scenarios and assertions are unchanged.', flush=True)


def backup_results(baseline, stamp):
    results = ROOT / 'results'
    sources = [results / baseline]
    if baseline == 'fetruth':
        sources.append(results / 'fetruth-paper')
    elif baseline == 'reynard':
        sources.extend(results.glob('reynard-*.log'))
    backup = ROOT / '.runtime/backups' / f'{baseline}-{stamp}'
    for source in sources:
        if source.exists():
            backup.mkdir(parents=True, exist_ok=True)
            destination = backup / source.name
            if source.is_dir():
                shutil.copytree(source, destination)
            else:
                shutil.copy2(source, destination)
    if backup.exists():
        print(f'Previous results saved: {backup}', flush=True)


def require_paper_match():
    comparison = json.loads((ROOT / 'results/fetruth-paper/comparison.json').read_text(encoding='utf-8'))
    if not comparison['exact_match'] or comparison['observed_recommendations'] != 16:
        raise RuntimeError('feTruth paper replay differs from the expected 16 recommendations.')


def execute(baseline, log):
    if baseline == 'sonarqube':
        print('Compiling jsoup with JDK 8...', flush=True)
        env = dict(os.environ, JAVA_HOME=str(JAVA8))
        env['PATH'] = str(JAVA8 / 'bin') + os.pathsep + env['PATH']
        run([str(MAVEN), '-B', '-ntp', '-f', 'baselines/sources/jsoup/pom.xml',
             '-DskipTests', 'compile'], log, env=env)
        print('Scanning jsoup; details: results/sonarqube/scan.log', flush=True)
        run([sys.executable, 'scripts/run_sonarqube.py'], log)
        issues = json.loads((ROOT / 'results/sonarqube/issues.json').read_text(encoding='utf-8'))
        print(f'SUCCESS: {len(issues)} SonarQube alerts. http://127.0.0.1:19000/dashboard?id=maturity-jsoup-1.15.3')
    elif baseline == 'fetruth':
        print('Replaying the archived paper example; details: results/fetruth-paper/inference.log', flush=True)
        run([sys.executable, 'scripts/replay_fetruth_artifact.py'], log)
        require_paper_match()
        print('Extracting fresh source features and running inference; details: results/fetruth/inference.log', flush=True)
        run([sys.executable, 'scripts/run_fetruth.py'], log)
        result = json.loads((ROOT / 'results/fetruth/execution.json').read_text(encoding='utf-8'))
        print(f"SUCCESS: paper example matched 16/16; fresh source produced {result['recommendations']} candidates.")
        print('The fresh-source model has a documented version discrepancy; candidates are not confirmed defects.')
    else:
        for case in ('register-ser', 'register-no-ser', 'patterns-ser', 'patterns-no-ser'):
            print(f'Running {case}; details: results/reynard-{case}.log', flush=True)
            run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass',
                 '-File', str(ROOT / 'scripts/run_reynard.ps1'), '-Case', case], log)
        print('SUCCESS: 4 Reynard scenarios verified (729 + 729 + 543 + 1849 executions).')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('baseline', choices=('sonarqube', 'fetruth', 'reynard'))
    baseline = parser.parse_args().baseline
    runtime = ROOT / '.runtime'
    runtime.mkdir(exist_ok=True)
    stamp = datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    logs = runtime / 'launcher-logs'
    logs.mkdir(exist_ok=True)
    log_path = logs / f'{baseline}-{stamp}.log'
    print(f'Project: {ROOT}\nLauncher log: {log_path}', flush=True)
    with (runtime / f'{baseline}.lock').open('a+b') as lock, log_path.open('w', encoding='utf-8') as log:
        if lock.tell() == 0:
            lock.write(b'0')
            lock.flush()
        lock.seek(0)
        try:
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            print(f'FAILED: another {baseline} launcher is already running.', file=sys.stderr)
            return 1
        try:
            prepare(baseline, log)
            backup_results(baseline, stamp)
            execute(baseline, log)
            print(f'Results: {ROOT / "results" / baseline}', flush=True)
            return 0
        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
            log.write(f'\nFAILED: {error}\n')
            print(f'FAILED: {error}\nSee {log_path}', file=sys.stderr, flush=True)
            return 1
        except KeyboardInterrupt:
            print('Interrupted; results may be incomplete. Previous results are in .runtime/backups.', file=sys.stderr)
            return 130


if __name__ == '__main__':
    sys.exit(main())
