"""Reader contracts exercised with archived native AppCAT/NeuVector results."""
import copy
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

ARCHIVE = ROOT / "results/commercial"
CLUSTER = "maturity-baselines"


def native(name, phase="before"):
    return ARCHIVE / name / "20261111-paired" / phase


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")
    return path.parent


def snapshot(tmp_path, name, phase="before"):
    files = ["report.json"] if name == "appcat" else ["workload.json", "pods.json", "deployment.json", "score-metrics.json"]
    for file in files:
        save(tmp_path / file, read(native(name, phase) / file))
    return tmp_path


def collect(name, directory, **kwargs):
    return BaselineCollector(name, directory, namespace="test", cluster=CLUSTER, **kwargs).collect()


def graph(name, phase):
    collector = BaselineCollector(name, native(name, phase), namespace="test", cluster=CLUSTER)
    report = BuildPipeline(BuildSettings(repo_path=ROOT, namespace="test", enrich=False)).run(
        collectors=[collector], write_outputs=False)
    assert not report.warnings
    return graph_to_dict(report.graph)


def test_appcat_preserves_native_positions_severity_and_raw_evidence():
    result = collect("appcat", native("appcat"))
    assert not result.warnings
    finding = next(n for n in result.nodes if n.type == "Metric" and n.name == "local-storage-00001")
    assert finding.attributes["status"] == "candidate"
    assert finding.attributes["severity"] == "mandatory"
    assert finding.attributes["occurrences"] == 1
    assert finding.attributes["locations"][0]["line"] == 3
    assert json.loads(finding.provenance[0].evidence)["ruleId"] == "local-storage-00001"
    assert finding.attributes["location"].endswith("CloudAudit.java")
    assert all(n.attributes["status"] == "measured" for n in result.nodes
               if n.type == "Metric" and n.name.startswith("discover-"))
    summary = next(n for n in result.nodes if n.type == "Metric" and n.name == "report-summary")
    assert summary.attributes["summary"]["totalIncidents"] == 7


@pytest.mark.parametrize("damage", ["incomplete", "count", "duplicate", "project", "missing-rule"])
def test_appcat_rejects_invalid_native_report(tmp_path, damage):
    report = read(native("appcat") / "report.json")
    if damage == "incomplete": report["metadata"]["status"] = "Incomplete"
    elif damage == "count": report["summary"]["totalIncidents"] = 0
    elif damage == "duplicate": report["projects"][0]["incidents"].append(report["projects"][0]["incidents"][0])
    elif damage == "project": report["projects"].append(report["projects"][0])
    elif damage == "missing-rule": del report["rules"]["local-storage-00001"]
    result = collect("appcat", save(tmp_path / "report.json", report))
    assert result.warnings and result.metrics["status"] == "error" and not result.nodes


def test_appcat_groups_locations_without_using_incident_uuid_or_line_as_identity(tmp_path):
    report = read(native("appcat") / "report.json")
    for item in report["projects"][0]["incidents"]:
        item["incidentId"] += "-rerun"
        if "line" in item: item["line"] += 20
    original = collect("appcat", native("appcat"))
    shifted = collect("appcat", save(tmp_path / "report.json", report))
    assert not shifted.warnings
    assert {n.id for n in original.nodes} == {n.id for n in shifted.nodes}
    version = next(n for n in shifted.nodes if n.type == "Metric" and n.name == "azure-java-version-02000")
    assert version.attributes["occurrences"] == 2


def test_appcat_complete_empty_report_retains_statistics_without_inventing_passes(tmp_path):
    report = read(native("appcat") / "report.json")
    report["projects"][0]["incidents"] = []
    report["summary"]["totalIncidents"] = 0
    report["summary"]["totalIssues"] = 0
    report["rules"] = {}
    result = collect("appcat", save(tmp_path / "report.json", report))
    assert not result.warnings and result.metrics["observations"] == 1
    assert all(n.attributes["status"] == "measured" for n in result.nodes if n.type == "Metric")


def test_appcat_absent_findings_are_reported_as_missing_observations():
    before, after = graph("appcat", "before"), graph("appcat", "after")
    changes = compare(before, after)
    local = next(r for r in changes["observations"] if r["rule"] == "local-storage-00001")
    assert (local["before_count"], local["after_count"], local["outcome"]) == (1, 0, "not-observed-after")
    assert "check-passed-after" not in changes["counts"]


def test_neuvector_rollout_preserves_check_identity_and_original_container_evidence():
    before, after = graph("neuvector", "before"), graph("neuvector", "after")
    root_before = next(n for n in before["nodes"] if n["type"] == "Metric" and n["name"] == "run_as_root")
    root_after = next(n for n in after["nodes"] if n["type"] == "Metric" and n["name"] == "run_as_root")
    assert root_before["id"] == root_after["id"]
    assert root_before["attributes"]["pod_uid"] != root_after["attributes"]["pod_uid"]
    assert root_before["attributes"]["run_as_root"] is True
    assert root_after["attributes"]["run_as_root"] is False
    assert root_after["attributes"]["coverage"] == "observed-container"
    assert json.loads(root_after["provenance"][0]["evidence"])["run_as_root"] is False
    assert compare(before, after)["counts"] == {"check-passed-after": 1, "unchanged": 1}
    for data in (before, after):
        score = next(n for n in data["nodes"] if n["type"] == "Metric" and n["name"] == "security_risk_score")
        assert score["attributes"]["status"] == "measured" and score["attributes"]["security_risk_score"] == 44


