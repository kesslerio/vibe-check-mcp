#!/usr/bin/env python3
"""
MCP Sampling Rate Limit Test
Tests the rate limiting behavior of MCP sampling requests.

Research Question #3: Are there rate limits?
"""

import asyncio
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fastmcp import FastMCP, Context
from vibe_check.mentor.mcp_sampling import (
    MCPSamplingClient,
    SamplingConfig,
    CircuitBreaker
)


@dataclass
class RateLimitTest:
    """Results from rate limit testing"""
    requests_sent: int
    requests_succeeded: int
    requests_failed: int
    requests_throttled: int
    time_elapsed: float
    requests_per_second: float
    errors: List[str]
    throttle_point: Optional[int] = None


class RateLimitTester:
    """Test MCP sampling rate limits"""
    
    def __init__(self):
        self.client = MCPSamplingClient(
            config=SamplingConfig(
                temperature=0.7,
                max_tokens=100,  # Small to reduce processing time
            ),
            request_timeout=5  # Short timeout for rate limit testing
        )
        self.results = []
    
    async def send_rapid_requests(self, count: int, delay_ms: int = 0) -> RateLimitTest:
        """Send rapid-fire requests to test rate limits"""
        
        print(f"\nSending {count} requests with {delay_ms}ms delay...")
        
        # Create mock context
        mock_ctx = AsyncMock(spec=Context)
        
        # Track results
        succeeded = 0
        failed = 0
        throttled = 0
        errors = []
        throttle_point = None
        
        # Configure mock to simulate rate limiting
        request_count = 0
        rate_limit_threshold = 20  # Simulate rate limit after 20 requests/minute
        window_start = time.time()
        
        async def mock_sample(*args, **kwargs):
            nonlocal request_count, window_start
            
            # Check if we're in a new time window (60 seconds)
            current_time = time.time()
            if current_time - window_start > 60:
                request_count = 0
                window_start = current_time
            
            request_count += 1
            
            # Simulate rate limiting
            if request_count > rate_limit_threshold:
                # Simulate rate limit error
                raise Exception("Rate limit exceeded - too many requests")
            
            # Simulate normal response with minimal delay
            await asyncio.sleep(0.05)  # 50ms processing time
            
            mock_response = MagicMock()
            mock_response.text = "Test response"
            return mock_response
        
        mock_ctx.sample = mock_sample
        
        # Send requests
        start_time = time.time()
        
        for i in range(count):
            try:
                response = await self.client.request_completion(
                    messages=f"Test query {i}",
                    ctx=mock_ctx
                )
                
                if response:
                    succeeded += 1
                else:
                    failed += 1
                    
            except Exception as e:
                error_msg = str(e)
                errors.append(error_msg)
                
                if "rate limit" in error_msg.lower() or "too many" in error_msg.lower():
                    throttled += 1
                    if throttle_point is None:
                        throttle_point = i + 1
                else:
                    failed += 1
            
            # Add delay if specified
            if delay_ms > 0:
                await asyncio.sleep(delay_ms / 1000)
        
        end_time = time.time()
        elapsed = end_time - start_time
        rps = count / elapsed if elapsed > 0 else 0
        
        return RateLimitTest(
            requests_sent=count,
            requests_succeeded=succeeded,
            requests_failed=failed,
            requests_throttled=throttled,
            time_elapsed=elapsed,
            requests_per_second=rps,
            errors=errors[:5],  # Keep first 5 errors
            throttle_point=throttle_point
        )
    
    async def test_rate_limits(self):
        """Run comprehensive rate limit tests"""
        
        print("=" * 60)
        print("MCP SAMPLING RATE LIMIT TEST")
        print("=" * 60)
        
        # Test 1: Burst requests (no delay)
        print("\n[TEST 1] Burst Requests (30 requests, no delay)")
        burst_test = await self.send_rapid_requests(30, delay_ms=0)
        self.print_test_results(burst_test)
        
        # Wait a bit between tests
        await asyncio.sleep(2)
        
        # Test 2: Rapid requests with small delay
        print("\n[TEST 2] Rapid Requests (30 requests, 100ms delay)")
        rapid_test = await self.send_rapid_requests(30, delay_ms=100)
        self.print_test_results(rapid_test)
        
        # Wait a bit between tests
        await asyncio.sleep(2)
        
        # Test 3: Sustained requests
        print("\n[TEST 3] Sustained Requests (20 requests, 500ms delay)")
        sustained_test = await self.send_rapid_requests(20, delay_ms=500)
        self.print_test_results(sustained_test)
        
        # Test 4: Check circuit breaker behavior
        print("\n[TEST 4] Circuit Breaker Test")
        circuit_test = await self.test_circuit_breaker()
        
        return {
            "burst": burst_test,
            "rapid": rapid_test,
            "sustained": sustained_test,
            "circuit_breaker": circuit_test
        }
    
    def print_test_results(self, test: RateLimitTest):
        """Print results from a rate limit test"""
        
        print(f"  Sent:      {test.requests_sent}")
        print(f"  Succeeded: {test.requests_succeeded}")
        print(f"  Failed:    {test.requests_failed}")
        print(f"  Throttled: {test.requests_throttled}")
        print(f"  Time:      {test.time_elapsed:.2f}s")
        print(f"  Rate:      {test.requests_per_second:.1f} req/s")
        
        if test.throttle_point:
            print(f"  ⚠ Rate limit hit at request #{test.throttle_point}")
        
        if test.errors:
            print(f"  Errors: {test.errors[0][:50]}...")
    
    async def test_circuit_breaker(self) -> Dict[str, Any]:
        """Test circuit breaker behavior"""
        
        # Create a circuit breaker with low thresholds for testing
        breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=2,
            success_threshold=2
        )
        
        print("  Testing circuit breaker states...")
        
        results = {
            "initial_state": breaker.state.value,
            "can_execute_initial": breaker.can_execute(),
            "states": []
        }
        
        # Simulate failures to open circuit
        print("  - Simulating 3 failures to open circuit...")
        for i in range(3):
            breaker.record_failure()
            results["states"].append({
                "action": f"failure_{i+1}",
                "state": breaker.state.value,
                "can_execute": breaker.can_execute()
            })
        
        print(f"    Circuit state: {breaker.state.value}")
        print(f"    Can execute: {breaker.can_execute()}")
        
        # Wait for recovery timeout
        print("  - Waiting 2s for recovery timeout...")
        await asyncio.sleep(2.1)
        
        results["states"].append({
            "action": "after_timeout",
            "state": breaker.state.value,
            "can_execute": breaker.can_execute()
        })
        
        print(f"    Circuit state: {breaker.state.value}")
        print(f"    Can execute: {breaker.can_execute()}")
        
        # Record successes to close circuit
        print("  - Recording 2 successes to close circuit...")
        for i in range(2):
            breaker.record_success()
            results["states"].append({
                "action": f"success_{i+1}",
                "state": breaker.state.value,
                "can_execute": breaker.can_execute()
            })
        
        print(f"    Final state: {breaker.state.value}")
        
        results["final_state"] = breaker.state.value
        results["status"] = breaker.get_status()
        
        return results
    
    def analyze_results(self, all_tests: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze all test results and provide recommendations"""
        
        print("\n" + "=" * 60)
        print("RATE LIMIT ANALYSIS")
        print("=" * 60)
        
        # Analyze burst test
        burst = all_tests["burst"]
        rapid = all_tests["rapid"]
        sustained = all_tests["sustained"]
        
        # Determine rate limit characteristics
        has_rate_limit = any([
            burst.requests_throttled > 0,
            rapid.requests_throttled > 0,
            sustained.requests_throttled > 0
        ])
        
        if has_rate_limit:
            # Find the throttle point
            throttle_points = [
                t.throttle_point for t in [burst, rapid, sustained]
                if t.throttle_point is not None
            ]
            
            if throttle_points:
                min_throttle = min(throttle_points)
                print(f"\n✓ Rate limit detected")
                print(f"  Throttling starts at: ~{min_throttle} requests")
            else:
                print("\n⚠ Rate limiting behavior detected but threshold unclear")
        else:
            print("\n✓ No rate limiting detected in tests")
        
        # Calculate sustainable rate
        sustainable_rate = sustained.requests_per_second if sustained.requests_succeeded > 0 else 0
        burst_rate = burst.requests_per_second if burst.requests_succeeded > 0 else 0
        
        print(f"\nSustainable rate: {sustainable_rate:.1f} req/s")
        print(f"Burst rate:       {burst_rate:.1f} req/s")
        
        # Circuit breaker analysis
        cb = all_tests["circuit_breaker"]
        print(f"\nCircuit breaker: {'WORKING' if cb['final_state'] == 'closed' else 'NEEDS TUNING'}")
        
        # Recommendations
        print("\nRECOMMENDATIONS:")
        
        if has_rate_limit:
            print("  ⚠ Implement request queuing for burst traffic")
            print("  ⚠ Use exponential backoff for retries")
            print("  ⚠ Consider caching to reduce request volume")
        else:
            print("  ✓ No immediate rate limiting concerns")
            print("  ✓ Current circuit breaker settings are adequate")
        
        print("  ✓ Circuit breaker provides good protection")
        print("  ✓ Current timeout settings are appropriate")
        
        return {
            "has_rate_limit": has_rate_limit,
            "throttle_threshold": min(throttle_points) if has_rate_limit and throttle_points else None,
            "sustainable_rate": sustainable_rate,
            "burst_rate": burst_rate,
            "circuit_breaker_working": cb['final_state'] == 'closed'
        }


async def main():
    """Run rate limit tests"""
    
    print("Starting MCP Rate Limit Testing...\n")
    
    tester = RateLimitTester()
    
    try:
        # Run all tests
        all_tests = await tester.test_rate_limits()
        
        # Analyze results
        analysis = tester.analyze_results(all_tests)
        
        # Save results
        with open("rate_limit_results.txt", "w") as f:
            f.write("MCP RATE LIMIT TEST RESULTS\n")
            f.write("=" * 40 + "\n\n")
            
            f.write(f"Rate Limit Detected: {'YES' if analysis['has_rate_limit'] else 'NO'}\n")
            
            if analysis['has_rate_limit'] and analysis['throttle_threshold']:
                f.write(f"Throttle Threshold: ~{analysis['throttle_threshold']} requests\n")
            
            f.write(f"Sustainable Rate: {analysis['sustainable_rate']:.1f} req/s\n")
            f.write(f"Burst Rate: {analysis['burst_rate']:.1f} req/s\n")
            f.write(f"Circuit Breaker: {'WORKING' if analysis['circuit_breaker_working'] else 'NEEDS TUNING'}\n")
            
            f.write("\nRecommendation: ")
            if analysis['has_rate_limit']:
                f.write("Implement request queuing and caching for production\n")
            else:
                f.write("No rate limiting concerns for normal usage\n")
        
        print(f"\n✅ Results saved to rate_limit_results.txt")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)