"""Record native verifier output and reject failed subprocesses before interpreting Kivi."""
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

sys.path[:0] = ["/opt/kivi", "/opt/kivi/kivi"]
output = Path(os.environ["KIVI_EVIDENCE"])
output.mkdir(parents=True, exist_ok=True)
import util

invocations = []


def observed_run(commands, print_stdout, _timeout=None):
    result = subprocess.run(commands, capture_output=True, timeout=_timeout, check=False)
    number = len(invocations)
    stdout = f"process-{number}.stdout.txt"
    stderr = f"process-{number}.stderr.txt"
    (output / stdout).write_bytes(result.stdout)
    (output / stderr).write_bytes(result.stderr)
    invocations.append(dict(command=commands, exit_code=result.returncode, stdout=stdout, stderr=stderr))
    (output / "processes.json").write_text(json.dumps(invocations, indent=2))
    result.check_returncode()
    return True, result.stdout, result.stderr


# The upstream helper ignores exit status; this boundary adds evidence, not model logic.
util.run_script = observed_run
main = importlib.import_module("kivi.main")
original_parser = main.parser


def captured_parser(path):
    model = original_parser(path)
    (output / "model-input.json").write_text(json.dumps(model, indent=2))
    return model


main.parser = captured_parser
original_generator = main.case_generator


def captured_generator(*args, **kwargs):
    model = original_generator(*args, **kwargs)
    (output / "model-input.json").write_text(json.dumps(model, indent=2))
    return model


main.case_generator = captured_generator
try:
    main.Kivi().run()
finally:
    for source in Path("/opt/kivi/temp").rglob("*.pml"):
        target = output / "model" / source.relative_to("/opt/kivi/temp")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
