"""
Hybrid Response Router for Vibe Check Mentor

Routes queries to either static response banks (fast) or dynamic generation (flexible)
based on confidence scoring and pattern matching.
"""

import logging
import time
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
from enum import Enum

# Import telemetry components
from .telemetry import get_telemetry_collector
from .metrics import RouteType

logger = logging.getLogger(__name__)


class RouteDecision(Enum):
    """Decision types for routing"""
    STATIC = "static"  # Use pre-written response
    DYNAMIC = "dynamic"  # Generate new response
    HYBRID = "hybrid"  # Combine both approaches


@dataclass
class RouteMetrics:
    """Metrics for routing decisions"""
    decision: RouteDecision
    confidence: float
    reasoning: str
    latency_estimate_ms: int
    fallback_available: bool


class ConfidenceScorer:
    """Scores confidence for routing decisions"""
    
    # Patterns that indicate well-understood scenarios (use static)
    HIGH_CONFIDENCE_PATTERNS = [
        # Common architecture decisions
        r"should\s+i\s+use\s+(react|vue|angular)",
        r"monolith\s+vs\s+microservices",
        r"rest\s+vs\s+graphql",
        r"sql\s+vs\s+nosql",
        
        # Standard implementation patterns
        r"implement\s+authentication",
        r"setup\s+ci\s*cd",
        r"docker\s+compose",
        r"database\s+migration",
        
        # Common debugging scenarios
        r"cors\s+error",
        r"memory\s+leak",
        r"slow\s+query",
        r"undefined\s+is\s+not",
        
        # Best practices
        r"best\s+practices?\s+for",
        r"how\s+to\s+structure",
        r"naming\s+convention",
        r"code\s+review"
    ]
    
    # Patterns that indicate novel/specific scenarios (use dynamic)
    LOW_CONFIDENCE_PATTERNS = [
        # Specific technology combinations
        r"[a-z]+\s+with\s+[a-z]+\s+and\s+[a-z]+",  # "X with Y and Z"
        
        # Project-specific questions
        r"in\s+my\s+(project|code|app)",
        r"specific\s+to\s+our",
        r"custom\s+implementation",
        
        # Complex multi-part questions
        r"first.*then.*finally",
        r"step\s+\d+.*step\s+\d+",
        
        # Edge cases and unusual scenarios
        r"edge\s+case",
        r"unusual\s+requirement",
        r"special\s+case",
        r"hybrid\s+approach",
        
        # Integration of many tools
        r"integrate.*with.*and.*using",
        
        # Very specific version combinations
        r"v\d+\.\d+.*with.*v\d+\.\d+"
    ]
    
    @classmethod
    def calculate_confidence(
        cls,
        query: str,
        intent: str,
        context: Dict[str, Any],
        has_workspace_context: bool = False
    ) -> Tuple[float, str]:
        """
        Calculate confidence score for using static responses
        
        Args:
            query: The user's query
            intent: Detected intent
            context: Extracted context
            has_workspace_context: Whether workspace files are available
            
        Returns:
            Tuple of (confidence_score, reasoning)
        """
        import re
        
        confidence = 0.5  # Start neutral
        reasons = []
        
        query_lower = query.lower()
        
        # Check for high confidence patterns
        for pattern in cls.HIGH_CONFIDENCE_PATTERNS:
            if re.search(pattern, query_lower):
                confidence += 0.2
                reasons.append(f"Common pattern detected: {pattern[:30]}...")
                break
        
        # Check for low confidence patterns
        for pattern in cls.LOW_CONFIDENCE_PATTERNS:
            if re.search(pattern, query_lower):
                confidence -= 0.3
                reasons.append(f"Novel scenario detected: {pattern[:30]}...")
                break
        
        # Adjust based on query complexity
        word_count = len(query.split())
        if word_count > 50:
            confidence -= 0.1
            reasons.append("Long, complex query")
        elif word_count < 10:
            confidence += 0.1
            reasons.append("Simple, direct query")
        
        # Adjust based on technologies mentioned
        tech_count = len(context.get("technologies", []))
        if tech_count > 5:
            confidence -= 0.15
            reasons.append(f"Many technologies ({tech_count}) mentioned")
        elif tech_count == 0:
            confidence += 0.1
            reasons.append("General question, no specific tech")
        
        # Workspace context indicates specific situation
        if has_workspace_context:
            confidence -= 0.2
            reasons.append("Has specific workspace context")
        
        # Check for specific file references
        if any(indicator in query_lower for indicator in [".py", ".js", ".ts", "file", "code"]):
            confidence -= 0.15
            reasons.append("References specific files/code")
        
        # Intent-based adjustments
        if intent in ["architecture_decision", "implementation_guide"]:
            confidence += 0.1
            reasons.append(f"Common intent type: {intent}")
        elif intent in ["debugging_help", "code_review"]:
            confidence -= 0.1
            reasons.append(f"Context-specific intent: {intent}")
        
        # Clamp confidence to valid range
        confidence = max(0.0, min(1.0, confidence))
        
        reasoning = " | ".join(reasons) if reasons else "Default scoring"
        
        return confidence, reasoning


