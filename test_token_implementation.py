#!/usr/bin/env python3
"""
Basic test to verify the token limit bypass implementation works.
"""

import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_token_counter():
    """Test basic TokenCounter functionality."""
    try:
        from vibe_check.utils.token_utils import get_token_counter, count_tokens, analyze_content_size
        
        print("✅ Successfully imported token utilities")
        
        # Test basic token counting
        test_text = "This is a test of the token counting system. It should work properly."
        token_count = count_tokens(test_text)
        print(f"✅ Token count for test text: {token_count}")
        
        # Test content analysis
        analysis = analyze_content_size(test_text, "test")
        print(f"✅ Content analysis: {analysis['analysis_mode']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Token counter test failed: {e}")
        return False

def test_mcp_handler():
    """Test MCP protocol handler."""
    try:
        from vibe_check.tools.mcp_protocol_handler import get_mcp_handler
        
        print("✅ Successfully imported MCP protocol handler")
        
        handler = get_mcp_handler()
        print(f"✅ MCP handler initialized with {handler.MCP_TOKEN_LIMIT} token limit")
        
        # Test requirements analysis
        test_prompt = "Analyze this code"
        test_data = "def hello(): print('hello world')"
        
        requirements = handler.analyze_content_requirements(test_prompt, test_data)
        print(f"✅ Requirements analysis: {requirements['mode'].value}")
        
        return True
        
    except Exception as e:
        print(f"❌ MCP handler test failed: {e}")
        return False

def test_claude_integration():
    """Test enhanced Claude integration."""
    try:
        from vibe_check.tools.pr_review.claude_integration import ClaudeIntegration
        
        print("✅ Successfully imported enhanced Claude integration")
        
        integration = ClaudeIntegration()
        print(f"✅ Claude integration initialized with {integration.MAX_TOKEN_LIMIT} token limit")
        
        return True
        
    except Exception as e:
        print(f"❌ Claude integration test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing Token Limit Bypass Implementation")
    print("=" * 50)
    
    tests = [
        ("Token Counter", test_token_counter),
        ("MCP Handler", test_mcp_handler), 
        ("Claude Integration", test_claude_integration)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 Testing {test_name}...")
        success = test_func()
        results.append((test_name, success))
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    
    all_passed = True
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} {test_name}")
        if not success:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All tests passed! Token limit bypass implementation is ready.")
    else:
        print("\n⚠️ Some tests failed. Please check the implementation.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)