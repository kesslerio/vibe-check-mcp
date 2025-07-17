#!/usr/bin/env python3
"""
Quick import test to validate refactoring didn't break imports.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

def test_vibe_mentor_imports():
    """Test that main vibe_mentor imports work correctly"""
    try:
        from vibe_check.tools.vibe_mentor import (
            VibeMentorEngine, 
            get_mentor_engine, 
            _generate_summary
        )
        print("✅ Main vibe_mentor imports successful")
        return True
    except ImportError as e:
        print(f"❌ Main vibe_mentor import failed: {e}")
        return False

def test_modular_imports():
    """Test that new modular imports work correctly"""
    try:
        # Test model imports
        from vibe_check.mentor.models.persona import PersonaData
        from vibe_check.mentor.models.session import CollaborativeReasoningSession, ContributionData
        from vibe_check.mentor.models.config import ConfidenceScores, DEFAULT_PERSONAS
        print("✅ Model imports successful")
        
        # Test session management imports
        from vibe_check.mentor.session.manager import SessionManager
        from vibe_check.mentor.session.state_tracker import StateTracker
        from vibe_check.mentor.session.synthesis import SessionSynthesizer
        print("✅ Session management imports successful")
        
        # Test response generation imports  
        from vibe_check.mentor.response.coordinator import ResponseCoordinator
        from vibe_check.mentor.response.formatters.console import ConsoleFormatter
        print("✅ Response generation imports successful")
        
        # Test pattern handler imports
        from vibe_check.mentor.patterns.handlers.infrastructure import InfrastructurePatternHandler
        print("✅ Pattern handler imports successful")
        
        return True
    except ImportError as e:
        print(f"❌ Modular import failed: {e}")
        return False

def test_functionality():
    """Test basic functionality works"""
    try:
        from vibe_check.tools.vibe_mentor import get_mentor_engine
        
        # Test engine creation
        engine = get_mentor_engine()
        print("✅ Engine creation successful")
        
        # Test session creation
        session = engine.create_session("Test refactoring")
        print("✅ Session creation successful")
        
        # Test that session has expected attributes
        assert hasattr(session, 'topic')
        assert hasattr(session, 'personas')
        assert hasattr(session, 'contributions')
        print("✅ Session structure validation successful")
        
        return True
    except Exception as e:
        print(f"❌ Functionality test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testing refactored vibe_mentor imports and functionality...")
    
    success = True
    success &= test_vibe_mentor_imports()
    success &= test_modular_imports() 
    success &= test_functionality()
    
    if success:
        print("\n🎉 All tests passed! Refactoring successful.")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed. Check imports and implementation.")
        sys.exit(1)