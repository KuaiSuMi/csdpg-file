"""Translate native baseline outputs without inventing a combined maturity score."""
import csv
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from .native import read_fetruth, read_kivi
from .insights import read_insights
from .appcat import read_appcat
from .neuvector import read_neuvector
from .academic import read_academic
from kg_builder.collectors.base import BaseCollector, CollectorResult
from kg_builder.graph.model import KGEdge, KGNode, Provenance, make_node_id


def _reynard(directory):
    suite = ET.parse(directory / "junit.xml").getroot()
    if suite.tag != "testsuite":
        raise ValueError("Expected one JUnit testsuite")
    counts = {k: int(suite.attrib[k]) for k in ("tests", "failures", "errors", "skipped")}
    if counts["errors"] or counts["skipped"]:
        raise ValueError(f"Reynard infrastructure errors or skipped tests: {counts}")
    files = sorted((directory / "observations").glob("*.json"))
    if len(files) != counts["tests"] or not files:
        raise ValueError("JUnit count does not match recorded observations")
    records, failures, healthy, injected = [], 0, 0, 0
    seen_faultloads = set()
    for path in files:
        obs = json.loads(path.read_text(encoding="utf-8"))
        if type(obs["passed"]) is not bool or obs["injection_verified"] is not True:
            raise ValueError("Reynard outcome/injection was not verified")
        if not obs["trace"]["reports"]:
            raise ValueError("Reynard trace has no proxy reports")
        reports = obs["trace"]["reports"]
        encode = lambda f: json.dumps(f, sort_keys=True)
        requested = sorted(encode(f) for f in obs["faultload"]["faults"])
        actual = sorted(encode(r["injected_fault"]) for r in reports if r["injected_fault"] is not None)
        if actual != requested or len(requested) != obs["fault_count"]:
            raise ValueError("Raw proxy faults do not match the requested faultload")
        if any(r["trace_id"] != obs["trace_id"] for r in reports):
            raise ValueError("Proxy reports belong to a different trace")
        identity = (obs["scenario"], tuple(requested))
        if identity in seen_faultloads:
            raise ValueError("Duplicate scenario/faultload observations")
        seen_faultloads.add(identity)
        calls = set()
        for report in reports:
            stack = report["uid"]["stack"]
            calls.update((a["destination"], b["destination"]) for a, b in zip(stack, stack[1:]))
        if obs["fault_count"] == 0:
            healthy += 1
            if not obs["passed"]:
                raise ValueError("Healthy control failed; fault result is not attributable")
        else:
            injected += 1
        failures += not obs["passed"]
        faults = sorted(obs["faultload"]["faults"], key=lambda f: json.dumps(f, sort_keys=True))
        records.append(dict(subject="service:" + obs["service"], type="Service",
                            rule=obs["scenario"], key=[obs["scenario"], faults],
                            status="pass" if obs["passed"] else "fail", source="runtime",
                            calls=sorted(calls),
                            attributes={k: obs[k] for k in ("phase", "trace_id", "http_status", "body",
                                                           "fault_count", "injection_verified", "dependency")},
                            evidence=[(path, "", obs)]))
    if healthy != 1 or injected == 0 or failures != counts["failures"]:
        raise ValueError("Reynard healthy/fault/outcome coverage is inconsistent")
    return records


