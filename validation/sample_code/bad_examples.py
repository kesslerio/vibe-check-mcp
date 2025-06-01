"""
Examples of BAD architectural decisions that SHOULD trigger detection
"""

# Example 1: Building custom HTTP client
http_client_bad = """
Title: API Integration

Let's build our own HTTP client with custom retry logic
instead of using the requests library. We need more control
over timeouts and error handling than their library provides.
"""

# Example 2: Avoiding SDK without research
sdk_avoidance_bad = """
Title: Payment Integration

We should avoid using their SDK and implement our own
API wrapper for better control. SDKs are usually too
restrictive for our advanced use cases.
"""

# Example 3: Custom solution without validation
assumed_limitations_bad = """
Title: Database Integration

Their ORM might be too limiting for our complex queries.
I'll implement our own database abstraction layer to
ensure we have full flexibility for future requirements.
"""

# Example 4: Complex solution without trying simple first
over_engineering_bad = """
Title: User Authentication

We need a sophisticated multi-layered authentication system
with custom JWT handling, advanced session management,
and enterprise-grade security patterns. Their simple
auth library won't meet our scalability requirements.
"""

# Example 5: No research mentioned
no_research_bad = """
Title: Email Service Integration

I'll create our own email delivery system with custom
templates and advanced analytics. We need more features
than what standard email services typically provide.
"""

# These should all have HIGH confidence scores and BE detected
examples_that_should_fail = [
    http_client_bad,
    sdk_avoidance_bad, 
    assumed_limitations_bad,
    over_engineering_bad,
    no_research_bad
]