@pytest.mark.parametrize("damage", ["root-type", "running", "pod-uid", "container-id", "namespace", "selector", "deleted", "missing-container"])
def test_neuvector_rejects_mismatched_or_stale_objects(tmp_path, damage):
    snapshot(tmp_path, "neuvector")
    file = "workload.json" if damage in {"root-type", "running", "pod-uid", "container-id", "namespace"} else "pods.json"
    data = read(tmp_path / file)
    if damage == "root-type": data["workload"]["run_as_root"] = "false"
    elif damage == "running": data["workload"]["running"] = False
    elif damage == "pod-uid": data["workload"]["labels"]["io.kubernetes.pod.uid"] = "other-pod"
    elif damage == "container-id": data["workload"]["id"] = "other-container"
    elif damage == "namespace": data["workload"]["domain"] = "other-namespace"
    elif damage == "selector": data["items"][0]["metadata"]["labels"]["app"] = "other-app"
    elif damage == "deleted": data["items"][0]["metadata"]["deletionTimestamp"] = "2026-11-11T00:00:00Z"
    elif damage == "missing-container": data["items"][0]["status"]["containerStatuses"] = []
    save(tmp_path / file, data)
    result = collect("neuvector", tmp_path)
    assert result.warnings and result.metrics["status"] == "error" and not result.nodes


def test_neuvector_cluster_is_required_and_part_of_identity():
    missing = BaselineCollector("neuvector", native("neuvector"), namespace="test").collect()
    assert missing.warnings and not missing.nodes
    original = collect("neuvector", native("neuvector"))
    other = BaselineCollector("neuvector", native("neuvector"), namespace="test", cluster="other").collect()
    assert {n.id for n in original.nodes}.isdisjoint(n.id for n in other.nodes)


def bindings():
    meta = read(native("neuvector") / "deployment.json")["metadata"]
    source_key = "appcat:.:src/main/java/com/example/CloudAudit.java"
    deployment_key = f"k8s:{CLUSTER}/{meta['namespace']}/Deployment/{meta['name']}"
    return {
        source_key: KGNode(id="existing-source", type="Module", name="CloudAudit", namespace="test",
                           attributes={"path": "src/main/java/com/example/CloudAudit.java", "keep": True}),
        deployment_key: KGNode(id="existing-deployment", type="Deployment", name=meta["name"], namespace="test",
                               attributes={"cluster": CLUSTER, "namespace": meta["namespace"], "replicas": 1})}


def test_bindings_keep_existing_nodes_and_reject_wrong_deployment():
    mapping = bindings()
    for name in ("appcat", "neuvector"):
        result = collect(name, native(name), bindings=mapping)
        assert not result.warnings
        expected = "existing-source" if name == "appcat" else "existing-deployment"
        assert expected in {e.source for e in result.edges}
    assert all(not n.provenance for n in mapping.values())
    broken = copy.deepcopy(mapping)
    next(n for n in broken.values() if n.type == "Deployment").attributes["cluster"] = "wrong"
    rejected = collect("neuvector", native("neuvector"), bindings=broken)
    assert rejected.warnings and not rejected.nodes


def test_cli_imports_both_readers_into_existing_graph_and_compares(tmp_path):
    mapping = bindings()
    base = tmp_path / "base.json"
    save(base, {"nodes": [n.to_dict() for n in mapping.values()], "edges": [], "meta": {"keep": True}})
    binding_file = tmp_path / "bindings.json"
    save(binding_file, {subject: node.id for subject, node in mapping.items()})
    for phase in ("before", "after"):
        subprocess.run([sys.executable, str(ROOT / "scripts/build_baseline_graph.py"),
                        "--appcat", str(native("appcat", phase)), "--neuvector", str(native("neuvector", phase)),
                        "--cluster", CLUSTER, "--namespace", "test", "--base-graph", str(base),
                        "--bindings", str(binding_file), "--output", str(tmp_path / (phase + ".json"))],
                       check=True, capture_output=True, text=True, encoding="utf-8")
        data = read(tmp_path / (phase + ".json"))
        assert data["meta"]["keep"] is True
        assert set(data["meta"]["baseline_runs"]) == {"baseline-appcat", "baseline-neuvector"}
        assert next(n for n in data["nodes"] if n["id"] == "existing-source")["attributes"]["keep"] is True
    subprocess.run([sys.executable, str(ROOT / "scripts/compare_baseline_graphs.py"),
                    str(tmp_path / "before.json"), str(tmp_path / "after.json"),
                    "--output", str(tmp_path / "comparison.json")], check=True, capture_output=True)
    assert read(tmp_path / "comparison.json")["counts"] == {
        "check-passed-after": 1, "not-observed-after": 2, "unchanged": 3}
