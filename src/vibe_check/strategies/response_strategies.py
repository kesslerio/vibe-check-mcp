"""
Response Generation Strategies

Strategy pattern implementation for generating mentor responses.
Replaces large if-else chains with maintainable, testable strategies.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass

from ..config.config_loader import get_config_loader
from ..mentor.models.config import ConfidenceScores


@dataclass
class TechnicalContext:
    """Technical context extracted from query"""
    technologies: List[str]
    frameworks: List[str]
    patterns: List[str]
    problem_type: str
    specific_features: List[str]
    decision_points: List[str]


class ResponseStrategy(ABC):
    """Abstract base strategy for generating responses"""
    
    @abstractmethod
    def can_handle(self, tech_context: TechnicalContext, query: str) -> bool:
        """Check if this strategy can handle the given context/query"""
        pass
    
    @abstractmethod
    def generate_response(
        self, 
        tech_context: TechnicalContext, 
        patterns: List[Dict[str, Any]], 
        query: str
    ) -> Tuple[str, str, float]:
        """Generate response for the given context"""
        pass
    
    @property
    @abstractmethod
    def priority(self) -> int:
        """Strategy priority (lower number = higher priority)"""
        pass


class LLMComparisonStrategy(ResponseStrategy):
    """Handle LLM model comparison queries"""
    
    @property
    def priority(self) -> int:
        return 1  # Highest priority
    
    def can_handle(self, tech_context: TechnicalContext, query: str) -> bool:
        llm_terms = ['gpt', 'claude', 'gemini', 'sonnet', 'opus', 'o3', 'nano', 'mini', 'haiku', 'deepseek']
        query_lower = query.lower()
        
        # MUST have comparison indicators AND LLM terms to trigger
        comparison_indicators = ['vs', 'versus', 'compare', 'comparison', 'which', 'better', 'choose', 'pick']
        has_comparison = any(indicator in query_lower for indicator in comparison_indicators)
        
        # Check if query contains LLM terms
        has_llm_terms = any(term in query_lower for term in llm_terms)
        
        # Only handle if it's actually comparing LLMs, not just mentioning them
        if has_llm_terms and has_comparison:
            return True
        
        # Check decision points for explicit LLM comparisons
        if any(term in dp.lower() for dp in tech_context.decision_points for term in ['gpt', 'claude', 'gemini', 'deepseek']):
            # Only if decision point also has comparison language
            if any(indicator in dp.lower() for dp in tech_context.decision_points for indicator in comparison_indicators):
                return True
        
        return False
    
    def generate_response(
        self, 
        tech_context: TechnicalContext, 
        patterns: List[Dict[str, Any]], 
        query: str
    ) -> Tuple[str, str, float]:
        """Generate LLM comparison response"""
        config_loader = get_config_loader()
        
        # Check if this is about budget models
        budget_terms = ['mini', 'nano', 'haiku', 'cheap', 'budget', 'cost-effective', 'deepseek']
        is_budget_query = any(term in query.lower() for term in budget_terms)
        
        if is_budget_query:
            return self._generate_budget_response(config_loader)
        else:
            return self._generate_premium_response(config_loader)
    
    def _generate_budget_response(self, config_loader) -> Tuple[str, str, float]:
        """Generate budget LLM response"""
        models = config_loader.get_budget_llm_models()
        
        response_parts = ["Budget LLMs for 2025 (research-backed pricing): "]
        
        for model in models.values():
            highlight = "BEST VALUE: " if model.highlight else ""
            response_parts.append(f"{model.name}: {model.format_pricing()} - {highlight}{model.description}. ")
        
        # Add recommendation
        response_parts.append("Winner: DeepSeek R1 for complex reasoning, GPT-4.1 nano for OpenAI ecosystem, Llama 4 for self-hosting.")
        
        return ("insight", "".join(response_parts), ConfidenceScores.VERY_HIGH)
    
    def _generate_premium_response(self, config_loader) -> Tuple[str, str, float]:
        """Generate premium LLM response"""
        models = config_loader.get_premium_llm_models()
        
        response_parts = ["For LLM model choice in 2025 (latest benchmarks + pricing): "]
        
        for model in models.values():
            response_parts.append(f"{model.name}: {model.description}, {model.format_pricing()}. ")
        
        # Add ranking and recommendation
        response_parts.append("Ranking: Coding→Claude 4 Opus, Cost-effective→Gemini 2.5 Pro, Reasoning→o3 Pro, Balanced→Claude 4 Sonnet. ")
        response_parts.append("My advice: Gemini 2.5 Pro for most use cases, Claude 4 for serious coding, GPT-4.1 for OpenAI ecosystem.")
        
        return ("insight", "".join(response_parts), ConfidenceScores.VERY_HIGH)


class FrameworkComparisonStrategy(ResponseStrategy):
    """Handle framework comparison queries"""
    
    @property
    def priority(self) -> int:
        return 2
    
    def can_handle(self, tech_context: TechnicalContext, query: str) -> bool:
        if not (tech_context.decision_points and tech_context.frameworks):
            return False
        
        # Check for common framework comparisons
        comparison_patterns = ['astro.*next', 'next.*astro', 'bun.*node', 'node.*bun']
        query_lower = query.lower()
        
        return any(
            any(framework in query_lower for framework in comparison.split('.*'))
            for comparison in comparison_patterns
        )
    
    def generate_response(
        self, 
        tech_context: TechnicalContext, 
        patterns: List[Dict[str, Any]], 
        query: str
    ) -> Tuple[str, str, float]:
        """Generate framework comparison response"""
        config_loader = get_config_loader()
        comparisons = config_loader.get_framework_comparisons()
        
        # Check for specific framework comparisons
        query_lower = query.lower()
        
        if 'astro' in query_lower and ('next' in query_lower or 'nextjs' in query_lower):
            comparison = comparisons.get('astro_vs_nextjs')
            if comparison:
                response_data = comparison['response']
                return (response_data['type'], response_data['content'].strip(), response_data['confidence'])
        
        if 'bun' in query_lower and 'node' in query_lower:
            comparison = comparisons.get('bun_vs_nodejs')
            if comparison:
                response_data = comparison['response']
                return (response_data['type'], response_data['content'].strip(), response_data['confidence'])
        
        # Fallback for other framework comparisons
        return (
            "suggestion",
            "For framework comparisons: Consider your team's expertise, project requirements, "
            "and long-term maintenance. Choose tools your team knows well and that have strong "
            "community support for your specific use case.",
            ConfidenceScores.MEDIUM
        )


class AIFrameworkStrategy(ResponseStrategy):
    """Handle AI framework comparison queries"""
    
    @property
    def priority(self) -> int:
        return 3
    
    def can_handle(self, tech_context: TechnicalContext, query: str) -> bool:
        ai_frameworks = ['langchain', 'llamaindex', 'crewai', 'autogen', 'semantic kernel', 'langgraph']
        
        # Check if multiple AI frameworks mentioned or explicit comparison
        ai_frameworks_mentioned = [t for t in tech_context.technologies if t in ai_frameworks]
        ai_in_query = any(fw in query.lower() for fw in ai_frameworks)
        
        return len(ai_frameworks_mentioned) >= 2 or ai_in_query
    
    def generate_response(
        self, 
        tech_context: TechnicalContext, 
        patterns: List[Dict[str, Any]], 
        query: str
    ) -> Tuple[str, str, float]:
        """Generate AI framework comparison response"""
        return (
            "insight",
            "For AI framework choice in 2025 (based on current research): "
            "LlamaIndex wins for RAG - cleaner APIs, purpose-built for search/retrieval. "
            "CrewAI is best for multi-agent systems but built on LangChain (inherits complexity). "
            "LangGraph offers fine-grained control over agent workflows, well-designed for production. "
            "AutoGen excels at autonomous code generation and agent-to-agent communication. "
            "LangChain has massive ecosystem but heavily abstracted, difficult for simple tasks. "
            "My 2025 advice: LlamaIndex for RAG, LangGraph for complex workflows, avoid LangChain for new projects.",
            ConfidenceScores.VERY_HIGH
        )


class TechnologyAdviceStrategy(ResponseStrategy):
    """Handle technology-specific advice"""
    
    @property
    def priority(self) -> int:
        return 4
    
    def can_handle(self, tech_context: TechnicalContext, query: str) -> bool:
        return bool(tech_context.technologies)
    
    def generate_response(
        self, 
        tech_context: TechnicalContext, 
        patterns: List[Dict[str, Any]], 
        query: str
    ) -> Tuple[str, str, float]:
        """Generate technology-specific advice"""
        tech = tech_context.technologies[0]
        
        # Technology-specific advice mapping
        advice_map = {
            ('stripe', 'paypal', 'square'): (
                "suggestion",
                f"For {tech} integration, three critical mistakes I've seen: "
                f"1) Never process payments on the frontend - always server-side only, "
                f"2) Use {tech}'s official SDK and webhooks - don't build custom HTTP calls, "
                f"3) Test with their sandbox extensively before going live. "
                f"Also, implement proper error handling for failed payments and refunds.",
                ConfidenceScores.HIGH
            ),
            ('postgres', 'mysql', 'mongodb'): (
                "insight",
                f"For {tech} in production: "
                f"1) Connection pooling is mandatory - use pgBouncer for Postgres, "
                f"2) Set up read replicas early if you expect growth, "
                f"3) Monitor slow queries from day 1 - add indexes proactively, "
                f"4) Backup strategy: automated daily backups + point-in-time recovery. "
                f"I've seen too many startups lose data because they skipped backups.",
                ConfidenceScores.VERY_HIGH
            )
        }
        
        # Find matching advice
        for tech_group, advice in advice_map.items():
            if tech in tech_group:
                return advice
        
        # Default fallback
        return (
            "concern",
            "This looks like premature infrastructure design. Start with working API calls first, "
            "then extract patterns only when you have 3+ similar use cases. Most 'future flexibility' "
            "never gets used but adds maintenance burden forever.",
            ConfidenceScores.HIGH
        )


class FallbackStrategy(ResponseStrategy):
    """Fallback strategy for unmatched queries"""
    
    @property
    def priority(self) -> int:
        return 999  # Lowest priority
    
    def can_handle(self, tech_context: TechnicalContext, query: str) -> bool:
        return True  # Always can handle as fallback
    
    def generate_response(
        self, 
        tech_context: TechnicalContext, 
        patterns: List[Dict[str, Any]], 
        query: str
    ) -> Tuple[str, str, float]:
        """Generate contextual fallback response based on query content"""
        
        # Check for specific decision patterns with options
        import re
        query_lower = query.lower()
        
        # Look for explicit options (Option A, Option B, etc.)
        options_pattern = r'option [a-c]|approach [a-c]|\b[a-c]\)'
        has_options = bool(re.search(options_pattern, query_lower))
        
        # Look for field/data operations
        has_field_ops = any(term in query_lower for term in 
                           ['field', 'deduplicate', 'duplicate', 'merge', 'data', 'column', 'attribute'])
        
        # Look for decision keywords
        has_decision = any(term in query_lower for term in 
                          ['should', 'choose', 'decide', 'vs', 'better', 'approach', 'option'])
        
        if has_options and has_field_ops:
            # Specific response for field deduplication with options
            return (
                "insight",
                "For your field deduplication options, let me analyze each approach: "
                "Option A (Keep all fields) - Safe but may have redundancy. Good for data preservation. "
                "Option B (Smart deduplication) - Efficient but needs careful validation logic. "
                "Option C (Manual review) - Most accurate but doesn't scale well. "
                "I'd recommend starting with Option B using a similarity threshold (e.g., 90% match), "
                "with Option C as a fallback for edge cases. Log all decisions for auditing. "
                "Test with real data samples first to validate the deduplication logic.",
                ConfidenceScores.HIGH
            )
        elif has_options and has_decision:
            # Response for general decision with options
            return (
                "suggestion",
                f"Looking at your specific options, I recommend evaluating each against: "
                f"1) Implementation complexity - how quickly can you ship? "
                f"2) Maintenance burden - who will maintain this in 6 months? "
                f"3) Scalability - will this work with 10x the data/users? "
                f"4) Reversibility - can you change course if wrong? "
                f"Start with a prototype of the most promising option and validate with real usage.",
                ConfidenceScores.GOOD
            )
        elif tech_context.decision_points:
            # Use decision points from context
            decision = tech_context.decision_points[0] if tech_context.decision_points else "this decision"
            return (
                "suggestion",
                f"For '{decision}': Apply first principles thinking - "
                f"what's the core problem you're solving? Often the simplest approach that "
                f"directly addresses the root cause is best. Consider building a minimal "
                f"proof-of-concept for each approach and measure against your success criteria.",
                ConfidenceScores.GOOD
            )
        elif tech_context.specific_features:
            # Feature-specific advice
            feature = tech_context.specific_features[0]
            return (
                "insight",
                f"For implementing '{feature}': Start with the core functionality that delivers "
                f"immediate value. Build iteratively - ship v0.1 that works for 80% of cases, "
                f"then enhance based on real usage. Avoid premature optimization. "
                f"Document your assumptions so you can revisit them as requirements evolve.",
                ConfidenceScores.GOOD
            )
        else:
            # Generic but slightly more contextual fallback
            query_snippet = query[:100] if len(query) > 100 else query
            return (
                "suggestion",
                f"For your specific question about '{query_snippet}...': "
                f"I recommend starting with the simplest approach that addresses your immediate needs. "
                f"Test with real data/users, measure outcomes, then iterate. "
                f"Most successful systems evolve from simple beginnings rather than complex initial designs.",
                ConfidenceScores.MEDIUM
            )


class ResponseStrategyManager:
    """Manages and orchestrates response strategies"""
    
    def __init__(self):
        self.strategies = [
            LLMComparisonStrategy(),
            FrameworkComparisonStrategy(),
            AIFrameworkStrategy(),
            TechnologyAdviceStrategy(),
            FallbackStrategy()
        ]
        # Sort by priority
        self.strategies.sort(key=lambda s: s.priority)
    
    def generate_response(
        self, 
        tech_context: TechnicalContext, 
        patterns: List[Dict[str, Any]], 
        query: str
    ) -> Tuple[str, str, float]:
        """Generate response using first matching strategy"""
        for strategy in self.strategies:
            if strategy.can_handle(tech_context, query):
                return strategy.generate_response(tech_context, patterns, query)
        
        # This should never happen due to FallbackStrategy
        raise RuntimeError("No strategy could handle the query")


# Global strategy manager instance
_strategy_manager: Optional[ResponseStrategyManager] = None

def get_strategy_manager() -> ResponseStrategyManager:
    """Get singleton strategy manager instance"""
    global _strategy_manager
    if _strategy_manager is None:
        _strategy_manager = ResponseStrategyManager()
    return _strategy_manager