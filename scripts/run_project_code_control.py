"""Reproduce six named-constant repairs on a copy of the pinned project Java example."""
import argparse
import csv
from datetime import datetime, timezone
import difflib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--java-home", type=Path, default=ROOT / ".runtime/jdk17/jdk-17.0.20.1+1")
    args = parser.parse_args()
    source = ROOT / "baselines/sources/maturity-evaluate/examples/comprehensive_test_repo/java_app/src/main/java"
    output = ROOT / "results/project-code-control" / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    output.mkdir(parents=True)
    # This is a fixed repair experiment; replacements are tied to the pinned source, not a generic refactorer.
    edits = {
        "InventoryService.java": (
            "    private static final int AVAILABLE_STOCK = 100;\n",
            {"quantity <= 100": "quantity <= AVAILABLE_STOCK"}),
        "PaymentService.java": (
            "    private static final int PAYMENT_LIMIT = 10000;\n",
            {"amount > 10000": "amount > PAYMENT_LIMIT"}),
        "OrderService.java": (
            "    private static final int LARGE_ORDER = 100;\n"
            "    private static final int MEDIUM_ORDER = 50;\n"
            "    private static final double LARGE_RATE = 0.9;\n"
            "    private static final double MEDIUM_RATE = 0.95;\n",
            {"quantity >= 100": "quantity >= LARGE_ORDER", "quantity >= 50": "quantity >= MEDIUM_ORDER",
             "total *= 0.9;": "total *= LARGE_RATE;", "total *= 0.95;": "total *= MEDIUM_RATE;"})}
    patch = []
    summary = {"date": datetime.now(timezone.utc).isoformat(), "cases": {}}
    for phase in ("before", "after"):
        dest = output / phase
        src, classes, analysis = dest / "src", dest / "classes", dest / "designite"
        shutil.copytree(source, src)
        classes.mkdir()
        analysis.mkdir()
        if phase == "after":
            for filename, (constants, replacements) in edits.items():
                path = src / "com/example" / filename
                original = path.read_text(encoding="utf-8")
                marker = f"public class {path.stem} {{"
                assert original.count(marker) == 1
                changed = original.replace(marker, marker + "\n" + constants)
                for old, new in replacements.items():
                    assert changed.count(old) == 1, (filename, old)
                    changed = changed.replace(old, new)
                path.write_text(changed, encoding="utf-8")
                relative = "com/example/" + filename
                patch.extend(difflib.unified_diff(original.splitlines(True), changed.splitlines(True),
                                                fromfile="a/" + relative, tofile="b/" + relative))
        java = args.java_home / "bin/java.exe"
        with (dest / "compile.log").open("w", encoding="utf-8") as log:
            subprocess.run([str(args.java_home / "bin/javac.exe"), "-encoding", "UTF-8", "-d", str(classes),
                            *map(str, sorted(src.rglob("*.java"))),
                            str(ROOT / "baselines/fixtures/ProjectContract.java")],
                           check=True, stdout=log, stderr=subprocess.STDOUT)
        contract = subprocess.run([str(java), "-cp", str(classes), "ProjectContract"], check=True,
                                  capture_output=True, encoding="utf-8")
        (dest / "contract.log").write_text(contract.stdout + contract.stderr, encoding="utf-8")
        assert "contract_checks=23" in contract.stdout
        with (dest / "designite.log").open("w", encoding="utf-8") as log:
            subprocess.run([str(java), "-Dfile.encoding=UTF-8", "-jar",
                            str(ROOT / "baselines/sources/designite-java/target/DesigniteJava.jar"),
                            "-i", str(src), "-o", str(analysis)], check=True,
                           stdout=log, stderr=subprocess.STDOUT)
        with (analysis / "implementationCodeSmells.csv").open(encoding="utf-8-sig", newline="") as stream:
            smells = list(csv.DictReader(stream))
        summary["cases"][phase] = {"magic_number_rows": sum(r["Code Smell"] == "Magic Number" for r in smells),
                                   "contract_checks_passed": 23}
    assert [summary["cases"][p]["magic_number_rows"] for p in ("before", "after")] == [10, 4]
    (output / "repair.patch").write_text("".join(patch), encoding="utf-8")
    (output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(output)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
