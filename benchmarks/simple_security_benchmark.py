#!/usr/bin/env python3
"""
Simplified Performance Benchmark for Security Patches (Issue #194)

Measures the key performance impacts of security patches.
"""

import asyncio
import time
import statistics
import json
import sys
import os
from typing import Dict, List, Any, Tuple

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(project_root, 'src'))

# Import modules
import vibe_check.mentor.mcp_sampling as original_module
from vibe_check.mentor import mcp_sampling_secure as secure_module
from vibe_check.mentor.mcp_sampling_patch import apply_security_patches


def benchmark_function(func, *args, iterations=1000, warmup=100, **kwargs):
    """Simple benchmark runner"""
    times = []
    
    # Warmup
    for _ in range(warmup):
        func(*args, **kwargs)
    
    # Actual benchmark
    for _ in range(iterations):
        start = time.perf_counter()
        func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        times.append(elapsed)
    
    return {
        "mean_ms": statistics.mean(times) * 1000,
        "median_ms": statistics.median(times) * 1000,
        "p95_ms": sorted(times)[int(len(times) * 0.95)] * 1000,
        "p99_ms": sorted(times)[int(len(times) * 0.99)] * 1000,
        "std_dev_ms": statistics.stdev(times) * 1000 if len(times) > 1 else 0
    }


def benchmark_template_rendering():
    """Compare string replacement vs Jinja2"""
    print("\n1. TEMPLATE RENDERING")
    print("-" * 40)
    
    # Test data
    template_str = "Query: {query}, Tech: {tech}, Pattern: {pattern}"
    jinja_template = "Query: {{ query }}, Tech: {{ tech }}, Pattern: {{ pattern }}"
    data = {"query": "Should I use OAuth?", "tech": "python", "pattern": "auth"}
    
    # Original - string replacement
    template = original_module.PromptTemplate(
        role="system",
        template=template_str,
        variables=["query", "tech", "pattern"]
    )
    
    def original_render():
        return template.render(**data)
    
    original_stats = benchmark_function(original_render, iterations=1000)
    
    # Jinja2 rendering
    renderer = secure_module.SafeTemplateRenderer()
    
    def jinja_render():
        return renderer.render(jinja_template, data)
    
    jinja_stats = benchmark_function(jinja_render, iterations=1000)
    
    # Calculate overhead
    overhead = ((jinja_stats["mean_ms"] - original_stats["mean_ms"]) / 
                original_stats["mean_ms"] * 100)
    
    print(f"String replacement: {original_stats['mean_ms']:.3f}ms")
    print(f"Jinja2 rendering:   {jinja_stats['mean_ms']:.3f}ms")
    print(f"Overhead: {overhead:.1f}%")
    
    return overhead


def benchmark_input_validation():
    """Compare no validation vs Pydantic"""
    print("\n2. INPUT VALIDATION")
    print("-" * 40)
    
    test_data = {
        "query": "How to implement authentication?",
        "intent": "architecture",
        "files": ["/src/auth.py", "/src/main.py"],
        "code": "def authenticate(): pass",
        "language": "python"
    }
    
    # No validation
    def no_validation():
        query = test_data["query"]
        if len(query) > 10000:
            query = query[:10000]
        return query
    
    no_val_stats = benchmark_function(no_validation, iterations=1000)
    
    # Pydantic validation
    def pydantic_validation():
        validated = secure_module.QueryInput(
            query=test_data["query"],
            intent=test_data["intent"]
        )
        workspace = secure_module.WorkspaceDataInput(
            files=test_data["files"],
            code=test_data["code"],
            language=test_data["language"]
        )
        return validated, workspace
    
    pydantic_stats = benchmark_function(pydantic_validation, iterations=1000)
    
    overhead = ((pydantic_stats["mean_ms"] - no_val_stats["mean_ms"]) / 
                no_val_stats["mean_ms"] * 100)
    
    print(f"No validation:      {no_val_stats['mean_ms']:.3f}ms")
    print(f"Pydantic validation: {pydantic_stats['mean_ms']:.3f}ms")
    print(f"Overhead: {overhead:.1f}%")
    
    return overhead


