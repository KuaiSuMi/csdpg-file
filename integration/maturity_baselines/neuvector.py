"""Read a native workload response alongside its Kubernetes identity snapshots."""
import json
from pathlib import Path


def _matches(labels, selector):
    if not selector.get("matchLabels") and not selector.get("matchExpressions"):
        raise ValueError("Deployment selector is empty")
    if any(labels.get(k) != v for k, v in selector.get("matchLabels", {}).items()):
        return False
    for expression in selector.get("matchExpressions", []):
        key, op, values = expression["key"], expression["operator"], expression.get("values", [])
        if op not in {"In", "NotIn", "Exists", "DoesNotExist"}:
            raise ValueError("Unsupported Kubernetes selector operator: " + op)
        matched = {"In": key in labels and labels[key] in values,
                   "NotIn": key not in labels or labels[key] not in values,
                   "Exists": key in labels, "DoesNotExist": key not in labels}[op]
        if not matched:
            return False
    return True


def read_neuvector(directory, *, cluster):
    if not isinstance(cluster, str) or not cluster.strip():
        raise ValueError("NeuVector import requires an explicit cluster name")
    directory = Path(directory)
    workload_path, pods_path, deployment_path = (directory / name for name in
                                                ("workload.json", "pods.json", "deployment.json"))
    raw = json.loads(workload_path.read_text(encoding="utf-8-sig"))
    workload = raw["workload"]
    pods = json.loads(pods_path.read_text(encoding="utf-8-sig"))["items"]
    deployment = json.loads(deployment_path.read_text(encoding="utf-8-sig"))
    meta = deployment["metadata"]
    if deployment["kind"] != "Deployment" or not meta["uid"]:
        raise ValueError("Expected a Kubernetes Deployment snapshot")
    for field in ("run_as_root", "privileged", "running"):
        if type(workload[field]) is not bool:
            raise ValueError("NeuVector " + field + " must be a boolean")
    if not workload["running"]:
        raise ValueError("NeuVector workload is no longer running")
    labels = workload["labels"]
    namespace, pod_name = workload["domain"], workload["pod_name"]
    uid, container_name = labels["io.kubernetes.pod.uid"], labels["io.kubernetes.container.name"]
    if (not uid or not container_name or meta["namespace"] != namespace
            or labels["io.kubernetes.pod.namespace"] != namespace
            or labels["io.kubernetes.pod.name"] != pod_name):
        raise ValueError("NeuVector and Kubernetes namespace/Pod identity mismatch")
    matches = [(i, pod) for i, pod in enumerate(pods) if pod["metadata"]["uid"] == uid]
    if len(matches) != 1:
        raise ValueError("NeuVector Pod UID must match exactly one exported Pod")
    index, pod = matches[0]
    pod_meta = pod["metadata"]
    if (pod_meta["name"] != pod_name or pod_meta["namespace"] != namespace
            or pod_meta.get("deletionTimestamp")
            or not _matches(pod_meta["labels"], deployment["spec"]["selector"])):
        raise ValueError("Observed Pod does not match the selected active Deployment snapshot")
    statuses = [s for s in pod["status"]["containerStatuses"] if s["name"] == container_name]
    if len(statuses) != 1:
        raise ValueError("Missing or ambiguous Kubernetes container status")
    container = statuses[0]
    if (container["containerID"].split("://", 1)[-1] != workload["id"]
            or container["ready"] is not True or "running" not in container["state"]):
        raise ValueError("NeuVector container ID does not match a ready running Kubernetes container")
    if container_name not in {c["name"] for c in deployment["spec"]["template"]["spec"]["containers"]}:
        raise ValueError("Observed container is not in the Deployment template")

    subject = f"k8s:{cluster}/{namespace}/Deployment/{meta['name']}"
    attributes = {"cluster": cluster, "resource_namespace": namespace,
                  "deployment": meta["name"], "deployment_uid": meta["uid"],
                  "container_name": container_name, "container_id": workload["id"],
                  "pod_name": pod_name, "pod_uid": uid, "image": workload["image"],
                  "running": workload["running"], "started_at": workload["started_at"],
                  "coverage": "observed-container",
                  "binding_basis": "selected-deployment-selector-and-container-identity"}
    evidence = [(workload_path, "/workload", workload),
                (pods_path, f"/items/{index}", pod), (deployment_path, "", deployment)]
    # Stable Deployment/container keys allow a rollout to replace the Pod while
    # preserving the identity of the compared check. Each result covers this sample.
    records = [dict(subject=subject, type="Deployment", rule=field, key=[container_name, field],
                    status="fail" if workload[field] else "pass", source="runtime",
                    attributes={**attributes, field: workload[field], "occurrences": int(workload[field])},
                    evidence=evidence) for field in ("run_as_root", "privileged")]
    score_path = directory / "score-metrics.json"
    if score_path.exists():
        scores = json.loads(score_path.read_text(encoding="utf-8-sig"))["security_scores"]
        if type(scores["security_risk_score"]) not in (int, float):
            raise ValueError("NeuVector global risk score must be numeric")
        records.append(dict(subject=f"k8s:{cluster}", type="Infrastructure", rule="security_risk_score",
                            key=["security_risk_score"], status="measured", source="runtime",
                            attributes={"cluster": cluster, "coverage": "cluster-overview", **scores},
                            evidence=[(score_path, "/security_scores", scores)]))
    return records
