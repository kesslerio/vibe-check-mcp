"""
Enhanced Vibe Check Mentor - Context-Aware Collaborative Reasoning

Provides specific, technical advice based on query analysis instead of generic responses.
Extracts technologies, frameworks, and specific problems to give targeted guidance.
"""

import re
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass

# Import existing structures
from .vibe_mentor import (
    PersonaData, ContributionData, PatternHandler, 
    ConfidenceScores, CollaborativeReasoningSession
)


@dataclass
class TechnicalContext:
    """Extracted technical context from query"""
    technologies: List[str]
    frameworks: List[str]
    patterns: List[str]
    problem_type: str  # integration, architecture, implementation, debugging
    specific_features: List[str]
    decision_points: List[str]


class ContextExtractor:
    """Extract technical context from queries for specific advice"""
    
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
    def extract_context(cls, query: str, context: Optional[str] = None) -> TechnicalContext:
        """Extract technical context from query and optional context"""
        combined_text = f"{query} {context or ''}".lower()
        
        # Extract technologies and frameworks
        technologies = []
        frameworks = []
        for category, terms in cls.TECH_PATTERNS.items():
            for term in terms:
                if term in combined_text:
                    if category in ['frameworks', 'languages']:
                        frameworks.append(term)
                    else:
                        technologies.append(term)
        
        # Determine problem type
        problem_type = 'general'
        for ptype, indicators in cls.PROBLEM_INDICATORS.items():
            if any(ind in combined_text for ind in indicators):
                problem_type = ptype
                break
        
        # Extract specific features mentioned
        features = []
        feature_patterns = [
            r'(?:implement|build|create|add)\s+(\w+(?:\s+\w+)?)',
            r'(\w+(?:\s+\w+)?)\s+(?:feature|functionality|capability)',
            r'custom\s+(\w+(?:\s+\w+)?)',
            r'(?:implementing|building|creating)\s+(\w+(?:\s+\w+)?)'
        ]
        for pattern in feature_patterns:
            matches = re.findall(pattern, combined_text)
            # Filter out incomplete matches
            features.extend([m for m in matches if len(m) > 3 and not m.endswith(' for')])
        
        # Extract decision points
        decisions = []
        decision_patterns = [
            r'(\w+)\s+vs\s+(\w+)',
            r'should\s+i\s+(\w+(?:\s+\w+)?)',
            r'(?:use|choose|pick)\s+(\w+(?:\s+\w+)?)'
        ]
        for pattern in decision_patterns:
            matches = re.findall(pattern, combined_text)
            if isinstance(matches[0], tuple) if matches else False:
                decisions.extend([f"{m[0]} vs {m[1]}" for m in matches])
            else:
                decisions.extend(matches)
        
        # Extract architectural patterns mentioned
        patterns = []
        pattern_keywords = ['microservice', 'monolith', 'serverless', 'event-driven', 
                          'mvc', 'mvvm', 'repository', 'factory', 'singleton']
        for keyword in pattern_keywords:
            if keyword in combined_text:
                patterns.append(keyword)
        
        return TechnicalContext(
            technologies=list(set(technologies)),
            frameworks=list(set(frameworks)),
            patterns=patterns,
            problem_type=problem_type,
            specific_features=list(set(features))[:5],  # Limit to top 5
            decision_points=list(set(decisions))[:3]    # Limit to top 3
        )


