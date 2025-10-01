"""
Console output formatter for collaborative reasoning sessions.

Provides ANSI-colored terminal output for session display.
"""

from vibe_check.mentor.models.session import CollaborativeReasoningSession


class ConsoleFormatter:
    """Formats collaborative reasoning sessions for console display"""
    
    # ANSI color codes
    BLUE = "\033[34m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    BOLD = "\033[1m"
    RESET = "\033[0m"
    
    @classmethod
    def format_session_output(cls, session: CollaborativeReasoningSession) -> str:
        """
        Format session for display - inspired by Clear-Thought's chalk formatting.
        Using ANSI codes for terminal colors.
        """

        output = f"\n{cls.BOLD}{cls.BLUE}🧠 Collaborative Reasoning Session{cls.RESET}\n"
        output += f"{cls.BOLD}{cls.GREEN}Topic:{cls.RESET} {session.topic}\n"
        output += f"{cls.BOLD}{cls.YELLOW}Stage:{cls.RESET} {session.stage} (Iteration: {session.iteration})\n"

        # Active persona
        active_persona = next(
            (p for p in session.personas if p.id == session.active_persona_id), None
        )
        if active_persona:
            output += f"\n{cls.BOLD}{cls.MAGENTA}Active Persona:{cls.RESET} {active_persona.name}\n"
            output += (
                f"{cls.BOLD}{cls.CYAN}Expertise:{cls.RESET} {', '.join(active_persona.expertise)}\n"
            )
            output += f"{cls.BOLD}{cls.CYAN}Perspective:{cls.RESET} {active_persona.perspective}\n"

        # Contributions
        if session.contributions:
            output += f"\n{cls.BOLD}{cls.GREEN}Contributions:{cls.RESET}\n"
            for contrib in session.contributions:
                persona = next(
                    (p for p in session.personas if p.id == contrib.persona_id), None
                )
                persona_name = persona.name if persona else contrib.persona_id

                output += f"\n{cls.BOLD}{persona_name} ({contrib.type}, confidence: {contrib.confidence:.2f}):{cls.RESET}\n"
                output += f"{contrib.content}\n"

        # Consensus points
        if session.consensus_points:
            output += f"\n{cls.BOLD}{cls.GREEN}Consensus Points:{cls.RESET}\n"
            for i, point in enumerate(session.consensus_points, 1):
                output += f"{cls.BOLD}{i}.{cls.RESET} {point}\n"

        # Key insights
        if session.key_insights:
            output += f"\n{cls.BOLD}{cls.YELLOW}Key Insights:{cls.RESET}\n"
            for i, insight in enumerate(session.key_insights, 1):
                output += f"{cls.BOLD}{i}.{cls.RESET} {insight}\n"

        # Final recommendation
        if session.final_recommendation:
            output += f"\n{cls.BOLD}{cls.CYAN}Final Recommendation:{cls.RESET}\n"
            output += f"{session.final_recommendation}\n"

        return output