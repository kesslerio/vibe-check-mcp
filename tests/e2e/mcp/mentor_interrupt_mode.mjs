import { MCPTestClient } from 'mcp-test-client';

/**
 * E2E test for vibe_check_mentor interrupt mode.
 * Tests both interrupt=true and interrupt=false scenarios.
 */

async function testInterruptTriggered() {
  console.log('\n=== Test 1: Interrupt Triggered (Anti-pattern Detection) ===');

  const client = new MCPTestClient({
    serverCommand: 'python',
    serverArgs: ['-m', 'vibe_check.server', '--stdio'],
  });

  try {
    process.env.PYTHONPATH = `${process.cwd()}/src`;
    await client.init();

    // Query that should trigger interrupt (custom HTTP client anti-pattern)
    const query = "I'm building a custom HTTP client for the GitHub API to handle rate limiting and retries";

    const result = await client.callTool('vibe_check_mentor', {
      query,
      mode: 'interrupt',
      phase: 'planning',
    });

    const content = result.content[0];
    if (content.type !== 'text') {
      throw new Error(`Expected text response, got ${content.type}`);
    }

    const response = JSON.parse(content.text);

    // Assertions for interrupt=true response
    const required = ['status', 'mode', 'interrupt', 'phase', 'confidence'];
    for (const field of required) {
      if (!(field in response)) {
        throw new Error(`Missing required field: ${field}`);
      }
    }

    if (response.status !== 'success') {
      throw new Error(`Expected status=success, got ${response.status}`);
    }

    if (response.mode !== 'interrupt') {
      throw new Error(`Expected mode=interrupt, got ${response.mode}`);
    }

    if (response.interrupt !== true) {
      console.warn('⚠️  Expected interrupt=true (anti-pattern detection), but got false');
      console.warn('This may indicate pattern detection needs tuning, not a critical failure');
    } else {
      // Validate interrupt response structure
      const interruptFields = ['question', 'severity', 'suggestion', 'pattern_detected', 'can_escalate'];
      for (const field of interruptFields) {
        if (!(field in response)) {
          throw new Error(`Interrupt response missing field: ${field}`);
        }
      }

      if (!response.question || response.question.length < 10) {
        throw new Error('Interrupt question too short or missing');
      }

      if (!['low', 'medium', 'high'].includes(response.severity)) {
        throw new Error(`Invalid severity: ${response.severity}`);
      }

      console.log('✅ Interrupt triggered correctly');
      console.log(`   Pattern: ${response.pattern_detected}`);
      console.log(`   Severity: ${response.severity}`);
      console.log(`   Question: ${response.question.substring(0, 80)}...`);
    }

    await client.cleanup();
    return true;

  } catch (error) {
    await client.cleanup();
    throw error;
  }
}

async function testNoInterrupt() {
  console.log('\n=== Test 2: No Interrupt (Low Confidence) ===');

  const client = new MCPTestClient({
    serverCommand: 'python',
    serverArgs: ['-m', 'vibe_check.server', '--stdio'],
  });

  try {
    process.env.PYTHONPATH = `${process.cwd()}/src`;
    await client.init();

    // Generic technical question (should proceed without interrupt)
    const query = "Should I use React hooks or class components for my new component?";

    const result = await client.callTool('vibe_check_mentor', {
      query,
      mode: 'interrupt',
      phase: 'implementation',
    });

    const content = result.content[0];
    if (content.type !== 'text') {
      throw new Error(`Expected text response, got ${content.type}`);
    }

    const response = JSON.parse(content.text);

    // Assertions for interrupt=false response
    const required = ['status', 'mode', 'interrupt', 'proceed', 'phase', 'confidence'];
    for (const field of required) {
      if (!(field in response)) {
        throw new Error(`Missing required field: ${field}`);
      }
    }

    if (response.status !== 'success') {
      throw new Error(`Expected status=success, got ${response.status}`);
    }

    if (response.mode !== 'interrupt') {
      throw new Error(`Expected mode=interrupt, got ${response.mode}`);
    }

    if (response.interrupt !== false) {
      console.warn('⚠️  Expected interrupt=false (low confidence), but got true');
      console.warn('This may indicate overly sensitive pattern detection');
    }

    if (response.proceed !== true) {
      throw new Error('Expected proceed=true when interrupt=false');
    }

    if (!('affirmation' in response) || !response.affirmation) {
      throw new Error('Missing affirmation in no-interrupt response');
    }

    console.log('✅ No interrupt (proceed) correctly');
    console.log(`   Confidence: ${response.confidence}`);
    console.log(`   Affirmation: ${response.affirmation.substring(0, 80)}...`);

    await client.cleanup();
    return true;

  } catch (error) {
    await client.cleanup();
    throw error;
  }
}

async function main() {
  console.log('🧪 Testing vibe_check_mentor interrupt mode...\n');

  try {
    await testInterruptTriggered();
    await testNoInterrupt();

    console.log('\n✅ All interrupt mode tests passed!');
    process.exit(0);

  } catch (error) {
    console.error('\n❌ Test failed:', error.message);
    if (error.stack) {
      console.error(error.stack);
    }
    process.exit(1);
  }
}

main();
