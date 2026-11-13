"""Run pinned GLITCH and Infer/Pulse with their built-in checks, saving native evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def command(args, output):
    started = time.monotonic()
    result = subprocess.run(args, cwd=ROOT, capture_output=True)
    (output / "stdout.txt").write_bytes(result.stdout)
    (output / "stderr.txt").write_bytes(result.stderr)
    record = dict(command=args, exit_code=result.returncode,
                  seconds=round(time.monotonic() - started, 3))
    write_json(output / "process.json", record)
    if result.returncode:
        raise RuntimeError(f"Command failed ({result.returncode}); see {output / 'stderr.txt'}")
    return record


def run(tool, project, source, output):
    source = source.resolve()
    output.mkdir(parents=True, exist_ok=False)
    image = "maturity-glitch:1.0.1" if tool == "glitch" else "maturity-infer:1.3.0"
    image_id = subprocess.check_output(["docker", "image", "inspect", image, "--format", "{{.Id}}"], text=True).strip()
    args = ["docker", "run", "--rm", "--network", "none", "-v", f"{source}:/input:ro",
            "-v", f"{output.resolve()}:/out"]
    if tool == "infer":
        args += ["-v", f"{ROOT / '.runtime/infer-download/deps'}:/deps:ro"]
    args += [image]
    if tool == "glitch":
        # Both public inputs are Ansible roles; fixtures are task lists.
        args += ["--tech", "ansible", "--smells", "security", "--csv"]
        args += ["--module", "/input"] if project.startswith("ansible-") else ["--type", "tasks", "/input/tasks.yml"]
        args += ["/out/findings.csv"]
    else:
        files = sorted(source.rglob("*.java"))
        assert files, f"No Java sources in {source}"
        (output / "sources.txt").write_text("\n".join('/input/' + p.relative_to(source).as_posix() for p in files) + "\n", encoding="utf-8")
        args += ["run", "--pulse-only", "--jobs", "2", "--results-dir", "/out/infer-out",
                 "--project-root", "/input", "--", "javac", "-encoding", "UTF-8", "-cp", "/deps/jsr305-3.0.2.jar", "-d", "/out/classes", "@/out/sources.txt"]
    process = command(args, output)
    if tool == "glitch":
        rows = (output / "findings.csv").read_text(encoding="utf-8").splitlines()
        assert all(len(row.split(",", 3)) == 4 and row.split(",", 3)[2].startswith("sec_") for row in rows)
        native = (output / "stdout.txt").read_text(encoding="utf-8")
        count = re.search(r"Total IaC files.*?\n\+[^\n]+\n\|\s*(\d+)\s*\|\s*(\d+)", native, re.S)
        assert count, "Native file/LOC coverage missing"
        coverage = dict(files=int(count[1]), lines=int(count[2]))
        assert coverage["files"] > 0
        stderr = (output / "stderr.txt").read_text(encoding="utf-8")
        assert not re.search(r"Ansible -|Could not parse|Traceback", stderr), "GLITCH reported a parse error"
        report = output / "findings.csv"
    else:
        report = output / "infer-out/report.json"
        rows = json.loads(report.read_text(encoding="utf-8"))
        assert isinstance(rows, list)
        capture = (output / "infer-out/logs").read_text(encoding="utf-8")
        count = re.search(r"Found (\d+) source files? to analyze", capture)
        assert count and int(count[1]) == len(files), "Capture did not cover the submitted Java files"
        coverage = dict(files=len(files))
    summary = dict(tool=tool, project=project, input=str(source.relative_to(ROOT)),
                   image=image, image_id=image_id, exit_code=process["exit_code"],
                   seconds=process["seconds"], coverage=coverage, findings=len(rows),
                   report=str(report.relative_to(output)),
                   report_sha256=hashlib.sha256(report.read_bytes()).hexdigest(),
                   custom_business_rules=False)
    write_json(output / "summary.json", summary)
    print(f'{tool}/{project}: {len(rows)} findings, {coverage}', flush=True)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tool", choices=["glitch", "infer"], required=True)
    parser.add_argument("--output", type=Path, required=True, help="New output directory; previous evidence is never overwritten")
    args = parser.parse_args()
    base = args.output.resolve()
    if args.tool == "glitch":
        cases = [(name, ROOT / "baselines/sources" / name) for name in ("ansible-role-nginx", "ansible-role-redis")]
    else:
        cases = [(name, ROOT / "baselines/sources" / name / "src/main/java") for name in ("jsoup", "commons-cli")]
        cases.append(("maturity-java", ROOT / "baselines/sources/maturity-evaluate/examples/comprehensive_test_repo/java_app/src/main/java"))
    cases += [(phase, ROOT / "baselines" / args.tool / "fixtures" / phase) for phase in ("before", "after")]
    results = [run(args.tool, name, path, base / name) for name, path in cases]
    before, after = results[-2:]
    assert before["findings"] > 0 and after["findings"] == 0, "Controlled repair was not detected"
    write_json(base / "summary.json", results)


if __name__ == "__main__":
    main()