class EnhancedPersonaReasoning:
    """Generate context-aware responses for each persona"""
    
    @staticmethod
    def generate_senior_engineer_response(
        tech_context: TechnicalContext,
        patterns: List[Dict[str, Any]],
        query: str
    ) -> Tuple[str, str, float]:
        """Generate specific senior engineer advice based on context"""
        
        # ENHANCEMENT: Prioritize technical context over patterns
        # If we have specific technologies mentioned, give specific advice
        if tech_context.technologies:
            tech = tech_context.technologies[0]
            
            # Check for infrastructure pattern with specific tech context
            if PatternHandler.has_pattern(patterns, "infrastructure_without_implementation"):
                return (
                    "concern",
                    f"I see you're planning infrastructure for {tech}. In my 15 years of experience, "
                    f"I've learned to always start with {tech}'s official SDK or container first. "
                    f"For example, {tech} likely provides official Docker images or client libraries that "
                    f"handle authentication, retries, and edge cases we'd miss in custom implementations. "
                    f"Have you checked {tech}'s official documentation for their recommended integration approach?",
                    ConfidenceScores.VERY_HIGH
                )
            
            # NEW: Technology-specific advice even without patterns
            if tech in ['stripe', 'paypal', 'square']:
                return (
                    "suggestion",
                    f"For {tech} integration, never build your own HTTP client. Use their official SDK - "
                    f"it handles webhooks, idempotency, retry logic, and PCI compliance automatically. "
                    f"I've seen teams spend months debugging payment edge cases that the SDK handles in one line. "
                    f"Check their quickstart docs first, then their testing sandbox environment.",
                    ConfidenceScores.VERY_HIGH
                )
            
            elif tech in ['openai', 'claude', 'gpt']:
                return (
                    "insight",
                    f"Working with {tech}? Three things I learned the hard way: "
                    f"1) Use their official Python/JS SDK, not raw HTTP calls, "
                    f"2) Implement exponential backoff for rate limiting, "
                    f"3) Stream responses for better UX. Also, set up proper prompt versioning from day 1 - "
                    f"you'll be iterating prompts constantly and need to track what works.",
                    ConfidenceScores.HIGH
                )
            
            elif tech in ['postgres', 'postgresql', 'mysql', 'mongodb']:
                return (
                    "concern",
                    f"Before building custom {tech} infrastructure, have you considered: "
                    f"1) Managed services like RDS/PlanetScale for {tech}? "
                    f"2) Connection pooling and read replicas from day 1? "
                    f"3) Migration strategy and backup automation? "
                    f"I've seen too many teams lose data because they skipped the boring infrastructure work.",
                    ConfidenceScores.HIGH
                )
            
            elif tech in ['auth0', 'clerk', 'nextauth', 'oauth', 'oauth2']:
                return (
                    "suggestion",
                    f"For {tech} authentication: This is exactly the right approach - don't build auth from scratch. "
                    f"{tech} handles password resets, social logins, MFA, and security compliance for you. "
                    f"I've debugged more custom auth systems than I care to remember. "
                    f"Use their quickstart guide, set up proper redirect URLs, and you'll save months of security headaches.",
                    ConfidenceScores.VERY_HIGH
                )
            
            elif tech in ['docker', 'kubernetes', 'k8s']:
                return (
                    "concern",
                    f"Are you sure you need {tech} complexity right now? "
                    f"For startups: Use managed platforms like Railway/Render/Fly.io first. "
                    f"For enterprises: {tech} is great, but start with their managed versions (EKS/GKE/AKS). "
                    f"I've seen teams spend 6 months on {tech} setup when they should've been building features.",
                    ConfidenceScores.HIGH
                )
            
            elif tech in ['bun']:
                return (
                    "insight",
                    f"Bun is impressive in 2025 - it's become production-ready: "
                    f"1) Drop-in Node.js replacement with 3x faster package installs, "
                    f"2) Built-in bundler, test runner, and TypeScript support, "
                    f"3) Much faster startup times than Node.js, "
                    f"4) Great for new projects, but check library compatibility first. "
                    f"I'd use it for new TypeScript projects, but migrate existing Node apps carefully.",
                    ConfidenceScores.HIGH
                )
            
            elif tech in ['deno']:
                return (
                    "suggestion",
                    f"Deno has matured significantly: "
                    f"1) Built-in TypeScript, testing, formatting - no config needed, "
                    f"2) Web-standard APIs instead of Node.js quirks, "
                    f"3) Excellent security model with permissions, "
                    f"4) Deno Deploy for edge computing. "
                    f"Perfect for new projects that want modern standards. The npm compatibility makes migration easier now.",
                    ConfidenceScores.HIGH
                )
            
            elif tech in ['vite', 'esbuild', 'swc', 'turbo']:
                return (
                    "observation",
                    f"{tech} is an excellent choice for build tooling in 2025: "
                    f"Vite: Amazing dev experience with HMR, great for React/Vue. "
                    f"ESBuild: Blazing fast bundling, good for libraries. "
                    f"SWC: Rust-based, faster than Babel, Next.js uses it. "
                    f"Turbo: Incremental builds, perfect for monorepos. "
                    f"All are significantly faster than webpack for most use cases.",
                    ConfidenceScores.HIGH
                )
            else:
                return (
                    "concern", 
                    "This looks like premature infrastructure design. Start with working API calls first, "
                    "then extract patterns only when you have 3+ similar use cases. Most 'future flexibility' "
                    "never gets used but adds maintenance burden forever.",
                    ConfidenceScores.HIGH
                )
        
        # Framework-specific advice (even without specific technologies)
        if tech_context.frameworks and not tech_context.technologies:
            framework = tech_context.frameworks[0]
            
            if framework in ['react', 'vue', 'angular']:
                return (
                    "suggestion",
                    f"For {framework} architecture: Keep components small and focused. "
                    f"I follow the rule: If a component does more than one thing, split it. "
                    f"Use TypeScript from day 1 - you'll thank me when refactoring. "
                    f"For state: Start with built-in state, add Zustand/Redux only when you feel the pain. "
                    f"Test user flows, not implementation details.",
                    ConfidenceScores.HIGH
                )
            
            elif framework in ['nextjs', 'next.js']:
                return (
                    "insight",
                    f"Next.js is excellent for full-stack React. Use these patterns: "
                    f"1) App Router for new projects (better than Pages Router), "
                    f"2) Server Components by default, Client Components only when needed, "
                    f"3) Vercel for deployment - it's made by the Next.js team, "
                    f"4) Use their built-in optimizations: Image, Font, Link components. "
                    f"Start with the T3 stack template if you need DB + auth.",
                    ConfidenceScores.HIGH
                )
            
            elif framework in ['django', 'fastapi']:
                return (
                    "suggestion",
                    f"For {framework} APIs: Follow their conventions religiously. "
                    f"Django: Use Django REST Framework for APIs, don't reinvent serialization. "
                    f"FastAPI: Use Pydantic models for everything - they generate docs automatically. "
                    f"Both: Set up automated testing with pytest from day 1. "
                    f"Deploy with Docker to avoid environment issues.",
                    ConfidenceScores.HIGH
                )
            
            elif framework in ['astro']:
                return (
                    "insight",
                    f"Astro is perfect for content-heavy sites! Use these 2025 patterns: "
                    f"1) Islands architecture - ship minimal JS, hydrate only what needs interactivity, "
                    f"2) View Transitions API for smooth page transitions, "
                    f"3) Content Collections for type-safe markdown/MDX, "
                    f"4) Astro DB for simple data needs. Perfect for blogs, marketing sites, docs. "
                    f"Deploy to Vercel/Netlify with zero config.",
                    ConfidenceScores.HIGH
                )
            
            elif framework in ['remix']:
                return (
                    "suggestion",
                    f"Remix is excellent for full-stack React apps that prioritize web standards: "
                    f"1) Use loaders for data fetching - they run on the server, "
                    f"2) Actions for mutations - built-in progressive enhancement, "
                    f"3) Nested routing for complex layouts, "
                    f"4) Deploy to Fly.io or Railway for best performance. "
                    f"Remix shines for apps that need to work without JS.",
                    ConfidenceScores.HIGH
                )
            
            elif framework in ['svelte', 'sveltekit']:
                return (
                    "observation",
                    f"Svelte/SvelteKit is gaining serious momentum in 2025: "
                    f"1) No virtual DOM means smaller bundles and faster runtime, "
                    f"2) Runes (new reactivity system) are more intuitive than React hooks, "
                    f"3) SvelteKit handles SSR, routing, and deployment out of the box, "
                    f"4) TypeScript support is excellent. Great for performance-critical apps.",
                    ConfidenceScores.HIGH
                )
            
            elif framework in ['solid', 'solid.js']:
                return (
                    "insight",
                    f"Solid.js offers React-like syntax with Vue-like performance: "
                    f"1) Fine-grained reactivity - no re-renders, only updates what changed, "
                    f"2) JSX without virtual DOM overhead, "
                    f"3) Excellent TypeScript support, "
                    f"4) SolidStart for full-stack apps. Perfect if you want React DX with better performance.",
                    ConfidenceScores.HIGH
                )
            
            elif framework in ['qwik']:
                return (
                    "challenge",
                    f"Qwik is interesting but still experimental. Consider: "
                    f"1) Resumability means 0ms JavaScript startup - revolutionary for performance, "
                    f"2) But ecosystem is tiny compared to React/Vue, "
                    f"3) Learning curve is steep - it thinks differently about reactivity, "
                    f"4) Great for content sites, questionable for complex apps. "
                    f"Wait for 1.0 unless you're building a simple marketing site.",
                    ConfidenceScores.MODERATE
                )
        
        # Integration-specific advice
        if tech_context.problem_type == "integration":
            if tech_context.technologies:
                tech = tech_context.technologies[0]
                return (
                    "insight",
                    f"For {tech} integration, I strongly recommend their official SDK. I've seen teams "
                    f"waste months on custom HTTP clients only to discover the SDK handles rate limiting, "
                    f"retries, auth refresh, and error mapping already. Check if {tech} provides: "
                    f"1) Official SDK in your language ({tech_context.frameworks[0] if tech_context.frameworks else 'your stack'}), "
                    f"2) OpenAPI spec for code generation, "
                    f"3) Webhook support for real-time updates. "
                    f"Only go custom if you have specific requirements the SDK truly can't meet.",
                    ConfidenceScores.VERY_HIGH
                )
        
        # Architecture decisions with specific context
        if tech_context.problem_type == "architecture":
            if tech_context.patterns:
                pattern = tech_context.patterns[0]
                return (
                    "suggestion",
                    f"For {pattern} architecture with {tech_context.technologies[0] if tech_context.technologies else 'your stack'}: "
                    f"Start with a modular monolith first. I've migrated 5 systems from microservices back to monoliths "
                    f"because the complexity wasn't justified. You can always extract services later when you have: "
                    f"1) Clear bounded contexts from real usage, "
                    f"2) Team size requiring independent deployments, "
                    f"3) Proven scaling bottlenecks. "
                    f"Focus on clean module boundaries now - they'll make future splits trivial.",
                    ConfidenceScores.HIGH
                )
        
        # Feature implementation advice
        if tech_context.specific_features:
            feature = tech_context.specific_features[0]
            return (
                "suggestion",
                f"For implementing {feature}: Check if there's a battle-tested library first. "
                f"I maintain a rule: 'Never write auth, payments, or file uploads from scratch.' "
                f"These solved problems have edge cases you'll discover painfully. "
                f"For {feature}, look for libraries with 1000+ GitHub stars, recent updates, "
                f"and good documentation. Custom code should be your business logic, not infrastructure.",
                ConfidenceScores.GOOD
            )
        
        # Decision-making advice
        if tech_context.decision_points:
            decision = tech_context.decision_points[0]
            return (
                "insight",
                f"Regarding '{decision}': Apply the 'Boring Technology' principle. "
                f"Choose the option that: 1) Your team already knows, "
                f"2) Has mature tooling and documentation, "
                f"3) Won't surprise you at 3 AM. "
                f"New tech is expensive - not in learning, but in discovering edge cases. "
                f"I'd need to see 10x improvement to justify the switch.",
                ConfidenceScores.HIGH
            )
        
        # Default but still specific based on query keywords
        if "custom" in query.lower():
            return (
                "concern",
                "Before building custom solutions, have you explored: "
                "1) Existing libraries in your ecosystem? "
                "2) Whether this is core to your business? "
                "3) The total cost including maintenance? "
                "Remember: today's clever abstraction is tomorrow's legacy nightmare.",
                ConfidenceScores.GOOD
            )
        
        return (
            "observation",
            "Let's think about long-term maintainability here. Whatever you build, "
            "optimize for the next developer (probably you in 6 months) to understand quickly. "
            "Clear code with good tests beats clever abstractions every time.",
            ConfidenceScores.MODERATE
        )
    
    @staticmethod
    def generate_product_engineer_response(
        tech_context: TechnicalContext,
        patterns: List[Dict[str, Any]],
        query: str
    ) -> Tuple[str, str, float]:
        """Generate specific product engineer advice based on context"""
        
        # ENHANCEMENT: Give specific advice based on technology, even without patterns
        
        # Technology + Framework combinations
        if tech_context.technologies and tech_context.frameworks:
            tech = tech_context.technologies[0]
            framework = tech_context.frameworks[0]
            return (
                "suggestion",
                f"Here's how I'd ship {tech} + {framework} this week: "
                f"1) Use {tech}'s quickstart template - they usually have one for {framework}, "
                f"2) Deploy a working prototype to Vercel/Netlify/Railway today, "
                f"3) Get 5 real users testing by Friday. "
                f"I've launched 50+ features - the ones that succeed iterate from real feedback, "
                f"not architectural perfection. Ship the 20% that delivers 80% value.",
                ConfidenceScores.VERY_HIGH
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
        
        # Check for RAG/Vector DB first (more specific than general AI)
        if any(term in query.lower() for term in ['rag', 'vector', 'embedding']) or any(t in tech_context.technologies for t in ['rag', 'vector', 'embedding', 'pinecone', 'weaviate']):
            # This is a RAG-specific query
            vector_techs = [t for t in tech_context.technologies if t in ['pinecone', 'weaviate', 'qdrant', 'vector', 'rag', 'openai', 'embedding']]
            return (
                "insight",
                f"For {'RAG with ' + vector_techs[0] if vector_techs else 'RAG/vector'} systems: Don't build from scratch. "
                f"1) Use LangChain/LlamaIndex for orchestration - they handle chunking, retrieval, and chain management, "
                f"2) For vector storage: Pinecone (easiest), Weaviate (feature-rich), or Qdrant (self-hostable), "
                f"3) Start with OpenAI embeddings (ada-002) - switch to open source later if needed, "
                f"4) Implement hybrid search (vector + BM25) for 30% better results, "
                f"5) Use metadata filtering to improve relevance. "
                f"I've built 5 RAG systems - custom implementations always miss edge cases like token limits and context windows.",
                ConfidenceScores.VERY_HIGH
            )
        
        # General AI/LLM integration (not RAG)
        elif any(ai_term in tech_context.technologies for ai_term in ['openai', 'claude', 'gpt', 'llm']):
            ai_tech = next(t for t in tech_context.technologies if t in ['openai', 'claude', 'gpt', 'llm'])
            return (
                "insight",
                f"For {ai_tech} integration, leverage these AI-specific patterns: "
                f"1) Use their official SDK - it handles streaming, token counting, and retry logic, "
                f"2) Implement prompt caching to reduce costs by 50-90%, "
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
        context: Optional[str] = None
    ) -> ContributionData:
        """Generate context-aware contribution from persona"""
        
        # Extract technical context - this is the key enhancement
        tech_context = self.context_extractor.extract_context(session.topic, context)
        
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
            reference_ids=self.base_engine._find_references(content, session.contributions),
        )
        
        return contribution
    
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