"""
Enhanced Vibe Check Mentor - Context-Aware Collaborative Reasoning

Provides specific, technical advice based on query analysis instead of generic responses.
Extracts technologies, frameworks, and specific problems to give targeted guidance.
"""

import re
import functools
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass

# Import existing structures
from ..mentor.models.persona import PersonaData
from ..mentor.models.session import ContributionData, CollaborativeReasoningSession
from ..mentor.models.config import ConfidenceScores
from ..mentor.patterns.handlers.base import PatternHandler

# Import strategy pattern components
from ..strategies.response_strategies import get_strategy_manager, TechnicalContext
from .semantic_engine import SemanticEngine, QueryIntent

# Constants for improved maintainability
MIN_FEATURE_LENGTH = 3
MAX_QUERY_LENGTH = 10000  # Prevent ReDoS attacks
MAX_FEATURES = 5  # Maximum features to extract
MAX_DECISION_POINTS = 3  # Maximum decision points to track
EXCLUDED_ENDINGS = [' for', ' with', ' by', ' in', ' on']
REGEX_TIMEOUT = 1.0  # seconds
DEFAULT_CONFIDENCE_THRESHOLD = 0.7  # Default confidence for decisions
MIN_CONTRIB_WORD_LENGTH = 4  # Minimum word length for contribution detection
CACHE_COST_REDUCTION_MIN = 50  # Minimum cache cost reduction percentage
CACHE_COST_REDUCTION_MAX = 90  # Maximum cache cost reduction percentage

# Configuration for performance tuning
@dataclass
class MentorConfig:
    enable_caching: bool = True
    max_cache_size: int = 128
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD
    max_response_length: int = 2000


# TechnicalContext is imported from response_strategies to avoid duplication


