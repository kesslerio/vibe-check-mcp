"""
E2E tests for vibe_check_mentor interrupt mode via MCP protocol.

Tests interrupt mode behavior through actual MCP communication:
- Interrupt triggered (high confidence anti-pattern detection)
- No interrupt (low confidence, proceed with affirmation)
"""

import pytest
import subprocess
import sys
from pathlib import Path


@pytest.mark.e2e
class TestMentorInterruptMode:
    """Test vibe_check_mentor interrupt mode via mcp-test-client"""

    def test_mentor_interrupt_mode_e2e(self):
        """
        Run mentor_interrupt_mode.mjs test via Node.js with timeout.

        This test validates:
        1. Interrupt triggered for anti-pattern queries
        2. No interrupt for low-confidence queries
        3. Correct response structure for both modes
        """
        test_script = Path(__file__).parent / "mcp" / "mentor_interrupt_mode.mjs"

        # Ensure test script exists
        assert test_script.exists(), f"Test script not found: {test_script}"

        try:
            # Run with timeout (30s + 5s kill buffer)
            result = subprocess.run(
                ["timeout", "-k5s", "30s", "node", str(test_script)],
                capture_output=True,
                text=True,
                timeout=40,  # Python-level timeout as safety net
            )

            # Print output for debugging
            if result.stdout:
                print("\n=== Test Output ===")
                print(result.stdout)

            if result.stderr:
                print("\n=== Error Output ===")
                print(result.stderr)

            # Assert test passed
            assert result.returncode == 0, (
                f"Interrupt mode E2E test failed with exit code {result.returncode}\n"
                f"stdout: {result.stdout}\n"
                f"stderr: {result.stderr}"
            )

            # Verify expected output markers
            assert "✅ All interrupt mode tests passed!" in result.stdout, (
                "Expected success message not found in output"
            )

        except subprocess.TimeoutExpired as e:
            pytest.fail(
                f"Test timed out after 40s\n"
                f"stdout: {e.stdout.decode() if e.stdout else 'N/A'}\n"
                f"stderr: {e.stderr.decode() if e.stderr else 'N/A'}"
            )
        except FileNotFoundError as e:
            pytest.skip(f"Required command not found: {e.filename}")

    def test_mentor_interrupt_mode_node_dependencies(self):
        """
        Verify mcp-test-client is installed before running E2E tests.
        """
        try:
            # Check if mcp-test-client can be imported (ESM package)
            result = subprocess.run(
                ["node", "-e", "import('mcp-test-client').then(() => process.exit(0)).catch(() => process.exit(1))"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            assert result.returncode == 0, (
                f"mcp-test-client not installed or not importable. Run: npm install\n"
                f"stderr: {result.stderr}"
            )

        except FileNotFoundError:
            pytest.skip("Node.js not available")
        except subprocess.TimeoutExpired:
            pytest.fail("Dependency check timed out")
