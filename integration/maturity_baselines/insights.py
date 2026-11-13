"""Read Deployment action items using the published Fairwinds Insights API contract."""
from datetime import datetime
import json
import math


def read_insights(path):
    rows = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(rows, list) or not rows:
        raise ValueError("Expected a nonempty API action-item array; empty export is not coverage")
    records, seen, scopes = [], set(), set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError("Each action item must be an object")
        required = ("Organization", "Cluster", "ReportType", "EventType", "ResourceNamespace",
                    "ResourceKind", "ResourceName", "Title", "LastReportedAt")
        if any(not isinstance(row.get(k), str) or not row[k].strip() for k in required):
            raise ValueError("Action item lacks identity, rule, title or observation time")
        if type(row.get("ID")) is not int or row["ID"] <= 0 or row["ID"] in seen:
            raise ValueError("Action item ID is invalid or duplicated")
        seen.add(row["ID"])
        scopes.add((row["Organization"], row["Cluster"]))
        if len(scopes) != 1 or row["ResourceKind"] != "Deployment":
            raise ValueError("Export must contain one organization/cluster and Deployment items only")
        if type(row.get("Fixed")) is not bool or row.get("IsCustom") is not False:
            raise ValueError("Require explicit Fixed and IsCustom=false for vendor-generated checks")
        severity = row.get("Severity")
        if type(severity) not in (int, float) or not math.isfinite(severity):
            raise ValueError("Severity must be a finite vendor number")
        observed = datetime.fromisoformat(row["LastReportedAt"].replace("Z", "+00:00"))
        if observed.tzinfo is None:
            raise ValueError("Observation time must include its timezone")
        if not isinstance(row.get("Resolution"), str):
            raise ValueError("Preserve the explicit vendor Resolution field")
        container = row.get("ResourceContainer")
        if container is not None and not isinstance(container, str):
            raise ValueError("ResourceContainer must be a string or null")
        if row.get("DeletedAt") is not None and not isinstance(row["DeletedAt"], str):
            raise ValueError("DeletedAt must be a string or null")
        # Vendor lifecycle states are not an independent repair-correctness test.
        status = ("vendor-deleted" if row.get("DeletedAt") else
                  "vendor-fixed" if row["Fixed"] else
                  "vendor-resolution-recorded" if row["Resolution"] else "candidate")
        subject = "k8s:" + "/".join(row[k] for k in (
            "Organization", "Cluster", "ResourceNamespace", "ResourceKind", "ResourceName"))
        records.append(dict(
            subject=subject, type="Deployment", rule=row["EventType"],
            key=[row["ID"]], status=status, source="deployment",
            attributes={"action_item_id": row["ID"], "report_type": row["ReportType"],
                        "title": row["Title"], "severity": severity, "resource_container": container,
                        "vendor_fixed": row["Fixed"], "vendor_resolution": row["Resolution"],
                        "last_reported_at": row["LastReportedAt"],
                        "interpretation": "vendor-lifecycle-not-independent-repair-verification",
                        "coverage": "exported-items-only-not-a-complete-cluster-audit"},
            evidence=[(path, f"index={index}", row)]))
    return records