class ContextExtractor:
    """Extract technical context from queries for specific advice"""
    
    # Compiled regex patterns for performance (lazy loading)
    _compiled_patterns: Optional[Dict[str, re.Pattern]] = None
    _all_terms_regex: Optional[re.Pattern] = None
    
    # Common technology/framework patterns (2025 enhanced with latest frameworks)
    TECH_PATTERNS = {
        'databases': ['postgres', 'postgresql', 'mysql', 'mongodb', 'redis', 'dynamodb', 'supabase', 'firebase', 'planetscale', 'cockroachdb', 'turso', 'neon'],
        'frameworks': ['react', 'vue', 'angular', 'nextjs', 'next.js', 'django', 'fastapi', 'express', 'rails', 'svelte', 'solid', 'solid.js', 'astro', 'remix', 'qwik', 'fresh', 'nuxt'],
        'backend_frameworks': ['fastapi', 'django', 'express', 'nestjs', 'flask', 'rails', 'spring boot', 'asp.net', 'gin', 'fiber', 'echo', 'koa', 'hapi', 'laravel'],
        'languages': ['python', 'javascript', 'typescript', 'java', 'go', 'rust', 'c++', 'c#', 'php', 'ruby', 'kotlin', 'swift', 'dart', 'zig'],
        'runtimes': ['node.js', 'deno', 'bun', 'cloudflare workers', 'edge runtime'],
        'cloud': ['aws', 'gcp', 'azure', 'vercel', 'netlify', 'cloudflare', 'railway', 'render', 'fly.io', 'supabase', 'planetscale'],
        'containers': ['docker', 'kubernetes', 'k8s', 'compose', 'swarm', 'podman', 'containerd'],
        'auth': ['oauth', 'oauth2', 'jwt', 'auth0', 'cognito', 'firebase auth', 'clerk', 'nextauth', 'supabase auth', 'lucia'],
        'payments': ['stripe', 'paypal', 'square', 'braintree', 'razorpay', 'lemon squeezy', 'paddle'],
        'api': ['rest', 'graphql', 'grpc', 'websocket', 'webhook', 'trpc', 'prisma', 'apollo', 'relay', 'urql'],
        'ai': ['openai', 'claude', 'gpt', 'llm', 'embedding', 'vector', 'rag', 'pinecone', 'weaviate', 'qdrant', 'langchain', 'llamaindex', 'vercel ai', 'huggingface'],
        'vector_dbs': ['pinecone', 'weaviate', 'qdrant', 'chroma', 'milvus', 'pgvector', 'zilliz', 'faiss'],
        'graph_dbs': ['neo4j', 'falkordb', 'neptune', 'arangodb', 'tigergraph', 'orientdb', 'nebula', 'dgraph'],
        'ai_frameworks': ['langchain', 'llamaindex', 'crewai', 'autogen', 'semantic kernel', 'langgraph', 'openai swarm', 'haystack', 'dspy', 'guidance'],
        'llm_models': ['gpt-4', 'gpt-4o', 'claude-3.5', 'claude', 'gemini', 'llama', 'mistral', 'anthropic', 'openai', 'deepseek', 'qwen'],
        'local_llm': ['ollama', 'llama.cpp', 'vllm', 'text-generation-webui', 'localai', 'jan'],
        'testing': ['jest', 'pytest', 'cypress', 'playwright', 'vitest', 'testing library', 'storybook', 'chromatic'],
        'bundlers': ['vite', 'webpack', 'parcel', 'rollup', 'esbuild', 'swc', 'turbo', 'rspack'],
        'ci_cd': ['github actions', 'jenkins', 'gitlab ci', 'circleci', 'travis', 'buildkite', 'drone'],
        'monitoring': ['datadog', 'sentry', 'prometheus', 'grafana', 'new relic', 'posthog', 'axiom', 'betterstack'],
        'messaging': ['rabbitmq', 'kafka', 'redis', 'sqs', 'pubsub', 'pusher', 'ably', 'socket.io'],
        'state_mgmt': ['redux', 'zustand', 'context', 'recoil', 'jotai', 'valtio', 'signal', 'pinia', 'xstate'],
        'styling': ['tailwind', 'styled-components', 'emotion', 'css modules', 'sass', 'scss', 'stitches', 'panda css', 'vanilla-extract', 'unocss'],
        'meta_frameworks': ['nextjs', 'nuxt', 'sveltekit', 'solidstart', 'remix', 'astro', 'qwik city', 'fresh'],
        'edge_computing': ['cloudflare workers', 'vercel edge', 'deno deploy', 'fastly compute', 'aws lambda@edge']
    }
    
    PROBLEM_INDICATORS = {
        'integration': ['integrate', 'connect', 'api', 'sdk', 'client', 'wrapper'],
        'architecture': ['design', 'structure', 'pattern', 'architect', 'system', 'scale'],
        'implementation': ['implement', 'build', 'create', 'develop', 'code', 'write'],
        'debugging': ['debug', 'fix', 'error', 'issue', 'problem', 'troubleshoot'],
        'decision': ['should i', 'vs', 'or', 'choose', 'decide', 'which', 'better']
    }
    
    @classmethod
    def _validate_input(cls, text: str) -> str:
        """Validate and sanitize input to prevent ReDoS attacks"""
        if not text or not isinstance(text, str):
            return ""
        
        # Prevent ReDoS attacks with length limits
        if len(text) > MAX_QUERY_LENGTH:
            text = text[:MAX_QUERY_LENGTH]
        
        # Enhanced sanitization to prevent ReDoS attacks
        # Only allow safe characters and limit consecutive special chars
        text = re.sub(r'[^\w\s\-\.\?\!,;:\'"()]', ' ', text)
        # Prevent repeated special characters that could cause regex issues
        text = re.sub(r'([^\w\s])\1{2,}', r'\1\1', text)
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.lower().strip()
    
    @classmethod
    def _build_compiled_patterns(cls) -> Dict[str, re.Pattern]:
        """Build compiled regex patterns for performance - O(1) lookup instead of O(n*m)"""
        if cls._compiled_patterns is not None:
            return cls._compiled_patterns
        
        compiled_patterns = {}
        
        # Build category-specific patterns
        for category, terms in cls.TECH_PATTERNS.items():
            # Escape special regex characters and create word boundaries
            escaped_terms = [re.escape(term) for term in terms]
            pattern = r'\b(' + '|'.join(escaped_terms) + r')\b'
            compiled_patterns[category] = re.compile(pattern, re.IGNORECASE)
        
        # Build problem indicator patterns
        for problem_type, indicators in cls.PROBLEM_INDICATORS.items():
            escaped_indicators = [re.escape(indicator) for indicator in indicators]
            pattern = r'\b(' + '|'.join(escaped_indicators) + r')\b'
            compiled_patterns[f'problem_{problem_type}'] = re.compile(pattern, re.IGNORECASE)
        
        cls._compiled_patterns = compiled_patterns
        return compiled_patterns
    
    @classmethod
    @functools.lru_cache(maxsize=128)  # Cache for performance
    def extract_context(cls, query: str, context: Optional[str] = None) -> TechnicalContext:
        """Extract technical context from query and optional context - OPTIMIZED"""
        # Input validation and sanitization
        query = cls._validate_input(query or "")
        context = cls._validate_input(context or "")
        
        if not query:  # Return empty context for invalid input
            return TechnicalContext([], [], [], 'general', [], [])
        
        combined_text = f"{query} {context}".strip()
        
        # Get compiled patterns for O(1) lookup performance
        patterns = cls._build_compiled_patterns()
        
        # Extract technologies and frameworks using compiled regex
        technologies = []
        frameworks = []
        
        for category, pattern in patterns.items():
            if category.startswith('problem_'):  # Skip problem patterns in this loop
                continue
                
            matches = pattern.findall(combined_text)
            if matches:
                if category in ['frameworks', 'languages']:
                    frameworks.extend(matches)
                else:
                    technologies.extend(matches)
        
        # Remove duplicates while preserving order
        technologies = list(dict.fromkeys(technologies))
        frameworks = list(dict.fromkeys(frameworks))
        
        # ENHANCEMENT: Semantic pattern detection (from Claude's suggestion)
        # Add budget model keywords to technologies if budget terms detected
        budget_terms = ['mini', 'nano', 'cheap', 'budget', 'cost-effective', 'affordable']
        if any(term in combined_text for term in budget_terms):
            if 'gpt' in combined_text or 'openai' in combined_text:
                technologies.extend(['gpt-4.1-nano', 'gpt-4o-mini'])
            if 'claude' in combined_text:
                technologies.append('claude-3.5-haiku')
            if 'deepseek' in combined_text:
                technologies.append('deepseek-r1')
        
        # Determine problem type using compiled patterns
        problem_type = 'general'
        for problem_key, pattern in patterns.items():
            if problem_key.startswith('problem_'):
                ptype = problem_key.replace('problem_', '')
                if pattern.search(combined_text):
                    problem_type = ptype
                    break
        
        # Pre-compile feature patterns for performance (compile once, use many times)
        if not hasattr(cls, '_feature_patterns_compiled'):
            cls._feature_patterns_compiled = [
                re.compile(r'(?:implement|build|create|add)\s+(\w+(?:\s+\w+)?)', re.IGNORECASE),
                re.compile(r'(\w+(?:\s+\w+)?)\s+(?:feature|functionality|capability)', re.IGNORECASE),
                re.compile(r'custom\s+(\w+(?:\s+\w+)?)', re.IGNORECASE),
                re.compile(r'(?:implementing|building|creating)\s+(\w+(?:\s+\w+)?)', re.IGNORECASE)
            ]
        
        # Extract specific features mentioned using constants
        features = []
        for pattern in cls._feature_patterns_compiled:
            try:
                matches = pattern.findall(combined_text)
                # Filter using constants instead of magic numbers
                filtered_matches = [
                    m for m in matches 
                    if len(m) > MIN_FEATURE_LENGTH and 
                    not any(m.endswith(ending) for ending in EXCLUDED_ENDINGS)
                ]
                features.extend(filtered_matches)
            except re.error:
                # Handle regex errors gracefully
                continue
        
        # Pre-compile decision patterns for performance
        if not hasattr(cls, '_decision_patterns_compiled'):
            cls._decision_patterns_compiled = [
                re.compile(r'(\w+)\s+vs\s+(\w+)', re.IGNORECASE),
                re.compile(r'should\s+i\s+(\w+(?:\s+\w+)?)', re.IGNORECASE),
                re.compile(r'(?:use|choose|pick)\s+(\w+(?:\s+\w+)?)', re.IGNORECASE)
            ]
        
        # Extract decision points with error handling
        decisions = []
        for pattern in cls._decision_patterns_compiled:
            try:
                matches = pattern.findall(combined_text)
                if matches and isinstance(matches[0], tuple):
                    decisions.extend([f"{m[0]} vs {m[1]}" for m in matches])
                else:
                    decisions.extend(matches)
            except (re.error, IndexError):
                # Handle regex errors and empty matches gracefully
                continue
        
        # Extract architectural patterns mentioned (using compiled pattern for consistency)
        pattern_keywords = ['microservice', 'monolith', 'serverless', 'event-driven', 
                          'mvc', 'mvvm', 'repository', 'factory', 'singleton']
        architectural_patterns = []
        for keyword in pattern_keywords:
            if keyword in combined_text:
                architectural_patterns.append(keyword)
        
        return TechnicalContext(
            technologies=list(dict.fromkeys(technologies)),  # Preserve order, remove duplicates
            frameworks=list(dict.fromkeys(frameworks)),
            patterns=architectural_patterns,
            problem_type=problem_type,
            specific_features=list(dict.fromkeys(features))[:MAX_FEATURES],
            decision_points=list(dict.fromkeys(decisions))[:MAX_DECISION_POINTS]
        )


