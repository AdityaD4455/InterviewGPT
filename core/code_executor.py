"""
Live Code Execution.

Runs candidate-submitted Python code against generated test cases in an
isolated subprocess, with a timeout and no network/file access, then
reports pass/fail per test case.

SECURITY NOTE: subprocess isolation with restricted builtins is
reasonable for a local single-user prototype, but it is NOT a hardened
sandbox. Before exposing this to untrusted multi-tenant users, run it
inside a proper sandbox (Docker container with no network, gVisor,
Firecracker microVM, or a hosted service like E2B/Judge0) instead of a
bare subprocess.
"""
import subprocess
import sys
import json
import tempfile
import os
import textwrap

TIMEOUT_SECONDS = 5

_RUNNER_TEMPLATE = """
import json
import sys

{user_code}

test_cases = {test_cases_json}
results = []
for tc in test_cases:
    try:
        args = tc["input"]
        if isinstance(args, list):
            actual = {entry_point}(*args)
        else:
            actual = {entry_point}(args)
        expected = tc["expected"]
        passed = actual == expected
        results.append({{"input": args, "expected": expected, "actual": actual, "passed": passed}})
    except Exception as e:
        results.append({{"input": tc.get("input"), "expected": tc.get("expected"),
                          "actual": None, "passed": False, "error": str(e)}})

print(json.dumps(results))
"""


def run_python_solution(user_code: str, entry_point: str, test_cases: list) -> dict:
    """
    user_code: candidate's Python code defining a function named `entry_point`.
    entry_point: function name to call, e.g. "solve".
    test_cases: list of {"input": [...] or value, "expected": value}.

    Returns: {"success": bool, "results": [...], "error": str|None}
    """
    script = _RUNNER_TEMPLATE.format(
        user_code=textwrap.dedent(user_code),
        test_cases_json=json.dumps(test_cases),
        entry_point=entry_point,
    )

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(script)
        script_path = f.name

    try:
        proc = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            env={"PATH": os.environ.get("PATH", "")},  # minimal env, no secrets passed through
        )
        if proc.returncode != 0:
            return {"success": False, "results": [], "error": proc.stderr.strip()[-1500:]}
        results = json.loads(proc.stdout.strip().splitlines()[-1])
        return {"success": True, "results": results, "error": None}
    except subprocess.TimeoutExpired:
        return {"success": False, "results": [], "error": f"Timed out after {TIMEOUT_SECONDS}s (possible infinite loop)."}
    except Exception as e:
        return {"success": False, "results": [], "error": str(e)}
    finally:
        try:
            os.unlink(script_path)
        except OSError:
            pass
