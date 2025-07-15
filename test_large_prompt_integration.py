#!/usr/bin/env python3
"""
Integration test for the Zen-style large prompt handling.
Tests the actual demo_large_prompt_analysis function.
"""

import os
import sys
import tempfile

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from vibe_check.tools.large_prompt_demo import demo_large_prompt_analysis

def test_small_content():
    """Test normal processing of small content."""
    print("🧪 Testing small content...")
    
    small_content = "Analyze this small piece of code: print('hello world')"
    result = demo_large_prompt_analysis(small_content)
    
    assert result["success"] == True
    assert result["mode"] == "normal_processing"
    print(f"✅ Small content: {result['character_count']} chars processed normally")

def test_large_content():
    """Test file mode request for large content."""
    print("🧪 Testing large content (>50K chars)...")
    
    # Create content larger than 50K characters
    large_content = "x" * 60000  # 60K characters
    result = demo_large_prompt_analysis(large_content)
    
    print(f"   Result keys: {list(result.keys())}")
    print(f"   Success: {result.get('success')}")
    print(f"   Mode: {result.get('mode')}")
    
    assert result["success"] == True, f"Expected success=True, got {result.get('success')}"
    assert result["mode"] == "file_mode_requested", f"Expected mode=file_mode_requested, got {result.get('mode')}"
    assert result["character_count"] == 60000, f"Expected count=60000, got {result.get('character_count')}"
    assert result["limit"] == 50000, f"Expected limit=50000, got {result.get('limit')}"
    assert "save the prompt text to a temporary file" in result["message"], f"Message missing expected text: {result.get('message', '')[:100]}"
    
    print(f"✅ Large content: {result['character_count']} chars triggers file mode")
    print(f"   Message: {result['message'][:100]}...")

def test_file_mode_processing():
    """Test actual file processing."""
    print("🧪 Testing file mode processing...")
    
    # Create a temporary file
    test_content = "This is large content loaded from a file for testing the Zen-style approach"
    with tempfile.NamedTemporaryFile(mode='w', suffix='_prompt.txt', delete=False) as f:
        f.write(test_content)
        temp_path = f.name
    
    try:
        # Test processing with file
        result = demo_large_prompt_analysis("", files=[temp_path])
        
        assert result["success"] == True
        assert result["mode"] == "file_mode_processing"
        assert result["source_file"] == temp_path
        assert result["character_count"] == len(test_content)
        assert "zen_style_benefits" in result
        
        print(f"✅ File mode: loaded {result['character_count']} chars from file")
        print(f"   Benefits: {len(result['zen_style_benefits'])} listed")
        
    finally:
        # Clean up
        os.unlink(temp_path)

def main():
    """Run integration tests."""
    print("🚀 Testing Zen-style Large Prompt Integration")
    print("=" * 50)
    
    tests = [
        test_small_content,
        test_large_content,
        test_file_mode_processing
    ]
    
    for test_func in tests:
        try:
            test_func()
        except Exception as e:
            print(f"❌ Integration test failed: {test_func.__name__}")
            print(f"   Error: {e}")
            return False
    
    print("\n" + "=" * 50)
    print("🎉 All integration tests passed!")
    print("\n📋 Summary:")
    print("- ✅ Small content processes normally")
    print("- ✅ Large content triggers file mode request")
    print("- ✅ File mode successfully loads and processes content")
    print("- ✅ Simple implementation works as designed")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)