class EnhancedPersonaReasoning:
    """Generate context-aware responses for each persona"""
    
    def __init__(self):
        """Initialize with semantic engine for better response generation"""
        self.semantic_engine = SemanticEngine()
    
    def generate_senior_engineer_response(
        self,
        tech_context: TechnicalContext,
        patterns: List[Dict[str, Any]],
        query: str
    ) -> Tuple[str, str, float]:
        """Generate specific senior engineer advice using semantic understanding"""
        
        # Use strategy manager for all response generation
        strategy_manager = get_strategy_manager()
        
        try:
            response_type, content, confidence = strategy_manager.generate_response(
                tech_context, patterns, query
            )
            return (response_type, content, confidence)
        except Exception as e:
            # Fallback to safe generic advice if strategy fails
            return (
                "concern",
                "This looks like premature infrastructure design. Start with working API calls first, "
                "then extract patterns only when you have 3+ similar use cases. Most 'future flexibility' "
                "never gets used but adds maintenance burden forever.",
                ConfidenceScores.MEDIUM
            )
    
    @staticmethod
    def generate_product_engineer_response(
        tech_context: TechnicalContext,
        patterns: List[Dict[str, Any]],
        query: str
    ) -> Tuple[str, str, float]:
        """Generate specific product engineer advice based on context"""
        
        # ENHANCEMENT: Give specific advice based on technology, even without patterns
        
        # Use semantic engine for intelligent response generation
        try:
            # Process query with semantic understanding
            context_str = self._build_context_string(tech_context, patterns)
            semantic_result = self.semantic_engine.process_query(query, context_str)
            
            # Get the semantically appropriate response
            if semantic_result['success'] and semantic_result['response']:
                # Determine contribution type based on intent
                intent_type = semantic_result['intent']['type']
                contribution_type = self._map_intent_to_contribution_type(intent_type)
                
                return (
                    contribution_type,
                    semantic_result['response'],
                    semantic_result['response_confidence']
                )
        except Exception as e:
            # Fall back to strategy manager on error
            pass
        
        # Technology + Framework combinations (fallback)
        if tech_context.technologies and tech_context.frameworks:
            tech = tech_context.technologies[0]
            framework = tech_context.frameworks[0]
            # Use semantic engine even for fallback
            fallback_query = f"ship {tech} with {framework} quickly"
            semantic_result = self.semantic_engine.process_query(fallback_query, None)
            if semantic_result['success']:
                return (
                    "suggestion",
                    semantic_result['response'],
                    semantic_result['response_confidence']
                )
            # Ultimate fallback
            return (
                "suggestion",
                f"For {tech} + {framework}: Start with the official quickstart, "
                f"deploy a working prototype today, and get user feedback immediately. "
                f"Real usage beats perfect architecture.",
                ConfidenceScores.MEDIUM
            )
        
        # Technology-specific MVP advice (even without frameworks)
        if tech_context.technologies:
            tech = tech_context.technologies[0]
            
            if tech in ['stripe', 'paypal']:
                return (
                    "suggestion",
                    f"For {tech} MVP: Start with their hosted checkout page - literally 5 lines of code. "
                    f"Skip building payment forms initially. I shipped a $50K MRR SaaS using just Stripe's "
                    f"hosted pages for 8 months. Users don't care if it's 'custom' - they care if it works. "
                    f"Once you have paying customers, then invest in custom UI.",
                    ConfidenceScores.HIGH
                )
            
            elif tech in ['openai', 'claude', 'gpt']:
                return (
                    "observation",
                    f"For {tech} products: Ship a simple chat interface this week. "
                    f"Use Streamlit or Gradio for rapid prototyping - I've built 20+ AI demos this way. "
                    f"Focus on the prompt engineering and user flow, not the tech stack. "
                    f"Once users love the experience, then optimize for performance.",
                    ConfidenceScores.HIGH
                )
            
            elif tech in ['react', 'vue', 'angular']:
                return (
                    "challenge",
                    f"Before building a custom {tech} app, ask: Can Webflow/Framer/Notion solve this? "
                    f"I've saved months by using no-code tools for MVPs. Once you validate the idea "
                    f"and have 100+ users asking for features the no-code tool can't handle, "
                    f"THEN build custom {tech}. Code is a liability, not an asset.",
                    ConfidenceScores.HIGH
                )
        
        # Feature-specific MVP advice
        if tech_context.specific_features:
            feature = tech_context.specific_features[0]
            return (
                "challenge",
                f"Is {feature} solving a real user pain or are we building it because it's cool? "
                f"Here's my framework: Can you name 3 specific users who asked for this? "
                f"If yes, build the simplest version and ship to just those 3. "
                f"If no, table it and talk to 10 more users. "
                f"I've killed more features than I've shipped, and that's a good thing.",
                ConfidenceScores.HIGH
            )
        
        # Integration from product perspective
        if tech_context.problem_type == "integration":
            return (
                "observation",
                f"From a product angle on this integration: What's the user-facing value? "
                f"I'd implement just enough to unblock user workflows - maybe hardcode responses initially. "
                f"Once users love the feature, then invest in robust integration. "
                f"I shipped a 'Slack integration' that was just webhooks for 6 months before building real sync.",
                ConfidenceScores.GOOD
            )
        
        # Decision with product lens
        if tech_context.decision_points:
            decision = tech_context.decision_points[0]
            return (
                "suggestion",
                f"For '{decision}' - ask: Which option gets us to user feedback fastest? "
                f"In my startup experience, technical 'best practices' killed more products than bad code. "
                f"Pick the option that: 1) Ships in days not weeks, "
                f"2) We can change based on user feedback, "
                f"3) Doesn't require a PhD to maintain. "
                f"Perfect is the enemy of shipped.",
                ConfidenceScores.HIGH
            )
        
        # Architecture from product view
        if tech_context.problem_type == "architecture":
            return (
                "challenge",
                "Are we solving user problems or playing with architecture? "
                "I've seen beautiful microservice architectures serve 10 users while monoliths scale to millions. "
                "Start simple: One repo, one database, one deploy button. "
                "When you have 10K active users, then let's talk architecture. "
                "Until then, every hour on architecture is an hour not talking to users.",
                ConfidenceScores.VERY_HIGH
            )
        
        # Default product-focused response
        return (
            "suggestion",
            "Whatever technical decision we make, let's optimize for iteration speed. "
            "Can we A/B test it? Can we roll back in 5 minutes? Can we ship improvements daily? "
            "These questions matter more than any architectural choice. "
            "Build for change, because user needs always surprise us.",
            ConfidenceScores.GOOD
        )
    
    @staticmethod
    def generate_ai_engineer_response(
        tech_context: TechnicalContext,
        patterns: List[Dict[str, Any]],
        query: str,
        previous_contributions: List[ContributionData]
    ) -> Tuple[str, str, float]:
        """Generate specific AI engineer advice based on context"""
        
        # RAG/Vector DB systems (corrected 2025 research)
        if any(term in query.lower() for term in ['rag', 'vector', 'embedding']) or any(t in tech_context.technologies for t in ['rag', 'vector', 'embedding', 'pinecone', 'weaviate', 'qdrant', 'chroma']):
            return (
                "insight",
                f"For RAG systems in 2025 (corrected benchmarks): "
                f"Vector DBs by use case: Milvus (highest QPS), Zilliz (managed Milvus, lowest latency), Qdrant (good balance), Pinecone (ease of use), Weaviate (feature-rich), Chroma (prototyping). "
                f"Real ranking: Milvus > Weaviate ≈ Qdrant > Pinecone > Chroma for performance. "
                f"Embeddings: OpenAI text-embedding-3-large (best quality, $0.00013/1K) vs sentence-transformers all-MiniLM-L6-v2 (free, 80% quality). "
                f"Chunking: Semantic > fixed-size. 512-1024 tokens, 20% overlap, respect document boundaries. "
                f"Architecture: LlamaIndex for RAG, hybrid search (vector+keyword), metadata filtering, pgvector for simple cases. "
                f"Monitor: retrieval precision@k matters more than generation quality.",
                ConfidenceScores.VERY_HIGH
            )
        
        # Graph Database systems
        if any(term in query.lower() for term in ['graph', 'knowledge graph', 'neo4j', 'relationships']) or any(t in tech_context.technologies for t in ['neo4j', 'falkordb', 'neptune', 'arangodb']):
            graph_dbs = [t for t in tech_context.technologies if t in ['neo4j', 'falkordb', 'neptune', 'arangodb', 'tigergraph']]
            return (
                "suggestion",
                f"For graph databases in 2025: "
                f"Performance: FalkorDB (sub-140ms p99) >> Neo4j (46.9s p99 in benchmarks), but Neo4j has massive ecosystem. "
                f"Managed: Amazon Neptune (AWS), ArangoDB Cloud (multi-model). "
                f"Use cases: Neo4j for mature ecosystems, FalkorDB for performance-critical AI/RAG, ArangoDB for multi-model needs. "
                f"For knowledge graphs in RAG: FalkorDB offers Redis compatibility + graph performance. "
                f"Architecture: Start with pgvector + basic relations, upgrade to dedicated graph DB when complexity increases. "
                f"Don't over-engineer - most 'graph' problems are just foreign keys with extra steps.",
                ConfidenceScores.HIGH
            )
        
        # General AI/LLM integration (not RAG)
        elif any(ai_term in tech_context.technologies for ai_term in ['openai', 'claude', 'gpt', 'llm']):
            ai_tech = next(t for t in tech_context.technologies if t in ['openai', 'claude', 'gpt', 'llm'])
            return (
                "insight",
                f"For {ai_tech} integration, leverage these AI-specific patterns: "
                f"1) Use their official SDK - it handles streaming, token counting, and retry logic, "
                f"2) Implement prompt caching to reduce costs by {CACHE_COST_REDUCTION_MIN}-{CACHE_COST_REDUCTION_MAX}%, "
                f"3) Use structured outputs (JSON mode) for reliable parsing, "
                f"4) Set up prompt version control from day 1, "
                f"5) Monitor token usage per user to prevent abuse. "
                f"I've built 10+ LLM integrations - the SDK saves weeks of edge case handling.",
                ConfidenceScores.VERY_HIGH
            )
        
        # Using AI tools for development
        if tech_context.problem_type == "implementation":
            tools_suggestion = f"For implementing {tech_context.specific_features[0] if tech_context.specific_features else 'this feature'}"
            return (
                "suggestion",
                f"{tools_suggestion}, use AI to accelerate: "
                f"1) GitHub Copilot for boilerplate - it knows common patterns, "
                f"2) Claude/GPT-4 for architecture reviews - paste your design and ask for issues, "
                f"3) AI-powered testing - generate test cases from requirements, "
                f"4) Cursor/Continue for refactoring - safer than manual changes. "
                f"I code 3x faster with AI assistance, but always review generated code for security.",
                ConfidenceScores.HIGH
            )
        
        # Synthesis response incorporating previous points
        if previous_contributions and len(previous_contributions) >= 2:
            return (
                "synthesis",
                f"Building on the excellent points about {tech_context.technologies[0] if tech_context.technologies else 'this technology'}: "
                f"Modern AI tools can validate our approach before we write code. "
                f"Try this: 1) Describe your design to Claude/GPT-4 and ask for issues, "
                f"2) Use MCP tools to check for anti-patterns in real-time, "
                f"3) Generate test cases with AI before implementation, "
                f"4) Use AI code review on every PR. "
                f"This catches 80% of issues before they reach production.",
                ConfidenceScores.GOOD
            )
        
        
        # AI Framework-specific recommendations
        if any(fw in tech_context.technologies for fw in ['langchain', 'llamaindex', 'crewai', 'autogen']):
            framework = next(fw for fw in tech_context.technologies if fw in ['langchain', 'llamaindex', 'crewai', 'autogen'])
            return (
                "insight",
                f"For {framework} in 2025: "
                f"LangChain: Use LangGraph for complex workflows, avoid deep nesting of chains. "
                f"LlamaIndex: Perfect for RAG - use their query engines, don't build retrieval from scratch. "
                f"CrewAI: Define clear agent roles and tasks, leverage their planning capabilities. "
                f"AutoGen: Set up proper conversation patterns, use code execution agents carefully. "
                f"All frameworks: Monitor token usage religiously and implement caching.",
                ConfidenceScores.VERY_HIGH
            )
        
        # Local vs Cloud LLM decision
        if any(local in tech_context.technologies for local in ['ollama', 'llama.cpp', 'local']) and \
           any(cloud in tech_context.technologies for cloud in ['openai', 'claude', 'gemini']):
            return (
                "suggestion",
                "For local vs cloud LLMs: Consider your requirements: "
                "Local (Ollama/Llama.cpp): Better for privacy, cost-effective at scale, no API limits. "
                "Cloud (OpenAI/Claude): Superior quality, multimodal capabilities, faster time-to-market. "
                "Hybrid approach works well: use cloud for prototyping, local for production if privacy/cost matters. "
                "In 2025, local models like Llama 3.2 are surprisingly capable for many tasks.",
                ConfidenceScores.HIGH
            )
        
        # AI-assisted debugging
        if tech_context.problem_type == "debugging":
            return (
                "suggestion",
                "For debugging with AI assistance: "
                "1) Paste error messages directly into Claude/GPT-4 with context, "
                "2) Use AI to explain complex stack traces in plain English, "
                "3) Generate hypotheses about root causes, "
                "4) Ask AI to write diagnostic code to test theories. "
                "I solve issues 50% faster by treating AI as a debugging partner.",
                ConfidenceScores.GOOD
            )
        
        # Default AI perspective
        return (
            "observation",
            "Consider how AI tools can accelerate this work: "
            "MCP tools for real-time pattern detection, "
            "Copilot for implementation speed, "
            "AI code review for quality gates. "
            "We're in an AI-augmented development era - use these tools as force multipliers.",
            ConfidenceScores.MODERATE
        )
    
    def _build_context_string(self, tech_context: TechnicalContext, patterns: List[Dict[str, Any]]) -> str:
        """Build context string for semantic analysis"""
        context_parts = []
        
        if tech_context.technologies:
            context_parts.append(f"technologies: {', '.join(tech_context.technologies)}")
        if tech_context.frameworks:
            context_parts.append(f"frameworks: {', '.join(tech_context.frameworks)}")
        if tech_context.problem_type:
            context_parts.append(f"problem type: {tech_context.problem_type}")
        if tech_context.specific_features:
            context_parts.append(f"features: {', '.join(tech_context.specific_features[:3])}")
        if patterns:
            pattern_names = [p.get('name', '') for p in patterns[:3] if p.get('name')]
            if pattern_names:
                context_parts.append(f"detected patterns: {', '.join(pattern_names)}")
        
        return ' | '.join(context_parts)
    
    def _map_intent_to_contribution_type(self, intent_type: str) -> str:
        """Map semantic intent to contribution type"""
        mapping = {
            "tool_evaluation": "challenge",
            "technical_debt": "concern",
            "decision": "suggestion",
            "debugging": "insight",
            "implementation": "suggestion",
            "integration": "observation",
            "architecture": "synthesis",
            "general": "observation"
        }
        return mapping.get(intent_type, "observation")


