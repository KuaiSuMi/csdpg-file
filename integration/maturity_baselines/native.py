"""Read native evidence for the selected conference baselines."""
import csv
import hashlib
import json
from pathlib import Path
import re


def read_fetruth(directory):
    summary_path = directory / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    features_path = directory / "features.json"
    features = json.loads(features_path.read_text(encoding="utf-8"))["RECORDS"]
    if summary["exit_code"] != 0 or not features:
        raise ValueError("feTruth extraction/inference did not provide nonempty coverage")
    if hashlib.sha256(features_path.read_bytes()).hexdigest() != summary["feature_sha256"]:
        raise ValueError("feTruth feature evidence changed")
    if len({row["id"] for row in features}) != len(features):
        raise ValueError("Duplicate feTruth candidate identity")
    candidates = {}
    for row in features:
        method = row["source_class_name"] + "::" + row["method_signature"]
        for target in row["target_class_list"].split(", "):
            key = (method, target)
            if key in candidates:
                raise ValueError("Duplicate method/target candidate")
            candidates[key] = row
    if len(features) != summary["candidate_methods"] or len(candidates) != summary["candidate_pairs"]:
        raise ValueError("feTruth coverage counts do not match features")
    native = directory / "recommendations.tsv"
    with native.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        if reader.fieldnames != ["Refactoring Type", "Source Method", "Target Class"]:
            raise ValueError("Unexpected feTruth columns")
        rows = list(reader)
    if len(rows) != summary["recommendations"]:
        raise ValueError("feTruth recommendation count mismatch")
    records, seen = [], set()
    for number, row in enumerate(rows, 2):
        if None in row or any(value is None for value in row.values()):
            raise ValueError("Malformed feTruth recommendation")
        row = {key: value.strip() for key, value in row.items()}
        key = (row["Source Method"], row["Target Class"])
        if row["Refactoring Type"] != "Move Method" or key not in candidates or key in seen:
            raise ValueError("Recommendation missing from extracted candidates or duplicated")
        seen.add(key)
        feature = candidates[key]
        records.append(dict(subject="java:" + feature["source_class_name"], type="Module",
                            rule="Feature Envy", key=list(key), status="candidate", source="source_code",
                            attributes={"method_signature": feature["method_signature"],
                                        "target_class": key[1], "threshold": summary["threshold"],
                                        "workflow": summary["workflow"], "model_sha256": summary["model_sha256"],
                                        "interpretation": "move-method-candidate-needs-validation"},
                            evidence=[(native, f"record={number}", row),
                                      (features_path, f"id={feature['id']}", feature), (summary_path, "", summary)]))
    records.append(dict(subject="java-analysis:" + features[0]["project_name"], type="Module",
                        rule="candidate-coverage", key=["candidate-coverage"], status="measured", source="source_code",
                        attributes={key: summary[key] for key in ("candidate_methods", "candidate_pairs", "recommendations", "workflow")},
                        evidence=[(summary_path, "", summary)]))
    return records


def verifier_result(directory):
    processes = json.loads((directory / "processes.json").read_text(encoding="utf-8"))
    if not processes or any(p["exit_code"] != 0 for p in processes):
        raise ValueError("A verifier subprocess failed")
    runs = [p for p in processes if p["command"][0] == "./pan" and "-r" not in p["command"]]
    if len(runs) != 1:
        raise ValueError("Expected exactly one fixed-topology verification")
    filename = runs[0]["stdout"]
    if not re.fullmatch(r"process-\d+\.stdout\.txt", filename):
        raise ValueError("Invalid native evidence filename")
    raw = (directory / filename).read_text(encoding="utf-8")
    match = re.search(r"errors:\s*(\d+)", raw)
    if not match or "elapsed time" not in raw or "max search depth too small" in raw:
        raise ValueError("No complete SPIN result")
    errors = int(match[1])
    if errors == 0 and "search not completed" in raw.lower():
        raise ValueError("Incomplete search is not a passing result")
    log = (directory / "kivi.log").read_text(encoding="utf-8")
    if "Working on the intents: pod_always_schedulable" not in log:
        raise ValueError("Schedulability intent was not checked")
    if errors and ("no_feasible_node" not in log or "No feasible node" not in log):
        raise ValueError("Failure does not match the checked schedulability intent")
    states = re.search(r"([\deE+.-]+) states, stored", raw)
    return {"status": "fail" if errors else "pass", "spin_errors": errors,
            "stored_states": float(states[1]) if states else None,
            "intent": "pod_always_schedulable", "scope": "fixed-topology-model",
            "native_stdout": filename}


def read_kivi(directory):
    checked = verifier_result(directory)
    result_path = directory / "result.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    if any(result.get(key) != value for key, value in checked.items()):
        raise ValueError("Kivi summary disagrees with native SPIN output")
    if result["input_source"] not in {"document", "deployment"} or not result["subject"].startswith("k8s:"):
        raise ValueError("Kivi subject/source must be explicit")
    model_path = directory / "model-input.json"
    model = json.loads(model_path.read_text(encoding="utf-8"))
    if not model["setup"]["nodes"] or not model["setup"]["d"]:
        raise ValueError("Kivi model has no topology/workload coverage")
    return [dict(subject=result["subject"], type="Deployment", rule=checked["intent"],
                 key=[checked["intent"]], status=checked["status"], source=result["input_source"],
                 attributes={**checked, "tool_commit": result["tool_commit"],
                             "interpretation": "model-result-not-live-fault-test"},
                 evidence=[(result_path, "", result), (model_path, "", model),
                           (directory / checked["native_stdout"], "", {"stdout": (directory / checked["native_stdout"]).read_text()}),
                           (directory / "kivi.log", "", {"log": (directory / "kivi.log").read_text()})])]