class BaselineCollector(BaseCollector):
    """Use with BuildPipeline.run(collectors=[...existing_collectors, collector])."""

    def __init__(self, baseline, path, *, namespace, bindings=None, cluster=None):
        if baseline not in {"fetruth", "kivi", "reynard", "insights", "appcat", "neuvector", "glitch", "infer"}:
            raise ValueError(f"Unknown baseline: {baseline}")
        self.name = "baseline-" + baseline
        self.baseline, self.path = baseline, Path(path)
        self.namespace = namespace
        self.cluster = cluster
        # Explicit subject -> KGNode bindings avoid guessing service/class identities.
        self.bindings = bindings or {}

    def collect(self):
        result = CollectorResult(collector=self.name)
        try:
            if self.baseline in {"glitch", "infer"}:
                records = read_academic(self.path, self.baseline)
            elif self.baseline == "fetruth":
                records = read_fetruth(self.path)
            elif self.baseline == "kivi":
                records = read_kivi(self.path)
            elif self.baseline == "insights":
                records = read_insights(self.path)
            elif self.baseline == "appcat":
                records = read_appcat(self.path)
            elif self.baseline == "neuvector":
                records = read_neuvector(self.path, cluster=self.cluster)
            else:
                records = _reynard(self.path)
            subjects = {}
            for record in records:
                subject = record["subject"]
                node = subjects.get(subject)
                if node is None:
                    node = self.bindings.get(subject)
                    if node is None:
                        node = KGNode(id=make_node_id(record["type"], subject, self.namespace),
                                      type=record["type"], name=subject, canonical_name=subject,
                                      namespace=self.namespace)
                    else:
                        allowed = {"fetruth": {"Module", "Service"}, "kivi": {"Deployment"}, "insights": {"Deployment"},
                                   "reynard": {"Service"}, "appcat": {"Module", "Service", "Function", "Config"},
                                   "neuvector": {"Deployment", "Infrastructure"},
                                   "glitch": {"Config", "Module"}, "infer": {"Module", "Function"}}
                        if node.namespace != self.namespace or node.type not in allowed[self.baseline]:
                            raise ValueError(f"Incompatible binding for {subject}")
                        if self.baseline == "neuvector":
                            if node.type != record["type"] or node.attributes.get("cluster") != self.cluster:
                                raise ValueError(f"NeuVector binding must match object type and cluster: {subject}")
                            if node.type == "Deployment" and (
                                    node.name != record["attributes"]["deployment"]
                                    or node.attributes.get("namespace") != record["attributes"]["resource_namespace"]):
                                raise ValueError(f"NeuVector binding must match Deployment identity: {subject}")
                        node = KGNode.from_dict(node.to_dict())
                    subjects[subject] = node
                    result.add_node(node)
                provenance = [Provenance(
                    source_type=record["source"], source_id=f"{path.as_posix()}#{pointer}",
                    evidence=json.dumps(raw, ensure_ascii=False, sort_keys=True),
                    detail={"tool": self.baseline, "evidence_type": "tool-output",
                            "interpretation": record["status"]})
                    for path, pointer, raw in record["evidence"]]
                for prov in provenance:
                    node.add_provenance(prov)
                canonical = json.dumps([self.baseline, subject, record["key"]],
                                       ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                identity = self.baseline + "/" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:20]
                metric = KGNode(id=make_node_id("Metric", identity, self.namespace),
                                type="Metric", name=record["rule"], canonical_name=canonical,
                                namespace=self.namespace,
                                attributes={"baseline": self.baseline, "status": record["status"],
                                            "subject_key": subject, **record["attributes"]},
                                provenance=provenance)
                result.add_node(metric)
                result.add_edge(KGEdge(source=node.id, target=metric.id, relation="OBSERVED_BY",
                                       provenance=provenance))
                for caller, callee in record.get("calls", []):
                    for name in (caller, callee):
                        key = "service:" + name
                        if key not in subjects:
                            service = self.bindings.get(key)
                            if service:
                                if service.type != "Service" or service.namespace != self.namespace:
                                    raise ValueError(f"Incompatible binding for {key}")
                                service = KGNode.from_dict(service.to_dict())
                            else:
                                service = KGNode(id=make_node_id("Service", key, self.namespace),
                                                 type="Service", name=name, canonical_name=key,
                                                 namespace=self.namespace)
                            subjects[key] = service
                            result.add_node(service)
                        for prov in provenance:
                            subjects[key].add_provenance(prov)
                    result.add_edge(KGEdge(source=subjects["service:" + caller].id,
                                           target=subjects["service:" + callee].id, relation="CALLS",
                                           attributes={"evidence_type": "proxy-trace"},
                                           provenance=provenance))
            result.metrics = {"status": "ok", "observations": len(records),
                              "subjects": len(subjects),
                              "findings": sum(r["status"] in {"candidate", "fail"} for r in records)}
        except (OSError, ValueError, KeyError, TypeError, csv.Error, ET.ParseError) as exc:
            result = CollectorResult(collector=self.name, metrics={"status": "error"},
                                     warnings=[f"{type(exc).__name__}: {exc}"])
        return result