class EnhancedVibeMentorEngine:
    """Enhanced mentor engine with context-aware reasoning"""
    
    def __init__(self, base_engine):
        self.base_engine = base_engine
        self.context_extractor = ContextExtractor()
        self.enhanced_reasoning = EnhancedPersonaReasoning()
    
    def generate_contribution(
        self,
        session: CollaborativeReasoningSession,
        persona: PersonaData,
        detected_patterns: List[Dict[str, Any]],
        context: Optional[str] = None,
        project_context: Optional[Any] = None,
        file_contexts: Optional[List[Any]] = None
    ) -> ContributionData:
        """Generate context-aware contribution from persona"""
        
        # Extract technical context - this is the key enhancement
        tech_context = self.context_extractor.extract_context(session.topic, context)
        
        # NEW: Incorporate actual file contents if provided
        if file_contexts:
            # Enhance context with actual code information
            code_references = []
            for fc in file_contexts[:3]:  # Analyze first 3 files
                # Add function/class information to technical context
                if fc.functions:
                    tech_context.specific_features.extend([f"function:{f}" for f in fc.functions[:5]])
                if fc.classes:
                    tech_context.specific_features.extend([f"class:{c}" for c in fc.classes[:3]])
                
                # Look for relevant code patterns
                if hasattr(fc, 'relevant_lines') and fc.relevant_lines.get('direct_mentions'):
                    for line_num, line in fc.relevant_lines['direct_mentions'][:2]:
                        code_references.append(f"Line {line_num} in {fc.path}: {line.strip()}")
            
            # Add code references to context for persona reasoning
            if code_references:
                context = (context or "") + "\n\nActual code being discussed:\n" + "\n".join(code_references)
        
        # ENHANCEMENT: Use technical context as primary driver for response generation
        # Patterns are now optional enhancement, not required for good responses
        contribution_type, content, confidence = self._reason_as_persona_enhanced(
            persona, session.topic, tech_context, detected_patterns, session.contributions
        )
        
        contribution = ContributionData(
            persona_id=persona.id,
            content=content,
            type=contribution_type,
            confidence=confidence,
            reference_ids=self._find_references(content, session.contributions),
        )
        
        return contribution
    
    def _find_references(self, content: str, contributions: List[ContributionData]) -> List[str]:
        """Find contributions that this content references"""
        references = []
        content_lower = content.lower()
        
        for contrib in contributions:
            # Simple reference detection based on keyword overlap
            contrib_words = contrib.content.lower().split()[:10]  # First 10 words
            if any(word in content_lower for word in contrib_words if len(word) > MIN_CONTRIB_WORD_LENGTH):
                references.append(f"{contrib.persona_id}_{contrib.type}")
        
        return references
    
    def _reason_as_persona_enhanced(
        self,
        persona: PersonaData,
        topic: str,
        tech_context: TechnicalContext,
        patterns: List[Dict[str, Any]],
        previous_contributions: List[ContributionData]
    ) -> Tuple[str, str, float]:
        """Generate enhanced persona reasoning with specific technical context"""
        
        if persona.id == "senior_engineer":
            return self.enhanced_reasoning.generate_senior_engineer_response(
                tech_context, patterns, topic
            )
        elif persona.id == "product_engineer":
            return self.enhanced_reasoning.generate_product_engineer_response(
                tech_context, patterns, topic
            )
        elif persona.id == "ai_engineer":
            return self.enhanced_reasoning.generate_ai_engineer_response(
                tech_context, patterns, topic, previous_contributions
            )
        
        # Fallback to base behavior
        return self.base_engine._reason_as_persona(
            persona, topic, patterns, previous_contributions, None
        )