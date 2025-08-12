# MCP Sampling Integration API Design

## Executive Summary

This document defines the API contracts for integrating MCP sampling capabilities into vibe_check_mentor, enabling dynamic response generation through the MCP protocol without requiring API keys.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    FastMCP Tool Layer                    │
│                   @server.tool(ctx)                      │
└─────────────────────┬───────────────────────────────────┘
                      │ ctx parameter
┌─────────────────────▼───────────────────────────────────┐
│                  Request Context Layer                   │
│              MCPRequestContext(ctx, metadata)            │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                   Hybrid Router Layer                    │
│           RouteDecision(STATIC/DYNAMIC/HYBRID)          │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                 MCP Sampling Client Layer                │
│              MCPSamplingAdapter(ctx_aware)               │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                  Response Generation Layer               │
│            DynamicResponseGenerator(templates)           │
└──────────────────────────────────────────────────────────┘
```

## 1. Core API Interfaces

### 1.1 Request Context Interface

```python
from typing import Optional, Dict, Any, Protocol
from dataclasses import dataclass
from datetime import datetime
import uuid

class MCPContext(Protocol):
    """Protocol for FastMCP context object"""
    async def sample(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> Any:
        """Sample completion from LLM"""
        ...

@dataclass
class MCPRequestContext:
    """
    Unified context object for MCP sampling requests
    
    This wraps the FastMCP ctx parameter and adds request metadata
    for tracing, monitoring, and error handling.
    """
    # Core context
    mcp_context: MCPContext  # The FastMCP ctx parameter
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Request metadata
    user_query: str = ""
    session_id: Optional[str] = None
    mode: str = "standard"  # interrupt/standard/comprehensive
    phase: str = "planning"  # planning/implementation/review
    
    # Security context
    workspace_path: Optional[str] = None
    allowed_operations: List[str] = field(default_factory=list)
    
    # Performance tracking
    timeout_seconds: int = 30
    max_retries: int = 3
    
    def validate(self) -> bool:
        """Validate context has required fields"""
        return self.mcp_context is not None and hasattr(self.mcp_context, 'sample')
```

### 1.2 Sampling Configuration API

```python
from enum import Enum
from typing import List, Optional, Dict, Any

class ModelPreference(Enum):
    """Model selection preferences"""
    FAST = "claude-3-haiku"  # Fastest, lower quality
    BALANCED = "claude-3-sonnet"  # Balanced
    HIGH_QUALITY = "claude-3-opus"  # Highest quality
    
class SamplingStrategy(Enum):
    """Response generation strategies"""
    SINGLE_SHOT = "single_shot"  # One request
    CHAIN_OF_THOUGHT = "chain_of_thought"  # Multi-step reasoning
    CONSENSUS = "consensus"  # Multiple samples, pick best
    ITERATIVE = "iterative"  # Refine through iterations

@dataclass
class EnhancedSamplingConfig:
    """
    Enhanced configuration for MCP sampling with validation
    """
    # Model parameters
    temperature: float = 0.7
    max_tokens: int = 2000
    top_p: float = 0.95
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    
    # Model selection
    model_preference: ModelPreference = ModelPreference.BALANCED
    model_hints: List[str] = field(default_factory=list)
    
    # Strategy
    strategy: SamplingStrategy = SamplingStrategy.SINGLE_SHOT
    consensus_samples: int = 3  # For CONSENSUS strategy
    
    # Context inclusion
    include_context: str = "thisServer"  # thisServer/allServers/none
    include_workspace: bool = True
    
    # Safety
    enable_sanitization: bool = True
    enable_secrets_scanning: bool = True
    max_prompt_length: int = 10000
    
    def validate(self) -> ValidationResult:
        """Validate configuration parameters"""
        errors = []
        warnings = []
        
        if not 0.0 <= self.temperature <= 2.0:
            errors.append(f"Temperature {self.temperature} out of range [0.0, 2.0]")
        
        if not 1 <= self.max_tokens <= 100000:
            errors.append(f"max_tokens {self.max_tokens} out of range [1, 100000]")
            
        if self.strategy == SamplingStrategy.CONSENSUS and self.consensus_samples < 2:
            errors.append("CONSENSUS strategy requires at least 2 samples")
            
        if self.max_tokens > 4000 and self.model_preference == ModelPreference.FAST:
            warnings.append("High token count with FAST model may impact latency")
            
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
```

### 1.3 Router Interface

```python
@dataclass
class RoutingContext:
    """Context for routing decisions"""
    query: str
    intent: str
    confidence_scores: Dict[str, float]
    has_workspace_context: bool
    technologies_count: int
    complexity_score: float
    previous_interactions: int = 0
    user_preference: Optional[str] = None  # fast/balanced/comprehensive

class IRoutingStrategy(Protocol):
    """Interface for routing strategies"""
    
    async def decide(
        self,
        context: RoutingContext,
        request_ctx: MCPRequestContext
    ) -> RouteDecision:
        """Make routing decision"""
        ...
    
    def get_confidence(self) -> float:
        """Get confidence in decision"""
        ...

class EnhancedHybridRouter:
    """
    Enhanced router with multiple strategies
    """
    
    def __init__(
        self,
        strategies: List[IRoutingStrategy],
        config: RouterConfig
    ):
        self.strategies = strategies
        self.config = config
        self._metrics = RouterMetrics()
    
    async def route(
        self,
        context: RoutingContext,
        request_ctx: MCPRequestContext
    ) -> RoutingResult:
        """
        Route request based on multiple strategies
        
        Returns:
            RoutingResult with decision, confidence, and metadata
        """
        decisions = []
        
        for strategy in self.strategies:
            decision = await strategy.decide(context, request_ctx)
            confidence = strategy.get_confidence()
            decisions.append((decision, confidence, strategy.__class__.__name__))
        
        # Aggregate decisions (weighted by confidence)
        final_decision = self._aggregate_decisions(decisions)
        
        # Record metrics
        self._metrics.record(final_decision, context)
        
        return RoutingResult(
            decision=final_decision,
            reasoning=self._build_reasoning(decisions),
            estimated_latency_ms=self._estimate_latency(final_decision),
            fallback_available=self._has_fallback(context)
        )
```

## 2. Data Models

### 2.1 Request/Response Models

```python
@dataclass
class SamplingRequest:
    """Request model for MCP sampling"""
    # Required fields
    query: str
    intent: str
    context: Dict[str, Any]
    
    # Optional fields
    session_id: Optional[str] = None
    workspace_data: Optional[WorkspaceData] = None
    config_override: Optional[EnhancedSamplingConfig] = None
    routing_hints: Optional[Dict[str, Any]] = None
    
    # Validation
    def validate(self) -> ValidationResult:
        """Validate request data"""
        if not self.query:
            return ValidationResult(False, ["Query cannot be empty"])
        if len(self.query) > 10000:
            return ValidationResult(False, ["Query exceeds maximum length"])
        return ValidationResult(True)

@dataclass
class SamplingResponse:
    """Response model for MCP sampling"""
    # Core response
    content: str
    confidence: float
    
    # Metadata
    request_id: str
    response_time_ms: int
    model_used: Optional[str] = None
    tokens_used: Optional[int] = None
    
    # Routing info
    route_decision: RouteDecision
    used_fallback: bool = False
    
    # Quality metrics
    quality_score: Optional[float] = None
    coherence_score: Optional[float] = None
    relevance_score: Optional[float] = None
    
    # Errors/warnings
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

@dataclass
class WorkspaceData:
    """Workspace context data"""
    files: List[FileInfo]
    language: str
    frameworks: List[str]
    imports: List[str]
    code_snippets: List[CodeSnippet]
    
@dataclass
class FileInfo:
    """File information"""
    path: str
    language: str
    size_bytes: int
    last_modified: datetime
    relevant_sections: List[str]

@dataclass
class CodeSnippet:
    """Code snippet with metadata"""
    content: str
    file_path: str
    start_line: int
    end_line: int
    language: str
    relevance_score: float
```

### 2.2 Error Models

```python
class MCPSamplingError(Exception):
    """Base exception for MCP sampling errors"""
    def __init__(
        self,
        message: str,
        error_code: str,
        request_id: Optional[str] = None,
        recoverable: bool = True
    ):
        super().__init__(message)
        self.error_code = error_code
        self.request_id = request_id
        self.recoverable = recoverable

class ErrorCode(Enum):
    """Standard error codes"""
    CONTEXT_MISSING = "E001"  # No FastMCP context
    TIMEOUT = "E002"  # Request timeout
    RATE_LIMIT = "E003"  # Rate limit exceeded
    INVALID_CONFIG = "E004"  # Invalid configuration
    CIRCUIT_OPEN = "E005"  # Circuit breaker open
    PROMPT_TOO_LONG = "E006"  # Prompt exceeds limits
    SECURITY_VIOLATION = "E007"  # Security check failed
    MODEL_UNAVAILABLE = "E008"  # Requested model unavailable
    WORKSPACE_ACCESS = "E009"  # Workspace access denied
    UNKNOWN = "E999"  # Unknown error

class ErrorHandler:
    """Centralized error handling"""
    
    @staticmethod
    def handle(
        error: Exception,
        context: MCPRequestContext
    ) -> ErrorResponse:
        """Handle and categorize errors"""
        if isinstance(error, MCPSamplingError):
            return ErrorResponse(
                error_code=error.error_code,
                message=str(error),
                request_id=error.request_id or context.request_id,
                recoverable=error.recoverable,
                suggested_action=ErrorHandler._suggest_action(error.error_code)
            )
        
        # Map common exceptions
        if isinstance(error, asyncio.TimeoutError):
            return ErrorResponse(
                error_code=ErrorCode.TIMEOUT.value,
                message="Request timed out",
                request_id=context.request_id,
                recoverable=True,
                suggested_action="Retry with shorter prompt or increase timeout"
            )
        
        # Default unknown error
        return ErrorResponse(
            error_code=ErrorCode.UNKNOWN.value,
            message=str(error),
            request_id=context.request_id,
            recoverable=False,
            suggested_action="Check logs for details"
        )
```

## 3. Integration Points

### 3.1 FastMCP Tool Integration

```python
from fastmcp import Context

@server.tool()
async def vibe_check_mentor(
    ctx: Context,  # FastMCP context parameter
    query: str,
    context: Optional[str] = None,
    session_id: Optional[str] = None,
    reasoning_depth: str = "standard",
    continue_session: bool = False,
    mode: str = "standard",
    phase: str = "planning",
    confidence_threshold: float = 0.7,
    file_paths: Optional[List[str]] = None,
    working_directory: Optional[str] = None
) -> Dict[str, Any]:
    """
    Enhanced vibe_check_mentor with MCP sampling integration
    """
    # Create request context
    request_ctx = MCPRequestContext(
        mcp_context=ctx,  # Pass the FastMCP context
        user_query=query,
        session_id=session_id,
        mode=mode,
        phase=phase
    )
    
    # Validate context
    if not request_ctx.validate():
        return {
            "error": "Invalid MCP context",
            "fallback": _generate_static_response(query)
        }
    
    # Create sampling adapter
    sampling_adapter = MCPSamplingAdapter(request_ctx)
    
    # Route the request
    router = get_hybrid_router()
    routing_result = await router.route(
        RoutingContext(
            query=query,
            intent=detect_intent(query),
            confidence_scores=calculate_confidence_scores(query),
            has_workspace_context=bool(file_paths),
            technologies_count=count_technologies(query),
            complexity_score=calculate_complexity(query)
        ),
        request_ctx
    )
    
    # Generate response based on routing
    if routing_result.decision == RouteDecision.DYNAMIC:
        response = await sampling_adapter.generate_dynamic_response(
            SamplingRequest(
                query=query,
                intent=routing_result.intent,
                context=extract_context(query, context),
                session_id=session_id,
                workspace_data=load_workspace_data(file_paths, working_directory)
            )
        )
    elif routing_result.decision == RouteDecision.HYBRID:
        # Combine static and dynamic
        static_response = _generate_static_response(query)
        dynamic_enhancement = await sampling_adapter.enhance_response(
            static_response,
            query,
            context
        )
        response = merge_responses(static_response, dynamic_enhancement)
    else:
        # Pure static
        response = _generate_static_response(query)
    
    return response
```

### 3.2 Sampling Adapter

```python
class MCPSamplingAdapter:
    """
    Adapter for MCP sampling with context management
    """
    
    def __init__(self, request_ctx: MCPRequestContext):
        self.request_ctx = request_ctx
        self.circuit_breaker = CircuitBreaker()
        self.prompt_builder = EnhancedPromptBuilder()
        self.response_validator = ResponseValidator()
        
    async def generate_dynamic_response(
        self,
        request: SamplingRequest
    ) -> SamplingResponse:
        """
        Generate dynamic response using MCP sampling
        """
        start_time = time.time()
        
        try:
            # Check circuit breaker
            if not self.circuit_breaker.can_proceed():
                raise MCPSamplingError(
                    "Circuit breaker is open",
                    ErrorCode.CIRCUIT_OPEN.value,
                    self.request_ctx.request_id
                )
            
            # Build prompt
            prompt = self.prompt_builder.build(
                request,
                self.request_ctx
            )
            
            # Validate prompt
            validation = self._validate_prompt(prompt)
            if not validation.is_valid:
                raise MCPSamplingError(
                    f"Prompt validation failed: {validation.errors}",
                    ErrorCode.INVALID_CONFIG.value,
                    self.request_ctx.request_id
                )
            
            # Make sampling request
            response_text = await self._sample_with_timeout(
                prompt,
                request.config_override
            )
            
            # Validate response
            validated_response = self.response_validator.validate(
                response_text,
                request
            )
            
            # Record success
            self.circuit_breaker.record_success()
            
            return SamplingResponse(
                content=validated_response,
                confidence=self._calculate_confidence(validated_response),
                request_id=self.request_ctx.request_id,
                response_time_ms=int((time.time() - start_time) * 1000),
                route_decision=RouteDecision.DYNAMIC
            )
            
        except Exception as e:
            # Record failure
            self.circuit_breaker.record_failure()
            
            # Handle error
            error_response = ErrorHandler.handle(e, self.request_ctx)
            
            # Return with fallback if available
            if error_response.recoverable:
                return SamplingResponse(
                    content=self._get_fallback_response(request),
                    confidence=0.3,
                    request_id=self.request_ctx.request_id,
                    response_time_ms=int((time.time() - start_time) * 1000),
                    route_decision=RouteDecision.STATIC,
                    used_fallback=True,
                    errors=[error_response.message]
                )
            
            raise
    
    async def _sample_with_timeout(
        self,
        prompt: str,
        config: Optional[EnhancedSamplingConfig]
    ) -> str:
        """Sample with timeout handling"""
        config = config or EnhancedSamplingConfig()
        
        try:
            # Create sampling task
            sample_task = self.request_ctx.mcp_context.sample(
                messages=[{"role": "user", "content": prompt}],
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                model_preferences={"hints": [config.model_preference.value]}
            )
            
            # Wait with timeout
            response = await asyncio.wait_for(
                sample_task,
                timeout=self.request_ctx.timeout_seconds
            )
            
            # Extract text from response
            if hasattr(response, 'text'):
                return response.text
            elif isinstance(response, dict) and 'text' in response:
                return response['text']
            else:
                return str(response)
                
        except asyncio.TimeoutError:
            raise MCPSamplingError(
                f"Sampling timeout after {self.request_ctx.timeout_seconds}s",
                ErrorCode.TIMEOUT.value,
                self.request_ctx.request_id
            )
```

## 4. Configuration API

```python
@dataclass
class MCPIntegrationConfig:
    """
    Global configuration for MCP sampling integration
    """
    # Routing configuration
    routing: RouterConfig = field(default_factory=RouterConfig)
    
    # Sampling configuration
    sampling: EnhancedSamplingConfig = field(default_factory=EnhancedSamplingConfig)
    
    # Circuit breaker configuration
    circuit_breaker: CircuitBreakerConfig = field(default_factory=CircuitBreakerConfig)
    
    # Performance configuration
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    
    # Security configuration
    security: SecurityConfig = field(default_factory=SecurityConfig)
    
    @classmethod
    def from_env(cls) -> 'MCPIntegrationConfig':
        """Load configuration from environment variables"""
        return cls(
            routing=RouterConfig(
                confidence_threshold=float(os.getenv('MCP_ROUTING_THRESHOLD', '0.7')),
                prefer_speed=os.getenv('MCP_PREFER_SPEED', 'false').lower() == 'true',
                enable_caching=os.getenv('MCP_ENABLE_CACHE', 'true').lower() == 'true'
            ),
            sampling=EnhancedSamplingConfig(
                temperature=float(os.getenv('MCP_TEMPERATURE', '0.7')),
                max_tokens=int(os.getenv('MCP_MAX_TOKENS', '2000')),
                model_preference=ModelPreference[os.getenv('MCP_MODEL_PREF', 'BALANCED')]
            ),
            circuit_breaker=CircuitBreakerConfig(
                failure_threshold=int(os.getenv('MCP_CB_FAILURE_THRESHOLD', '5')),
                recovery_timeout=int(os.getenv('MCP_CB_RECOVERY_TIMEOUT', '60')),
                success_threshold=int(os.getenv('MCP_CB_SUCCESS_THRESHOLD', '2'))
            ),
            performance=PerformanceConfig(
                request_timeout=int(os.getenv('MCP_REQUEST_TIMEOUT', '30')),
                max_retries=int(os.getenv('MCP_MAX_RETRIES', '3')),
                retry_delay_ms=int(os.getenv('MCP_RETRY_DELAY_MS', '1000'))
            ),
            security=SecurityConfig(
                enable_sanitization=os.getenv('MCP_ENABLE_SANITIZATION', 'true').lower() == 'true',
                enable_secrets_scanning=os.getenv('MCP_ENABLE_SECRETS_SCAN', 'true').lower() == 'true',
                max_prompt_length=int(os.getenv('MCP_MAX_PROMPT_LENGTH', '10000'))
            )
        )

@dataclass
class RouterConfig:
    """Router configuration"""
    confidence_threshold: float = 0.7
    prefer_speed: bool = False
    enable_caching: bool = True
    cache_ttl_seconds: int = 300
    
@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5
    recovery_timeout: int = 60
    success_threshold: int = 2
    
@dataclass
class PerformanceConfig:
    """Performance configuration"""
    request_timeout: int = 30
    max_retries: int = 3
    retry_delay_ms: int = 1000
    max_concurrent_requests: int = 10
    
@dataclass
class SecurityConfig:
    """Security configuration"""
    enable_sanitization: bool = True
    enable_secrets_scanning: bool = True
    max_prompt_length: int = 10000
    allowed_file_extensions: List[str] = field(
        default_factory=lambda: ['.py', '.js', '.ts', '.go', '.rs', '.java']
    )
```

## 5. Versioning Strategy

### 5.1 API Versioning

```python
from enum import Enum

class APIVersion(Enum):
    """API version enumeration"""
    V1 = "1.0.0"  # Initial release
    V2 = "2.0.0"  # Breaking changes
    
    @property
    def is_deprecated(self) -> bool:
        """Check if version is deprecated"""
        return self == APIVersion.V1

class VersionedAPI:
    """
    Version-aware API wrapper
    """
    
    def __init__(self, version: APIVersion = APIVersion.V2):
        self.version = version
        self._compatibility_mode = False
        
    def enable_compatibility_mode(self):
        """Enable backward compatibility mode"""
        self._compatibility_mode = True
        
    async def handle_request(
        self,
        request: Dict[str, Any],
        ctx: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Handle request with version awareness
        """
        # Detect API version from request
        requested_version = request.get('api_version', APIVersion.V2.value)
        
        if requested_version == APIVersion.V1.value:
            # Transform V1 request to V2
            request = self._transform_v1_to_v2(request)
            
        # Process with V2 handler
        response = await self._process_v2(request, ctx)
        
        if requested_version == APIVersion.V1.value:
            # Transform V2 response to V1
            response = self._transform_v2_to_v1(response)
            
        return response
    
    def _transform_v1_to_v2(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Transform V1 request format to V2"""
        # Map old field names to new
        transformations = {
            'prompt': 'query',
            'max_length': 'max_tokens',
            'use_dynamic': 'mode'
        }
        
        transformed = {}
        for old_key, new_key in transformations.items():
            if old_key in request:
                transformed[new_key] = request[old_key]
            elif new_key not in request:
                transformed[new_key] = request.get(new_key)
                
        return transformed
```

### 5.2 Migration Path

```python
class MigrationGuide:
    """
    Migration guide for API versions
    """
    
    BREAKING_CHANGES = {
        "V1_to_V2": [
            "ctx parameter is now required for all sampling operations",
            "prompt field renamed to query",
            "max_length renamed to max_tokens",
            "Response format includes metadata fields",
            "Error codes standardized to ErrorCode enum"
        ]
    }
    
    MIGRATION_STEPS = {
        "V1_to_V2": [
            "1. Update tool decorators to include ctx parameter",
            "2. Replace prompt with query in request objects",
            "3. Update max_length to max_tokens",
            "4. Handle new response metadata fields",
            "5. Update error handling to use ErrorCode enum"
        ]
    }
    
    @classmethod
    def get_migration_guide(
        cls,
        from_version: str,
        to_version: str
    ) -> Dict[str, Any]:
        """Get migration guide between versions"""
        key = f"{from_version}_to_{to_version}"
        
        return {
            "breaking_changes": cls.BREAKING_CHANGES.get(key, []),
            "migration_steps": cls.MIGRATION_STEPS.get(key, []),
            "estimated_effort": cls._estimate_effort(key),
            "tools_available": cls._get_migration_tools(key)
        }
```

## 6. Example Usage Patterns

### 6.1 Basic Usage

```python
# In FastMCP tool function
@server.tool()
async def my_tool(ctx: Context, query: str) -> Dict[str, Any]:
    # Create request context
    request_ctx = MCPRequestContext(
        mcp_context=ctx,
        user_query=query
    )
    
    # Create adapter
    adapter = MCPSamplingAdapter(request_ctx)
    
    # Generate response
    response = await adapter.generate_dynamic_response(
        SamplingRequest(
            query=query,
            intent="general_advice",
            context={}
        )
    )
    
    return {"response": response.content}
```

### 6.2 Advanced Usage with Custom Configuration

```python
@server.tool()
async def advanced_tool(
    ctx: Context,
    query: str,
    quality: str = "balanced"
) -> Dict[str, Any]:
    # Map quality to model preference
    model_pref = {
        "fast": ModelPreference.FAST,
        "balanced": ModelPreference.BALANCED,
        "high": ModelPreference.HIGH_QUALITY
    }.get(quality, ModelPreference.BALANCED)
    
    # Custom configuration
    config = EnhancedSamplingConfig(
        temperature=0.8,
        max_tokens=3000,
        model_preference=model_pref,
        strategy=SamplingStrategy.CONSENSUS if quality == "high" else SamplingStrategy.SINGLE_SHOT,
        consensus_samples=3
    )
    
    # Create context with custom config
    request_ctx = MCPRequestContext(
        mcp_context=ctx,
        user_query=query,
        timeout_seconds=60 if quality == "high" else 30
    )
    
    # Generate with custom config
    adapter = MCPSamplingAdapter(request_ctx)
    response = await adapter.generate_dynamic_response(
        SamplingRequest(
            query=query,
            intent=detect_intent(query),
            context=extract_context(query),
            config_override=config
        )
    )
    
    return {
        "response": response.content,
        "confidence": response.confidence,
        "model_used": response.model_used,
        "tokens_used": response.tokens_used
    }
```

### 6.3 Error Handling Pattern

```python
@server.tool()
async def robust_tool(ctx: Context, query: str) -> Dict[str, Any]:
    request_ctx = MCPRequestContext(mcp_context=ctx, user_query=query)
    adapter = MCPSamplingAdapter(request_ctx)
    
    try:
        response = await adapter.generate_dynamic_response(
            SamplingRequest(query=query, intent="help", context={})
        )
        return {"success": True, "response": response.content}
        
    except MCPSamplingError as e:
        if e.recoverable:
            # Try fallback
            fallback = get_static_response(query)
            return {
                "success": False,
                "response": fallback,
                "error": str(e),
                "using_fallback": True
            }
        else:
            # Non-recoverable error
            return {
                "success": False,
                "error": str(e),
                "error_code": e.error_code,
                "request_id": e.request_id
            }
            
    except Exception as e:
        # Unexpected error
        logger.error(f"Unexpected error: {e}")
        return {
            "success": False,
            "error": "Internal error",
            "request_id": request_ctx.request_id
        }
```

## 7. Performance Considerations

### 7.1 Latency Targets

- **Interrupt mode**: < 500ms (using cached static responses)
- **Standard mode**: < 3s (dynamic generation with balanced model)
- **Comprehensive mode**: < 10s (multiple samples with consensus)

### 7.2 Optimization Strategies

1. **Request Batching**: Combine multiple small requests
2. **Response Caching**: Cache frequent queries for 5 minutes
3. **Prompt Optimization**: Minimize prompt size while maintaining context
4. **Model Selection**: Auto-select model based on query complexity
5. **Circuit Breaking**: Fail fast when service is degraded

### 7.3 Monitoring Metrics

```python
@dataclass
class PerformanceMetrics:
    """Performance monitoring metrics"""
    
    # Latency metrics (in ms)
    p50_latency: float
    p95_latency: float
    p99_latency: float
    
    # Throughput metrics
    requests_per_second: float
    tokens_per_second: float
    
    # Error metrics
    error_rate: float
    timeout_rate: float
    fallback_rate: float
    
    # Circuit breaker metrics
    circuit_breaker_trips: int
    circuit_breaker_state: str
    
    # Cache metrics
    cache_hit_rate: float
    cache_size_mb: float
```

## 8. Security Considerations

### 8.1 Input Sanitization

- Remove prompt injection patterns
- Scan for secrets and PII
- Validate file paths against workspace
- Enforce maximum prompt length
- HTML escape special characters

### 8.2 Access Control

```python
class SecurityValidator:
    """Security validation for MCP sampling"""
    
    @staticmethod
    def validate_request(
        request: SamplingRequest,
        context: MCPRequestContext
    ) -> ValidationResult:
        """Validate request security"""
        
        # Check for injection attempts
        if SecurityValidator._has_injection_patterns(request.query):
            return ValidationResult(
                False,
                ["Potential injection detected"]
            )
        
        # Validate workspace access
        if request.workspace_data:
            if not SecurityValidator._validate_workspace_access(
                request.workspace_data,
                context.workspace_path
            ):
                return ValidationResult(
                    False,
                    ["Workspace access denied"]
                )
        
        # Scan for secrets
        if SecurityValidator._contains_secrets(request.query):
            return ValidationResult(
                False,
                ["Secrets detected in query"]
            )
        
        return ValidationResult(True)
```

## 9. Testing Strategy

### 9.1 Unit Tests

```python
class TestMCPSamplingIntegration:
    """Unit tests for MCP sampling integration"""
    
    @pytest.mark.asyncio
    async def test_context_validation(self):
        """Test context validation"""
        mock_ctx = MockMCPContext()
        request_ctx = MCPRequestContext(mcp_context=mock_ctx)
        assert request_ctx.validate()
    
    @pytest.mark.asyncio
    async def test_routing_decision(self):
        """Test routing decisions"""
        router = EnhancedHybridRouter([ConfidenceStrategy()], RouterConfig())
        context = RoutingContext(
            query="Should I use React?",
            intent="architecture_decision",
            confidence_scores={"react": 0.9},
            has_workspace_context=False,
            technologies_count=1,
            complexity_score=0.3
        )
        result = await router.route(context, MockMCPContext())
        assert result.decision == RouteDecision.STATIC
    
    @pytest.mark.asyncio
    async def test_error_recovery(self):
        """Test error recovery with fallback"""
        ctx = MockMCPContext(should_fail=True)
        adapter = MCPSamplingAdapter(MCPRequestContext(mcp_context=ctx))
        
        response = await adapter.generate_dynamic_response(
            SamplingRequest(
                query="Test query",
                intent="help",
                context={}
            )
        )
        
        assert response.used_fallback
        assert len(response.errors) > 0
```

### 9.2 Integration Tests

```python
@pytest.mark.integration
class TestEndToEnd:
    """End-to-end integration tests"""
    
    @pytest.mark.asyncio
    async def test_full_flow(self, mcp_server):
        """Test complete request flow"""
        response = await mcp_server.call_tool(
            "vibe_check_mentor",
            query="How should I structure my React app?",
            mode="standard"
        )
        
        assert response["success"]
        assert "response" in response
        assert len(response["response"]) > 100
```

## 10. Deployment Checklist

- [ ] Environment variables configured
- [ ] Circuit breaker thresholds set
- [ ] Rate limiting configured
- [ ] Monitoring dashboards created
- [ ] Error alerting configured
- [ ] Performance baselines established
- [ ] Security scanning enabled
- [ ] Backup static responses available
- [ ] Documentation updated
- [ ] Migration guide published