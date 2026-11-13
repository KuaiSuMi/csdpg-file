"""Run the original ATC 2024 C3 case and a YAML repair with native SPIN evidence."""
import argparse
from datetime import datetime, timezone
import difflib
import json
from pathlib import Path
import shutil
import subprocess
import tarfile
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
IMAGE = "maturity-kivi:atc2024"
COMMIT = "81e6c253573b0cc41727885948c1240892d1a6e2"
sys.path.insert(0, str(ROOT / "integration"))
from maturity_baselines.native import verifier_result


def run(directory, options, input_path=None):
    directory.mkdir(parents=True)
    command = ["docker", "run", "--rm", "--pull=never", "--entrypoint", "python",
               "-e", "KIVI_EVIDENCE=/evidence", "-v", f"{directory}:/evidence",
               "-v", f"{ROOT / 'baselines/kivi/observe.py'}:/observe.py:ro"]
    if input_path:
        command += ["-v", f"{input_path}:/input:ro"]
    command += [IMAGE, "/observe.py", *options, "-o", "-v", "2", "-to", "60"]
    (directory / "command.json").write_text(json.dumps(command, indent=2), encoding="utf-8")
    with (directory / "kivi.log").open("w", encoding="utf-8") as log:
        subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True)
    result = verifier_result(directory)
    result.update(tool_commit=COMMIT, input_source="document",
                  subject="k8s:kivi-c3/default/Deployment/php-apache")
    (directory / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(directory.name, result, flush=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output = (args.output or ROOT / "results/kivi" / datetime.now().strftime("%Y%m%d-%H%M%S-%f")).resolve()
    output.mkdir(parents=True, exist_ok=False)
    before = output / "inputs/before"
    with tarfile.open(ROOT / ".runtime/kivi-build/source.tar") as archive:
        prefix = "examples/c3/configs/"
        for member in archive.getmembers():
            if member.isfile() and member.name.startswith(prefix):
                target = before / member.name[len(prefix):]
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.extractfile(member).read())
    after = output / "inputs/after"
    shutil.copytree(before, after)
    deployment = after / "yaml/deploy.yaml"
    old = deployment.read_text(encoding="utf-8")
    data = yaml.safe_load(old)
    constraints = data["spec"]["template"]["spec"]["topologySpreadConstraints"]
    zone = [c for c in constraints if c["topologyKey"] == "zone"]
    assert len(zone) == 1 and zone[0]["maxSkew"] == 1
    zone[0]["maxSkew"] = 2
    new = yaml.safe_dump(data, sort_keys=False)
    deployment.write_text(new, encoding="utf-8")
    (output / "repair.patch").write_text("".join(difflib.unified_diff(
        old.splitlines(True), new.splitlines(True), fromfile="before/deploy.yaml", tofile="after/deploy.yaml")), encoding="utf-8")
    cases = {}
    for name, options, inputs in (
        ("paper-violation", ["-c", "c3", "-s", "3"], None),
        ("paper-control", ["-c", "c3", "-s", "3", "-cn"], None),
        ("before", ["-p", "/input"], before),
        ("after", ["-p", "/input"], after),
    ):
        cases[name] = run(output / name, options, inputs)
    assert [cases[name]["status"] for name in cases] == ["fail", "pass", "fail", "pass"], cases
    summary = {"executed_at": datetime.now(timezone.utc).isoformat(), "tool_commit": COMMIT,
               "cases": cases, "repair": "zone topologySpreadConstraints maxSkew: 1 -> 2",
               "scope": "Original model checker; no live Kubernetes failure reproduction"}
    (output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
