"""Run original feTruth extraction and inference, keeping the author checkout intact."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'baselines/sources/feTruth'
WORK = ROOT / '.runtime/fetruth'
OUT = ROOT / 'results/fetruth'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    implementation = WORK / 'implementation'
    implementation.mkdir(parents=True, exist_ok=True)
    for name in ('feTruth.py', 'preprocess.py', 'feTruth.h5', 'testingDataGeneration.jar'):
        shutil.copy2(SOURCE / 'implementation' / name, implementation / name)
    shutil.copy2(SOURCE / 'word2vec/new_model.bin', WORK / 'word2vec/new_model.bin')
    for name in ('new_model.bin.trainables.syn1neg.npy', 'new_model.bin.wv.vectors.npy'):
        assert (WORK / 'word2vec' / name).stat().st_size == 485452928, name

    features = implementation / 'testing_data/jsoup.json'
    output = implementation / 'output/jsoup.txt'
    features.unlink(missing_ok=True)
    output.unlink(missing_ok=True)
    java = ROOT / '.runtime/jdk17/jdk-17.0.20.1+1/bin/java.exe'
    extraction = [str(java), '-Dfile.encoding=UTF-8', '-jar', 'testingDataGeneration.jar',
                  str(ROOT / 'baselines/sources/jsoup')]
    inference = ['docker', 'exec', '-e', 'PYTHONPATH=/workspace/.runtime/fetruth',
                 '-e', 'TF_NUM_INTRAOP_THREADS=2', '-e', 'TF_NUM_INTEROP_THREADS=2',
                 '-w', '/workspace/.runtime/fetruth/implementation',
                 'maturity-fetruth', 'python', 'feTruth.py', '-a', '/workspace/baselines/sources/jsoup']
    started = time.perf_counter()
    with (OUT / 'extraction.log').open('w', encoding='utf-8') as log:
        subprocess.run(extraction, cwd=implementation, stdout=log, stderr=subprocess.STDOUT, check=True)
    records = json.loads(features.read_text(encoding='utf-8'))['RECORDS']
    assert records and len({row['id'] for row in records}) == len(records), 'Invalid extracted methods'
    extraction_seconds = time.perf_counter() - started
    started = time.perf_counter()
    with (OUT / 'inference.log').open('w', encoding='utf-8') as log:
        subprocess.run(inference, stdout=log, stderr=subprocess.STDOUT, check=True)
    inference_seconds = time.perf_counter() - started
    rows = output.read_text(encoding='utf-8').splitlines()
    assert rows[0] == 'Refactoring Type\tSource Method\tTarget Class', 'Invalid feTruth output'
    recommendations = [line for line in rows[1:] if line.strip()]
    assert all(line.startswith('Move Method\t') for line in recommendations)
    assert len(recommendations) <= len(records)
    shutil.copy2(features, OUT / 'jsoup-features.json')
    shutil.copy2(output, OUT / 'jsoup.txt')
    evidence = {
        'extraction_command': extraction, 'inference_command': inference,
        'candidate_methods': len(records),
        'candidate_pairs': sum(len(row['target_class_list'].split(', ')) for row in records),
        'recommendations': len(recommendations), 'threshold': 0.95,
        'extraction_seconds': extraction_seconds, 'inference_seconds': inference_seconds,
        'feature_sha256': hashlib.sha256(features.read_bytes()).hexdigest(),
        'model_sha256': hashlib.sha256((implementation / 'feTruth.h5').read_bytes()).hexdigest(),
        'exit_code': 0,
    }
    (OUT / 'execution.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(evidence, ensure_ascii=False))


if __name__ == '__main__':
    main()
