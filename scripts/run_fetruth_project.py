"""Run the author's source-input workflow on a project, separately from paper replay."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    args = parser.parse_args()
    source = args.source.resolve()
    relative = source.relative_to(ROOT)
    if not source.is_dir() or not any(source.rglob("*.java")):
        parser.error("source must contain Java files inside this workspace")
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    output = ROOT / "results/fetruth-project" / stamp
    work = ROOT / ".runtime/fetruth-project" / stamp
    implementation = work / "implementation"
    implementation.mkdir(parents=True)
    (work / "word2vec").mkdir()
    output.mkdir(parents=True)
    original = ROOT / "baselines/sources/feTruth"
    for name in ("feTruth.py", "preprocess.py", "feTruth.h5", "testingDataGeneration.jar"):
        shutil.copy2(original / "implementation" / name, implementation / name)
    for name in ("new_model.bin", "new_model.bin.trainables.syn1neg.npy", "new_model.bin.wv.vectors.npy"):
        (work / "word2vec" / name).hardlink_to(ROOT / ".runtime/fetruth/word2vec" / name)
    java = ROOT / ".runtime/jdk17/jdk-17.0.20.1+1/bin/java.exe"
    with (output / "extraction.log").open("w", encoding="utf-8") as log:
        subprocess.run([str(java), "-Dfile.encoding=UTF-8", "-jar", "testingDataGeneration.jar", str(source)],
                       cwd=implementation, stdout=log, stderr=subprocess.STDOUT, check=True)
    features = implementation / "testing_data" / (source.name + ".json")
    records = json.loads(features.read_text(encoding="utf-8"))["RECORDS"]
    if not records:
        raise RuntimeError("No extracted candidate methods; this is not a clean quality result")
    container_work = "/workspace/" + work.relative_to(ROOT).as_posix()
    with (output / "inference.log").open("w", encoding="utf-8") as log:
        subprocess.run(["docker", "exec", "-e", "PYTHONPATH=" + container_work,
                        "-e", "TF_NUM_INTRAOP_THREADS=2", "-e", "TF_NUM_INTEROP_THREADS=2",
                        "-w", container_work + "/implementation", "maturity-fetruth",
                        "python", "feTruth.py", "-a", "/workspace/" + relative.as_posix()],
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    native = implementation / "output" / (source.name + ".txt")
    rows = native.read_text(encoding="utf-8").splitlines()
    assert rows[0] == "Refactoring Type\tSource Method\tTarget Class"
    suggestions = [line for line in rows[1:] if line.strip()]
    assert all(line.startswith("Move Method\t") for line in suggestions)
    shutil.copy2(features, output / "features.json")
    shutil.copy2(native, output / "recommendations.tsv")
    summary = dict(executed_at=datetime.now(timezone.utc).isoformat(),
                   workflow="author-source-workflow", source=str(source),
                   source_commit=subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip(),
                   tool_commit=subprocess.check_output(["git", "-C", str(original), "rev-parse", "HEAD"], text=True).strip(),
                   candidate_methods=len(records),
                   candidate_pairs=sum(len(r["target_class_list"].split(", ")) for r in records),
                   recommendations=len(suggestions), threshold=0.95, exit_code=0,
                   model_sha256=hashlib.sha256((implementation / "feTruth.h5").read_bytes()).hexdigest(),
                   feature_sha256=hashlib.sha256(features.read_bytes()).hexdigest(),
                   scope="Author source workflow has a known discrepancy with the archived paper model; suggestions need review")
    (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(output)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