class HybridRouter:
    """
    Routes queries between static and dynamic response generation
    """
    
    def __init__(
        self,
        confidence_threshold: float = 0.7,
        enable_caching: bool = True,
        prefer_speed: bool = False
    ):
        """
        Initialize the hybrid router
        
        Args:
            confidence_threshold: Minimum confidence for static responses
            enable_caching: Whether to cache routing decisions
            prefer_speed: Prefer faster static responses when possible
        """
        self.confidence_threshold = confidence_threshold
        self.enable_caching = enable_caching
        self.prefer_speed = prefer_speed
        self.scorer = ConfidenceScorer()
        self.decision_cache: Dict[str, RouteMetrics] = {}
        self._stats = {
            "static_routes": 0,
            "dynamic_routes": 0,
            "hybrid_routes": 0,
            "cache_hits": 0,
            "total_requests": 0
        }
        
        # Initialize telemetry integration
        self.telemetry = get_telemetry_collector()
        
        logger.info(f"Hybrid router initialized: threshold={confidence_threshold}, cache={enable_caching}")
    
    def decide_route(
        self,
        query: str,
        intent: str,
        context: Dict[str, Any],
        has_workspace_context: bool = False,
        has_static_response: bool = True,
        force_dynamic: bool = False
    ) -> RouteMetrics:
        """
        Decide how to route the query
        
        Args:
            query: The user's query
            intent: Detected intent
            context: Extracted context
            has_workspace_context: Whether workspace files are available
            has_static_response: Whether a static response exists
            force_dynamic: Force dynamic generation
            
        Returns:
            RouteMetrics with the routing decision
        """
        self._stats["total_requests"] += 1
        
        # Check cache first
        cache_key = self._get_cache_key(query, intent, context, has_workspace_context)
        if self.enable_caching and cache_key in self.decision_cache:
            self._stats["cache_hits"] += 1
            cached = self.decision_cache[cache_key]
            
            # Record cache hit in telemetry
            self.telemetry.record_response(
                route_type=RouteType.CACHE_HIT,
                latency_ms=1.0,  # Cache hits are very fast
                success=True,
                intent=intent,
                query_length=len(query),
                cache_hit=True
            )
            
            logger.debug(f"Using cached routing decision: {cached.decision.value}")
            return cached
        
        # Force dynamic if requested
        if force_dynamic:
            metrics = RouteMetrics(
                decision=RouteDecision.DYNAMIC,
                confidence=0.0,
                reasoning="Forced dynamic generation",
                latency_estimate_ms=2000,
                fallback_available=has_static_response
            )
            self._stats["dynamic_routes"] += 1
            return metrics
        
        # Calculate confidence
        confidence, reasoning = self.scorer.calculate_confidence(
            query, intent, context, has_workspace_context
        )
        
        # Make routing decision
        if not has_static_response:
            # No static response available, must use dynamic
            decision = RouteDecision.DYNAMIC
            latency = 2000  # ~2 seconds for dynamic
            self._stats["dynamic_routes"] += 1
            route_type = RouteType.DYNAMIC
            
        elif confidence >= self.confidence_threshold:
            # High confidence, use static
            decision = RouteDecision.STATIC
            latency = 50  # ~50ms for static
            self._stats["static_routes"] += 1
            route_type = RouteType.STATIC
            
        elif confidence >= 0.4 and self.prefer_speed:
            # Medium confidence but preferring speed
            decision = RouteDecision.HYBRID
            latency = 500  # ~500ms for hybrid
            self._stats["hybrid_routes"] += 1
            route_type = RouteType.HYBRID
            
        else:
            # Low confidence, use dynamic
            decision = RouteDecision.DYNAMIC
            latency = 2000  # ~2 seconds for dynamic
            self._stats["dynamic_routes"] += 1
            route_type = RouteType.DYNAMIC
        
        # Record routing decision in telemetry
        self.telemetry.record_response(
            route_type=route_type,
            latency_ms=latency,
            success=True,
            intent=intent,
            query_length=len(query),
            cache_hit=False
        )
        
        # Create metrics
        metrics = RouteMetrics(
            decision=decision,
            confidence=confidence,
            reasoning=reasoning,
            latency_estimate_ms=latency,
            fallback_available=has_static_response
        )
        
        # Cache the decision
        if self.enable_caching:
            self.decision_cache[cache_key] = metrics
        
        logger.info(
            f"Routing decision: {decision.value} "
            f"(confidence={confidence:.2f}, reason={reasoning[:50]}...)"
        )
        
        return metrics
    
    def should_fallback(
        self,
        metrics: RouteMetrics,
        generation_failed: bool,
        latency_ms: int
    ) -> bool:
        """
        Determine if we should fallback to static response
        
        Args:
            metrics: The original routing metrics
            generation_failed: Whether dynamic generation failed
            latency_ms: Actual latency of the attempt
            
        Returns:
            True if should fallback to static
        """
        if not metrics.fallback_available:
            return False
        
        if generation_failed:
            logger.warning("Dynamic generation failed, falling back to static")
            return True
        
        if latency_ms > 5000:  # More than 5 seconds
            logger.warning(f"Dynamic generation too slow ({latency_ms}ms), falling back")
            return True
        
        return False
    
    def _get_cache_key(self, query: str, intent: str, context: Dict[str, Any], 
                       has_workspace: bool = False) -> str:
        """Generate a cache key for the routing decision"""
        # Include workspace context in the key to differentiate cached decisions
        tech_count = len(context.get("technologies", []))
        workspace_flag = "W" if has_workspace else "N"
        return f"{query[:50]}|{intent}|{tech_count}|{workspace_flag}"
    
    def get_stats(self) -> Dict[str, Any]:
        """Get routing statistics"""
        total = self._stats["total_requests"]
        if total == 0:
            return self._stats
        
        return {
            **self._stats,
            "static_percentage": f"{self._stats['static_routes'] / total * 100:.1f}%",
            "dynamic_percentage": f"{self._stats['dynamic_routes'] / total * 100:.1f}%",
            "hybrid_percentage": f"{self._stats['hybrid_routes'] / total * 100:.1f}%",
            "cache_hit_rate": f"{self._stats['cache_hits'] / total * 100:.1f}%"
        }
    
    def optimize_threshold(self, feedback: List[Dict[str, Any]]):
        """
        Optimize the confidence threshold based on feedback
        
        Args:
            feedback: List of feedback items with decision outcomes
        """
        # Simple optimization: adjust threshold based on success rates
        static_success = []
        dynamic_success = []
        
        for item in feedback:
            if item["decision"] == RouteDecision.STATIC.value:
                static_success.append(item.get("success", False))
            elif item["decision"] == RouteDecision.DYNAMIC.value:
                dynamic_success.append(item.get("success", False))
        
        if len(static_success) > 10:
            static_rate = sum(static_success) / len(static_success)
            if static_rate < 0.7:
                # Static responses not working well, increase threshold
                self.confidence_threshold = min(0.9, self.confidence_threshold + 0.05)
                logger.info(f"Increased confidence threshold to {self.confidence_threshold}")
            elif static_rate > 0.9 and len(dynamic_success) > 10:
                dynamic_rate = sum(dynamic_success) / len(dynamic_success)
                if dynamic_rate > 0.8:
                    # Both working well, can lower threshold for speed
                    self.confidence_threshold = max(0.6, self.confidence_threshold - 0.05)
                    logger.info(f"Decreased confidence threshold to {self.confidence_threshold}")


