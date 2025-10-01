"""
Comprehensive Test Runner and Coverage Reporter

Provides utilities for running the complete test suite with coverage reporting,
performance metrics, and detailed analysis of test results.
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path
from typing import Dict, List, Any


class TestRunner:
    """Comprehensive test runner with coverage and performance reporting"""

    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.test_dir = self.project_root / "tests"
        self.coverage_dir = self.project_root / "htmlcov"

    def run_unit_tests(self, verbose: bool = True) -> Dict[str, Any]:
        """Run unit tests with coverage"""
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "tests/unit/",
            "--cov=src/vibe_check",
            "--cov-report=html",
            "--cov-report=json",
            "--cov-report=term",
            "-v" if verbose else "-q",
            "--tb=short",
        ]

        start_time = time.time()
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=self.project_root
        )
        duration = time.time() - start_time

        return {
            "category": "unit",
            "returncode": result.returncode,
            "duration": duration,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0,
        }

    def run_integration_tests(self, verbose: bool = True) -> Dict[str, Any]:
        """Run integration tests"""
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "tests/integration/",
            "-m",
            "integration",
            "-v" if verbose else "-q",
            "--tb=short",
            "--timeout=60",
        ]

        start_time = time.time()
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=self.project_root
        )
        duration = time.time() - start_time

        return {
            "category": "integration",
            "returncode": result.returncode,
            "duration": duration,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0,
        }

    def run_security_tests(self, verbose: bool = True) -> Dict[str, Any]:
        """Run security tests"""
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "tests/security/",
            "-m",
            "security",
            "-v" if verbose else "-q",
            "--tb=short",
        ]

        start_time = time.time()
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=self.project_root
        )
        duration = time.time() - start_time

        return {
            "category": "security",
            "returncode": result.returncode,
            "duration": duration,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0,
        }

    def run_performance_tests(self, verbose: bool = True) -> Dict[str, Any]:
        """Run performance tests with benchmarking"""
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "tests/performance/",
            "-m",
            "performance",
            "--benchmark-only",
            "--benchmark-json=benchmark_results.json",
            "-v" if verbose else "-q",
        ]

        start_time = time.time()
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=self.project_root
        )
        duration = time.time() - start_time

        return {
            "category": "performance",
            "returncode": result.returncode,
            "duration": duration,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0,
        }

    def run_edge_case_tests(self, verbose: bool = True) -> Dict[str, Any]:
        """Run edge case tests"""
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "tests/edge_cases/",
            "-m",
            "edge_case",
            "-v" if verbose else "-q",
            "--tb=short",
        ]

        start_time = time.time()
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=self.project_root
        )
        duration = time.time() - start_time

        return {
            "category": "edge_case",
            "returncode": result.returncode,
            "duration": duration,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0,
        }

    def run_novel_query_tests(self, verbose: bool = True) -> Dict[str, Any]:
        """Run novel query stress tests"""
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "tests/novel_queries/",
            "-m",
            "novel_query",
            "-v" if verbose else "-q",
            "--tb=short",
            "--timeout=120",
        ]

        start_time = time.time()
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=self.project_root
        )
        duration = time.time() - start_time

        return {
            "category": "novel_query",
            "returncode": result.returncode,
            "duration": duration,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0,
        }

    def run_e2e_tests(self, verbose: bool = True) -> Dict[str, Any]:
        """Run end-to-end tests"""
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "tests/e2e/",
            "-m",
            "e2e",
            "-v" if verbose else "-q",
            "--tb=short",
            "--timeout=180",
        ]

        start_time = time.time()
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=self.project_root
        )
        duration = time.time() - start_time

        return {
            "category": "e2e",
            "returncode": result.returncode,
            "duration": duration,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0,
        }

    def run_all_tests(
        self, verbose: bool = True, parallel: bool = False
    ) -> Dict[str, Any]:
        """Run all test categories"""
        if parallel:
            return self._run_tests_parallel(verbose)
        else:
            return self._run_tests_sequential(verbose)

    def _run_tests_sequential(self, verbose: bool) -> Dict[str, Any]:
        """Run all tests sequentially"""
        test_methods = [
            self.run_unit_tests,
            self.run_integration_tests,
            self.run_security_tests,
            self.run_performance_tests,
            self.run_edge_case_tests,
            self.run_novel_query_tests,
            self.run_e2e_tests,
        ]

        results = []
        total_start = time.time()

        for test_method in test_methods:
            print(f"\n{'='*60}")
            print(
                f"Running {test_method.__name__.replace('run_', '').replace('_', ' ').title()}"
            )
            print("=" * 60)

            result = test_method(verbose)
            results.append(result)

            if result["success"]:
                print(
                    f"✅ {result['category']} tests passed ({result['duration']:.2f}s)"
                )
            else:
                print(
                    f"❌ {result['category']} tests failed ({result['duration']:.2f}s)"
                )

        total_duration = time.time() - total_start

        return {
            "results": results,
            "total_duration": total_duration,
            "overall_success": all(r["success"] for r in results),
            "summary": self._generate_summary(results),
        }

    def _run_tests_parallel(self, verbose: bool) -> Dict[str, Any]:
        """Run tests in parallel (basic implementation)"""
        # For now, run sequentially but could be enhanced with multiprocessing
        return self._run_tests_sequential(verbose)

    def _generate_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate test results summary"""
        total_duration = sum(r["duration"] for r in results)
        success_count = sum(1 for r in results if r["success"])

        return {
            "total_categories": len(results),
            "successful_categories": success_count,
            "failed_categories": len(results) - success_count,
            "total_duration": total_duration,
            "average_duration": total_duration / len(results),
            "success_rate": success_count / len(results),
        }

    def generate_coverage_report(self) -> Dict[str, Any]:
        """Generate comprehensive coverage report"""
        coverage_json_path = self.project_root / "coverage.json"

        if not coverage_json_path.exists():
            return {"error": "Coverage data not found. Run tests with coverage first."}

        with open(coverage_json_path) as f:
            coverage_data = json.load(f)

        return {
            "overall_coverage": coverage_data.get("totals", {}).get(
                "percent_covered", 0
            ),
            "files_covered": len(coverage_data.get("files", {})),
            "missing_lines": coverage_data.get("totals", {}).get("missing_lines", 0),
            "covered_lines": coverage_data.get("totals", {}).get("covered_lines", 0),
            "total_lines": coverage_data.get("totals", {}).get("num_statements", 0),
            "coverage_html": str(self.coverage_dir / "index.html"),
        }

    def run_quality_checks(self) -> Dict[str, Any]:
        """Run code quality checks"""
        checks = {}

        # Type checking with mypy
        mypy_result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mypy",
                "src/vibe_check",
                "--ignore-missing-imports",
            ],
            capture_output=True,
            text=True,
            cwd=self.project_root,
        )

        checks["mypy"] = {
            "success": mypy_result.returncode == 0,
            "output": mypy_result.stdout + mypy_result.stderr,
        }

        # Linting with flake8 (if available)
        try:
            flake8_result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "flake8",
                    "src/vibe_check",
                    "--max-line-length=100",
                ],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )

            checks["flake8"] = {
                "success": flake8_result.returncode == 0,
                "output": flake8_result.stdout + flake8_result.stderr,
            }
        except FileNotFoundError:
            checks["flake8"] = {"success": None, "output": "flake8 not available"}

        return checks


