"""Synthetic API-contract tests; these are not commercial-platform experiment results."""
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "integration"))
sys.path.insert(0, str(ROOT / "scripts"))
from maturity_baselines import BaselineCollector
from kg_builder import BuildPipeline, BuildSettings
from kg_builder.graph.model import KGNode
from kg_builder.graph.serialization import graph_to_dict
from compare_baseline_graphs import compare


def item():
    return dict(ID=7, Organization="test-org", Cluster="test-cluster", ReportType="polaris",
                EventType="readinessProbeMissing", ResourceNamespace="demo", ResourceKind="Deployment",
                ResourceName="api", ResourceContainer="app", Title="Synthetic contract fixture",
                LastReportedAt="2026-10-29T12:00:00Z", Fixed=False, IsCustom=False,
                Severity=0.5, Resolution="", DeletedAt=None)


def write_report(tmp_path, rows):
    path = tmp_path / "action-items.json"
    path.write_text(json.dumps(rows), encoding="utf-8")
    return path


def test_vendor_item_uses_existing_deployment_and_raw_provenance(tmp_path):
    node = KGNode(id="existing", type="Deployment", name="api", namespace="test",
                  attributes={"replicas": 2})
    collector = BaselineCollector("insights", write_report(tmp_path, [item()]), namespace="test",
                                  bindings={"k8s:test-org/test-cluster/demo/Deployment/api": node})
    report = BuildPipeline(BuildSettings(repo_path=tmp_path, namespace="test", enrich=False)).run(
        collectors=[collector], write_outputs=False)
    assert not report.warnings
    assert report.graph.get_node("existing").attributes["replicas"] == 2
    metric = next(n for n in report.graph.nodes if n.type == "Metric")
    assert metric.attributes["status"] == "candidate"
    assert metric.attributes["coverage"].startswith("exported-items-only")
    assert json.loads(metric.provenance[0].evidence)["ID"] == 7
    assert not node.provenance


@pytest.mark.parametrize("change,expected", [
    ({"Fixed": True}, "vendor-fixed"),
    ({"Resolution": "accepted-risk"}, "vendor-resolution-recorded"),
    ({"DeletedAt": "2026-10-29T13:00:00Z"}, "vendor-deleted"),
])
def test_vendor_lifecycle_does_not_become_verified_repair(tmp_path, change, expected):
    def graph(row):
        collector = BaselineCollector("insights", write_report(tmp_path, [row]), namespace="test")
        report = BuildPipeline(BuildSettings(repo_path=tmp_path, namespace="test", enrich=False)).run(
            collectors=[collector], write_outputs=False)
        assert not report.warnings
        return graph_to_dict(report.graph)
    before, after = graph(item()), graph({**item(), **change})
    metric = next(n for n in after["nodes"] if n["type"] == "Metric")
    assert metric["attributes"]["status"] == expected
    assert "check-passed-after" not in compare(before, after)["counts"]


@pytest.mark.parametrize("damage", ["empty", "duplicate", "custom", "kind", "mixed-cluster", "fixed-type", "time", "shape"])
def test_invalid_vendor_export_is_rejected(tmp_path, damage):
    rows = [item()]
    if damage == "empty": rows = []
    elif damage == "duplicate": rows *= 2
    elif damage == "custom": rows[0]["IsCustom"] = True
    elif damage == "kind": rows[0]["ResourceKind"] = "ClusterRole"
    elif damage == "mixed-cluster": rows.append({**item(), "ID": 8, "Cluster": "other"})
    elif damage == "fixed-type": rows[0]["Fixed"] = "false"
    elif damage == "time": rows[0]["LastReportedAt"] = "2026-10-29T12:00:00"
    elif damage == "shape": rows = {"ActionItems": rows}
    result = BaselineCollector("insights", write_report(tmp_path, rows), namespace="test").collect()
    assert result.metrics["status"] == "error" and not result.nodes


def test_published_contract_contains_consumed_fields_and_cli_runs(tmp_path):
    contract = json.loads((ROOT / "baselines/insights/api-contract.json").read_text(encoding="utf-8"))
    fields = set(contract["ActionItem"]["allOf"][0]["properties"]) | set(contract["AddActionItem"]["properties"])
    assert set(item()) <= fields
    output = tmp_path / "graph.json"
    subprocess.run([sys.executable, str(ROOT / "scripts/build_baseline_graph.py"),
                    "--insights", str(write_report(tmp_path, [item()])),
                    "--namespace", "test", "--output", str(output)],
                   check=True, capture_output=True)
    assert json.loads(output.read_text(encoding="utf-8"))["meta"]["baseline_runs"]["baseline-insights"]["observations"] == 1
