#!/usr/bin/env python3
"""
Performance Benchmark for Security Patches (Issue #194)

This script measures the performance impact of security patches applied to mcp_sampling.py
by comparing execution times and resource usage between original and patched implementations.

Metrics measured:
- Template rendering speed (Jinja2 vs string replacement)
- Input validation overhead (Pydantic models)
- Rate limiting impact (token bucket algorithm)
- Secrets scanning time (regex patterns)
- File access control checks
- Overall request processing time
- Memory usage
"""

import asyncio
import time
import tracemalloc
import statistics
import json
import sys
import os
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, field
from contextlib import contextmanager
import gc

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

# Import both original and secure implementations
import vibe_check.mentor.mcp_sampling as original_module
from vibe_check.mentor import mcp_sampling_secure as secure_module
from vibe_check.mentor.mcp_sampling_patch import apply_security_patches, verify_patches


@dataclass
class BenchmarkResult:
    """Container for benchmark results"""
    name: str
    iterations: int
    times: List[float] = field(default_factory=list)
    memory_usage: List[int] = field(default_factory=list)
    
    @property
    def mean_time(self) -> float:
        return statistics.mean(self.times) if self.times else 0
    
    @property
    def median_time(self) -> float:
        return statistics.median(self.times) if self.times else 0
    
    @property
    def std_dev(self) -> float:
        return statistics.stdev(self.times) if len(self.times) > 1 else 0
    
    @property
    def p95_time(self) -> float:
        if not self.times:
            return 0
        sorted_times = sorted(self.times)
        index = int(len(sorted_times) * 0.95)
        return sorted_times[min(index, len(sorted_times) - 1)]
    
    @property
    def p99_time(self) -> float:
        if not self.times:
            return 0
        sorted_times = sorted(self.times)
        index = int(len(sorted_times) * 0.99)
        return sorted_times[min(index, len(sorted_times) - 1)]
    
    @property
    def mean_memory(self) -> int:
        return int(statistics.mean(self.memory_usage)) if self.memory_usage else 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "iterations": self.iterations,
            "mean_time_ms": self.mean_time * 1000,
            "median_time_ms": self.median_time * 1000,
            "p95_time_ms": self.p95_time * 1000,
            "p99_time_ms": self.p99_time * 1000,
            "std_dev_ms": self.std_dev * 1000,
            "mean_memory_bytes": self.mean_memory
        }


