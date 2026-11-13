"""Scan the pinned jsoup checkout and export original SonarQube API results."""
import base64
import json
import os
from pathlib import Path
import secrets
import subprocess
import time
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results' / 'sonarqube'
BASE = 'http://127.0.0.1:19000'
KEY = 'maturity-jsoup-1.15.3'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    secret_dir = ROOT / '.secrets'
    secret_dir.mkdir(exist_ok=True)
    password_file = secret_dir / 'sonarqube-admin.txt'
    password = password_file.read_text() if password_file.exists() else 'admin'

    def api(path, params=None, post=False):
        encoded = urllib.parse.urlencode(params or {}).encode()
        url = BASE + '/api/' + path
        if not post and encoded:
            url += '?' + encoded.decode()
        request = urllib.request.Request(url, data=encoded if post else None)
        request.add_header('Authorization', 'Basic ' + base64.b64encode(
            ('admin:' + password).encode()).decode())
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = response.read()
        return json.loads(raw) if raw else {}

    def save(name, value):
        (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')

    status = api('system/status')
    assert status['status'] == 'UP', status
    save('server.json', status)
    if password == 'admin':
        new_password = secrets.token_urlsafe(24) + 'aA1!'
        api('users/change_password', {'login': 'admin', 'previousPassword': password,
                                    'password': new_password}, post=True)
        password = new_password
        password_file.write_text(password)

    projects = api('projects/search', {'projects': KEY})
    if not projects.get('components'):
        api('projects/create', {'project': KEY, 'name': 'jsoup 1.15.3 baseline'}, post=True)
    token_name = 'baseline-' + secrets.token_hex(6)
    token = api('user_tokens/generate', {'name': token_name}, post=True)['token']
    env = dict(os.environ, SONAR_TOKEN=token)
    network = 'maturity-baselines'
    networks = subprocess.check_output(['docker', 'network', 'ls', '--format', '{{.Name}}'], text=True).splitlines()
    if network not in networks:
        subprocess.run(['docker', 'network', 'create', network], check=True)
    attached = json.loads(subprocess.check_output(['docker', 'inspect', 'maturity-sonarqube']))[0]['NetworkSettings']['Networks']
    if network not in attached:
        subprocess.run(['docker', 'network', 'connect', network, 'maturity-sonarqube'], check=True)
    image = 'sonarsource/sonar-scanner-cli@sha256:a3f4215076706c95a17a68c19322ee916e40a3acd081a8c1a1e839e0194afa57'
    scanner = json.loads(subprocess.check_output(['docker', 'image', 'inspect', image]))[0]
    save('scanner-image.json', {'image': image, 'id': scanner['Id']})
    command = ['docker', 'run', '--rm', '--network', network, '-e', 'SONAR_TOKEN',
               '--mount', f'type=bind,source={ROOT / "baselines/sources/jsoup"},target=/usr/src,readonly',
               '--mount', 'type=bind,source=C:/Users/YuRui/Tools/jdk8,target=/target-jdk,readonly',
               image, '-Dsonar.host.url=http://maturity-sonarqube:9000',
               '-Dsonar.projectKey=' + KEY, '-Dsonar.projectVersion=1.15.3',
               '-Dsonar.sources=src/main/java', '-Dsonar.java.binaries=target/classes',
               '-Dsonar.java.jdkHome=/target-jdk', '-Dsonar.sourceEncoding=UTF-8',
               '-Dsonar.scm.disabled=true', '-Dsonar.working.directory=/tmp/sonarwork',
               '-Dsonar.qualitygate.wait=true', '-Dsonar.qualitygate.timeout=300']
    save('scan-command.json', command)
    started = time.perf_counter()
    try:
        with (OUT / 'scan.log').open('w', encoding='utf-8') as log:
            result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, env=env)
        save('execution.json', {'exit_code': result.returncode,
                               'wall_seconds': time.perf_counter() - started})
        result.check_returncode()
        measures = api('measures/component', {'component': KEY, 'metricKeys':
            'ncloc,files,classes,functions,complexity,cognitive_complexity,duplicated_lines_density,'
            'code_smells,bugs,vulnerabilities,security_hotspots,sqale_index,sqale_debt_ratio,'
            'sqale_rating,reliability_rating,security_rating'})
        save('measures.json', measures)
        save('quality-gate.json', api('qualitygates/project_status', {'projectKey': KEY}))
        save('quality-profiles.json', api('qualityprofiles/search', {'project': KEY}))
        issues = []
        page = 1
        while True:
            data = api('issues/search', {'componentKeys': KEY, 'ps': 500, 'p': page})
            save(f'issues-page-{page}.json', data)
            issues.extend(data['issues'])
            if len(issues) >= data['paging']['total']:
                break
            page += 1
        save('issues.json', issues)
        assert measures['component']['measures'], 'No measured results'
        print(json.dumps({'server': status['version'], 'issues': len(issues),
                          'scanner_exit_code': result.returncode}, ensure_ascii=False))
    finally:
        api('user_tokens/revoke', {'name': token_name}, post=True)


if __name__ == '__main__':
    main()
