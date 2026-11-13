import hashlib
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "integration"))
from maturity_baselines import BaselineCollector


def evidence(tmp_path, tool, empty=False):
    if tool == "glitch":
        report = tmp_path / "findings.csv"
        report.write_text("" if empty else "/input/tasks.yml,3,sec_https,url: 'http://example.org/a,b'\n", encoding="utf-8")
    else:
        report = tmp_path / "infer-out/report.json"
        report.parent.mkdir()
        report.write_text(json.dumps([] if empty else [dict(
            file="Example.java", line=3, procedure="Example.main()", bug_type="NULLPTR_DEREFERENCE",
            qualifier="value is null", severity="ERROR", bug_trace=[dict(line_number=3, description="dereference")])]), encoding="utf-8")
    summary = dict(tool=tool, project="example", exit_code=0, coverage=dict(files=1),
                   findings=0 if empty else 1, image_id="fixed", custom_business_rules=False,
                   report_sha256=hashlib.sha256(report.read_bytes()).hexdigest())
    (tmp_path / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    (tmp_path / "process.json").write_text('{"exit_code": 0}', encoding="utf-8")
    return report


@pytest.mark.parametrize("tool", ["glitch", "infer"])
def test_native_evidence_and_empty_report_are_not_safety_proofs(tmp_path, tool):
    evidence(tmp_path, tool)
    result = BaselineCollector(tool, tmp_path, namespace="project").collect()
    assert result.metrics == dict(status="ok", observations=2, subjects=2, findings=1)
    finding = next(n for n in result.nodes if n.type == "Metric" and n.attributes["status"] == "candidate")
    assert finding.provenance
    if tool == "glitch":
        assert finding.attributes["snippet"].endswith("a,b'")
    else:
        assert finding.attributes["bug_trace"][0]["line_number"] == 3
    clean = tmp_path / "empty"
    clean.mkdir()
    evidence(clean, tool, empty=True)
    result = BaselineCollector(tool, clean, namespace="project").collect()
    assert result.metrics["findings"] == 0
    assert all(n.attributes.get("status") != "pass" for n in result.nodes)


@pytest.mark.parametrize("tool", ["glitch", "infer"])
@pytest.mark.parametrize("damage", ["report", "exit", "coverage", "count"])
def test_rejects_incomplete_or_changed_evidence(tmp_path, tool, damage):
    report = evidence(tmp_path, tool)
    if damage == "report":
        report.write_text("damaged", encoding="utf-8")
    elif damage == "exit":
        (tmp_path / "process.json").write_text('{"exit_code": 1}', encoding="utf-8")
    else:
        path = tmp_path / "summary.json"
        summary = json.loads(path.read_text(encoding="utf-8"))
        if damage == "coverage":
            summary["coverage"]["files"] = 0
        else:
            summary["findings"] = 0
        path.write_text(json.dumps(summary), encoding="utf-8")
    result = BaselineCollector(tool, tmp_path, namespace="project").collect()
    assert result.metrics["status"] == "error" and not result.nodes
