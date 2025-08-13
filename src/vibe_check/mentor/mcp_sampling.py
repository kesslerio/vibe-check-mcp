"""
MCP Sampling Integration for Dynamic Response Generation

This module provides the integration with MCP's native sampling protocol,
allowing vibe_check_mentor to request LLM completions from the client
without requiring API keys.
"""

import logging
import json
import html
import re
import string
import time
import asyncio
from collections import OrderedDict
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum

# Import telemetry components
from .telemetry import get_telemetry_collector, track_latency, TelemetryContext
from .metrics import RouteType

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


def sanitize_code_for_llm(code: str, max_length: int = 2000) -> str:
    """Sanitize code before sending to LLM to prevent injection attacks"""
    if not code:
        return ""
    
    # Remove potential prompt injection patterns
    injection_patterns = [
        r'#\s*ignore\s+all\s+previous',
        r'#\s*system\s*:',
        r'#\s*assistant\s*:',
        r'#\s*user\s*:',
        r'/\*\s*SYSTEM\s*\*/',
        r'""".*?ignore.*?instructions.*?"""',
        r"'''.*?ignore.*?instructions.*?'''"
    ]
    
    sanitized = code
    for pattern in injection_patterns:
        sanitized = re.sub(pattern, '# [REDACTED - POTENTIAL INJECTION]', sanitized, flags=re.IGNORECASE | re.DOTALL)
    
    # Escape HTML entities to prevent rendering issues
    sanitized = html.escape(sanitized)
    
    # Truncate safely at word boundaries
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length].rsplit(' ', 1)[0] + '...'
    
    return sanitized


class SecretsScanner:
    """Scan and redact secrets before processing"""
    
    # Common secret patterns
    SECRET_PATTERNS = [
        (r'api[_-]?key\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?', 'API_KEY'),
        (r'secret[_-]?key\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?', 'SECRET_KEY'),
        (r'password\s*[:=]\s*["\']?([^"\'\\s]{8,})["\']?', 'PASSWORD'),
        (r'token\s*[:=]\s*["\']?([a-zA-Z0-9_\-\.]{20,})["\']?', 'TOKEN'),
        (r'bearer\s+([a-zA-Z0-9_\-\.]+)', 'BEARER_TOKEN'),
        (r'aws_access_key_id\s*=\s*["\']?([A-Z0-9]{20})["\']?', 'AWS_ACCESS_KEY'),
        (r'aws_secret_access_key\s*=\s*["\']?([a-zA-Z0-9/+=]{40})["\']?', 'AWS_SECRET_KEY'),
        (r'-----BEGIN (RSA |EC )?PRIVATE KEY-----', 'PRIVATE_KEY'),
        (r'sk-[a-zA-Z0-9]{48}', 'OPENAI_API_KEY'),
        (r'ghp_[a-zA-Z0-9]{36}', 'GITHUB_TOKEN'),
    ]
    
    @classmethod
    def scan_and_redact(cls, text: str) -> Tuple[str, List[Dict[str, str]]]:
        """Scan text for secrets and redact them"""
        redacted_text = text
        found_secrets = []
        
        for pattern, secret_type in cls.SECRET_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                secret_value = match.group(0)
                redacted_value = f"[REDACTED_{secret_type}]"
                redacted_text = redacted_text.replace(secret_value, redacted_value)
                
                found_secrets.append({
                    'type': secret_type,
                    'location': match.start(),
                    'length': len(secret_value)
                })
        
        if found_secrets:
            logger.warning(f"Detected and redacted {len(found_secrets)} potential secrets")
        
        return redacted_text, found_secrets
    
    @classmethod
    def validate_safe(cls, text: str) -> bool:
        """Check if text is safe (no secrets detected)"""
        for pattern, _ in cls.SECRET_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return False
        return True


class ResponseQuality(Enum):
    """Quality levels for dynamic response generation"""
    FAST = "fast"  # Quick responses, lower quality
    BALANCED = "balanced"  # Balance between speed and quality
    HIGH = "high"  # High quality, slower responses


class CircuitBreakerState(Enum):
    """States for the circuit breaker"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failures exceeded threshold, blocking requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """Circuit breaker to prevent cascading failures"""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        success_threshold: int = 2
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0
        self.last_state_change = time.time()
    
    def record_success(self):
        """Record a successful operation"""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                # Service recovered, close the circuit
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                self.last_state_change = time.time()
                logger.info("Circuit breaker closed - service recovered")
        elif self.state == CircuitBreakerState.CLOSED:
            self.failure_count = max(0, self.failure_count - 1)
    
    def record_failure(self):
        """Record a failed operation"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitBreakerState.CLOSED:
            if self.failure_count >= self.failure_threshold:
                # Too many failures, open the circuit
                self.state = CircuitBreakerState.OPEN
                self.last_state_change = time.time()
                logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
        elif self.state == CircuitBreakerState.HALF_OPEN:
            # Failed during recovery test, reopen circuit
            self.state = CircuitBreakerState.OPEN
            self.success_count = 0
            self.last_state_change = time.time()
            logger.warning("Circuit breaker reopened - recovery test failed")
    
    def can_execute(self) -> bool:
        """Check if we can execute a request"""
        if self.state == CircuitBreakerState.CLOSED:
            return True
        elif self.state == CircuitBreakerState.OPEN:
            # Check if recovery timeout has passed
            if time.time() - self.last_failure_time > self.recovery_timeout:
                # Try half-open state
                self.state = CircuitBreakerState.HALF_OPEN
                self.success_count = 0
                self.last_state_change = time.time()
                logger.info("Circuit breaker half-open - testing recovery")
                return True
            return False
        else:  # HALF_OPEN
            return True
    
    def get_status(self) -> Dict[str, Any]:
        """Get circuit breaker status"""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure": self.last_failure_time,
            "uptime": time.time() - self.last_state_change
        }


