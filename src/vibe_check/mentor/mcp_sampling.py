"""
MCP Sampling Integration for Dynamic Response Generation

This module provides the integration with MCP's native sampling protocol,
allowing vibe_check_mentor to request LLM completions from the client
without requiring API keys.
"""

import logging
import json
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

# Import MCP types for sampling
try:
    from mcp.types import (
        TextContent,
        ImageContent,
        SamplingMessage
    )
except ImportError:
    # Fallback definitions for development
    TextContent = Dict[str, Any]
    ImageContent = Dict[str, Any]
    SamplingMessage = Dict[str, Any]

logger = logging.getLogger(__name__)


class ResponseQuality(Enum):
    """Quality levels for dynamic response generation"""
    FAST = "fast"  # Quick responses, lower quality
    BALANCED = "balanced"  # Balance between speed and quality
    HIGH = "high"  # High quality, slower responses


@dataclass
class SamplingConfig:
    """Configuration for MCP sampling requests"""
    temperature: float = 0.7
    max_tokens: int = 1000
    model_preferences: Optional[List[str]] = None
    include_context: str = "thisServer"
    quality: ResponseQuality = ResponseQuality.BALANCED
    
    def to_params(self) -> Dict[str, Any]:
        """Convert config to MCP sampling parameters"""
        params = {
            "temperature": self.temperature,
            "maxTokens": self.max_tokens,
            "includeContext": self.include_context
        }
        
        if self.model_preferences:
            params["modelPreferences"] = {
                "hints": self.model_preferences
            }
        
        return params


@dataclass
class PromptTemplate:
    """Template for generating structured prompts"""
    role: str
    template: str
    variables: List[str]
    
    def render(self, **kwargs) -> str:
        """Render the template with provided variables"""
        text = self.template
        for var in self.variables:
            if var in kwargs:
                text = text.replace(f"{{{var}}}", str(kwargs[var]))
        return text


