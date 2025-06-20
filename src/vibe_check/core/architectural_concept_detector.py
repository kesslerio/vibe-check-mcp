"""
Architectural Concept Detection for Issue Analysis

This module implements minimal viable architecture-aware analysis by detecting
architectural concepts (auth, payment, database, etc.) in natural language
and mapping them to relevant code search terms.

Following the MVP approach from vibe mentor feedback - simple detection first,
then iterate based on real user feedback.
"""

import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass


@dataclass
class ArchitecturalConcept:
    """Detected architectural concept with search guidance"""
    concept_name: str
    confidence: float
    keywords_found: List[str]
    search_terms: List[str]
    file_patterns: List[str]
    common_files: List[str]


@dataclass
class ConceptDetectionResult:
    """Result of architectural concept detection"""
    detected_concepts: List[ArchitecturalConcept]
    original_text: str
    search_recommendations: List[str]
    github_search_queries: List[str]


class ArchitecturalConceptDetector:
    """
    Minimal viable architectural concept detector.
    
    Detects architectural concepts like "authentication system", "payment processing"
    from natural language and provides search guidance for finding relevant code.
    
    This is the MVP implementation focusing on the 5 most common architectural
    areas based on the issue analysis requirements.
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize with architectural concept definitions"""
        if config_file is None:
            config_path = Path(__file__).parent.parent / "config" / "tech_patterns.yaml"
        else:
            config_path = Path(config_file)
        
        with open(config_path) as f:
            config = yaml.safe_load(f)
        
        # Extract architectural concepts from config
        self.concepts = config.get("architectural_concepts", {})
        
        # Minimum confidence threshold for detection
        self.min_confidence = 0.3
    
    def detect_concepts(
        self, 
        text: str, 
        context: Optional[str] = None
    ) -> ConceptDetectionResult:
        """
        Detect architectural concepts in text and provide search guidance.
        
        Args:
            text: Primary text to analyze (e.g., issue description)
            context: Additional context (e.g., issue title)
            
        Returns:
            ConceptDetectionResult with detected concepts and search guidance
        """
        # Combine text and context
        full_text = f"{text} {context or ''}"
        text_lower = full_text.lower()
        
        detected_concepts = []
        all_search_terms = []
        all_github_queries = []
        
        # Check each architectural concept
        for concept_name, concept_config in self.concepts.items():
            keywords = concept_config.get("keywords", [])
            keywords_found = []
            
            # Find matching keywords
            for keyword in keywords:
                # Use flexible matching - keyword can be part of a larger word
                if keyword.lower() in text_lower:
                    keywords_found.append(keyword)
            
            # Calculate confidence based on keyword matches
            if keywords_found:
                # Use a more generous confidence calculation
                # Give higher weight to having any matches at all
                base_confidence = 0.4  # Base confidence for any match
                match_bonus = min(len(keywords_found) * 0.2, 0.6)  # Up to 0.6 for multiple matches
                confidence = min(base_confidence + match_bonus, 1.0)
                
                # Apply minimum confidence threshold
                if confidence >= self.min_confidence:
                    concept = ArchitecturalConcept(
                        concept_name=concept_name,
                        confidence=confidence,
                        keywords_found=keywords_found,
                        search_terms=concept_config.get("search_terms", []),
                        file_patterns=concept_config.get("file_patterns", []),
                        common_files=concept_config.get("common_files", [])
                    )
                    detected_concepts.append(concept)
                    
                    # Add search recommendations
                    all_search_terms.extend(concept.search_terms)
                    
                    # Generate GitHub search queries
                    for search_term in concept.search_terms:
                        all_github_queries.append(search_term)
        
        return ConceptDetectionResult(
            detected_concepts=detected_concepts,
            original_text=full_text,
            search_recommendations=list(set(all_search_terms)),
            github_search_queries=list(set(all_github_queries))
        )
    
    def get_file_discovery_guidance(
        self, 
        concept: ArchitecturalConcept,
        repository: str = ""
    ) -> Dict[str, Any]:
        """
        Get specific guidance for finding files related to architectural concept.
        
        Args:
            concept: Detected architectural concept
            repository: Repository name for scoped search
            
        Returns:
            Dictionary with file discovery guidance
        """
        guidance = {
            "concept": concept.concept_name,
            "confidence": concept.confidence,
            "search_strategy": {
                "file_patterns": concept.file_patterns,
                "common_files": concept.common_files,
                "search_terms": concept.search_terms
            },
            "github_search_queries": []
        }
        
        # Generate specific GitHub search queries
        for search_term in concept.search_terms:
            if repository:
                query = f"repo:{repository} {search_term}"
            else:
                query = search_term
            guidance["github_search_queries"].append(query)
        
        # Add file pattern searches
        for pattern in concept.file_patterns:
            if repository:
                query = f"repo:{repository} path:{pattern}"
            else:
                query = f"path:{pattern}"
            guidance["github_search_queries"].append(query)
        
        return guidance
    
    def generate_analysis_context(
        self, 
        detection_result: ConceptDetectionResult
    ) -> Dict[str, Any]:
        """
        Generate analysis context for issue analysis based on detected concepts.
        
        This provides structured guidance for the issue analyzer to understand
        what architectural areas to focus on.
        
        Args:
            detection_result: Result from concept detection
            
        Returns:
            Analysis context with architectural guidance
        """
        if not detection_result.detected_concepts:
            return {
                "architectural_focus": None,
                "search_guidance": [],
                "analysis_mode": "general"
            }
        
        # Sort concepts by confidence
        concepts_by_confidence = sorted(
            detection_result.detected_concepts,
            key=lambda x: x.confidence,
            reverse=True
        )
        
        primary_concept = concepts_by_confidence[0]
        
        return {
            "architectural_focus": primary_concept.concept_name,
            "primary_concept": {
                "name": primary_concept.concept_name,
                "confidence": primary_concept.confidence,
                "keywords_found": primary_concept.keywords_found
            },
            "all_detected_concepts": [
                {
                    "name": concept.concept_name,
                    "confidence": concept.confidence,
                    "keywords": concept.keywords_found
                }
                for concept in concepts_by_confidence
            ],
            "search_guidance": {
                "recommended_queries": detection_result.github_search_queries,
                "file_patterns": primary_concept.file_patterns,
                "common_files": primary_concept.common_files
            },
            "analysis_mode": "architecture_aware",
            "recommendations": self._get_concept_specific_recommendations(primary_concept)
        }
    
    def _get_concept_specific_recommendations(
        self, 
        concept: ArchitecturalConcept
    ) -> List[str]:
        """Get concept-specific analysis recommendations"""
        recommendations = {
            "authentication": [
                "Check JWT token validation performance",
                "Review session management implementation",
                "Analyze password hashing and comparison",
                "Examine OAuth integration patterns",
                "Validate middleware authentication flow"
            ],
            "payment": [
                "Review payment provider integration (Stripe, PayPal)",
                "Check webhook signature validation",
                "Analyze transaction state management",
                "Examine error handling and retry logic",
                "Validate PCI compliance patterns"
            ],
            "api": [
                "Review API route structure and organization",
                "Check request validation and middleware",
                "Analyze rate limiting implementation",
                "Examine error handling and responses",
                "Validate API documentation alignment"
            ],
            "database": [
                "Check database connection and pooling",
                "Review query optimization and indexes",
                "Analyze migration and schema management",
                "Examine ORM usage patterns",
                "Validate transaction handling"
            ],
            "caching": [
                "Review cache key generation and invalidation",
                "Check Redis/memory cache configuration",
                "Analyze cache hit/miss patterns",
                "Examine TTL and expiration strategies",
                "Validate cache consistency patterns"
            ]
        }
        
        return recommendations.get(concept.concept_name, [
            "Review system architecture and design patterns",
            "Check for common anti-patterns in implementation",
            "Analyze component integration and dependencies"
        ])
    
    def get_supported_concepts(self) -> List[str]:
        """Get list of supported architectural concepts"""
        return list(self.concepts.keys())
    
    def get_concept_info(self, concept_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific concept"""
        if concept_name not in self.concepts:
            return None
        
        config = self.concepts[concept_name]
        return {
            "name": concept_name,
            "keywords": config.get("keywords", []),
            "file_patterns": config.get("file_patterns", []),
            "common_files": config.get("common_files", []),
            "search_terms": config.get("search_terms", [])
        }