import re
import subprocess
from typing import Any

TIMEOUT_SECONDS = 180
FAILURE_MARKERS = ("BUILD FAILURE", "FAILED", "ERROR")


def _parse_failed_tests(output: str) -> list[str]:
    pattern = re.compile(r"Tests run:.*?FAILED.*?(?:\n|$)", re.MULTILINE)
    return pattern.findall(output)


def run(state: dict[str, Any]) -> dict[str, Any]:
    repo_path = state["repo_path"]
    retry_count = state.get("retry_count", 0) + 1
    print(f"[test_runner] Running mvn test (attempt {retry_count}) in {repo_path} ...")

    try:
        proc = subprocess.run(
            ["mvn", "test", "-q"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
        )
        combined = proc.stdout + proc.stderr
        passed = proc.returncode == 0 and not any(m in combined for m in FAILURE_MARKERS)
    except subprocess.TimeoutExpired:
        combined = f"ERROR: mvn test timed out after {TIMEOUT_SECONDS}s"
        passed = False
    except FileNotFoundError:
        combined = "ERROR: 'mvn' not found on PATH — ensure Maven is installed"
        passed = False

    failed_tests = _parse_failed_tests(combined)
    tail = combined[-2000:] if len(combined) > 2000 else combined

    status = "PASSED" if passed else "FAILED"
    print(f"[test_runner] Tests {status}")

    return {
        "test_result": {
            "passed": passed,
            "output": tail,
            "failed_tests": failed_tests,
        },
        "retry_count": retry_count,
    }
