"""Build or augment the kg_builder graph with conference and commercial baseline evidence."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "integration"))

from kg_builder import BuildPipeline, BuildSettings
from kg_builder.collectors.base import BaseCollector, CollectorResult
from kg_builder.graph.serialization import load_graph, save_graph
from maturity_baselines import BaselineCollector


class ExistingGraph(BaseCollector):
    name = "existing-graph"

    def __init__(self, graph):
        self.graph = graph

    def collect(self):
        return CollectorResult(collector=self.name, nodes=self.graph.nodes, edges=self.graph.edges)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--glitch", type=Path, help="GLITCH run directory with native findings.csv and summary.json")
    parser.add_argument("--infer", type=Path, help="Infer/Pulse run directory with infer-out/report.json and summary.json")
    parser.add_argument("--fetruth", type=Path, help="Directory with recommendations.tsv, features.json and summary.json")
    parser.add_argument("--kivi", type=Path, help="Kivi phase directory with SPIN evidence")
    parser.add_argument("--reynard", type=Path, help="Contract phase directory with junit.xml and observations/")
    parser.add_argument("--insights", type=Path, help="Fairwinds Insights API JSON array of Deployment action items")
    parser.add_argument("--appcat", type=Path, help="AppCAT phase directory containing native report.json")
    parser.add_argument("--neuvector", type=Path, help="NeuVector phase directory with workload, pods and deployment JSON")
    parser.add_argument("--cluster", help="Actual Kubernetes cluster name; required with --neuvector")
    parser.add_argument("--namespace", required=True, help="Project identity, same as the existing graph")
    parser.add_argument("--base-graph", type=Path)
    parser.add_argument("--bindings", type=Path, help="JSON object: exact baseline subject key -> existing graph node id")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if not any((args.fetruth, args.kivi, args.reynard, args.insights, args.appcat, args.neuvector, args.glitch, args.infer)):
        parser.error("at least one baseline output is required")
    if args.neuvector and not args.cluster:
        parser.error("--neuvector requires --cluster")
    if args.bindings and not args.base_graph:
        parser.error("--bindings requires --base-graph")
    collectors, bindings, base = [], {}, None
    if args.base_graph:
        base = load_graph(args.base_graph)
        collectors.append(ExistingGraph(base))
    if args.bindings:
        for subject, node_id in json.loads(args.bindings.read_text(encoding="utf-8")).items():
            node = base.get_node(node_id)
            if node is None or node.namespace != args.namespace:
                raise ValueError(f"Binding {subject}: missing node or graph namespace mismatch")
            bindings[subject] = node
    for name in ("fetruth", "kivi", "reynard", "insights", "appcat", "neuvector", "glitch", "infer"):
        if path := getattr(args, name):
            collectors.append(BaselineCollector(name, path, namespace=args.namespace,
                                                bindings=bindings, cluster=args.cluster))
    settings = BuildSettings(repo_path=ROOT, output_path=args.output, namespace=args.namespace, enrich=False)
    report = BuildPipeline(settings).run(collectors=collectors, write_outputs=False)
    if report.warnings:
        raise RuntimeError("; ".join(report.warnings))
    # The upstream pipeline only folds its own extras; keep baseline coverage explicitly in graph meta.
    if base:
        report.graph.meta.update(base.meta)
    report.graph.meta["baseline_runs"] = {
        **report.graph.meta.get("baseline_runs", {}),
        **{result.collector: result.metrics for result in report.results if result.collector.startswith("baseline-")}}
    save_graph(report.graph, args.output)
    print(json.dumps({"output": str(args.output), "stats": report.graph.stats(),
                      "baseline_runs": report.graph.meta["baseline_runs"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
