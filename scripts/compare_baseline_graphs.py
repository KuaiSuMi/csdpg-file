"""Compare baseline evidence with explicit treatment of missing checks."""
import argparse
import json
from pathlib import Path


def compare(before, after):
    def metrics(graph):
        return {n["id"]: n for n in graph["nodes"]
                if n["type"] == "Metric" and "baseline" in n["attributes"]}

    old, new = metrics(before), metrics(after)
    rows = []
    for identity in sorted(old.keys() | new.keys()):
        left, right = old.get(identity), new.get(identity)
        a, b = (left or {}).get("attributes", {}), (right or {}).get("attributes", {})
        if a.get("status") == "measured" or b.get("status") == "measured":
            continue
        before_count = a.get("occurrences", int(a.get("status") in {"candidate", "fail"}))
        after_count = b.get("occurrences", int(b.get("status") in {"candidate", "fail"}))
        if left and not right:
            # A disappeared rule has not proved a repair: it may have stopped running.
            outcome = "not-observed-after"
        elif right and not left:
            outcome = "new-observation"
        elif a["status"] in {"candidate", "fail"} and b["status"] == "pass":
            outcome = "check-passed-after"
        elif before_count > after_count:
            outcome = "fewer-candidates"
        elif before_count < after_count:
            outcome = "more-findings"
        elif a["status"] != b["status"]:
            outcome = "status-changed"
        else:
            outcome = "unchanged"
        rows.append({"id": identity, "baseline": (a or b)["baseline"], "rule": (left or right)["name"],
                     "before_count": before_count, "after_count": after_count, "outcome": outcome})
    return {"observations": rows,
            "counts": {status: sum(r["outcome"] == status for r in rows)
                       for status in sorted({r["outcome"] for r in rows})}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("before", type=Path)
    parser.add_argument("after", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = compare(json.loads(args.before.read_text(encoding="utf-8")),
                     json.loads(args.after.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["counts"], ensure_ascii=False))


if __name__ == "__main__":
    main()
