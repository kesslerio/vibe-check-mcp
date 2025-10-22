/**
 * Shared utilities for MCP E2E tests.
 * Handles client creation, cleanup, and common assertions.
 */

import { MCPTestClient } from 'mcp-test-client';

/**
 * Creates an MCPTestClient with proper PYTHONPATH propagation.
 * Uses 'env' command to explicitly set PYTHONPATH for the spawned server.
 * No editable install (pip install -e .) needed - PYTHONPATH points to src/.
 */
export function createMCPClient() {
  const projectRoot = process.cwd();
  const pythonPath = `${projectRoot}/src`;

  // Set for logging/debugging (not inherited by child process)
  process.env.PYTHONPATH = pythonPath;

  return new MCPTestClient({
    serverCommand: 'env',
    serverArgs: [
      `PYTHONPATH=${pythonPath}`,
      'python',
      '-m', 'vibe_check.server',
      '--stdio'
    ],
  });
}

/**
 * Properly shuts down MCP client and kills server process.
 * Ensures no zombie python processes remain after tests.
 *
 * Process:
 * 1. Close stdio transport
 * 2. Send SIGTERM to server process
 * 3. Wait 5s for graceful shutdown
 * 4. Send SIGKILL if process still alive
 *
 * @param {MCPTestClient} client - Client instance to shutdown
 */
export async function shutdownClient(client) {
  let pid = null;

  try {
    // Get PID before closing transport
    if (client.client?._transport?.pid) {
      pid = client.client._transport.pid;
    }

    // Close stdio transport
    if (client.client?._transport?.close) {
      await client.client._transport.close();
    }
  } catch (e) {
    console.warn('⚠️  Transport close warning:', e.message);
  }

  // Ensure process is killed (even if close() throws)
  if (pid) {
    try {
      // Send SIGTERM
      process.kill(pid, 'SIGTERM');

      // Wait for graceful shutdown
      await new Promise(resolve => setTimeout(resolve, 2000));

      // Check if still alive, send SIGKILL
      try {
        process.kill(pid, 0); // Throws if process doesn't exist
        console.warn(`⚠️  Process ${pid} didn't exit, sending SIGKILL`);
        process.kill(pid, 'SIGKILL');
      } catch {
        // Process already exited, good
      }
    } catch (e) {
      if (e.code !== 'ESRCH') {
        // ESRCH = No such process (already dead)
        console.warn(`⚠️  Error killing process ${pid}:`, e.message);
      }
    }
  }

  try {
    await client.cleanup();
  } catch (e) {
    console.warn('⚠️  Cleanup warning:', e.message);
  }
}

/**
 * Extracts all text content from MCP tool response.
 * Flattens collaborative_insights, immediate_feedback, etc.
 *
 * @param {Object} result - MCP tool call result
 * @returns {string} All text content joined
 */
export function extractAllText(result) {
  const texts = [];

  try {
    const content = result.content[0];
    if (content.type === 'text') {
      // Debug: Log raw content for troubleshooting
      if (content.text.startsWith('Error')) {
        console.error('RAW ERROR RESPONSE:', content.text.substring(0, 200));
        throw new Error(`Tool returned error: ${content.text.substring(0, 100)}`);
      }
      const response = JSON.parse(content.text);

      // Extract from collaborative_insights
      if (response.collaborative_insights) {
        const insights = response.collaborative_insights;

        // Consensus points
        if (insights.consensus && Array.isArray(insights.consensus)) {
          texts.push(...insights.consensus);
        }

        // Persona perspectives
        if (insights.perspectives) {
          for (const [persona, data] of Object.entries(insights.perspectives)) {
            if (data.message) texts.push(data.message);
          }
        }

        // Key insights
        if (insights.key_insights && Array.isArray(insights.key_insights)) {
          texts.push(...insights.key_insights);
        }

        // Concerns
        if (insights.concerns && Array.isArray(insights.concerns)) {
          texts.push(...insights.concerns);
        }

        // Recommendations
        if (insights.recommendations) {
          if (insights.recommendations.immediate_actions) {
            texts.push(...insights.recommendations.immediate_actions);
          }
          if (insights.recommendations.avoid) {
            texts.push(...insights.recommendations.avoid);
          }
        }
      }

      // Extract from immediate_feedback
      if (response.immediate_feedback) {
        const feedback = response.immediate_feedback;
        if (feedback.summary) texts.push(feedback.summary);
        if (feedback.detected_patterns && Array.isArray(feedback.detected_patterns)) {
          for (const pattern of feedback.detected_patterns) {
            if (pattern.description) texts.push(pattern.description);
            if (pattern.recommendation) texts.push(pattern.recommendation);
          }
        }
      }

      // Extract from coaching_guidance
      if (response.coaching_guidance) {
        const coaching = response.coaching_guidance;
        if (coaching.primary_recommendation) texts.push(coaching.primary_recommendation);
        if (coaching.action_steps && Array.isArray(coaching.action_steps)) {
          texts.push(...coaching.action_steps);
        }
        if (coaching.prevention_checklist && Array.isArray(coaching.prevention_checklist)) {
          texts.push(...coaching.prevention_checklist);
        }
      }

      // Extract from formatted_output
      if (response.formatted_output) {
        texts.push(response.formatted_output);
      }
    }
  } catch (e) {
    console.error('Error extracting text from response:', e.message);
  }

  return texts.join('\n');
}

/**
 * Assert helper with descriptive error messages.
 *
 * @param {boolean} condition - Condition to assert
 * @param {string} message - Error message if condition is false
 */
export function assert(condition, message) {
  if (!condition) {
    throw new Error(`Assertion failed: ${message}`);
  }
}
