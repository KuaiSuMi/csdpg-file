"""Convert AppCAT's native report into source findings and scan statistics."""
from collections import defaultdict
import json
from pathlib import Path


def read_appcat(directory):
    path = Path(directory) / "report.json"
    report = json.loads(path.read_text(encoding="utf-8-sig"))
    metadata = report["metadata"]
    if metadata["status"] != "Complete":
        raise ValueError("AppCAT analysis must be Complete")
    targets = metadata["targetIds"]
    if not targets or any(not isinstance(t, str) or not t for t in targets) or len(set(targets)) != len(targets):
        raise ValueError("AppCAT targetIds must contain distinct target names")
    projects, rules = report["projects"], report["rules"]
    if not isinstance(projects, list) or not projects or not isinstance(rules, dict):
        raise ValueError("AppCAT report must contain projects and a rules object")
    groups, seen_ids, seen_projects = defaultdict(list), set(), set()
    incident_count = 0
    for pi, project in enumerate(projects):
        project_path = project["path"]
        if not isinstance(project_path, str) or not project_path or project_path in seen_projects:
            raise ValueError("AppCAT project path is missing or duplicated")
        seen_projects.add(project_path)
        for ii, incident in enumerate(project["incidents"]):
            incident_count += 1
            identity = (project_path, incident["incidentId"])
            if not identity[1] or identity in seen_ids:
                raise ValueError("AppCAT incidentId is missing or duplicated")
            seen_ids.add(identity)
            rule_id, location = incident["ruleId"], incident["location"]
            rule = rules[rule_id]
            if rule["id"] != rule_id or not isinstance(location, str):
                raise ValueError("AppCAT rule identity or source location is invalid")
            labels = incident["labels"]
            violation = "type=violation" in labels
            if violation == ("type=insight" in labels):
                raise ValueError("AppCAT incident must be a violation or an insight")
            for target in targets:
                if violation and target not in incident["targets"]:
                    continue
                groups[(project_path, location, target, rule_id, violation)].append(
                    (f"/projects/{pi}/incidents/{ii}", incident))
    if incident_count != report["summary"]["totalIncidents"] or len(projects) != report["summary"]["totalProjects"]:
        raise ValueError("AppCAT summary disagrees with native incidents/projects")

    records = []
    for (project, location, target, rule_id, violation), rows in sorted(groups.items()):
        rule = rules[rule_id]
        selected = rows[0][1]["targets"][target] if violation else rule
        records.append(dict(
            subject=f"appcat:{project}:{location or '<project>'}", type="Module",
            rule=rule_id, key=[target, rule_id],
            status="candidate" if violation else "measured", source="source_code",
            attributes={"target": target, "project": project, "location": location,
                        "title": rule["title"], "description": rule["description"],
                        "severity": selected["severity"], "effort": selected["effort"],
                        "occurrences": len(rows), "analysis_status": metadata["status"],
                        "observed_at": metadata["analysisEndTime"],
                        "coverage": "reported-incidents",
                        "locations": [{k: row[k] for k in ("incidentId", "location", "line", "column", "snippet")
                                       if k in row} for _, row in rows]},
            evidence=[(path, pointer, row) for pointer, row in rows]
                     + [(path, "/rules/" + rule_id, rule), (path, "/metadata", metadata)]))
    # A complete empty report is scan evidence, not proof that every possible rule passed.
    records.append(dict(
        subject="appcat:analysis", type="Module", rule="report-summary", key=["report-summary"],
        status="measured", source="source_code",
        attributes={"analysis_status": metadata["status"], "targets": targets,
                    "observed_at": metadata["analysisEndTime"],
                    "summary": report["summary"], "coverage": "reported-incidents"},
        evidence=[(path, "/summary", report["summary"]), (path, "/metadata", metadata)]))
    return records