async def benchmark_rate_limiting():
    """Benchmark rate limiting overhead"""
    print("\n3. RATE LIMITING")
    print("-" * 40)
    
    # Create rate limiter with high limit
    rate_limiter = secure_module.RateLimiter(
        requests_per_minute=6000,
        burst_capacity=100
    )
    
    times = []
    for _ in range(1000):
        start = time.perf_counter()
        allowed, wait_time = await rate_limiter.check_rate_limit("test_user")
        elapsed = time.perf_counter() - start
        times.append(elapsed)
    
    stats = {
        "mean_ms": statistics.mean(times) * 1000,
        "p95_ms": sorted(times)[int(len(times) * 0.95)] * 1000
    }
    
    print(f"Rate limit check: {stats['mean_ms']:.3f}ms (p95: {stats['p95_ms']:.3f}ms)")
    
    # Overhead compared to no check (essentially 0ms)
    overhead = stats['mean_ms'] * 100  # Assume no check is ~0ms
    print(f"Overhead: ~{stats['mean_ms']:.3f}ms per request")
    
    return overhead


def benchmark_secrets_scanning():
    """Compare basic vs enhanced secrets scanning"""
    print("\n4. SECRETS SCANNING")
    print("-" * 40)
    
    test_code = """
import os
API_KEY = 'sk-proj-abc123xyz789def456'
SECRET = 'super_secret_password_123'
TOKEN = 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test'
AWS_KEY = 'AKIAIOSFODNN7EXAMPLE'

def process():
    return API_KEY
"""
    
    # Basic scanning
    basic_scanner = original_module.SecretsScanner()
    
    def basic_scan():
        return basic_scanner.scan_and_redact(test_code)
    
    basic_stats = benchmark_function(basic_scan, iterations=500)
    
    # Enhanced scanning
    enhanced_scanner = secure_module.EnhancedSecretsScanner()
    
    def enhanced_scan():
        return enhanced_scanner.scan_and_redact(test_code, "benchmark")
    
    enhanced_stats = benchmark_function(enhanced_scan, iterations=500)
    
    overhead = ((enhanced_stats["mean_ms"] - basic_stats["mean_ms"]) / 
                basic_stats["mean_ms"] * 100)
    
    print(f"Basic scanning:    {basic_stats['mean_ms']:.3f}ms")
    print(f"Enhanced scanning: {enhanced_stats['mean_ms']:.3f}ms")
    print(f"Overhead: {overhead:.1f}%")
    
    return overhead


def benchmark_file_access_control():
    """Benchmark file access control checks"""
    print("\n5. FILE ACCESS CONTROL")
    print("-" * 40)
    
    controller = secure_module.FileAccessController()
    test_paths = [
        "/src/auth.py",
        "/etc/passwd",
        "../../../etc/shadow",
        "/tmp/test.py",
        "/Users/test/project/src/main.py"
    ]
    
    def check_access():
        results = []
        for path in test_paths:
            allowed, reason = controller.is_allowed(path)
            results.append((allowed, reason))
        return results
    
    stats = benchmark_function(check_access, iterations=1000)
    
    print(f"File access checks: {stats['mean_ms']:.3f}ms for {len(test_paths)} paths")
    print(f"Per-path overhead: {stats['mean_ms']/len(test_paths):.3f}ms")
    
    return stats['mean_ms']


