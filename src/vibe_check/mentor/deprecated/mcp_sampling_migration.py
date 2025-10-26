"""
Migration module to integrate security fixes into existing mcp_sampling.py
This provides a backward-compatible layer while transitioning to secure implementation
"""

import logging
from typing import Dict, Any, Optional, List, Union, Tuple
from dataclasses import dataclass

# Import secure components
from .mcp_sampling_secure import (
    QueryInput,
    WorkspaceDataInput,
    RateLimiter,
    FileAccessController,
    SafeTemplateRenderer,
    EnhancedSecretsScanner,
    sanitize_code_for_llm as secure_sanitize_code,
)

# Import original components for compatibility
from ..mcp_sampling import (
    MCPSamplingClient as OriginalMCPSamplingClient,
    PromptBuilder as OriginalPromptBuilder,
    PromptTemplate as OriginalPromptTemplate,
    SamplingConfig,
    ResponseQuality,
    CircuitBreaker,
    ResponseCache,
)

logger = logging.getLogger(__name__)


class SecurePromptTemplate:
    """Secure replacement for PromptTemplate using Jinja2"""

    def __init__(self, role: str, template: str, variables: List[str]):
        self.role = role
        self.template = template
        self.variables = variables
        self.renderer = SafeTemplateRenderer()

    def render(self, **kwargs) -> str:
        """Render template using secure Jinja2 sandbox"""
        try:
            # Convert template from {var} format to {{ var }} for Jinja2
            jinja_template = self.template
            for var in self.variables:
                jinja_template = jinja_template.replace(
                    f"{{{var}}}", f"{{{{ {var} }}}}"
                )

            # Render with Jinja2
            return self.renderer.render(jinja_template, kwargs)
        except Exception as e:
            logger.error(f"Secure template rendering failed: {e}")
            # Fallback to safe default
            return f"[Template Error: {self.role}]"


