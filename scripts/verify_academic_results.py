"""Verify current selection, reused native evidence, and unified report artifacts."""
import hashlib
import json
from pathlib import Path
import re
import struct
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]


def read(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8-sig"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def recommendation_rows(path):
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    assert lines[0] == "Refactoring Type\tSource Method\tTarget Class"
    rows = [tuple(x.strip() for x in line.split("\t")) for line in lines[1:] if line.strip()]
    assert all(len(row) == 3 and row[0] == "Move Method" for row in rows)
    return rows


def main():
    manifest = read("baselines/academic-review-manifest.json")
    assert manifest["selected"] == ["infer", "fetruth"]
    assert manifest["commercial_selected"] == ["appcat", "neuvector"]
    assert all(manifest[name]["ccf"] == "A" for name in manifest["selected"])
    assert read("references/authority/candidate-evidence.json")["current_academic_selected"] == manifest["selected"]
    verified = {}
    base = "results/academic-20261113/infer/"
    summaries = read(base + "summary.json")
    for case, expected in {"jsoup": (75, 6), "commons-cli": (23, 0), "maturity-java": (4, 0), "before": (1, 1), "after": (1, 0)}.items():
        prefix = base + case + "/"
        s = read(prefix + "summary.json")
        native = ROOT / prefix / "infer-out/report.json"
        process = read(prefix + "process.json")
        assert s in summaries and process["exit_code"] == s["exit_code"] == 0
        assert "--pulse-only" in process["command"] and s["custom_business_rules"] is False
        assert (s["coverage"]["files"], s["findings"]) == expected
        assert len(read(prefix + "infer-out/report.json")) == expected[1]
        assert digest(native) == s["report_sha256"]
        assert re.search(rf"Found {expected[0]} source files? to analyze", (ROOT / prefix / "infer-out/logs").read_text(encoding="utf-8"))
        verified["infer/" + case] = {"files": expected[0], "findings": expected[1]}
    fp = ROOT / "results/fetruth-paper"
    observed = recommendation_rows(fp / "jsoup.txt")
    expected = recommendation_rows(fp / "expected-jsoup.txt")
    comparison = read("results/fetruth-paper/comparison.json")
    assert len(observed) == len(set(observed)) == 16 and set(observed) == set(expected)
    assert comparison["exact_match"] is True and comparison["exit_code"] == 0
    for folder, summary_name, feature_name, native_name, counts in [
        ("results/fetruth", "execution.json", "jsoup-features.json", "jsoup.txt", (204, 300, 180)),
        ("results/fetruth-project/20261111-141246-910830", "summary.json", "features.json", "recommendations.tsv", (1, 2, 1)),
    ]:
        s = read(folder + "/" + summary_name)
        records = read(folder + "/" + feature_name)["RECORDS"]
        rows = recommendation_rows(ROOT / folder / native_name)
        actual = (len(records), sum(len(x["target_class_list"].split(", ")) for x in records), len(rows))
        assert actual == counts == (s["candidate_methods"], s["candidate_pairs"], s["recommendations"])
        assert s["exit_code"] == 0 and s["threshold"] == 0.95
        assert digest(ROOT / folder / feature_name) == s["feature_sha256"]
        verified[folder] = {"methods": counts[0], "pairs": counts[1], "recommendations": counts[2]}
    shots = read("results/baseline-output-screenshots.json")
    assert shots["selected_academic"] == manifest["selected"]
    assert len(shots["panels"]) == 16
    assert [p["number"] for p in shots["panels"]] == list(range(1, 17))
    report = ROOT / "docs/成熟度评估baseline调研结果.md"
    text = report.read_text(encoding="utf-8")
    images = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", text)
    assert len(images) == len(set(images)) == 16
    assert {str((report.parent / name).resolve()) for name in images} == {str((ROOT / p["file"]).resolve()) for p in shots["panels"]}
    for panel in shots["panels"]:
        assert panel["clipped"] == 0 and panel["box"]["width"] == 1440
        png = (ROOT / panel["file"]).read_bytes()
        assert png[:8] == b"\x89PNG\r\n\x1a\n" and struct.unpack(">I", png[16:20])[0] == 2160
    for source, checksum in shots["input_sha256"].items():
        assert digest(ROOT / source) == checksum, source
    paths = [ROOT / "README.md", *ROOT.joinpath("docs").glob("*.md"), ROOT / "references/README.md", ROOT / "references/authority/README.md"]
    links = 0
    for path in paths:
        for target in re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
            if re.match(r"[a-zA-Z]+://|#", target):
                continue
            target_path = (path.parent / unquote(target.split("#")[0])).resolve()
            assert target_path.exists(), f"Broken local link: {path.name}: {target}"
            links += 1
    result = {"date": "2026-11-13", "status": "passed", "selected": manifest["selected"],
              "reused_native_runs": verified, "fetruth_paper_matches": 16, "screenshots": 16,
              "shared_style": shots["style"], "local_links_checked": links,
              "not_run": ["new native scans", "model training", "full-paper experiments", "unchanged graph integration tests"]}
    output = ROOT / "results/report-verification/current-selection.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
