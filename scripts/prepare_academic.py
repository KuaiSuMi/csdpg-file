"""Prepare the pinned academic reproductions on Windows with Git, Python and Docker."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def run(*args):
    subprocess.run([str(arg) for arg in args], cwd=ROOT, check=True)


def fetch(url, path, checksum):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        run("curl.exe", "-L", "--fail", "--retry", "2", "-o", path, url)
    with path.open("rb") as stream:
        actual = hashlib.file_digest(stream, "sha256").hexdigest()
    if actual != checksum:
        raise ValueError(f"Checksum mismatch: {path}")


def main():
    manifest = json.loads((ROOT / "baselines/selected-manifest.json").read_text(encoding="utf-8"))
    for name, source in manifest["repositories"].items():
        path = ROOT / "baselines/sources" / name
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            run("git", "init", path)
            run("git", "-C", path, "remote", "add", "origin", source["url"])
            run("git", "-C", path, "fetch", "--depth", "1", "origin", source["commit"])
            run("git", "-C", path, "checkout", "--detach", "FETCH_HEAD")
        commit = subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()
        dirty = subprocess.check_output(["git", "-C", str(path), "status", "--porcelain"], text=True).strip()
        if commit != source["commit"] or dirty:
            raise ValueError(f"Source must be at the pinned, unmodified commit: {path}")
    for asset in manifest["downloads"]:
        fetch(asset["url"], ROOT / asset["path"], asset["sha256"])
    wheels = ROOT / ".runtime/glitch-wheels"
    run(sys.executable, "-m", "pip", "download", "--only-binary=:all:", "--no-deps",
        "--python-version", "310", "--platform", "manylinux2014_x86_64", "--dest", wheels,
        "-r", ROOT / "baselines/glitch/requirements.lock")
    run(sys.executable, "-m", "pip", "wheel", "--no-deps", "--wheel-dir", wheels, "grapheme==0.6.0")
    run("docker", "build", "-t", "maturity-glitch:1.0.1", "-f", "baselines/glitch/Dockerfile", ".")
    run("docker", "build", "-t", "maturity-infer:1.3.0", "-f", "baselines/infer/Dockerfile", ".runtime/infer-download")
    run("docker", "run", "--rm", "maturity-glitch:1.0.1", "--help")
    run("docker", "run", "--rm", "maturity-infer:1.3.0", "--version")


if __name__ == "__main__":
    main()