class RouteOptimizer:
    """
    Optimizes routing decisions based on historical performance
    """
    
    def __init__(self, max_history_size: int = 1000, max_patterns: int = 500):
        self.history: List[Dict[str, Any]] = []
        self.pattern_performance: Dict[str, Dict[str, float]] = {}
        self.max_history_size = max_history_size
        self.max_patterns = max_patterns
    
    def record_outcome(
        self,
        query: str,
        decision: RouteDecision,
        latency_ms: int,
        success: bool,
        user_feedback: Optional[str] = None
    ):
        """Record the outcome of a routing decision"""
        outcome = {
            "timestamp": time.time(),
            "query": query[:100],  # Store first 100 chars
            "decision": decision.value,
            "latency_ms": latency_ms,
            "success": success,
            "feedback": user_feedback
        }
        
        self.history.append(outcome)
        
        # Enforce history size limit (remove oldest entries)
        if len(self.history) > self.max_history_size:
            # Keep only the most recent entries
            self.history = self.history[-self.max_history_size:]
        
        # Update pattern performance
        self._update_pattern_performance(query, decision, success)
        
        # Enforce pattern limit (remove least used patterns)
        if len(self.pattern_performance) > self.max_patterns:
            # Sort by total usage and keep most used patterns
            sorted_patterns = sorted(
                self.pattern_performance.items(),
                key=lambda x: x[1].get("static_total", 0) + x[1].get("dynamic_total", 0),
                reverse=True
            )
            self.pattern_performance = dict(sorted_patterns[:self.max_patterns])
    
    def _update_pattern_performance(
        self,
        query: str,
        decision: RouteDecision,
        success: bool
    ):
        """Update performance metrics for query patterns"""
        # Extract simple patterns (first few words)
        words = query.lower().split()[:3]
        pattern = " ".join(words)
        
        if pattern not in self.pattern_performance:
            self.pattern_performance[pattern] = {
                "static_success": 0,
                "static_total": 0,
                "dynamic_success": 0,
                "dynamic_total": 0
            }
        
        stats = self.pattern_performance[pattern]
        
        if decision == RouteDecision.STATIC:
            stats["static_total"] += 1
            if success:
                stats["static_success"] += 1
        elif decision == RouteDecision.DYNAMIC:
            stats["dynamic_total"] += 1
            if success:
                stats["dynamic_success"] += 1
    
    def get_pattern_recommendation(self, query: str) -> Optional[RouteDecision]:
        """Get routing recommendation based on pattern history"""
        words = query.lower().split()[:3]
        pattern = " ".join(words)
        
        if pattern not in self.pattern_performance:
            return None
        
        stats = self.pattern_performance[pattern]
        
        # Calculate success rates
        static_rate = (
            stats["static_success"] / stats["static_total"]
            if stats["static_total"] > 0 else 0
        )
        dynamic_rate = (
            stats["dynamic_success"] / stats["dynamic_total"]
            if stats["dynamic_total"] > 0 else 0
        )
        
        # Need minimum samples
        if stats["static_total"] < 3 and stats["dynamic_total"] < 3:
            return None
        
        # Recommend based on success rates
        if static_rate > dynamic_rate and static_rate > 0.7:
            return RouteDecision.STATIC
        elif dynamic_rate > static_rate and dynamic_rate > 0.7:
            return RouteDecision.DYNAMIC
        
        return None
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get overall performance summary"""
        if not self.history:
            return {"message": "No history available"}
        
        total = len(self.history)
        successes = sum(1 for h in self.history if h["success"])
        avg_latency = sum(h["latency_ms"] for h in self.history) / total
        
        static_items = [h for h in self.history if h["decision"] == "static"]
        dynamic_items = [h for h in self.history if h["decision"] == "dynamic"]
        
        return {
            "total_requests": total,
            "success_rate": f"{successes / total * 100:.1f}%",
            "avg_latency_ms": int(avg_latency),
            "static_requests": len(static_items),
            "dynamic_requests": len(dynamic_items),
            "static_avg_latency": int(
                sum(h["latency_ms"] for h in static_items) / len(static_items)
            ) if static_items else 0,
            "dynamic_avg_latency": int(
                sum(h["latency_ms"] for h in dynamic_items) / len(dynamic_items)
            ) if dynamic_items else 0
        }