class SecurePromptBuilder:
    """Secure replacement for PromptBuilder with backward compatibility."""

    _renderer = SafeTemplateRenderer()
    _templates_initialized = False
    TEMPLATES: Dict[str, str] = {}

    def __init__(self):
        # Preserve instance attributes for legacy callers using object instances
        self.renderer = self.__class__._renderer
        self.__class__._ensure_templates()

    @classmethod
    def _ensure_templates(cls) -> None:
        if not cls._templates_initialized:
            cls._init_templates()
            cls._templates_initialized = True

    @classmethod
    def _init_templates(cls) -> None:
        """Initialize secure templates once per process."""
        # Convert existing templates to Jinja2 format
        cls.TEMPLATES = {}

        # Architecture decision template
        cls.TEMPLATES[
            "architecture_decision"
        ] = """
You are vibe_check_mentor, a senior engineering advisor focused on pragmatic, experience-based guidance.

Context:
- Query: {{ query | sanitize | truncate_safe(500) }}
- Intent: {{ intent | sanitize }}
- Technologies: {{ technologies | join(', ') | sanitize }}
- Workspace context: {{ workspace_context | sanitize | truncate_safe(1000) }}
- Detected patterns: {{ patterns | join(', ') | sanitize }}

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
- Next Steps (actionable items)
"""

        # Add other templates similarly...
        cls.TEMPLATES[
            "code_review"
        ] = """
You are vibe_check_mentor reviewing code for architectural issues and anti-patterns.

Code Context:
{{ code_context | sanitize | truncate_safe(2000) }}

Query: {{ query | sanitize | truncate_safe(500) }}
File: {{ file_path | sanitize }}
Language: {{ language | sanitize }}

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
- Includes code examples for fixes
"""

        cls.TEMPLATES[
            "implementation_guide"
        ] = """
You are vibe_check_mentor providing implementation guidance.

Task: {{ query | sanitize | truncate_safe(500) }}
Technologies: {{ technologies | join(', ') | sanitize }}
Current Setup: {{ workspace_context | sanitize | truncate_safe(1000) }}
Constraints: {{ constraints | sanitize }}

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
- Deployment considerations
"""

        cls.TEMPLATES[
            "debugging_help"
        ] = """
You are vibe_check_mentor helping debug an issue.

Problem: {{ query | sanitize | truncate_safe(500) }}
Error Context: {{ error_context | sanitize | truncate_safe(500) }}
Code: {{ code_context | sanitize | truncate_safe(2000) }}
Stack: {{ technology_stack | sanitize }}

Approach this systematically:
1. Identify the root cause (not symptoms)
2. Explain why this happens
3. Provide the fix
4. Suggest how to prevent recurrence
5. Include debugging techniques

Be specific to their actual code and error.
"""

        # General template as fallback
        cls.TEMPLATES[
            "general_advice"
        ] = """
You are vibe_check_mentor, a pragmatic senior engineer.

Query: {{ query | sanitize | truncate_safe(500) }}
Context: {{ context | sanitize | truncate_safe(1000) }}

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
- Theoretical discussions without practical value
"""

    @classmethod
    def build_prompt(
        cls,
        intent: str,
        query: str,
        context: Dict[str, Any],
        workspace_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Build a secure prompt using validated inputs and Jinja2"""
        try:
            cls._ensure_templates()
            # Validate query input
            validated_query = QueryInput(query=query, intent=intent)

            # Validate workspace data if provided
            if workspace_data:
                validated_workspace = WorkspaceDataInput(**workspace_data)
                workspace_data = validated_workspace.model_dump()

            # Select template
            template_key = cls._map_intent_to_template(intent)
            template = cls.TEMPLATES.get(template_key, cls.TEMPLATES["general_advice"])

            # Prepare variables
            variables = {
                "query": validated_query.query,
                "intent": intent,
                "context": str(context),
                "technologies": context.get("technologies", []),
                "patterns": context.get("patterns", []),
                "workspace_context": cls._format_workspace_context(workspace_data),
                "code_context": (
                    workspace_data.get("code", "") if workspace_data else ""
                ),
                "file_path": (
                    workspace_data.get("file_path", "") if workspace_data else ""
                ),
                "language": (
                    workspace_data.get("language", "") if workspace_data else ""
                ),
                "constraints": (
                    context.get("constraints", "Not specified")
                    if context
                    else "Not specified"
                ),
                "technology_stack": ", ".join(context.get("technologies", [])),
                "error_context": context.get("error", "") if context else "",
            }

            # Render with Jinja2
            return cls._renderer.render(template, variables)

        except Exception as e:
            logger.error(f"Secure prompt building failed: {e}")
            # Return safe fallback
            return f"Query: {query[:500]}\nPlease provide guidance on this topic."

    @classmethod
    def _map_intent_to_template(cls, intent: str) -> str:
        """Map intent to template key"""
        intent_lower = intent.lower()

        if any(
            word in intent_lower
            for word in ["architect", "design", "structure", "pattern"]
        ):
            return "architecture_decision"
        elif any(word in intent_lower for word in ["review", "feedback", "check"]):
            return "code_review"
        elif any(
            word in intent_lower for word in ["implement", "build", "create", "develop"]
        ):
            return "implementation_guide"
        elif any(word in intent_lower for word in ["debug", "fix", "error", "issue"]):
            return "debugging_help"
        else:
            return "general_advice"

    @classmethod
    def _format_workspace_context(cls, workspace_data: Optional[Dict[str, Any]]) -> str:
        """Format workspace data safely"""
        if not workspace_data:
            return "No workspace context available"

        parts = []

        if "files" in workspace_data:
            files = workspace_data["files"][:10]  # Limit
            parts.append(f"Files analyzed: {', '.join(files)}")

        if "language" in workspace_data:
            parts.append(f"Primary language: {workspace_data['language']}")

        if "frameworks" in workspace_data:
            frameworks = workspace_data["frameworks"][:5]  # Limit
            parts.append(f"Frameworks detected: {', '.join(frameworks)}")

        if "imports" in workspace_data:
            imports = workspace_data["imports"][:10]
            parts.append(f"Key imports: {', '.join(imports)}")

        return "\n".join(parts) if parts else "No specific workspace context"


class SecureMCPSamplingClient(OriginalMCPSamplingClient):
    """Secure wrapper for MCPSamplingClient with added security features"""

    def __init__(
        self, config: Optional[SamplingConfig] = None, request_timeout: int = 30
    ):
        super().__init__(config, request_timeout)

        # Replace with secure components
        self.prompt_builder = SecurePromptBuilder()
        self.rate_limiter = RateLimiter(requests_per_minute=60, burst_capacity=10)
        self.file_controller = FileAccessController()
        self.secrets_scanner = EnhancedSecretsScanner()

        logger.info("Secure MCP Sampling client initialized with security features")

    async def generate_dynamic_response(
        self,
        intent: str,
        query: str,
        context: Dict[str, Any],
        workspace_data: Optional[Dict[str, Any]] = None,
        ctx: Optional[Any] = None,
        user_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Generate dynamic response with security checks

        Added parameters:
            user_id: Optional user identifier for rate limiting
        """
        # Check rate limit
        allowed, wait_time = await self.rate_limiter.check_rate_limit(user_id)
        if not allowed:
            logger.warning(
                f"Rate limit exceeded for user {user_id}, wait {wait_time:.1f}s"
            )
            return {
                "content": f"Rate limit exceeded. Please wait {wait_time:.1f} seconds.",
                "generated": False,
                "rate_limited": True,
                "wait_time": wait_time,
            }

        try:
            # Validate inputs
            validated_query = QueryInput(query=query, intent=intent)

            if workspace_data:
                # Validate workspace data
                validated_workspace = WorkspaceDataInput(**workspace_data)
                workspace_data = validated_workspace.model_dump()

                # Check file access if file paths provided
                if "files" in workspace_data:
                    filtered_files = []
                    for file_path in workspace_data["files"]:
                        allowed, reason = self.file_controller.is_allowed(file_path)
                        if allowed:
                            filtered_files.append(file_path)
                        else:
                            logger.warning(
                                f"File access denied: {file_path} - {reason}"
                            )
                    workspace_data["files"] = filtered_files

                # Scan and redact secrets from code
                if "code" in workspace_data:
                    workspace_data["code"], secrets = (
                        self.secrets_scanner.scan_and_redact(
                            workspace_data["code"], "workspace_code"
                        )
                    )
                    if secrets:
                        logger.warning(
                            f"Redacted {len(secrets)} secrets from workspace code"
                        )

            # Build secure prompt
            system_prompt = self.prompt_builder.build_prompt(
                intent=intent,
                query=validated_query.query,
                context=context,
                workspace_data=workspace_data,
            )

            # Prepare user message
            user_message = f"Query: {validated_query.query}"

            if workspace_data and "code" in workspace_data:
                # Already sanitized above
                user_message += (
                    f"\n\nRelevant code:\n```\n{workspace_data['code'][:2000]}\n```"
                )

            # Continue with original flow using circuit breaker
            if not self.circuit_breaker.can_execute():
                logger.warning("Circuit breaker is open - skipping MCP request")
                return None

            # Make the actual MCP call
            return await super().generate_dynamic_response(
                intent=intent,
                query=validated_query.query,
                context=context,
                workspace_data=workspace_data,
                ctx=ctx,
            )

        except Exception as e:
            logger.error(f"Secure dynamic response generation failed: {e}")
            return None


# Export migration utilities
def migrate_to_secure_client(
    client: OriginalMCPSamplingClient,
) -> SecureMCPSamplingClient:
    """
    Migrate an existing MCPSamplingClient to secure version

    Args:
        client: Original MCPSamplingClient instance

    Returns:
        SecureMCPSamplingClient with same configuration
    """
    secure_client = SecureMCPSamplingClient(
        config=client.config, request_timeout=getattr(client, "request_timeout", 30)
    )

    # Preserve circuit breaker state
    secure_client.circuit_breaker = client.circuit_breaker

    return secure_client


# Compatibility exports
__all__ = [
    "SecurePromptTemplate",
    "SecurePromptBuilder",
    "SecureMCPSamplingClient",
    "migrate_to_secure_client",
    # Re-export secure components
    "QueryInput",
    "WorkspaceDataInput",
    "RateLimiter",
    "FileAccessController",
    "SafeTemplateRenderer",
    "EnhancedSecretsScanner",
]
