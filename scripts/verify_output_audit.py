"""Verify the historical 2026-11-11 experiments and their archived illustrated report."""
import json
from pathlib import Path
import re
import struct
import xml.etree.ElementTree as ET

import yaml

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/output-audit/20261111"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def main():
    coverage = {}
    fe = ROOT / "results/fetruth-project/20261111-141246-910830"
    features, summary = read(fe / "features.json")["RECORDS"], read(fe / "summary.json")
    rows = (fe / "recommendations.tsv").read_text(encoding="utf-8").splitlines()
    assert len(features) == summary["candidate_methods"] == 1
    assert len(rows) - 1 == summary["recommendations"] == 1
    assert summary["candidate_pairs"] == 2
    assert rows[1].split("\t")[2].strip() in features[0]["target_class_list"].split(", ")
    for suffix in ("dist", "cbmc", "mcmc"):
        assert len(features[0]["target_" + suffix + "_list"].split(", ")) == 2
    coverage["fetruth"] = ["TSV recommendations", "JSON candidate features and couplings", "coverage statistics", "extraction and inference logs"]

    for phase, status, states in (("paper-violation", "fail", 207), ("paper-control", "pass", 669),
                                  ("before", "fail", 220), ("after", "pass", 1830)):
        directory = OUT / "kivi" / phase
        result = read(directory / "result.json")
        assert result["status"] == status and result["stored_states"] == states
        assert result["spin_errors"] == int(status == "fail")
        for name in ("main.pml", "config.pml", "event.pml", "intentsCheck.pml"):
            assert any(p.stat().st_size for p in directory.rglob(name))
        if status == "fail":
            assert "No feasible node!" in (directory / "process-3.stdout.txt").read_text(encoding="utf-8")
    assert "+      - maxSkew: 2" in (OUT / "kivi/repair.patch").read_text(encoding="utf-8")
    coverage["kivi"] = ["generated Promela models", "4 property results", "search state counts", "counterexample replay", "YAML patch"]

    reynard = ROOT / "results/reynard-contract/20261111-141246-936241"
    for phase, failed in (("before", 4), ("after", 0)):
        suite = ET.parse(reynard / phase / "junit.xml").getroot()
        assert [int(suite.attrib[k]) for k in ("tests", "failures", "errors", "skipped")] == [5, failed, 0, 0]
        records = [read(p) for p in (reynard / phase / "observations").glob("*.json")]
        assert len(records) == 5 and all(r["injection_verified"] for r in records)
        assert {r["faultload"]["faults"][0]["mode"]["args"][0] for r in records if r["fault_count"]} == {"500", "502", "503", "504"}
    for case, count in (("patterns-ser", 543), ("patterns-no-ser", 1849)):
        file = next((OUT / "ser/reynard" / case).glob("TEST-*.xml"))
        suite = ET.parse(file).getroot()
        assert [int(suite.attrib[k]) for k in ("tests", "failures", "errors", "skipped")] == [count, 0, 0, 0]
    coverage["reynard"] = ["requested and actual injected faults", "proxy traces", "10 business responses and assertions", "JUnit XML", "SER 543 versus 1849 executions"]

    for phase, issues, incidents in (("before", 6, 7), ("after", 4, 5)):
        report = read(OUT / "appcat" / phase / "report.json")
        assert report["metadata"]["status"] == "Complete"
        assert (report["summary"]["totalIssues"], report["summary"]["totalIncidents"]) == (issues, incidents)
        assert sum(len(p["incidents"]) for p in report["projects"]) == incidents
        assert "CONTRACT_OK:2" in (OUT / "appcat" / phase / "business/stdout.txt").read_text(encoding="utf-8")
    yaml_report = yaml.safe_load((OUT / "appcat-yaml/report.yaml").read_text(encoding="utf-8"))
    assert yaml_report["summary"] == read(OUT / "appcat/before/report.json")["summary"]
    dep = [d for p in read(OUT / "appcat-full/dependencies.json") for d in p["dependencies"]]
    assert any(d["name"] == "commons-io.commons-io" and d["version"] == "2.16.1" for d in dep)
    html_check = read(ROOT / "results/report-verification/appcat-html.json")
    for phase, count in (("before", 4), ("after", 2)):
        checked = html_check["phases"][phase]
        assert checked["status"] == "Complete" and checked["native_issue_count"] == count
        assert not checked["errors"] and "No data available" not in checked["list_text"]
        assert "Assessment Report" in checked["details_text"] and "cloud-audit" in checked["details_text"]
        assert checked["summary"] == read(OUT / "appcat" / phase / "report.json")["summary"]
    coverage["appcat"] = ["native JSON and YAML", "rules, incidents, snippets, severity, effort", "technology properties", "dependency list", "business and audit outputs", "loaded native HTML assessment report; issue counts 4 to 2"]

    nv = OUT / "neuvector-complete"
    for phase, uid, privileged in (("before", 0, False), ("privileged", 0, True), ("after", 1000, False)):
        directory = nv / phase
        w, business = read(directory / "workload.json")["workload"], read(directory / "business.json")
        assert w["running"] is True and w["run_as_root"] is (uid == 0) and w["privileged"] is privileged
        assert business == {"status": 200, "body": "maturity-ok\n", "uid": uid}
        pod = next(p for p in read(directory / "pods.json")["items"] if p["metadata"]["uid"] == w["labels"]["io.kubernetes.pod.uid"])
        assert any(s["containerID"].endswith(w["id"]) for s in pod["status"]["containerStatuses"])
        assert pod["spec"]["containers"][0]["securityContext"]["privileged"] is privileged
        for name in ("stats", "process", "process-history", "config", "compliance", "scan"):
            assert read(directory / (name + "-response.json"))["http_status"] == 200
        assert any(p["name"] == "node" and p["root"] is (uid == 0) for p in read(directory / "process-response.json")["body"]["processes"])
        assert all(v >= 0 for v in read(directory / "stats-response.json")["body"]["stats"]["span_1"].values())
        assert read(directory / "score-metrics.json")["security_scores"]["security_risk_score"] == 48
    assert read(nv / "summary.json")["test_namespace_deleted"]
    cis = read(OUT / "neuvector-scanning/bench-kubernetes-after.json")["body"]
    assert cis["cis_version"] == "1.8.0" and len(cis["items"]) == 130
    assert {level: sum(i["level"] == level for i in cis["items"]) for level in ("PASS", "WARN", "MANUAL")} == {"PASS": 52, "WARN": 38, "MANUAL": 40}
    scan_dir = OUT / "neuvector-scanning/cve"
    brief = read(scan_dir / "workload-scanned.json")["workload"]["scan_summary"]
    assert brief["status"] == "finished" and brief["result"] == "succeeded" and brief["scanned_at"]
    scan = read(scan_dir / "scan-report.json")["body"]["report"]
    assert len(scan["vulnerabilities"]) == 27 and len(scan["modules"]) == 209
    assert sum(v["severity"] == "High" for v in scan["vulnerabilities"]) == brief["high"] == 12
    assert sum(v["severity"] == "Medium" for v in scan["vulnerabilities"]) == brief["medium"] == 15
    assert all({"package_name", "package_version", "fixed_version", "score_v3"} <= v.keys() for v in scan["vulnerabilities"])
    coverage["neuvector"] = ["3 security configurations", "Pod/container identity", "UID, capabilities and HTTP", "processes and history", "resource and network statistics", "policy configuration", "global score components", "130 node CIS items", "27 vulnerability records and 209 modules", "preserved first-run privilege discrepancy and pre-scan empty responses"]

    graphs = {p: read(OUT / "graph" / (p + ".kg.json")) for p in ("before", "after")}
    for phase, nodes, edges in (("before", 29, 19), ("after", 27, 17)):
        graph = graphs[phase]
        assert (len(graph["nodes"]), len(graph["edges"])) == (nodes, edges)
        assert set(graph["meta"]["baseline_runs"]) == {"baseline-" + n for n in coverage}
        assert all(v["status"] == "ok" for v in graph["meta"]["baseline_runs"].values())
        assert all(n["provenance"] for n in graph["nodes"] if n["type"] == "Metric")
    counts = read(OUT / "graph/comparison.json")["counts"]
    assert counts == {"check-passed-after": 6, "not-observed-after": 2, "unchanged": 5}

    report = ROOT / "docs/history/20261113-替换前基线调研结果.md"
    markdown = report.read_text(encoding="utf-8")
    assert not re.search(r"[A-Za-z]:[\\/]|YuRui|\.runtime|SonarQube|[0-9a-f]{40}", markdown, re.I)
    assert not re.search(r"(?<!!)\[[^\]]+\]\([^)]+\)", markdown)
    images = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", markdown)
    assert len(images) == 14 and len(set(images)) == 14
    sizes = {}
    for name in images:
        data = (report.parent / name).read_bytes()
        assert data[:8] == b"\x89PNG\r\n\x1a\n"
        sizes[name] = struct.unpack(">II", data[16:24])
        assert sizes[name][0] == 2160
    result = {"date": "2026-11-13", "experiment_date": "2026-11-11", "status": "completed", "tested_outputs": coverage,
              "graph_comparison": counts, "screenshots": sizes,
              "observed_issues": ["AppCAT initial empty table was captured before asynchronous data loading; fixed by waiting for the application row", "First NeuVector privileged sample reported false; new three-case run matched configuration"],
              "empty_outputs": ["NeuVector container-scope compliance items; node-scope report contains 130 items", "NeuVector pre-scan vulnerability report; completed scan contains 27 records"],
              "not_run": ["team otel-demo or full-paper datasets"],
              "reused_checks": "53 existing integration tests; readers and their dependencies unchanged"}
    (ROOT / "results/report-verification/output-audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "completed", "baselines": len(coverage), "images": len(images), "comparison": counts}))


if __name__ == "__main__":
    main()
