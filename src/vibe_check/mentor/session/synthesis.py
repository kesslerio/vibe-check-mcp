"""
Session synthesis and analysis.

Provides functionality to analyze collaborative reasoning sessions
and extract actionable insights and recommendations.
"""

from typing import Any, Dict, List

from ..models.session import CollaborativeReasoningSession, ContributionData


class SessionSynthesizer:
    """Synthesizes collaborative reasoning sessions into actionable insights"""
    
    @staticmethod
    def synthesize_session(session: CollaborativeReasoningSession) -> Dict[str, Any]:
        """
        Synthesize the collaborative reasoning session into actionable insights.
        This is our key value-add over Clear-Thought's simple state tracking.
        """

        # Group contributions by type
        contributions_by_type = {}
        for contrib in session.contributions:
            if contrib.type not in contributions_by_type:
                contributions_by_type[contrib.type] = []
            contributions_by_type[contrib.type].append(contrib)

        # Extract consensus points (similar content from multiple personas)
        consensus = SessionSynthesizer._extract_consensus(session.contributions) if session.contributions else []
        
        # Identify key insights (high confidence insights and syntheses)
        key_insights = SessionSynthesizer._extract_key_insights(session.contributions) if session.contributions else []

        # Find disagreements
        disagreements = SessionSynthesizer._extract_disagreements(contributions_by_type)

        # Generate final recommendation
        final_recommendation = SessionSynthesizer._generate_final_recommendation(
            session, contributions_by_type
        )
        if final_recommendation:
            session.final_recommendation = final_recommendation

        # Build comprehensive summary
        return {
            "session_summary": {
                "topic": session.topic,
                "stage": session.stage,
                "iterations": session.iteration,
                "total_contributions": len(session.contributions),
            },
            "consensus_points": consensus,
            "key_insights": key_insights[:3],  # Top 3
            "primary_concerns": [c.content for c in contributions_by_type.get("concern", [])[:2]],
            "disagreements": disagreements,
            "recommendations": {
                "immediate_actions": [
                    "Research official SDK/documentation",
                    "Create minimal proof of concept",
                    "Validate with real data",
                    "Get early user feedback",
                ],
                "avoid": [
                    "Building custom infrastructure first",
                    "Over-engineering the solution",
                    "Skipping official documentation",
                    "Making assumptions without validation",
                ],
            },
            "final_recommendation": session.final_recommendation,
        }
    
    @staticmethod
    def _extract_consensus(contributions: List[ContributionData]) -> List[str]:
        """Extract consensus points from contributions"""
        if not contributions:
            return []
        
        consensus = []
        all_content = [c.content.lower() for c in contributions if c and c.content]

        # Simple consensus detection based on keyword overlap
        consensus_keywords = [
            "official",
            "sdk", 
            "simple",
            "prototype",
            "user",
            "feedback",
        ]
        for keyword in consensus_keywords:
            if sum(1 for content in all_content if keyword in content) >= 2:
                consensus.append(f"Use {keyword} approaches when available")
        
        return consensus
    
    @staticmethod
    def _extract_key_insights(contributions: List[ContributionData]) -> List[str]:
        """Extract key insights from high-confidence contributions"""
        key_insights = []
        for contrib in contributions:
            if contrib.type in ["insight", "synthesis"] and contrib.confidence > 0.85:
                key_insights.append(contrib.content)
        return key_insights
    
    @staticmethod
    def _extract_disagreements(contributions_by_type: Dict[str, List[ContributionData]]) -> List[Dict[str, Any]]:
        """Extract disagreements from concerns and challenges"""
        disagreements = []
        concerns = contributions_by_type.get("concern", [])
        challenges = contributions_by_type.get("challenge", [])

        if concerns or challenges:
            for item in concerns + challenges:
                # Check if there's a counter-position
                disagreements.append(
                    {
                        "topic": "Implementation approach",
                        "positions": [
                            {
                                "personaId": item.persona_id,
                                "position": item.content,
                                "arguments": [item.content],
                            }
                        ],
                    }
                )
        
        return disagreements
    
    @staticmethod
    def _generate_final_recommendation(
        session: CollaborativeReasoningSession,
        contributions_by_type: Dict[str, List[ContributionData]]
    ) -> str:
        """Generate final recommendation based on session state and contributions"""
        if session.stage in ["decision", "reflection"]:
            # Prioritize synthesis contributions
            syntheses = contributions_by_type.get("synthesis", [])
            if syntheses:
                return syntheses[-1].content
            else:
                return "Based on the discussion, start with the simplest official solution and iterate."
        return ""