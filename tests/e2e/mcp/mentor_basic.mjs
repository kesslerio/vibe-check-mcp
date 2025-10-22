import { createMCPClient, shutdownClient } from './test-utils.mjs';

async function main() {
  const client = createMCPClient();

  try {
    await client.init();
    const tools = await client.listTools();
    console.log('✅ Server started, tools count:', tools.length);

    const query = "We've migrated Stripe validation, demo qualification, and financing workflows into Claude Desktop skills. Should we pull the corresponding JSON files out of tier1 or keep them?";

    const result = await client.callTool('vibe_check_mentor', {
      query,
      reasoning_depth: 'standard',
      mode: 'standard',
      phase: 'planning',
    });

    console.log(JSON.stringify(result, null, 2));
    console.log('\n✅ Test passed');

  } catch (err) {
    console.error('❌ Test failed:', err.message);
    if (err.stack) console.error(err.stack);
    process.exit(1);
  } finally {
    await shutdownClient(client);
  }
}

main().catch((err) => {
  console.error('❌ Unexpected error:', err.message);
  process.exit(1);
});
