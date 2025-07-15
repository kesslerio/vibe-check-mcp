#!/usr/bin/env python3
"""
Simple test for the Zen-style large prompt handler.
"""

import os
import sys
import tempfile

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from vibe_check.tools.large_prompt_handler import handle_large_prompt

def test_small_prompt():
    """Test normal handling of small prompts."""
    print("🧪 Testing small prompt...")
    
    small_prompt = "Analyze this code: print('hello')"
    result = handle_large_prompt(small_prompt)
    
    assert result["status"] == "normal_mode"
    assert result["content"] == small_prompt
    assert result["character_count"] == len(small_prompt)
    
    print(f"✅ Small prompt handled normally: {result['character_count']} chars")

def test_large_prompt():
    """Test file mode request for large prompts."""
    print("🧪 Testing large prompt...")
    
    # Create a large prompt (>50K chars)
    large_prompt = "x" * 60000  # 60K characters
    result = handle_large_prompt(large_prompt)
    
    assert result["status"] == "prompt_too_large"
    assert result["character_count"] == 60000
    assert result["limit"] == 50000
    assert "save the prompt text to a temporary file" in result["message"]
    
    print(f"✅ Large prompt triggers file mode: {result['character_count']} chars")

def test_file_mode():
    """Test actual file reading."""
    print("🧪 Testing file mode...")
    
    # Create a temporary file with content
    with tempfile.NamedTemporaryFile(mode='w', suffix='_prompt.txt', delete=False) as f:
        test_content = "This is file content for testing"
        f.write(test_content)
        temp_path = f.name
    
    try:
        # Test file mode
        result = handle_large_prompt("", files=[temp_path])
        
        assert result["status"] == "file_mode_success"
        assert result["content"] == test_content
        assert result["source"] == temp_path
        assert result["character_count"] == len(test_content)
        
        print(f"✅ File mode works: loaded {result['character_count']} chars from file")
        
    finally:
        # Clean up
        os.unlink(temp_path)

def test_missing_file():
    """Test handling of missing files."""
    print("🧪 Testing missing file...")
    
    result = handle_large_prompt("fallback prompt", files=["/nonexistent/prompt.txt"])
    
    # Should fall back to normal mode since file doesn't exist
    assert result["status"] == "normal_mode"
    assert result["content"] == "fallback prompt"
    
    print("✅ Missing file falls back to normal mode")

def main():
    """Run all tests."""
    print("🚀 Testing Zen-style Large Prompt Handler")
    print("=" * 50)
    
    tests = [
        test_small_prompt,
        test_large_prompt,
        test_file_mode,
        test_missing_file
    ]
    
    for test_func in tests:
        try:
            test_func()
        except Exception as e:
            print(f"❌ Test failed: {test_func.__name__}")
            print(f"   Error: {e}")
            return False
    
    print("\n" + "=" * 50)
    print("🎉 All tests passed! Zen-style handler is working.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)