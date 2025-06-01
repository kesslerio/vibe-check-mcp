"""
Examples of GOOD architectural decisions that should NOT trigger detection
"""

# Example 1: Proper SDK research
stripe_good_example = """
Title: Implement Stripe Payment Integration

I've reviewed the official Stripe SDK documentation and tested
their examples. The stripe.checkout.Session.create() method
handles our payment flow perfectly.

The official integration guide shows exactly how to:
1. Create payment sessions
2. Handle webhooks for confirmation
3. Manage subscription billing

I'll implement using their recommended approach first,
then optimize if needed.
"""

# Example 2: Testing standard approach first
api_good_example = """
Title: Integrate with External API

I tested the official SDK and it covers 90% of our use cases.
For the remaining 10%, their documentation shows how to
make direct API calls using the same authentication.

Starting with the standard SDK integration as recommended
in their quickstart guide.
"""

# Example 3: Researched decision to customize
informed_custom_example = """
Title: Custom Authentication Layer

After testing the standard OAuth library and reviewing
their documentation thoroughly, I found it doesn't support
our specific enterprise SSO requirements.

I've documented the specific limitations:
1. No support for SAML assertions with custom attributes
2. Missing token refresh handling for our IdP
3. No callback URL validation for our subdomain setup

Building minimal custom layer to address only these gaps,
using their library for everything else.
"""

# These should all have LOW confidence scores and NOT be detected
examples_that_should_pass = [
    stripe_good_example,
    api_good_example,
    informed_custom_example
]