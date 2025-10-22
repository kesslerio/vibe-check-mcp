/**
 * E2E test for vibe_check_mentor response relevance.
 * Guards against regression of issue #279 where canned Stripe/LLM responses
 * returned instead of query-specific advice for tier1/tier2 architecture.
 */

import { createMCPClient, shutdownClient, extractAllText, assert } from './test-utils.mjs';

// Canned sentences that should NEVER appear in architecture guidance
const BANNED_CANNED_PHRASES = [
  'hosted checkout page',              // Stripe MVP advice
  'prompt caching to reduce costs',    // LLM pricing blurb
  '2025 llm model pricing',            // LLM pricing table
  'stripe integration MVP',            // Stripe boilerplate
];

async function main() {
  console.log('🧪 Testing mentor response relevance (tier1/tier2 guard)...\n');

  const client = createMCPClient();

  try {
    await client.init();
    console.log('✅ Server started\n');

    // THE EXACT QUERY FROM ISSUE #279
    const query = "We've migrated Stripe validation, demo qualification, and financing workflows into Claude Desktop skills. Should we pull the corresponding JSON files out of tier1 or keep them?";

    console.log('Running tier1/tier2 architecture query...');

    const result = await client.callTool('vibe_check_mentor', {
      query,
      reasoning_depth: 'standard',
      mode: 'standard',
      phase: 'planning',  // Architecture phase
    });

    const content = result.content[0];
    assert(content.type === 'text', `Expected text response, got ${content.type}`);

    // Extract all response text
    const responseText = extractAllText(result);
    const lowerText = responseText.toLowerCase();

    console.log('\n=== Response Text (first 500 chars) ===');
    console.log(responseText.substring(0, 500) + '...\n');

    // POSITIVE ASSERTIONS: Response must mention the query topic
    console.log('Checking for tier1 references...');

    const hasTier1 = lowerText.includes('tier1') || lowerText.includes('tier 1');

    assert(hasTier1,
      'Response must mention tier1 (the query topic) - found canned response instead');

    console.log('✅ Response mentions tier1: YES');

    // NEGATIVE ASSERTIONS: Canned responses must NOT appear
    console.log('\nChecking for banned canned phrases...');

    for (const phrase of BANNED_CANNED_PHRASES) {
      if (lowerText.includes(phrase)) {
        // Dump full response for debugging
        console.error('\n=== FULL RESPONSE (DEBUG) ===');
        console.error(responseText);
        console.error('===========================\n');

        assert(false,
          `Response contains canned phrase "${phrase}" - regression of issue #279 detected`);
      }
    }

    console.log('✅ No banned canned phrases found');

    // Additional context-specific checks for architecture phase
    console.log('\nVerifying architecture-appropriate response...');

    // Should have some architectural considerations (not strict requirement)
    const hasArchitecturalTerms = (
      lowerText.includes('architecture') ||
      lowerText.includes('structure') ||
      lowerText.includes('organize') ||
      lowerText.includes('decision') ||
      lowerText.includes('approach')
    );

    if (hasArchitecturalTerms) {
      console.log('✅ Response includes architectural guidance');
    } else {
      console.warn('⚠️  Response may lack architectural context (not a failure)');
    }

    console.log('\n✅ PASS: mentor_relevance_e2e');
    console.log('Response is query-specific and canned responses are suppressed.');

  } catch (error) {
    console.error('\n❌ FAIL: mentor_relevance_e2e');
    console.error('Error:', error.message);
    if (error.stack) {
      console.error(error.stack);
    }
    process.exit(1);
  } finally {
    await shutdownClient(client);
  }
}

main().catch((err) => {
  console.error('❌ Unexpected error:', err.message);
  process.exit(1);
});