def main():
    """Main entry point for test runner"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Run comprehensive vibe-check-mcp tests"
    )
    parser.add_argument(
        "--category",
        choices=[
            "unit",
            "integration",
            "security",
            "performance",
            "edge_case",
            "novel_query",
            "e2e",
            "all",
        ],
        default="all",
        help="Test category to run",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument(
        "--parallel", "-p", action="store_true", help="Run tests in parallel"
    )
    parser.add_argument(
        "--coverage", "-c", action="store_true", help="Generate coverage report"
    )
    parser.add_argument(
        "--quality", "-q", action="store_true", help="Run quality checks"
    )

    args = parser.parse_args()

    runner = TestRunner()

    print("🧪 Vibe Check MCP Comprehensive Test Suite")
    print("=" * 50)

    # Run selected tests
    if args.category == "all":
        results = runner.run_all_tests(args.verbose, args.parallel)
    else:
        method_name = f"run_{args.category}_tests"
        method = getattr(runner, method_name)
        results = method(args.verbose)

    # Generate coverage report if requested
    if args.coverage:
        print("\n📊 Generating Coverage Report...")
        coverage = runner.generate_coverage_report()
        if "error" not in coverage:
            print(f"Overall Coverage: {coverage['overall_coverage']:.1f}%")
            print(f"Files Covered: {coverage['files_covered']}")
            print(f"HTML Report: {coverage['coverage_html']}")

    # Run quality checks if requested
    if args.quality:
        print("\n🔍 Running Quality Checks...")
        quality = runner.run_quality_checks()
        for check, result in quality.items():
            if result["success"]:
                print(f"✅ {check} passed")
            elif result["success"] is False:
                print(f"❌ {check} failed")
                if result["output"]:
                    print(f"   {result['output']}")
            else:
                print(f"⚠️  {check} skipped")

    # Print summary
    if isinstance(results, dict) and "summary" in results:
        summary = results["summary"]
        print(f"\n📈 Test Summary:")
        print(
            f"Categories: {summary['successful_categories']}/{summary['total_categories']} passed"
        )
        print(f"Success Rate: {summary['success_rate']:.1%}")
        print(f"Total Duration: {summary['total_duration']:.2f}s")

        if results["overall_success"]:
            print("🎉 All tests passed!")
            sys.exit(0)
        else:
            print("❌ Some tests failed!")
            sys.exit(1)
    else:
        if results.get("success", False):
            print("✅ Tests passed!")
            sys.exit(0)
        else:
            print("❌ Tests failed!")
            sys.exit(1)


if __name__ == "__main__":
    main()
