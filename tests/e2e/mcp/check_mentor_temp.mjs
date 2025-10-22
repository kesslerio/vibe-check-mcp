import { MCPTestClient } from 'mcp-test-client';

async function main() {
  process.env.PYTHONPATH = `${process.cwd()}/src`;
  const client = new MCPTestClient({
    serverCommand: 'python',
    serverArgs: ['-m', 'vibe_check.server', '--stdio'],
  });
  await client.init();
  const tools = await client.listTools();
  console.log('tools count', tools.length);
  const query = "We've migrated Stripe validation, demo qualification, and financing workflows into Claude Desktop skills. Should we pull the corresponding JSON files out of tier1 or keep them?";
  const result = await client.callTool('vibe_check_mentor', {
    query,
    reasoning_depth: 'standard',
    mode: 'standard',
    phase: 'planning',
  });
  console.log(JSON.stringify(result, null, 2));
  await client.cleanup();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
