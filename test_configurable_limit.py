#!/usr/bin/env python3
"""
Integration test for configurable character limit functionality.
Tests environment variable configuration for VIBE_CHECK_CHARACTER_LIMIT.
"""

import os
import sys
import tempfile

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_default_limit():
    """Test default 50K character limit."""
    print("🧪 Testing default character limit...")
    
    # Import fresh to avoid cached handler
    from vibe_check.tools.large_prompt_handler import LargePromptHandler
    
    handler = LargePromptHandler()
    assert handler.character_limit == 50000, f"Expected default limit 50000, got {handler.character_limit}"
    
    # Test with content just under limit
    small_content = "x" * 49999
    assert not handler.should_use_file_mode(small_content), "Should not use file mode for content under limit"
    
    # Test with content over limit
    large_content = "x" * 50001
    assert handler.should_use_file_mode(large_content), "Should use file mode for content over limit"
    
    print(f"✅ Default limit: {handler.character_limit:,} chars working correctly")

def test_custom_limit_via_env():
    """Test custom character limit via environment variable."""
    print("🧪 Testing custom character limit via environment variable...")
    
    # Set custom limit
    original_env = os.environ.get('VIBE_CHECK_CHARACTER_LIMIT')
    os.environ['VIBE_CHECK_CHARACTER_LIMIT'] = '25000'
    
    try:
        # Force reload of module to pick up new env var
        import importlib
        import vibe_check.tools.large_prompt_handler
        importlib.reload(vibe_check.tools.large_prompt_handler)
        
        from vibe_check.tools.large_prompt_handler import LargePromptHandler
        
        handler = LargePromptHandler()
        assert handler.character_limit == 25000, f"Expected custom limit 25000, got {handler.character_limit}"
        
        # Test with content just under custom limit
        small_content = "x" * 24999
        assert not handler.should_use_file_mode(small_content), "Should not use file mode for content under custom limit"
        
        # Test with content over custom limit but under default
        medium_content = "x" * 30000
        assert handler.should_use_file_mode(medium_content), "Should use file mode for content over custom limit"
        
        print(f"✅ Custom limit: {handler.character_limit:,} chars working correctly")
        
    finally:
        # Restore original environment
        if original_env is not None:
            os.environ['VIBE_CHECK_CHARACTER_LIMIT'] = original_env
        else:
            os.environ.pop('VIBE_CHECK_CHARACTER_LIMIT', None)

def test_flexible_file_detection():
    """Test more flexible file detection patterns."""
    print("🧪 Testing flexible file detection...")
    
    # Reset environment and reload
    os.environ.pop('VIBE_CHECK_CHARACTER_LIMIT', None)
    import importlib
    import vibe_check.tools.large_prompt_handler
    importlib.reload(vibe_check.tools.large_prompt_handler)
    
    from vibe_check.tools.large_prompt_handler import handle_large_prompt
    
    test_content = "This is test content for flexible file detection"
    test_files = [
        # Traditional prompt file
        "/tmp/prompt.txt",
        # Content-related files
        "/tmp/content.txt", 
        "/tmp/analysis_input.txt",
        "/tmp/text_data.txt",
        # Any .txt file
        "/tmp/random_file.txt"
    ]
    
    for file_path in test_files:
        # Create temporary file
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as f:
            f.write(test_content)
        
        try:
            # Test file detection
            result = handle_large_prompt("", files=[file_path])
            
            assert result["status"] == "file_mode_success", f"Should detect file {file_path}"
            assert result["content"] == test_content, f"Should read correct content from {file_path}"
            assert result["source"] == file_path, f"Should report correct source {file_path}"
            
            print(f"✅ File detected: {os.path.basename(file_path)}")
            
        finally:
            # Clean up
            if os.path.exists(file_path):
                os.unlink(file_path)

def main():
    """Run configurable limit integration tests."""
    print("🚀 Testing Configurable Character Limit")
    print("=" * 50)
    
    tests = [
        test_default_limit,
        test_custom_limit_via_env,
        test_flexible_file_detection
    ]
    
    for test_func in tests:
        try:
            test_func()
        except Exception as e:
            print(f"❌ Test failed: {test_func.__name__}")
            print(f"   Error: {e}")
            return False
    
    print("\n" + "=" * 50)
    print("🎉 All configurable limit tests passed!")
    print("\n📋 Summary:")
    print("- ✅ Default 50K character limit works correctly")
    print("- ✅ Custom limit via VIBE_CHECK_CHARACTER_LIMIT environment variable")
    print("- ✅ Flexible file detection for multiple filename patterns")
    print("- ✅ Support for .txt files and content-related filenames")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)