class PromptBuilder:
    """Builds structured prompts for different intent types"""
    
    # Templates for different intent types
    TEMPLATES = {
        "architecture_decision": PromptTemplate(
            role="system",
            template="""You are vibe_check_mentor, a senior engineering advisor focused on pragmatic, experience-based guidance.

Context:
- Query: {query}
- Intent: {intent}
- Technologies: {technologies}
- Workspace context: {workspace_context}
- Detected patterns: {patterns}

Your persona traits:
- Senior engineer with 15+ years experience
- Believes in "boring technology" and proven patterns
- Anti-complexity, pro-simplicity
- Focuses on maintainability over perfection
- Uses real examples from production systems

Provide specific, actionable advice that:
1. Addresses the exact question asked
2. References the actual code/context provided
3. Suggests concrete next steps
4. Warns about common pitfalls
5. Considers team capability and project constraints

Format your response with clear sections:
- Direct Answer (1-2 sentences)
- Reasoning (why this approach)
- Implementation Notes (specific to their stack)
- Watch Out For (common mistakes)
- Next Steps (actionable items)""",
            variables=["query", "intent", "technologies", "workspace_context", "patterns"]
        ),
        
        "code_review": PromptTemplate(
            role="system",
            template="""You are vibe_check_mentor reviewing code for architectural issues and anti-patterns.

Code Context:
{code_context}

Query: {query}
File: {file_path}
Language: {language}

Focus on:
1. Anti-patterns and code smells
2. Security vulnerabilities
3. Performance bottlenecks
4. Maintainability issues
5. Missing error handling

Provide feedback that is:
- Specific to the code shown
- Actionable and constructive
- Prioritized by severity
- Includes code examples for fixes""",
            variables=["code_context", "query", "file_path", "language"]
        ),
        
        "implementation_guide": PromptTemplate(
            role="system",
            template="""You are vibe_check_mentor providing implementation guidance.

Task: {query}
Technologies: {technologies}
Current Setup: {workspace_context}
Constraints: {constraints}

Provide a practical implementation guide that:
1. Breaks down the task into clear steps
2. Uses the existing tech stack
3. Avoids over-engineering
4. Includes error handling
5. Considers edge cases

Format as:
- Overview (what we're building)
- Prerequisites (what's needed)
- Step-by-step implementation
- Testing approach
- Deployment considerations""",
            variables=["query", "technologies", "workspace_context", "constraints"]
        ),
        
        "debugging_help": PromptTemplate(
            role="system",
            template="""You are vibe_check_mentor helping debug an issue.

Problem: {query}
Error Context: {error_context}
Code: {code_context}
Stack: {technology_stack}

Approach this systematically:
1. Identify the root cause (not symptoms)
2. Explain why this happens
3. Provide the fix
4. Suggest how to prevent recurrence
5. Include debugging techniques

Be specific to their actual code and error.""",
            variables=["query", "error_context", "code_context", "technology_stack"]
        ),
        
        "general_advice": PromptTemplate(
            role="system",
            template="""You are vibe_check_mentor, a pragmatic senior engineer.

Query: {query}
Context: {context}

Provide advice that is:
- Direct and actionable
- Based on real experience
- Focused on simplicity
- Aware of trade-offs
- Specific to their situation

Avoid:
- Generic platitudes
- Over-engineering
- Unnecessary complexity
- Theoretical discussions without practical value""",
            variables=["query", "context"]
        )
    }
    
    @classmethod
    def build_prompt(
        cls,
        intent: str,
        query: str,
        context: Dict[str, Any],
        workspace_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Build a structured prompt based on intent and context
        
        Args:
            intent: The detected intent type
            query: The user's original query
            context: Extracted context (technologies, patterns, etc.)
            workspace_data: Optional workspace/file context
            
        Returns:
            Formatted prompt string
        """
        # Map intent to template
        template_key = cls._map_intent_to_template(intent)
        template = cls.TEMPLATES.get(template_key, cls.TEMPLATES["general_advice"])
        
        # Prepare variables
        variables = {
            "query": query,
            "intent": intent,
            "context": json.dumps(context, indent=2) if context else "",
            "technologies": ", ".join(context.get("technologies", [])),
            "patterns": ", ".join(context.get("patterns", [])),
            "workspace_context": cls._format_workspace_context(workspace_data),
            "constraints": context.get("constraints", "Not specified"),
            "technology_stack": ", ".join(context.get("technologies", [])),
            "code_context": workspace_data.get("code", "") if workspace_data else "",
            "error_context": context.get("error", "") if context else "",
            "file_path": workspace_data.get("file_path", "") if workspace_data else "",
            "language": workspace_data.get("language", "") if workspace_data else ""
        }
        
        return template.render(**variables)
    
    @classmethod
    def _map_intent_to_template(cls, intent: str) -> str:
        """Map detected intent to appropriate template"""
        intent_lower = intent.lower()
        
        if any(word in intent_lower for word in ["architect", "design", "structure", "pattern"]):
            return "architecture_decision"
        elif any(word in intent_lower for word in ["review", "feedback", "check"]):
            return "code_review"
        elif any(word in intent_lower for word in ["implement", "build", "create", "develop"]):
            return "implementation_guide"
        elif any(word in intent_lower for word in ["debug", "fix", "error", "issue"]):
            return "debugging_help"
        else:
            return "general_advice"
    
    @classmethod
    def _format_workspace_context(cls, workspace_data: Optional[Dict[str, Any]]) -> str:
        """Format workspace data into readable context"""
        if not workspace_data:
            return "No workspace context available"
        
        parts = []
        
        if "files" in workspace_data:
            parts.append(f"Files analyzed: {', '.join(workspace_data['files'])}")
        
        if "language" in workspace_data:
            parts.append(f"Primary language: {workspace_data['language']}")
        
        if "frameworks" in workspace_data:
            parts.append(f"Frameworks detected: {', '.join(workspace_data['frameworks'])}")
        
        if "imports" in workspace_data:
            imports = workspace_data["imports"][:10]  # Limit to first 10
            parts.append(f"Key imports: {', '.join(imports)}")
        
        return "\n".join(parts) if parts else "No specific workspace context"


class MCPSamplingClient:
    """
    Client for making MCP sampling requests
    
    This class handles the actual communication with the MCP client
    to request LLM completions.
    """
    
    def __init__(self, config: Optional[SamplingConfig] = None):
        """Initialize the sampling client"""
        self.config = config or SamplingConfig()
        self.prompt_builder = PromptBuilder()
        logger.info("MCP Sampling client initialized")
    
    async def request_completion(
        self,
        messages: Union[str, List[Union[str, SamplingMessage]]],
        system_prompt: Optional[str] = None,
        config_override: Optional[SamplingConfig] = None
    ) -> Optional[str]:
        """
        Request a completion from the MCP client
        
        Args:
            messages: The messages to send to the LLM
            system_prompt: Optional system prompt
            config_override: Optional config to override defaults
            
        Returns:
            The generated text response, or None if failed
        """
        config = config_override or self.config
        
        try:
            # Import Context here to avoid circular dependency
            from fastmcp import Context
            
            # Get the current context (this would be passed from the tool)
            # In actual implementation, this needs to be passed as a parameter
            ctx = Context.get_current()  # This is pseudocode - actual implementation differs
            
            # Make the sampling request
            response = await ctx.sample(
                messages=messages,
                system_prompt=system_prompt,
                **config.to_params()
            )
            
            # Extract text from response
            if hasattr(response, 'text'):
                return response.text
            elif isinstance(response, dict) and 'text' in response:
                return response['text']
            else:
                logger.warning(f"Unexpected response format: {type(response)}")
                return str(response)
                
        except Exception as e:
            logger.error(f"MCP sampling request failed: {e}")
            return None
    
    async def generate_dynamic_response(
        self,
        intent: str,
        query: str,
        context: Dict[str, Any],
        workspace_data: Optional[Dict[str, Any]] = None,
        ctx: Optional[Any] = None  # FastMCP Context object
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a dynamic response using MCP sampling
        
        Args:
            intent: The detected intent
            query: The user's query
            context: Extracted context
            workspace_data: Optional workspace data
            ctx: The FastMCP Context object (passed from tool)
            
        Returns:
            Generated response with metadata, or None if failed
        """
        # Build the prompt
        system_prompt = self.prompt_builder.build_prompt(
            intent=intent,
            query=query,
            context=context,
            workspace_data=workspace_data
        )
        
        # Prepare user message
        user_message = f"Query: {query}"
        
        if workspace_data and "code" in workspace_data:
            user_message += f"\n\nRelevant code:\n```\n{workspace_data['code'][:2000]}\n```"
        
        try:
            if ctx:
                # Use the provided context for sampling
                response = await ctx.sample(
                    messages=user_message,
                    system_prompt=system_prompt,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                    model_preferences=self.config.model_preferences
                )
                
                if hasattr(response, 'text'):
                    response_text = response.text
                else:
                    response_text = str(response)
            else:
                # Fallback for testing or when context not available
                logger.warning("No FastMCP context provided, using fallback")
                response_text = await self.request_completion(
                    messages=user_message,
                    system_prompt=system_prompt
                )
            
            if response_text:
                return {
                    "content": response_text,
                    "generated": True,
                    "intent": intent,
                    "confidence": 0.9,  # High confidence for generated responses
                    "model_used": self.config.model_preferences[0] if self.config.model_preferences else "default"
                }
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to generate dynamic response: {e}")
            return None


class ResponseCache:
    """Simple cache for frequently generated responses"""
    
    def __init__(self, max_size: int = 100):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
    
    def get_cache_key(self, intent: str, query: str, context: Dict[str, Any]) -> str:
        """Generate a cache key from request parameters"""
        # Create a simple hash of the key components
        key_parts = [
            intent,
            query[:100],  # First 100 chars of query
            ",".join(sorted(context.get("technologies", []))),
            ",".join(sorted(context.get("patterns", [])))
        ]
        return "|".join(key_parts)
    
    def get(self, intent: str, query: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get a cached response if available"""
        key = self.get_cache_key(intent, query, context)
        if key in self.cache:
            self.hits += 1
            logger.debug(f"Cache hit for key: {key[:50]}...")
            return self.cache[key]
        else:
            self.misses += 1
            return None
    
    def put(self, intent: str, query: str, context: Dict[str, Any], response: Dict[str, Any]):
        """Store a response in the cache"""
        if len(self.cache) >= self.max_size:
            # Remove oldest entry (simple FIFO)
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
        
        key = self.get_cache_key(intent, query, context)
        self.cache[key] = response
        logger.debug(f"Cached response for key: {key[:50]}...")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        return {
            "size": len(self.cache),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{hit_rate:.1f}%"
        }