class PerformanceBenchmark:
    """Main benchmark runner"""
    
    def __init__(self, iterations: int = 1000, warmup_iterations: int = 100):
        self.iterations = iterations
        self.warmup_iterations = warmup_iterations
        self.results: Dict[str, BenchmarkResult] = {}
        
        # Test data
        self.test_query = "Should I implement custom authentication or use Auth0?"
        self.test_code = """
import os
import requests

API_KEY = 'sk-proj-abc123xyz789'
SECRET_KEY = 'super_secret_password_12345'
DATABASE_URL = 'postgresql://user:pass@localhost/db'

def authenticate_user(username, password):
    # This is a test function for benchmarking
    token = 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test'
    aws_key = 'AKIAIOSFODNN7EXAMPLE'
    return {'token': token, 'aws': aws_key}
"""
        
        self.test_context = {
            "technologies": ["python", "fastapi", "postgresql", "auth0"],
            "patterns": ["authentication", "security", "api"],
            "constraints": "Team of 3 developers, 6 month timeline"
        }
        
        self.test_workspace = {
            "files": ["/src/auth.py", "/src/api.py", "/config/settings.py"],
            "code": self.test_code,
            "language": "python",
            "frameworks": ["fastapi", "sqlalchemy"],
            "imports": ["os", "requests", "fastapi", "pydantic"],
            "file_path": "/src/auth.py"
        }
    
    def measure_time_and_memory(self):
        """Measure execution time and memory"""
        gc.collect()
        tracemalloc.start()
        start_time = time.perf_counter()
        start_snapshot = tracemalloc.take_snapshot()
        
        def measure():
            end_time = time.perf_counter()
            end_snapshot = tracemalloc.take_snapshot()
            tracemalloc.stop()
            
            elapsed = end_time - start_time
            
            # Calculate memory difference
            stats = end_snapshot.compare_to(start_snapshot, 'lineno')
            total_memory = sum(stat.size_diff for stat in stats if stat.size_diff > 0)
            
            return elapsed, total_memory
        
        return measure
    
    def benchmark_template_rendering(self) -> Tuple[BenchmarkResult, BenchmarkResult]:
        """Benchmark template rendering: string replacement vs Jinja2"""
        
        # Original string replacement
        original_result = BenchmarkResult("String Replacement", self.iterations)
        template = original_module.PromptTemplate(
            role="system",
            template="Query: {query}, Technologies: {technologies}, Patterns: {patterns}",
            variables=["query", "technologies", "patterns"]
        )
        
        print("Benchmarking original template rendering...")
        for i in range(self.iterations + self.warmup_iterations):
            measure = self.measure_time_and_memory()
            result = template.render(
                query=self.test_query,
                technologies=", ".join(self.test_context["technologies"]),
                patterns=", ".join(self.test_context["patterns"])
            )
            elapsed, memory = measure()
            
            if i >= self.warmup_iterations:
                original_result.times.append(elapsed)
                original_result.memory_usage.append(memory)
        
        # Jinja2 rendering
        jinja_result = BenchmarkResult("Jinja2 Rendering", self.iterations)
        renderer = secure_module.SafeTemplateRenderer()
        jinja_template = "Query: {{ query }}, Technologies: {{ technologies }}, Patterns: {{ patterns }}"
        
        print("Benchmarking Jinja2 template rendering...")
        for i in range(self.iterations + self.warmup_iterations):
            with self.measure_time_and_memory() as (elapsed, memory):
                result = renderer.render(jinja_template, {
                    "query": self.test_query,
                    "technologies": ", ".join(self.test_context["technologies"]),
                    "patterns": ", ".join(self.test_context["patterns"])
                })
            
            if i >= self.warmup_iterations:
                jinja_result.times.append(elapsed)
                jinja_result.memory_usage.append(memory)
        
        return original_result, jinja_result
    
    def benchmark_input_validation(self) -> Tuple[BenchmarkResult, BenchmarkResult]:
        """Benchmark input validation: none vs Pydantic"""
        
        # No validation (original)
        no_validation_result = BenchmarkResult("No Validation", self.iterations)
        
        print("Benchmarking without input validation...")
        for i in range(self.iterations + self.warmup_iterations):
            with self.measure_time_and_memory() as (elapsed, memory):
                # Simulate original processing without validation
                query = self.test_query
                workspace = self.test_workspace
                # Simple length check (original behavior)
                if len(query) > 10000:
                    query = query[:10000]
            
            if i >= self.warmup_iterations:
                no_validation_result.times.append(elapsed)
                no_validation_result.memory_usage.append(memory)
        
        # Pydantic validation
        pydantic_result = BenchmarkResult("Pydantic Validation", self.iterations)
        
        print("Benchmarking Pydantic input validation...")
        for i in range(self.iterations + self.warmup_iterations):
            with self.measure_time_and_memory() as (elapsed, memory):
                validated_query = secure_module.QueryInput(
                    query=self.test_query,
                    intent="architecture_decision"
                )
                validated_workspace = secure_module.WorkspaceDataInput(**self.test_workspace)
            
            if i >= self.warmup_iterations:
                pydantic_result.times.append(elapsed)
                pydantic_result.memory_usage.append(memory)
        
        return no_validation_result, pydantic_result
    
    async def benchmark_rate_limiting(self) -> Tuple[BenchmarkResult, BenchmarkResult]:
        """Benchmark rate limiting overhead"""
        
        # No rate limiting
        no_limit_result = BenchmarkResult("No Rate Limiting", self.iterations)
        
        print("Benchmarking without rate limiting...")
        for i in range(self.iterations + self.warmup_iterations):
            start_time = time.perf_counter()
            # Simulate processing without rate limit check
            allowed = True
            elapsed = time.perf_counter() - start_time
            
            if i >= self.warmup_iterations:
                no_limit_result.times.append(elapsed)
        
        # With rate limiting
        rate_limit_result = BenchmarkResult("Token Bucket Rate Limiting", self.iterations)
        rate_limiter = secure_module.RateLimiter(
            requests_per_minute=6000,  # High limit to avoid blocking
            burst_capacity=100
        )
        
        print("Benchmarking with rate limiting...")
        for i in range(self.iterations + self.warmup_iterations):
            start_time = time.perf_counter()
            allowed, wait_time = await rate_limiter.check_rate_limit("test_user")
            elapsed = time.perf_counter() - start_time
            
            if i >= self.warmup_iterations:
                rate_limit_result.times.append(elapsed)
        
        return no_limit_result, rate_limit_result
    
    def benchmark_secrets_scanning(self) -> Tuple[BenchmarkResult, BenchmarkResult]:
        """Benchmark secrets scanning performance"""
        
        # Basic scanning (original)
        basic_result = BenchmarkResult("Basic Secrets Scan", self.iterations)
        basic_scanner = original_module.SecretsScanner()
        
        print("Benchmarking basic secrets scanning...")
        for i in range(self.iterations + self.warmup_iterations):
            with self.measure_time_and_memory() as (elapsed, memory):
                redacted, secrets = basic_scanner.scan_and_redact(self.test_code)
            
            if i >= self.warmup_iterations:
                basic_result.times.append(elapsed)
                basic_result.memory_usage.append(memory)
        
        # Enhanced scanning
        enhanced_result = BenchmarkResult("Enhanced Secrets Scan", self.iterations)
        enhanced_scanner = secure_module.EnhancedSecretsScanner()
        
        print("Benchmarking enhanced secrets scanning...")
        for i in range(self.iterations + self.warmup_iterations):
            with self.measure_time_and_memory() as (elapsed, memory):
                redacted, secrets = enhanced_scanner.scan_and_redact(
                    self.test_code, 
                    context="benchmark"
                )
            
            if i >= self.warmup_iterations:
                enhanced_result.times.append(elapsed)
                enhanced_result.memory_usage.append(memory)
        
        return basic_result, enhanced_result
    
    def benchmark_file_access_control(self) -> BenchmarkResult:
        """Benchmark file access control checks"""
        
        controller = secure_module.FileAccessController()
        result = BenchmarkResult("File Access Control", self.iterations)
        
        test_paths = [
            "/src/auth.py",
            "/etc/passwd",  # Should be denied
            "../../../etc/shadow",  # Path traversal
            "/tmp/test.py",
            "/Users/test/project/src/main.py"
        ]
        
        print("Benchmarking file access control...")
        for i in range(self.iterations + self.warmup_iterations):
            with self.measure_time_and_memory() as (elapsed, memory):
                for path in test_paths:
                    allowed, reason = controller.is_allowed(path)
            
            if i >= self.warmup_iterations:
                result.times.append(elapsed)
                result.memory_usage.append(memory)
        
        return result
    
    async def benchmark_full_request(self) -> Tuple[BenchmarkResult, BenchmarkResult]:
        """Benchmark full request processing"""
        
        # Original implementation
        original_result = BenchmarkResult("Original Full Request", self.iterations // 10)
        original_client = original_module.MCPSamplingClient()
        
        print("Benchmarking original full request processing...")
        for i in range(original_result.iterations + self.warmup_iterations):
            start_time = time.perf_counter()
            
            # Simulate full request processing
            prompt_builder = original_module.PromptBuilder()
            prompt = prompt_builder.build_prompt(
                intent="architecture_decision",
                query=self.test_query,
                context=self.test_context,
                workspace_data=self.test_workspace
            )
            
            # Sanitize code
            if "code" in self.test_workspace:
                sanitized = original_module.sanitize_code_for_llm(
                    self.test_workspace["code"], 
                    2000
                )
            
            elapsed = time.perf_counter() - start_time
            
            if i >= self.warmup_iterations:
                original_result.times.append(elapsed)
        
        # Patched implementation
        patched_result = BenchmarkResult("Patched Full Request", self.iterations // 10)
        
        # Apply patches
        apply_security_patches()
        patched_client = original_module.MCPSamplingClient()
        
        print("Benchmarking patched full request processing...")
        for i in range(patched_result.iterations + self.warmup_iterations):
            start_time = time.perf_counter()
            
            # Simulate full request processing with security checks
            prompt_builder = original_module.PromptBuilder()
            prompt = prompt_builder.build_prompt(
                intent="architecture_decision",
                query=self.test_query,
                context=self.test_context,
                workspace_data=self.test_workspace
            )
            
            # Enhanced sanitization with secrets scanning
            if "code" in self.test_workspace:
                sanitized = original_module.sanitize_code_for_llm(
                    self.test_workspace["code"], 
                    2000
                )
            
            elapsed = time.perf_counter() - start_time
            
            if i >= self.warmup_iterations:
                patched_result.times.append(elapsed)
        
        return original_result, patched_result
    
    def calculate_overhead(self, original: BenchmarkResult, enhanced: BenchmarkResult) -> Dict[str, float]:
        """Calculate performance overhead percentage"""
        return {
            "mean_overhead_pct": ((enhanced.mean_time - original.mean_time) / original.mean_time * 100) if original.mean_time > 0 else 0,
            "p95_overhead_pct": ((enhanced.p95_time - original.p95_time) / original.p95_time * 100) if original.p95_time > 0 else 0,
            "p99_overhead_pct": ((enhanced.p99_time - original.p99_time) / original.p99_time * 100) if original.p99_time > 0 else 0,
            "memory_overhead_pct": ((enhanced.mean_memory - original.mean_memory) / original.mean_memory * 100) if original.mean_memory > 0 else 0
        }
    
    async def run_all_benchmarks(self):
        """Run all benchmarks and collect results"""
        
        print("\n" + "="*60)
        print("SECURITY PATCHES PERFORMANCE BENCHMARK")
        print("="*60)
        print(f"Iterations: {self.iterations}")
        print(f"Warmup iterations: {self.warmup_iterations}")
        print()
        
        results = {}
        
        # 1. Template Rendering
        print("\n1. TEMPLATE RENDERING BENCHMARK")
        print("-" * 40)
        orig_template, jinja_template = self.benchmark_template_rendering()
        results["template_rendering"] = {
            "original": orig_template.to_dict(),
            "enhanced": jinja_template.to_dict(),
            "overhead": self.calculate_overhead(orig_template, jinja_template)
        }
        
        # 2. Input Validation
        print("\n2. INPUT VALIDATION BENCHMARK")
        print("-" * 40)
        no_validation, pydantic_validation = self.benchmark_input_validation()
        results["input_validation"] = {
            "original": no_validation.to_dict(),
            "enhanced": pydantic_validation.to_dict(),
            "overhead": self.calculate_overhead(no_validation, pydantic_validation)
        }
        
        # 3. Rate Limiting
        print("\n3. RATE LIMITING BENCHMARK")
        print("-" * 40)
        no_limit, rate_limited = await self.benchmark_rate_limiting()
        results["rate_limiting"] = {
            "original": no_limit.to_dict(),
            "enhanced": rate_limited.to_dict(),
            "overhead": self.calculate_overhead(no_limit, rate_limited)
        }
        
        # 4. Secrets Scanning
        print("\n4. SECRETS SCANNING BENCHMARK")
        print("-" * 40)
        basic_scan, enhanced_scan = self.benchmark_secrets_scanning()
        results["secrets_scanning"] = {
            "original": basic_scan.to_dict(),
            "enhanced": enhanced_scan.to_dict(),
            "overhead": self.calculate_overhead(basic_scan, enhanced_scan)
        }
        
        # 5. File Access Control
        print("\n5. FILE ACCESS CONTROL BENCHMARK")
        print("-" * 40)
        file_control = self.benchmark_file_access_control()
        results["file_access_control"] = {
            "enhanced": file_control.to_dict(),
            "overhead": {"mean_time_ms": file_control.mean_time * 1000}
        }
        
        # 6. Full Request Processing
        print("\n6. FULL REQUEST PROCESSING BENCHMARK")
        print("-" * 40)
        orig_full, patched_full = await self.benchmark_full_request()
        results["full_request"] = {
            "original": orig_full.to_dict(),
            "patched": patched_full.to_dict(),
            "overhead": self.calculate_overhead(orig_full, patched_full)
        }
        
        return results
    
    def print_results(self, results: Dict[str, Any]):
        """Print formatted benchmark results"""
        
        print("\n" + "="*60)
        print("BENCHMARK RESULTS SUMMARY")
        print("="*60)
        
        total_overhead = []
        
        for component, data in results.items():
            print(f"\n{component.upper().replace('_', ' ')}:")
            print("-" * 40)
            
            if "original" in data and "enhanced" in data:
                orig = data["original"]
                enh = data["enhanced"]
                overhead = data["overhead"]
                
                print(f"Original: {orig['mean_time_ms']:.3f}ms (p95: {orig['p95_time_ms']:.3f}ms)")
                print(f"Enhanced: {enh['mean_time_ms']:.3f}ms (p95: {enh['p95_time_ms']:.3f}ms)")
                print(f"Overhead: {overhead['mean_overhead_pct']:.1f}% (p95: {overhead['p95_overhead_pct']:.1f}%)")
                
                if component == "full_request":
                    total_overhead.append(overhead['mean_overhead_pct'])
            elif "enhanced" in data:
                enh = data["enhanced"]
                print(f"Time: {enh['mean_time_ms']:.3f}ms (p95: {enh.get('p95_time_ms', 0):.3f}ms)")
        
        # Overall assessment
        print("\n" + "="*60)
        print("PERFORMANCE IMPACT ASSESSMENT")
        print("="*60)
        
        if total_overhead:
            avg_overhead = sum(total_overhead) / len(total_overhead)
            print(f"\nTotal Average Overhead: {avg_overhead:.1f}%")
            
            if avg_overhead < 10:
                print("✅ PASS: Performance impact is within acceptable threshold (<10%)")
                print("Recommendation: APPROVE deployment of security patches")
            elif avg_overhead < 20:
                print("⚠️ WARNING: Performance impact is moderate (10-20%)")
                print("Recommendation: Consider optimization or accept trade-off")
            else:
                print("❌ FAIL: Performance impact exceeds threshold (>20%)")
                print("Recommendation: OPTIMIZE before deployment")
        
        # Component breakdown
        print("\nComponent Impact Breakdown:")
        for component, data in results.items():
            if "overhead" in data and "mean_overhead_pct" in data["overhead"]:
                overhead = data["overhead"]["mean_overhead_pct"]
                status = "✅" if overhead < 10 else "⚠️" if overhead < 20 else "❌"
                print(f"  {status} {component.replace('_', ' ').title()}: {overhead:.1f}%")
        
        # Save detailed results
        with open("benchmark_results.json", "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nDetailed results saved to benchmark_results.json")


async def main():
    """Main entry point"""
    
    # Parse command line arguments
    iterations = 1000
    if len(sys.argv) > 1:
        try:
            iterations = int(sys.argv[1])
        except ValueError:
            print(f"Invalid iterations: {sys.argv[1]}, using default {iterations}")
    
    # Run benchmarks
    benchmark = PerformanceBenchmark(iterations=iterations)
    results = await benchmark.run_all_benchmarks()
    benchmark.print_results(results)


if __name__ == "__main__":
    asyncio.run(main())