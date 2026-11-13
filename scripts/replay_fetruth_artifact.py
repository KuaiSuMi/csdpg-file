"""Replay the archived paper's jsoup features and compare the original saved result."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'baselines/sources/feTruth'
COMMIT = 'a89644539cd639ee7adc21543aae20f8895c47d6'
WORK = ROOT / '.runtime/paper/feTruth'
OUT = ROOT / 'results/fetruth-paper'


def recommendations(path):
    rows = [line for line in path.read_text(encoding='utf-8-sig').splitlines()[1:] if line.strip()]
    result = {tuple(field.strip() for field in line.split('\t')) for line in rows}
    assert len(result) == len(rows)
    assert all(len(row) == 3 and row[0] == 'Move Method' for row in result)
    return result


def compare():
    expected = recommendations(OUT / 'expected-jsoup.txt')
    observed = recommendations(OUT / 'jsoup.txt')
    result = {'commit': COMMIT, 'tag': 'v1.0.0', 'zenodo_record': 8267775,
              'input': 'author-provided extracted jsoup features; not a new source extraction',
              'expected_recommendations': len(expected), 'observed_recommendations': len(observed),
              'matching_recommendations': len(expected & observed),
              'expected_only': sorted(expected - observed), 'observed_only': sorted(observed - expected),
              'exact_match': expected == observed, 'exit_code': 0}
    (OUT / 'comparison.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k not in ('expected_only', 'observed_only')}))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    archive = ROOT / '.runtime/fetruth-v1.zip'
    subprocess.run(['git', '-C', str(SOURCE), 'archive', '--format=zip', '--output=' + str(archive), COMMIT], check=True)
    with zipfile.ZipFile(archive) as source:
        source.extractall(WORK)
    for name in ('new_model.bin.trainables.syn1neg.npy', 'new_model.bin.wv.vectors.npy'):
        target = WORK / 'word2vec' / name
        if not target.exists():
            os.link(ROOT / '.runtime/fetruth/word2vec' / name, target)
    shutil.copy2(WORK / 'experiment/jsoup(feTruth).txt', OUT / 'expected-jsoup.txt')
    with (OUT / 'inference.log').open('w', encoding='utf-8') as log:
        subprocess.run(['docker', 'exec', '-e', 'TF_NUM_INTRAOP_THREADS=2', '-e', 'TF_NUM_INTEROP_THREADS=2',
                        '-w', '/workspace/.runtime/paper/feTruth/implementation/feTruth',
                        'maturity-fetruth', 'python', 'evaluate.py', 'jsoup'],
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    shutil.copy2(WORK / 'implementation/feTruth/output/jsoup(feTruth).txt', OUT / 'jsoup.txt')
    compare()


if __name__ == '__main__':
    main()
