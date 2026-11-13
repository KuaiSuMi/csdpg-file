"""Download the author's fixed Zenodo archive in verified HTTP ranges."""
import concurrent.futures
import hashlib
import http.client
import json
from pathlib import Path
import subprocess
import urllib.request
import urllib.error
import zipfile

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / '.runtime'
CHUNK = 16 * 1024 * 1024


def fetch(request):
    for attempt in range(3):
        try:
            return urllib.request.urlopen(request, timeout=180)
        except (urllib.error.URLError, TimeoutError):
            if attempt == 2:
                raise
            print('Transient transport failure; retrying connection', flush=True)


def main():
    metadata = RUNTIME / 'zenodo-model-record.json'
    if not metadata.exists():
        subprocess.run(['curl.exe', '--fail', '--location', '--max-time', '60',
                        '--output', str(metadata), 'https://zenodo.org/api/records/5749111'], check=True)
    record = json.loads(metadata.read_text(encoding='utf-8'))
    file = next(item for item in record['files'] if item['key'] == 'DeepSmellPyFiles.zip')
    size, url = file['size'], file['links']['self']
    parts = RUNTIME / 'weight-parts'
    parts.mkdir(parents=True, exist_ok=True)

    def download(index):
        start = index * CHUNK
        end = min(start + CHUNK, size) - 1
        path = parts / f'{index:04}.part'
        if path.exists() and path.stat().st_size == end - start + 1:
            return index
        partial = path.with_suffix('.partial')
        for attempt in range(6):
            offset = partial.stat().st_size if partial.exists() else 0
            assert offset <= end - start + 1, 'Oversized partial range'
            if offset == end - start + 1:
                break
            current = start + offset
            request = urllib.request.Request(url, headers={'Range': f'bytes={current}-{end}'})
            print(f'Range {index + 1}: {current}-{end}', flush=True)
            try:
                with fetch(request) as response, partial.open('ab') as target:
                    assert response.status == 206, 'Server did not honor byte range'
                    assert response.headers['Content-Range'] == f'bytes {current}-{end}/{size}'
                    while True:
                        data = response.read(1024 * 1024)
                        if not data:
                            break
                        target.write(data)
            except (OSError, http.client.HTTPException) as error:
                print(f'Range {index + 1}, attempt {attempt + 1}: {error}', flush=True)
                if attempt == 5:
                    raise
        assert partial.stat().st_size == end - start + 1, 'Truncated range'
        partial.replace(path)
        return index

    count = (size + CHUNK - 1) // CHUNK
    failed = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        for done, future in enumerate(concurrent.futures.as_completed(
            [pool.submit(download, index) for index in range(count)]), 1):
            try:
                print(f'part {future.result() + 1}/{count}, completed {done}', flush=True)
            except Exception as error:
                failed.append(str(error))
                print(f'Failed range: {error}', flush=True)
    assert not failed, failed
    archive = RUNTIME / 'fetruth-weights.zip'
    digest = hashlib.md5()
    with archive.open('wb') as target:
        for index in range(count):
            data = (parts / f'{index:04}.part').read_bytes()
            digest.update(data)
            target.write(data)
    assert 'md5:' + digest.hexdigest() == file['checksum'], 'Zenodo checksum mismatch'
    target = RUNTIME / 'fetruth' / 'word2vec'
    target.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as source:
        for name in ('new_model.bin.trainables.syn1neg.npy', 'new_model.bin.wv.vectors.npy'):
            source.extract(name, target)
    evidence = {'record': 5749111, 'file': file['key'], 'size': size,
                'checksum': file['checksum'], 'download_verified': True}
    (ROOT / 'results' / 'fetruth-weights.json').write_text(json.dumps(evidence, indent=2))
    print('Author weights downloaded and verified', flush=True)


if __name__ == '__main__':
    main()
