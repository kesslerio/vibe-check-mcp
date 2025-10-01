"""
Session lifecycle management.

Handles creation, storage, and cleanup of collaborative reasoning sessions.
"""

import logging
import secrets
from datetime import datetime
from typing import Dict, List, Optional

from vibe_check.mentor.models.config import DEFAULT_MAX_SESSIONS, DEFAULT_PERSONAS, SESSION_TIMESTAMP_FORMAT
from vibe_check.mentor.models.persona import PersonaData
from vibe_check.mentor.models.session import CollaborativeReasoningSession

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages the lifecycle of collaborative reasoning sessions"""
    
    def __init__(self):
        self.sessions: Dict[str, CollaborativeReasoningSession] = {}
    
    def create_session(
        self,
        topic: str,
        personas: Optional[List[PersonaData]] = None,
        session_id: Optional[str] = None,
    ) -> CollaborativeReasoningSession:
        """Initialize a new collaborative reasoning session"""
        
        # Input validation
        if not topic or not topic.strip():
            raise ValueError("Topic cannot be empty")
        
        if personas is not None and not personas:
            raise ValueError("Personas list cannot be empty if provided")
        
        try:
            session_id = session_id or SESSION_TIMESTAMP_FORMAT.format(
                timestamp=int(datetime.now().timestamp()),
                token=secrets.token_hex(4)
            )
            # Log session creation for debugging correlation
            logger.info(f"Creating mentor session {session_id} for topic: {topic[:100]}")

            session = CollaborativeReasoningSession(
                topic=topic,
                personas=personas or DEFAULT_PERSONAS,
                contributions=[],
                stage="problem-definition",
                active_persona_id=DEFAULT_PERSONAS[0].id,
                session_id=session_id,
                iteration=0,
                suggested_contribution_types=["observation", "question"],
            )

            self.sessions[session_id] = session
            return session
        except Exception as e:
            logger.error(f"Failed to create session for topic '{topic[:50]}': {str(e)}")
            raise RuntimeError(f"Session creation failed: {str(e)}") from e
    
    def get_session(self, session_id: str) -> Optional[CollaborativeReasoningSession]:
        """Retrieve a session by ID"""
        return self.sessions.get(session_id)
    
    def cleanup_old_sessions(self, max_sessions: int = DEFAULT_MAX_SESSIONS) -> None:
        """
        Clean up old sessions to prevent memory leaks.
        
        Args:
            max_sessions: Maximum number of sessions to keep in memory
        """
        if len(self.sessions) > max_sessions:
            # Sort sessions by last update time and keep the most recent
            sorted_sessions = sorted(
                self.sessions.items(),
                key=lambda x: x[1].iteration,  # Use iteration as proxy for recency
                reverse=True
            )
            
            # Keep only the most recent sessions
            sessions_to_keep = dict(sorted_sessions[:max_sessions])
            removed_count = len(self.sessions) - len(sessions_to_keep)
            
            self.sessions = sessions_to_keep
            logger.info(f"Cleaned up {removed_count} old mentor sessions")
    
    def list_sessions(self) -> List[str]:
        """Get list of active session IDs"""
        return list(self.sessions.keys())
    
    def remove_session(self, session_id: str) -> bool:
        """Remove a specific session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Removed mentor session {session_id}")
            return True
        return False