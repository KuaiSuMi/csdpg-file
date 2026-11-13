"""Replay the official BARO sample without using incident ground truth."""
import hashlib
import importlib.metadata
import json
import platform
from pathlib import Path
import subprocess
import sys
import time

from baro.anomaly_detection import bocpd
from baro.root_cause_analysis import robust_scorer
from baro.utility import read_data

root = Path(__file__).resolve().parent
source = json.loads((root / "input-source.json").read_text(encoding="utf-8"))
assert hashlib.sha256((root / "data.csv").read_bytes()).hexdigest() == source["sha256"]
data = read_data(str(root / "data.csv"), strip=False)
started = time.perf_counter()
anomalies = [int(index) for index in bocpd(data)]
result = robust_scorer(data, anomalies=anomalies) if anomalies else {"ranks": []}
summary = {
    "tool": "BARO",
    "version": importlib.metadata.version("fse-baro"),
    "python": platform.python_version(),
    "platform": platform.platform(),
    "status": "official_sample_smoke_completed",
    "input": source,
    "rows": len(data),
    "metric_columns": len(data.columns) - 1,
    "ground_truth_used_as_input": False,
    "read_data_strip": False,
    "native_change_point_indices": anomalies,
    "time_values_at_valid_indices": [
        data["time"].iloc[index].item() if 0 <= index < len(data) else None
        for index in anomalies
    ],
    "outside_row_range_indices": [index for index in anomalies if not 0 <= index < len(data)],
    "ranks": result["ranks"],
    "elapsed_seconds": round(time.perf_counter() - started, 3),
    "not_claimed": [
        "project live deployment reproduction",
        "full paper dataset reproduction",
        "confirmed causal root cause",
        "graph integration",
    ],
}
(root / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
(root / "requirements-lock.txt").write_text(
    subprocess.check_output([sys.executable, "-m", "pip", "freeze"], text=True),
    encoding="utf-8",
)
print(json.dumps(summary, indent=2))
