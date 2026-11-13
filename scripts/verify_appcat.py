"""Check native reports and preserve the same order/audit contract across the change."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("results", type=Path)
    parser.add_argument("--jdk", type=Path, default=ROOT / ".runtime/jdk17/jdk-17.0.20.1+1")
    args = parser.parse_args()
    results = args.results.resolve()
    fixture = ROOT / "baselines/fixtures/appcat"
    summary = {"baseline": "Microsoft AppCAT for Java", "version": "7.7.0.11",
               "scope": "controlled Java source fixture; azure-aks; source-only",
               "native_rules_modified": False, "phases": {}}
    for phase in ("before", "after"):
        report = json.loads((results / phase / "report.json").read_text(encoding="utf-8"))
        assert report["metadata"]["status"] == "Complete", report["metadata"]
        assert report["metadata"]["targetIds"] == ["azure-aks"]
        incidents = [i for p in report["projects"] for i in p["incidents"]]
        target = [i for i in incidents if i["ruleId"] == "local-storage-00001"]
        assert len(target) == (1 if phase == "before" else 0), target
        if target:
            assert target[0]["location"].endswith("CloudAudit.java")
        snapshot = results / phase / "input"
        snapshot.mkdir(exist_ok=True)
        hashes = {}
        for source in (fixture / phase).rglob("*"):
            if source.is_file() and source.suffix in (".java", ".xml") and ".mvn" not in source.parts:
                relative = source.relative_to(fixture / phase)
                dest = snapshot / relative
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, dest)
                hashes[relative.as_posix()] = hashlib.sha256(source.read_bytes()).hexdigest()
        business = results / phase / "business"
        business.mkdir(exist_ok=True)
        classes = business / "classes"
        classes.mkdir(exist_ok=True)
        compile_result = subprocess.run([str(args.jdk / "bin/javac.exe"), "-encoding", "UTF-8",
            "-d", str(classes), str(snapshot / "src/main/java/com/example/CloudAudit.java"),
            str(fixture / "Contract.java")], capture_output=True, text=True, check=True)
        (business / "compile.log").write_text(compile_result.stdout + compile_result.stderr, encoding="utf-8")
        audit_file = business / "orders.log"
        initial_size = audit_file.stat().st_size if audit_file.exists() else 0
        run = subprocess.run([str(args.jdk / "bin/java.exe"), "-cp", str(classes), "Contract"],
                             cwd=business, capture_output=True, text=True, check=True)
        (business / "stdout.txt").write_text(run.stdout, encoding="utf-8")
        assert "CONTRACT_OK:2" in run.stdout
        audit = audit_file.read_bytes()[initial_size:].decode().strip() if phase == "before" else run.stdout.splitlines()[0]
        assert audit == "AUDIT ORD-book-2", audit
        summary["phases"][phase] = {"native_status": report["metadata"]["status"],
            "native_summary": report["summary"], "local_storage_incidents": len(target),
            "violation_incidents": sum("type=violation" in i.get("labels", []) for i in incidents),
            "contract_checks_passed": 2, "audit_record": audit, "source_sha256": hashes}
    summary["validation"] = "passed: complete native reports, issue removed, order and audit contracts preserved"
    save(results / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
