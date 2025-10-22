import os
import shutil
import subprocess
from pathlib import Path

import pytest


SCRIPT_PATH = Path(__file__).resolve().parent / "mcp" / "mentor_relevance.mjs"
REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js not available")
@pytest.mark.skipif(shutil.which("timeout") is None, reason="timeout command not available")
def test_mentor_relevance_e2e():
    assert SCRIPT_PATH.exists(), f"Missing scenario script: {SCRIPT_PATH}"

    if not (REPO_ROOT / "node_modules" / "mcp-test-client").exists():
        pytest.skip("mcp-test-client not installed. Run `npm install` first.")

    command = [
        "timeout",
        "-k5s",
        "90s",
        "node",
        str(SCRIPT_PATH),
    ]

    env = os.environ.copy()
    result = subprocess.run(
        command,
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    stdout = result.stdout.strip()
    stderr = result.stderr.strip()

    if result.returncode != 0:
        pytest.fail(
            "mentor_relevance_e2e failed\n"
            f"stdout:\n{stdout}\n\nstderr:\n{stderr}\n\nreturncode: {result.returncode}"
        )

    assert "PASS: mentor_relevance_e2e" in stdout
