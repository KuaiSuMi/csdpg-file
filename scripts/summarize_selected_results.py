"""Cross-check native conference-baseline evidence and saved graph summaries."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "integration"))
from maturity_baselines import BaselineCollector
from maturity_baselines.native import verifier_result


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def suite_counts(path):
    root = ET.parse(path).getroot()
    return {name: int(root.attrib[name]) for name in ("tests", "failures", "errors", "skipped")}


def summarize():
    manifest = read_json(ROOT / "baselines/history/selected-manifest-20261028.json")
    assert manifest["selected"] == ["fetruth", "kivi", "reynard"]
    paths = {key: ROOT / value for key, value in manifest["results"].items()}
    paper = read_json(paths["fetruth_paper"] / "comparison.json")

    def recommendations(name):
        rows = (paths["fetruth_paper"] / name).read_text(encoding="utf-8-sig").splitlines()[1:]
        rows = [tuple(field.strip() for field in row.split("\t")) for row in rows if row.strip()]
        assert len(set(rows)) == len(rows)
        assert all(len(row) == 3 and row[0] == "Move Method" for row in rows)
        return set(rows)

    expected = recommendations("expected-jsoup.txt")
    observed = recommendations("jsoup.txt")
    assert expected == observed and len(observed) == 16 and paper["exact_match"]
    fetruth = read_json(paths["fetruth_project"] / "summary.json")
    assert [fetruth[key] for key in ("candidate_methods", "candidate_pairs", "recommendations")] == [1, 2, 1]
    kivi = {}
    for phase, status in (("paper-violation", "fail"), ("paper-control", "pass"), ("before", "fail"), ("after", "pass")):
        kivi[phase] = verifier_result(paths["kivi"] / phase)
        assert kivi[phase]["status"] == status
    contract, faultsets, graphs = {}, {}, {}
    for phase, failures in (("before", 4), ("after", 0)):
        for baseline, directory in (("fetruth", paths["fetruth_project"]),
                                    ("kivi", paths["kivi"] / phase),
                                    ("reynard", paths["reynard_contract"] / phase)):
            report = BaselineCollector(baseline, directory, namespace="baseline-validation").collect()
            assert not report.warnings and report.metrics["status"] == "ok", report.warnings
        contract[phase] = suite_counts(paths["reynard_contract"] / phase / "junit.xml")
        assert contract[phase] == {"tests": 5, "failures": failures, "errors": 0, "skipped": 0}
        observations = [read_json(p) for p in (paths["reynard_contract"] / phase / "observations").glob("*.json")]
        faultsets[phase] = {json.dumps(o["faultload"]["faults"], sort_keys=True) for o in observations}
        graph = read_json(paths[phase + "_graph"])
        ids = {n["id"] for n in graph["nodes"]}
        assert len(ids) == len(graph["nodes"]) == 13
        assert len(graph["edges"]) == 9
        assert all(e["source"] in ids and e["target"] in ids for e in graph["edges"])
        assert set(graph["meta"]["baseline_runs"]) == {"baseline-" + b for b in manifest["selected"]}
        assert all(r["status"] == "ok" for r in graph["meta"]["baseline_runs"].values())
        graphs[phase] = graph["stats"]
    assert faultsets["before"] == faultsets["after"]
    ser = {}
    for key, expected_count in (("reynard_ser", 543), ("reynard_no_ser", 1849)):
        files = list(paths[key].glob("TEST-*.xml"))
        assert len(files) == 1
        ser[key] = suite_counts(files[0])
        assert ser[key] == {"tests": expected_count, "failures": 0, "errors": 0, "skipped": 0}
    comparison = read_json(paths["comparison"])
    assert comparison["counts"] == {"check-passed-after": 5, "unchanged": 2}
    result = {
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "experiment_date": manifest["date"], "project_commit": manifest["project"]["commit"],
        "selected": manifest["selected"], "fetruth_paper": paper, "fetruth_project": fetruth,
        "kivi": kivi, "reynard_contract": contract, "same_faultsets_before_after": True,
        "reynard_ser": ser, "ser_execution_reduction_percent": round((1849 - 543) / 1849 * 100, 4),
        "graphs": graphs, "graph_comparison": comparison["counts"],
        "interpretation": "Five passed observations are one Kivi intent and four fault modes of one runtime contract; they are not five independent bugs",
        "not_run": manifest["scope"]["not_run"]}
    target = paths["summary"]
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"validated": True, "output": str(target), "selected": manifest["selected"],
                      "graph_comparison": result["graph_comparison"]}, ensure_ascii=False))


if __name__ == "__main__":
    summarize()