@dataclass
class SamplingConfig:
    """Configuration for MCP sampling requests"""
    temperature: float = 0.7
    max_tokens: int = 1000
    model_preferences: Optional[List[str]] = None
    include_context: str = "thisServer"
    quality: ResponseQuality = ResponseQuality.BALANCED
    
    def __post_init__(self):
        """Validate configuration parameters"""
        # Validate temperature (0.0 to 2.0 is typical range)
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError(f"Temperature must be between 0.0 and 2.0, got {self.temperature}")
        
        # Validate max_tokens (reasonable bounds)
        if not 1 <= self.max_tokens <= 100000:
            raise ValueError(f"max_tokens must be between 1 and 100000, got {self.max_tokens}")
        
        # Validate include_context
        valid_contexts = ["thisServer", "allServers", "none"]
        if self.include_context not in valid_contexts:
            raise ValueError(f"include_context must be one of {valid_contexts}, got {self.include_context}")
        
        # Validate model preferences format
        if self.model_preferences:
            if not isinstance(self.model_preferences, list):
                raise TypeError("model_preferences must be a list of model names")
            for model in self.model_preferences:
                if not isinstance(model, str):
                    raise TypeError(f"Each model preference must be a string, got {type(model)}")
    
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
    
    def __init__(self, config: Optional[SamplingConfig] = None, request_timeout: int = 30):
        """Initialize the sampling client"""
        self.config = config or SamplingConfig()
        self.prompt_builder = PromptBuilder()
        self.circuit_breaker = CircuitBreaker()
        self.request_timeout = request_timeout  # Timeout in seconds
        
        # Initialize telemetry integration
        self.telemetry = get_telemetry_collector()
        self.telemetry.set_circuit_breaker(self.circuit_breaker)
        
        logger.info("MCP Sampling client initialized with circuit breaker and telemetry")
    
    async def request_completion(
        self,
        messages: Union[str, List[Union[str, SamplingMessage]]],
        system_prompt: Optional[str] = None,
        config_override: Optional[SamplingConfig] = None,
        ctx: Optional[Any] = None
    ) -> Optional[str]:
        """
        Request a completion from the MCP client
        
        Args:
            messages: The messages to send to the LLM
            system_prompt: Optional system prompt
            config_override: Optional config to override defaults
            ctx: The FastMCP Context object (must be passed from tool)
            
        Returns:
            The generated text response, or None if failed
        """
        config = config_override or self.config
        
        if not ctx:
            logger.error("No FastMCP context provided to request_completion")
            return None
        
        try:
            
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
    
    @track_latency(RouteType.DYNAMIC, intent="dynamic_generation")
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
            # Sanitize code to prevent injection attacks
            raw_code = workspace_data['code']
            
            # First, scan and redact any secrets
            sanitized_code, found_secrets = SecretsScanner.scan_and_redact(raw_code)
            
            # Then apply injection prevention sanitization
            sanitized_code = sanitize_code_for_llm(sanitized_code, 2000)
            
            if found_secrets:
                logger.warning(f"[SECURITY] Redacted {len(found_secrets)} secrets from workspace code")
            
            user_message += f"\n\nRelevant code:\n```\n{sanitized_code}\n```"
        
        # Check circuit breaker
        if not self.circuit_breaker.can_execute():
            logger.warning("Circuit breaker is open - skipping MCP request")
            return None
        
        try:
            if not ctx:
                # No context available - cannot make MCP sampling request
                logger.warning("No FastMCP context provided, cannot generate dynamic response")
                return None  # Let the caller handle fallback to static responses
            
            # Apply timeout to the sampling request
            try:
                response = await asyncio.wait_for(
                    ctx.sample(
                        messages=user_message,
                        system_prompt=system_prompt,
                        temperature=self.config.temperature,
                        max_tokens=self.config.max_tokens,
                        model_preferences=self.config.model_preferences
                    ),
                    timeout=self.request_timeout
                )
                
                if hasattr(response, 'text'):
                    response_text = response.text
                else:
                    response_text = str(response)
                
                # Record success
                self.circuit_breaker.record_success()
                
            except asyncio.TimeoutError:
                logger.error(f"MCP sampling request timed out after {self.request_timeout}s")
                self.circuit_breaker.record_failure()
                return None
            
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
            self.circuit_breaker.record_failure()
            return None


class ResponseCache:
    """LRU cache for frequently generated responses with TTL support"""
    
    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600):
        self.cache: OrderedDict[str, Tuple[Dict[str, Any], float]] = OrderedDict()
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
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
        """Get a cached response if available and not expired"""
        key = self.get_cache_key(intent, query, context)
        if key in self.cache:
            response, timestamp = self.cache[key]
            
            # Check if expired
            if time.time() - timestamp > self.ttl_seconds:
                # Remove expired entry
                del self.cache[key]
                self.misses += 1
                return None
            
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            self.hits += 1
            logger.debug(f"Cache hit for key: {key[:50]}...")
            return response
        else:
            self.misses += 1
            return None
    
    def put(self, intent: str, query: str, context: Dict[str, Any], response: Dict[str, Any]):
        """Store a response in the cache with timestamp"""
        key = self.get_cache_key(intent, query, context)
        
        # If key exists, move to end
        if key in self.cache:
            self.cache.move_to_end(key)
        
        # Add new entry
        self.cache[key] = (response, time.time())
        
        # Remove least recently used if over limit
        while len(self.cache) > self.max_size:
            # Remove least recently used (first item)
            self.cache.popitem(last=False)
        
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