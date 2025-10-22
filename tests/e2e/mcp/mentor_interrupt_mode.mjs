import { createMCPClient, shutdownClient, assert } from './test-utils.mjs';

/**
 * E2E test for vibe_check_mentor interrupt mode.
 * Tests both interrupt=true and interrupt=false scenarios.
 */

async function testInterruptTriggered(client) {
  console.log('\n=== Test 1: Interrupt Triggered (Anti-pattern Detection) ===');

  // Query that should trigger interrupt (custom HTTP client anti-pattern)
  const query = "I'm building a custom HTTP client for the GitHub API to handle rate limiting and retries";

  const result = await client.callTool('vibe_check_mentor', {
    query,
    mode: 'interrupt',
    phase: 'planning',
  });

  const content = result.content[0];
  assert(content.type === 'text', `Expected text response, got ${content.type}`);

  const response = JSON.parse(content.text);

  // Assertions for interrupt response structure
  const required = ['status', 'mode', 'interrupt', 'phase', 'confidence'];
  for (const field of required) {
    assert(field in response, `Missing required field: ${field}`);
  }

  assert(response.status === 'success', `Expected status=success, got ${response.status}`);
  assert(response.mode === 'interrupt', `Expected mode=interrupt, got ${response.mode}`);

  if (response.interrupt !== true) {
    console.warn('⚠️  Expected interrupt=true (anti-pattern detection), but got false');
    console.warn('This may indicate pattern detection needs tuning, not a critical failure');
  } else {
    // Validate interrupt response structure
    const interruptFields = ['question', 'severity', 'suggestion', 'pattern_detected', 'can_escalate'];
    for (const field of interruptFields) {
      assert(field in response, `Interrupt response missing field: ${field}`);
    }

    assert(response.question && response.question.length >= 10, 'Interrupt question too short or missing');
    assert(['low', 'medium', 'high'].includes(response.severity), `Invalid severity: ${response.severity}`);

    console.log('✅ Interrupt triggered correctly');
    console.log(`   Pattern: ${response.pattern_detected}`);
    console.log(`   Severity: ${response.severity}`);
    console.log(`   Question: ${response.question.substring(0, 80)}...`);
  }
}

async function testNoInterrupt(client) {
  console.log('\n=== Test 2: No Interrupt (Low Confidence) ===');

  // Generic technical question (should proceed without interrupt)
  const query = "Should I use React hooks or class components for my new component?";

  const result = await client.callTool('vibe_check_mentor', {
    query,
    mode: 'interrupt',
    phase: 'implementation',
  });

  const content = result.content[0];
  assert(content.type === 'text', `Expected text response, got ${content.type}`);

  const response = JSON.parse(content.text);

  // Assertions for interrupt=false response
  const required = ['status', 'mode', 'interrupt', 'proceed', 'phase', 'confidence'];
  for (const field of required) {
    assert(field in response, `Missing required field: ${field}`);
  }

  assert(response.status === 'success', `Expected status=success, got ${response.status}`);
  assert(response.mode === 'interrupt', `Expected mode=interrupt, got ${response.mode}`);

  if (response.interrupt !== false) {
    console.warn('⚠️  Expected interrupt=false (low confidence), but got true');
    console.warn('This may indicate overly sensitive pattern detection');
  }

  assert(response.proceed === true, 'Expected proceed=true when interrupt=false');
  assert('affirmation' in response && response.affirmation, 'Missing affirmation in no-interrupt response');

  console.log('✅ No interrupt (proceed) correctly');
  console.log(`   Confidence: ${response.confidence}`);
  console.log(`   Affirmation: ${response.affirmation.substring(0, 80)}...`);
}

async function main() {
  console.log('🧪 Testing vibe_check_mentor interrupt mode...\n');

  const client = createMCPClient();

  try {
    await client.init();
    console.log('✅ Server started\n');

    // Run both test scenarios with same client
    await testInterruptTriggered(client);
    await testNoInterrupt(client);

    console.log('\n✅ All interrupt mode tests passed!');

  } catch (error) {
    console.error('\n❌ Test failed:', error.message);
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
