"""Import native GLITCH/Pulse findings; absence of findings is never a proof of safety."""
import hashlib
import json
from pathlib import Path


def read_academic(directory, tool):
    directory = Path(directory)
    summary_path = directory / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    process = json.loads((directory / "process.json").read_text(encoding="utf-8"))
    if summary["tool"] != tool or summary["exit_code"] != 0 or process["exit_code"] != 0:
        raise ValueError("Analysis was not completed successfully")
    if summary["coverage"]["files"] <= 0 or summary["custom_business_rules"] is not False:
        raise ValueError("No supported source coverage or unexpected custom rules")
    report = directory / ("findings.csv" if tool == "glitch" else "infer-out/report.json")
    if hashlib.sha256(report.read_bytes()).hexdigest() != summary["report_sha256"]:
        raise ValueError("Native report changed after summarization")
    records = []
    if tool == "glitch":
        rows = report.read_text(encoding="utf-8").splitlines()
        for index, raw in enumerate(rows, 1):
            # GLITCH's native export does not CSV-escape the trailing code snippet.
            file, line, rule, snippet = raw.split(",", 3)
            if not file.startswith("/input/") or not rule.startswith("sec_") or int(line) < 1:
                raise ValueError("Malformed GLITCH finding")
            file = file.removeprefix("/input/")
            records.append(dict(subject="iac:" + file, type="Config", rule=rule,
                                key=[file, int(line), rule], status="candidate", source="source_code",
                                attributes=dict(file=file, line=int(line), snippet=snippet),
                                evidence=[(report, f"line={index}", raw)]))
    else:
        rows = json.loads(report.read_text(encoding="utf-8"))
        if not isinstance(rows, list):
            raise ValueError("Infer report must be an array")
        for index, row in enumerate(rows):
            if not row["file"] or row["line"] < 1 or not row["bug_type"] or not row["bug_trace"]:
                raise ValueError("Incomplete Infer finding")
            records.append(dict(subject="java:" + row["file"], type="Module", rule=row["bug_type"],
                                key=[row["file"], row["line"], row["bug_type"], row["procedure"]],
                                status="candidate", source="source_code",
                                attributes={key: row[key] for key in ("file", "line", "procedure", "qualifier", "severity", "bug_trace")},
                                evidence=[(report, f"/{index}", row)]))
    if len(rows) != summary["findings"]:
        raise ValueError("Finding count disagrees with native report")
    records.append(dict(subject=f'{tool}-analysis:{summary["project"]}', type="Module",
                        rule="analysis-coverage", key=["analysis-coverage"], status="measured", source="source_code",
                        attributes={key: summary[key] for key in ("project", "coverage", "findings", "image_id")},
                        evidence=[(summary_path, "", summary)]))
    return records