def benchmark_full_processing():
    """Benchmark full request processing"""
    print("\n6. FULL REQUEST PROCESSING")
    print("-" * 40)
    
    query = "Should I implement custom authentication?"
    context = {
        "technologies": ["python", "fastapi"],
        "patterns": ["authentication", "security"]
    }
    workspace = {
        "code": "def auth(): pass",
        "files": ["/src/auth.py"],
        "language": "python"
    }
    
    # Original processing
    def original_process():
        # Build prompt
        builder = original_module.PromptBuilder()
        prompt = builder.build_prompt(
            intent="architecture",
            query=query,
            context=context,
            workspace_data=workspace
        )
        # Sanitize code
        if "code" in workspace:
            sanitized = original_module.sanitize_code_for_llm(workspace["code"])
        return prompt, sanitized
    
    original_stats = benchmark_function(original_process, iterations=500)
    
    # Apply patches and benchmark
    apply_security_patches()
    
    def patched_process():
        # Build prompt (now uses secure version)
        builder = original_module.PromptBuilder()
        prompt = builder.build_prompt(
            intent="architecture",
            query=query,
            context=context,
            workspace_data=workspace
        )
        # Sanitize code (now includes enhanced scanning)
        if "code" in workspace:
            sanitized = original_module.sanitize_code_for_llm(workspace["code"])
        return prompt, sanitized
    
    patched_stats = benchmark_function(patched_process, iterations=500)
    
    overhead = ((patched_stats["mean_ms"] - original_stats["mean_ms"]) / 
                original_stats["mean_ms"] * 100)
    
    print(f"Original processing: {original_stats['mean_ms']:.3f}ms")
    print(f"Patched processing:  {patched_stats['mean_ms']:.3f}ms")
    print(f"Overhead: {overhead:.1f}%")
    
    return overhead


async def main():
    print("\n" + "="*60)
    print("SECURITY PATCHES PERFORMANCE BENCHMARK")
    print("="*60)
    
    overheads = []
    
    # Run benchmarks
    overhead1 = benchmark_template_rendering()
    overheads.append(overhead1)
    
    overhead2 = benchmark_input_validation()
    overheads.append(overhead2)
    
    overhead3 = await benchmark_rate_limiting()
    # Rate limiting is additive, not percentage-based
    
    overhead4 = benchmark_secrets_scanning()
    overheads.append(overhead4)
    
    overhead5 = benchmark_file_access_control()
    # File access is additive overhead
    
    overhead6 = benchmark_full_processing()
    overheads.append(overhead6)
    
    # Summary
    print("\n" + "="*60)
    print("PERFORMANCE IMPACT ASSESSMENT")
    print("="*60)
    
    avg_overhead = statistics.mean([o for o in overheads if o < 100])
    print(f"\nAverage Component Overhead: {avg_overhead:.1f}%")
    print(f"Full Processing Overhead: {overhead6:.1f}%")
    
    if overhead6 < 10:
        print("\n✅ PASS: Performance impact is within acceptable threshold (<10%)")
        print("Recommendation: APPROVE deployment of security patches")
    elif overhead6 < 20:
        print("\n⚠️ WARNING: Performance impact is moderate (10-20%)")
        print("Recommendation: Consider optimization or accept trade-off for security")
    else:
        print("\n❌ FAIL: Performance impact exceeds threshold (>20%)")
        print("Recommendation: OPTIMIZE before deployment")
    
    # Component assessment
    print("\nComponent Breakdown:")
    components = [
        ("Template Rendering", overhead1),
        ("Input Validation", overhead2),
        ("Secrets Scanning", overhead4),
        ("Full Processing", overhead6)
    ]
    
    for name, overhead in components:
        status = "✅" if overhead < 10 else "⚠️" if overhead < 20 else "❌"
        print(f"  {status} {name}: {overhead:.1f}%")
    
    # Save results
    results = {
        "template_rendering_overhead": overhead1,
        "input_validation_overhead": overhead2,
        "secrets_scanning_overhead": overhead4,
        "full_processing_overhead": overhead6,
        "average_overhead": avg_overhead,
        "recommendation": "APPROVE" if overhead6 < 10 else "REVIEW" if overhead6 < 20 else "OPTIMIZE"
    }
    
    with open("benchmark_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to benchmark_results.json")


if __name__ == "__main__":
    asyncio.run(main())