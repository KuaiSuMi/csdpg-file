"""Collect native workload outputs for root, privileged and non-root containers."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import time

import requests
import yaml

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://127.0.0.1:10443"


def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--kubeconfig", type=Path, required=True)
    parser.add_argument("--password-file", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    namespace = "maturity-nv-check-" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    kubectl = ["kubectl", "--kubeconfig", str(args.kubeconfig.resolve())]

    def kube(*arguments):
        cmd = kubectl + list(arguments)
        result = subprocess.run(cmd, capture_output=True, encoding="utf-8", check=True)
        with (output / "commands.log").open("a", encoding="utf-8") as log:
            log.write(json.dumps(cmd, ensure_ascii=False) + "\n" + result.stdout + result.stderr + "\n")
        return result.stdout

    # Only the loopback port-forward uses the laboratory's generated TLS certificate.
    requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
    session = requests.Session()
    session.trust_env = False
    session.verify = False
    auth = session.post(BASE + "/v1/auth", json={"password": {"username": "admin",
        "password": args.password_file.read_text(encoding="utf-8").strip()}}, timeout=30)
    auth.raise_for_status()
    session.headers["X-Auth-Token"] = auth.json()["token"]["token"]

    def api(path):
        response = session.get(BASE + path, timeout=30)
        response.raise_for_status()
        return response.json()

    created = False
    summary = {"baseline": "SUSE Security / NeuVector open-source distribution", "version": "5.6.4",
        "namespace": namespace, "native_rules_modified": False,
        "scope": "live workload identity, root/privileged risk, processes, statistics and platform overview", "phases": {}}
    try:
        system = api("/v1/system/summary")
        assert "v5.6.4" in system["summary"]["component_versions"], system
        assert system["summary"]["enforcers"] >= 1
        save(output / "system.json", system)
        kube("create", "namespace", namespace)
        created = True
        for phase, uid, privileged in (("before", 0, False), ("privileged", 0, True), ("after", 1000, False)):
            dest = output / phase
            dest.mkdir()
            source = ROOT / "baselines/fixtures/neuvector" / (("before" if privileged else phase) + ".yaml")
            document = yaml.safe_load(source.read_text(encoding="utf-8"))
            document["spec"]["template"]["spec"]["containers"][0]["securityContext"]["privileged"] = privileged
            (dest / "input.yaml").write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
            kube("-n", namespace, "apply", "-f", str(dest / "input.yaml"))
            kube("-n", namespace, "rollout", "status", "deployment/maturity-http", "--timeout=180s")
            deployment = json.loads(kube("-n", namespace, "get", "deployment", "maturity-http", "-o", "json"))
            pods = json.loads(kube("-n", namespace, "get", "pods", "-l", "app=maturity-http", "-o", "json"))
            save(dest / "deployment.json", deployment)
            save(dest / "pods.json", pods)
            active = [p for p in pods["items"] if not p["metadata"].get("deletionTimestamp")]
            assert len(active) == 1, active
            pod = active[0]
            status = pod["status"]["containerStatuses"][0]
            assert status["ready"]
            container_id = status["containerID"].removeprefix("containerd://")
            health = json.loads(kube("-n", namespace, "exec", pod["metadata"]["name"], "--", "node", "-e",
                "require('http').get('http://127.0.0.1:8080/',r=>{let b='';r.on('data',x=>b+=x);r.on('end',()=>console.log(JSON.stringify({status:r.statusCode,body:b,uid:process.getuid()})))})"))
            save(dest / "business.json", health)
            assert health == {"status": 200, "body": "maturity-ok\n", "uid": uid}, health
            deadline = time.monotonic() + 180
            delay = 5
            while True:
                response = session.get(BASE + "/v1/workload/" + container_id, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    if data["workload"]["running"]:
                        break
                elif response.status_code != 404:
                    response.raise_for_status()
                if time.monotonic() >= deadline:
                    raise TimeoutError("NeuVector did not discover the running target container")
                time.sleep(delay)
                delay = min(delay * 2, 30)
            save(dest / "workload.json", data)
            workload = data["workload"]
            assert workload["id"] == container_id
            assert workload["domain"] == namespace
            assert workload["run_as_root"] is (uid == 0), workload
            privilege_matches = workload["privileged"] is privileged
            runtime_status = kube("-n", namespace, "exec", pod["metadata"]["name"], "--", "cat", "/proc/1/status")
            (dest / "process-status.txt").write_text(runtime_status, encoding="utf-8")
            save(dest / "score-metrics.json", api("/v1/system/score/metrics"))
            compliance = session.get(BASE + "/v1/workload/" + container_id + "/compliance", timeout=30)
            save(dest / "compliance-response.json", {"http_status": compliance.status_code, "body": compliance.json()})
            endpoints = {"stats": "/v1/workload/" + container_id + "/stats",
                         "process": "/v1/workload/" + container_id + "/process",
                         "process-history": "/v1/workload/" + container_id + "/process_history",
                         "config": "/v1/workload/" + container_id + "/config",
                         "scan": "/v1/scan/workload/" + container_id}
            for name, endpoint in endpoints.items():
                response = session.get(BASE + endpoint, timeout=30)
                save(dest / (name + "-response.json"), {"http_status": response.status_code, "body": response.json()})
                if name in ("stats", "process", "config"):
                    response.raise_for_status()
            if not privilege_matches:
                time.sleep(30)
                repeated = api("/v1/workload/" + container_id)
                save(dest / "workload-recheck.json", repeated)
                privilege_matches = repeated["workload"]["privileged"] is privileged
            summary["phases"][phase] = {"run_as_root": workload["run_as_root"], "running": workload["running"],
                "privileged": workload["privileged"],
                "expected_privileged": privileged, "privileged_matches_configuration": privilege_matches,
                "container_id": container_id, "image_id": status["imageID"], "business": health,
                "input_sha256": hashlib.sha256((dest / "input.yaml").read_bytes()).hexdigest()}
            print(phase, "run_as_root =", workload["run_as_root"], "privileged =", workload["privileged"], "HTTP =", health["status"], flush=True)
        assert summary["phases"]["before"]["image_id"] == summary["phases"]["after"]["image_id"]
        summary["validation"] = "passed" if all(p["privileged_matches_configuration"] for p in summary["phases"].values()) else "completed_with_mismatch"
        summary["mismatches"] = [phase + ": privileged flag differs from Kubernetes securityContext" for phase, p in summary["phases"].items() if not p["privileged_matches_configuration"]]
    finally:
        if created:
            kube("delete", "namespace", namespace, "--wait=true", "--timeout=180s")
            summary["test_namespace_deleted"] = True
        session.delete(BASE + "/v1/auth", timeout=15).raise_for_status()
        session.close()
    save(output / "summary.json", summary)
    print(str(output / "summary.json"))


if __name__ == "__main__":
    main()
