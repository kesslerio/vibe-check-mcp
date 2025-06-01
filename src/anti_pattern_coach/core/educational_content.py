"""
Educational Content Generation System

This module provides comprehensive educational content for anti-pattern detection,
explaining WHY patterns are problematic and HOW to fix them using real-world case studies.

Phase 1.2 enhancement: Dedicated educational content system with multiple detail levels.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum


class DetailLevel(Enum):
    """Educational content detail levels"""
    BRIEF = "brief"
    STANDARD = "standard" 
    COMPREHENSIVE = "comprehensive"


@dataclass
class CaseStudy:
    """Case study data structure"""
    title: str
    pattern_type: str
    timeline: str
    outcome: str
    impact: Dict[str, str]
    root_cause: str
    lesson: str
    prevention_checklist: List[str]


@dataclass
class EducationalResponse:
    """Comprehensive educational response"""
    pattern_name: str
    pattern_type: str
    severity: str
    confidence: float
    
    # Core educational content
    why_problematic: str
    impact_explanation: str
    evidence_explanation: str
    
    # Remediation guidance
    immediate_actions: List[str]
    remediation_steps: List[str]
    prevention_checklist: List[str]
    
    # Case studies and examples
    case_study: Optional[CaseStudy]
    related_examples: List[str]
    
    # Additional resources
    learning_resources: List[str]
    best_practices: List[str]
    
    # Metadata
    detail_level: DetailLevel
    response_time: Optional[float] = None


class EducationalContentGenerator:
    """
    Dedicated educational content generation system for anti-pattern coaching.
    
    This class separates educational concerns from detection logic and provides
    comprehensive, multi-level educational responses with real-world case studies.
    """
    
    def __init__(
        self, 
        patterns_file: Optional[str] = None,
        case_studies_file: Optional[str] = None,
        default_detail_level: DetailLevel = DetailLevel.STANDARD
    ):
        """Initialize educational content generator"""
        
        self.default_detail_level = default_detail_level
        
        # Load pattern definitions
        if patterns_file is None:
            patterns_file = Path(__file__).parent.parent.parent.parent / "data" / "anti_patterns.json"
        
        with open(patterns_file) as f:
            self.patterns = json.load(f)
        
        # Load case studies
        if case_studies_file is None:
            case_studies_file = Path(__file__).parent.parent.parent.parent / "data" / "cognee_case_study.json"
        
        with open(case_studies_file) as f:
            case_study_data = json.load(f)
            self.case_studies = self._parse_case_studies(case_study_data)
        
        # Load additional educational content
        self._load_educational_extensions()
    
    def generate_educational_response(
        self,
        pattern_type: str,
        confidence: float,
        evidence: List[str],
        detail_level: Optional[DetailLevel] = None
    ) -> EducationalResponse:
        """
        Generate comprehensive educational response for detected anti-pattern.
        
        Args:
            pattern_type: Type of anti-pattern detected
            confidence: Detection confidence score (0.0-1.0)
            evidence: List of evidence that triggered detection
            detail_level: Level of detail to include in response
            
        Returns:
            Comprehensive educational response with explanations and guidance
        """
        if detail_level is None:
            detail_level = self.default_detail_level
        
        pattern_config = self.patterns.get(pattern_type)
        if not pattern_config:
            raise ValueError(f"Unknown pattern type: {pattern_type}")
        
        # Generate core educational content
        why_problematic = self._generate_why_explanation(pattern_type, detail_level)
        impact_explanation = self._generate_impact_explanation(pattern_type, confidence, detail_level)
        evidence_explanation = self._generate_evidence_explanation(evidence, pattern_type, detail_level)
        
        # Generate remediation guidance
        immediate_actions = self._get_immediate_actions(pattern_type, detail_level)
        remediation_steps = self._get_remediation_steps(pattern_type, detail_level)
        prevention_checklist = self._get_prevention_checklist(pattern_type, detail_level)
        
        # Get case study and examples
        case_study = self._get_case_study(pattern_type)
        related_examples = self._get_related_examples(pattern_type, detail_level)
        
        # Additional educational resources
        learning_resources = self._get_learning_resources(pattern_type, detail_level)
        best_practices = self._get_best_practices(pattern_type, detail_level)
        
        return EducationalResponse(
            pattern_name=pattern_config["name"],
            pattern_type=pattern_type,
            severity=pattern_config["severity"],
            confidence=confidence,
            why_problematic=why_problematic,
            impact_explanation=impact_explanation,
            evidence_explanation=evidence_explanation,
            immediate_actions=immediate_actions,
            remediation_steps=remediation_steps,
            prevention_checklist=prevention_checklist,
            case_study=case_study,
            related_examples=related_examples,
            learning_resources=learning_resources,
            best_practices=best_practices,
            detail_level=detail_level
        )
    
    def _generate_why_explanation(self, pattern_type: str, detail_level: DetailLevel) -> str:
        """Generate WHY explanation based on detail level"""
        
        base_explanations = {
            "infrastructure_without_implementation": {
                "brief": "Building custom solutions before testing standard APIs leads to technical debt.",
                "standard": (
                    "Building custom infrastructure before testing standard approaches leads to "
                    "massive technical debt. The Cognee integration failure resulted in 2+ years "
                    "of zero functionality despite significant engineering investment."
                ),
                "comprehensive": (
                    "The Infrastructure-Without-Implementation anti-pattern occurs when development "
                    "teams build custom solutions before thoroughly testing and validating standard "
                    "APIs, SDKs, or established approaches. This pattern is particularly dangerous "
                    "because it often appears rational in the moment - teams believe they need "
                    "\"more control\" or assume standard solutions \"won't work for our use case.\"\n\n"
                    "The Cognee integration serves as a perfect case study: despite 2+ years of "
                    "engineering effort building custom HTTP servers and vector processing pipelines, "
                    "the team achieved zero working functionality. The standard approach "
                    "(cognee.add() → cognee.cognify() → cognee.search()) would have provided "
                    "working vector search in under a week.\n\n"
                    "This pattern compounds because custom infrastructure requires ongoing "
                    "maintenance, debugging, and feature development that standard solutions "
                    "provide out-of-the-box. Teams become trapped supporting their custom "
                    "implementation while missing updates and improvements to standard solutions."
                )
            },
            "symptom_driven_development": {
                "brief": "Treating symptoms instead of root causes creates accumulating technical debt.",
                "standard": (
                    "Addressing symptoms instead of root causes creates accumulating technical debt. "
                    "Quick fixes and workarounds multiply over time, making systems increasingly "
                    "fragile and difficult to maintain."
                ),
                "comprehensive": (
                    "Symptom-Driven Development occurs when teams repeatedly apply quick fixes to "
                    "surface problems without investigating or addressing underlying root causes. "
                    "While individual fixes may seem reasonable under time pressure, this pattern "
                    "creates a cascade of technical debt that compounds exponentially.\n\n"
                    "Each symptom fix typically introduces new edge cases, dependencies, or "
                    "behavioral quirks that require additional fixes. Over time, the system "
                    "becomes a brittle collection of patches where changes in one area "
                    "unpredictably break functionality elsewhere.\n\n"
                    "The hidden cost is enormous: teams spend increasing amounts of time "
                    "maintaining and debugging symptom fixes rather than building new features. "
                    "Root cause analysis, while initially time-consuming, pays exponential "
                    "dividends by solving entire classes of problems at once."
                )
            },
            "complexity_escalation": {
                "brief": "Adding unnecessary complexity makes systems difficult to maintain and debug.",
                "standard": (
                    "Adding complexity without questioning necessity leads to over-engineered solutions "
                    "that are difficult to maintain, debug, and extend. Simple problems get buried "
                    "under layers of unnecessary abstraction."
                ),
                "comprehensive": (
                    "Complexity Escalation occurs when teams add architectural complexity without "
                    "demonstrating clear necessity or exhausting simpler alternatives. This pattern "
                    "often stems from premature optimization, over-engineering for imagined future "
                    "requirements, or applying enterprise patterns to simple problems.\n\n"
                    "Complex systems have exponentially higher maintenance costs, debugging "
                    "difficulty, and onboarding time for new team members. Each layer of "
                    "abstraction introduces potential failure points and makes system behavior "
                    "harder to predict and understand.\n\n"
                    "The most successful systems start simple and add complexity incrementally "
                    "only when specific requirements demand it. This approach allows teams to "
                    "validate that complexity provides measurable value rather than theoretical "
                    "benefits that may never materialize."
                )
            },
            "documentation_neglect": {
                "brief": "Skipping documentation research often leads to reinventing existing solutions poorly.",
                "standard": (
                    "Building solutions without researching standard approaches often leads to "
                    "reinventing existing solutions poorly. Documentation research prevents "
                    "unnecessary custom development and reveals proven approaches."
                ),
                "comprehensive": (
                    "Documentation Neglect occurs when teams begin implementation without "
                    "thoroughly researching existing solutions, best practices, or official "
                    "guidance. This pattern often appears when teams feel pressure to \"start "
                    "coding\" or believe documentation is incomplete or low-quality.\n\n"
                    "The consequences extend beyond wasted development time. Teams that skip "
                    "documentation research often miss important security considerations, "
                    "performance optimizations, edge cases, and integration patterns that "
                    "official documentation addresses.\n\n"
                    "Comprehensive documentation research typically reveals that perceived "
                    "limitations or gaps in standard solutions are actually documented edge "
                    "cases with established workarounds or configuration options."
                )
            }
        }
        
        pattern_explanations = base_explanations.get(pattern_type, {})
        return pattern_explanations.get(detail_level.value, pattern_explanations.get("standard", "This pattern can lead to technical debt."))
    
    def _generate_impact_explanation(self, pattern_type: str, confidence: float, detail_level: DetailLevel) -> str:
        """Generate impact explanation based on confidence and detail level"""
        
        if confidence >= 0.8:
            severity_text = "HIGH RISK"
            impact_level = "severe"
        elif confidence >= 0.6:
            severity_text = "MEDIUM RISK" 
            impact_level = "moderate"
        else:
            severity_text = "LOW RISK"
            impact_level = "minor"
        
        impact_templates = {
            "infrastructure_without_implementation": {
                "severe": f"🚨 {severity_text}: This approach has extremely high probability of creating long-term technical debt. Based on the Cognee case study, similar patterns result in 2+ years of zero functionality and massive engineering waste.",
                "moderate": f"⚠️ {severity_text}: This approach shows concerning signs of the infrastructure anti-pattern. While not certain, similar approaches often lead to significant technical debt and delayed delivery.",
                "minor": f"💡 {severity_text}: Some indicators suggest potential infrastructure anti-pattern. Consider validating standard approaches before proceeding with custom implementation."
            }
        }
        
        # Default impact explanation for patterns without specific templates
        default_impact = f"{severity_text}: Detected confidence {confidence:.0%} suggests {impact_level} risk of technical debt from this anti-pattern."
        
        pattern_impacts = impact_templates.get(pattern_type, {})
        return pattern_impacts.get(impact_level, default_impact)
    
    def _generate_evidence_explanation(self, evidence: List[str], pattern_type: str, detail_level: DetailLevel) -> str:
        """Generate explanation of evidence based on detail level"""
        
        if not evidence:
            return "No specific evidence indicators were found."
        
        if detail_level == DetailLevel.BRIEF:
            return f"Detected {len(evidence)} indicators suggesting this anti-pattern."
        
        elif detail_level == DetailLevel.STANDARD:
            explanation = f"The following {len(evidence)} indicators suggest this anti-pattern: "
            explanation += "; ".join(evidence)
            explanation += ". These patterns typically indicate decisions being made without proper validation of standard approaches."
            return explanation
        
        else:  # COMPREHENSIVE
            explanation = f"Evidence Analysis ({len(evidence)} indicators detected):\n\n"
            
            for i, indicator in enumerate(evidence, 1):
                explanation += f"{i}. **{indicator.title()}**: "
                
                # Add detailed explanation for each type of evidence
                if "custom" in indicator.lower():
                    explanation += "Planning custom implementation suggests assumption that standard solutions are inadequate without validation."
                elif "sdk" in indicator.lower() or "limitation" in indicator.lower():
                    explanation += "Assuming limitations without testing indicates the Infrastructure-Without-Implementation pattern."
                elif "documentation" in indicator.lower():
                    explanation += "Lack of documentation research often leads to reinventing existing solutions."
                elif "workaround" in indicator.lower() or "quick" in indicator.lower():
                    explanation += "Quick fixes and workarounds indicate symptom-driven rather than root-cause solutions."
                else:
                    explanation += "This indicator suggests decisions being made without proper validation."
                
                explanation += "\n"
            
            explanation += "\nCollectively, these indicators suggest high risk of creating technical debt through systematic anti-patterns."
            return explanation
    
    def _get_immediate_actions(self, pattern_type: str, detail_level: DetailLevel) -> List[str]:
        """Get immediate actions to take when pattern is detected"""
        
        immediate_actions = {
            "infrastructure_without_implementation": [
                "🛑 STOP custom development immediately",
                "📚 Research official SDK/API documentation",
                "🧪 Create 10-line proof-of-concept with standard approach",
                "📝 Document any actual limitations found",
                "👥 Get peer review on custom vs standard decision"
            ],
            "symptom_driven_development": [
                "🛑 PAUSE quick fix implementation", 
                "🔍 Identify the root cause of the underlying problem",
                "📋 Document symptoms and their relationship to root causes",
                "🎯 Design solution that addresses root cause",
                "✅ Validate fix resolves entire class of problems"
            ],
            "complexity_escalation": [
                "🛑 STOP adding new layers/abstractions",
                "❓ Question whether complexity is truly necessary",
                "🎯 Try the simplest solution that could work",
                "📊 Document justification for each layer of complexity",
                "🔄 Consider if existing simple solutions meet requirements"
            ],
            "documentation_neglect": [
                "🛑 PAUSE implementation to do research",
                "📚 Review official documentation thoroughly",
                "🔍 Search for community examples and best practices", 
                "🧪 Test recommended approaches before building custom",
                "📝 Document research findings and decision rationale"
            ]
        }
        
        actions = immediate_actions.get(pattern_type, ["Review approach and consider alternatives"])
        
        if detail_level == DetailLevel.BRIEF:
            return actions[:3]  # First 3 most critical actions
        else:
            return actions
    
    def _get_remediation_steps(self, pattern_type: str, detail_level: DetailLevel) -> List[str]:
        """Get detailed remediation steps"""
        
        remediation_steps = {
            "infrastructure_without_implementation": [
                "1. Research Phase: Thoroughly review official SDK/API documentation",
                "2. POC Phase: Create minimal proof-of-concept using standard approaches",
                "3. Testing Phase: Test standard approach with realistic data and scenarios",
                "4. Limitation Analysis: Document specific limitations found (if any)",
                "5. Decision Point: Only build custom if standard approach is proven insufficient",
                "6. Review Phase: Get independent peer review of custom vs standard decision",
                "7. Implementation: If custom is necessary, build minimal viable solution first"
            ],
            "symptom_driven_development": [
                "1. Root Cause Analysis: Use 5 Whys or other systematic techniques",
                "2. Impact Assessment: Map all symptoms to underlying root causes",
                "3. Solution Design: Create solution targeting root cause, not symptoms",
                "4. Validation Planning: Define how to verify root cause resolution",
                "5. Implementation: Focus on sustainable, root-cause addressing solution",
                "6. Testing: Verify solution eliminates entire class of related problems",
                "7. Documentation: Record root cause and solution for future reference"
            ],
            "complexity_escalation": [
                "1. Complexity Audit: List all layers/abstractions and their justifications",
                "2. Simplification Analysis: Identify which complexity is truly necessary",
                "3. Simple Solution Attempt: Try solving with minimal complexity first",
                "4. Incremental Complexity: Add complexity only when simple approach fails",
                "5. Cost-Benefit Analysis: Document maintenance cost vs. benefits for each layer",
                "6. Alternative Evaluation: Consider existing simple solutions that meet requirements",
                "7. Future-Proofing Review: Ensure complexity solves actual, not theoretical problems"
            ],
            "documentation_neglect": [
                "1. Documentation Research: Systematic review of official docs and guides",
                "2. Community Research: Search forums, Stack Overflow, GitHub examples",
                "3. Best Practices Review: Identify recommended patterns and approaches",
                "4. Standard Testing: Implement and test documented standard approaches",
                "5. Gap Analysis: Document what standard approaches don't cover",
                "6. Decision Documentation: Record research findings and rationale",
                "7. Knowledge Sharing: Share findings with team to prevent repeat research"
            ]
        }
        
        steps = remediation_steps.get(pattern_type, ["Review approach and create systematic plan"])
        
        if detail_level == DetailLevel.BRIEF:
            return steps[:4]  # First 4 key steps
        elif detail_level == DetailLevel.STANDARD:
            return steps[:6]  # Most important steps
        else:
            return steps  # All steps for comprehensive
    
    def _get_prevention_checklist(self, pattern_type: str, detail_level: DetailLevel) -> List[str]:
        """Get prevention checklist for future"""
        
        prevention_checklists = {
            "infrastructure_without_implementation": [
                "□ Official documentation reviewed and understood",
                "□ Standard API/SDK tested with realistic example", 
                "□ Specific limitations documented with examples",
                "□ Custom approach justified with clear evidence",
                "□ Peer review completed before custom development",
                "□ Standard approach proven insufficient for specific requirements",
                "□ Maintenance plan for custom solution documented",
                "□ Migration path back to standard solution considered"
            ],
            "symptom_driven_development": [
                "□ Root cause identified using systematic analysis",
                "□ Solution addresses underlying issue, not just symptoms",
                "□ All related symptoms mapped to root cause",
                "□ Solution designed for long-term sustainability",
                "□ Impact on system architecture considered",
                "□ Testing plan verifies root cause resolution",
                "□ Documentation includes problem analysis process"
            ],
            "complexity_escalation": [
                "□ Simplest possible solution attempted first",
                "□ Each layer of complexity has documented justification",
                "□ Alternative simple approaches evaluated and rejected",
                "□ Complexity costs (maintenance, debugging) documented",
                "□ Future maintenance impact assessed",
                "□ Team members can understand and modify the solution",
                "□ Complexity solves actual problems, not theoretical ones"
            ],
            "documentation_neglect": [
                "□ Official documentation thoroughly reviewed",
                "□ Community best practices researched",
                "□ Standard approaches tested before custom development",
                "□ Research findings documented for team reference",
                "□ Decision rationale clearly explained and justified",
                "□ Knowledge shared to prevent duplicate research",
                "□ Regular documentation review process established"
            ]
        }
        
        checklist = prevention_checklists.get(pattern_type, ["□ Approach reviewed and validated"])
        
        if detail_level == DetailLevel.BRIEF:
            return checklist[:4]
        elif detail_level == DetailLevel.STANDARD:
            return checklist[:6]
        else:
            return checklist
    
    def _get_case_study(self, pattern_type: str) -> Optional[CaseStudy]:
        """Get relevant case study for pattern type"""
        return self.case_studies.get(pattern_type)
    
    def _get_related_examples(self, pattern_type: str, detail_level: DetailLevel) -> List[str]:
        """Get related examples of the pattern"""
        
        examples = {
            "infrastructure_without_implementation": [
                "Building custom HTTP clients instead of using requests library",
                "Creating custom authentication instead of using OAuth libraries", 
                "Implementing custom caching instead of using Redis/Memcached",
                "Building custom logging instead of using standard logging frameworks",
                "Creating custom ORM instead of using established options"
            ],
            "symptom_driven_development": [
                "Adding try/catch to suppress errors without fixing root cause",
                "Increasing timeouts instead of optimizing slow operations",
                "Adding more servers instead of fixing memory leaks",
                "Creating duplicate code instead of refactoring shared logic",
                "Patching data inconsistencies instead of fixing data flow"
            ],
            "complexity_escalation": [
                "Using enterprise patterns for simple CRUD operations",
                "Building microservices for functionality that fits in one service",
                "Adding multiple abstraction layers for straightforward logic",
                "Implementing complex caching for rarely-accessed data",
                "Creating elaborate configuration systems for simple settings"
            ],
            "documentation_neglect": [
                "Skipping API documentation and guessing endpoint behavior",
                "Not reading database migration guides before schema changes",
                "Avoiding framework documentation and copying Stack Overflow code",
                "Implementing security without reading security best practices",
                "Building integrations without reading partner API guidelines"
            ]
        }
        
        pattern_examples = examples.get(pattern_type, [])
        
        if detail_level == DetailLevel.BRIEF:
            return pattern_examples[:2]
        elif detail_level == DetailLevel.STANDARD:
            return pattern_examples[:4]
        else:
            return pattern_examples
    
    def _get_learning_resources(self, pattern_type: str, detail_level: DetailLevel) -> List[str]:
        """Get learning resources for the pattern"""
        
        if detail_level == DetailLevel.BRIEF:
            return []  # No additional resources for brief mode
        
        resources = {
            "infrastructure_without_implementation": [
                "📚 'The Pragmatic Programmer' - Chapter on avoiding premature optimization",
                "🎥 'Microservices vs Monolith' - When NOT to build custom infrastructure", 
                "📄 'API-First Development' - Testing standard approaches first",
                "🔗 Official SDK documentation and integration guides"
            ],
            "symptom_driven_development": [
                "📚 'Debugging: The 9 Indispensable Rules' - Root cause analysis techniques",
                "🎥 'Technical Debt: From Metaphor to Theory' - Understanding debt accumulation",
                "📄 '5 Whys Technique' - Systematic root cause analysis",
                "🔗 Incident response best practices and post-mortems"
            ],
            "complexity_escalation": [
                "📚 'Clean Code' - Chapter on simplicity and YAGNI principle",
                "🎥 'Simple vs Easy' by Rich Hickey - Understanding true simplicity", 
                "📄 'KISS Principle in Software Development' - Keeping it simple",
                "🔗 Architecture decision records (ADR) templates"
            ],
            "documentation_neglect": [
                "📚 'Code Complete' - Chapter on documentation and research",
                "🎥 'How to Read Technical Documentation Effectively'",
                "📄 'Documentation-Driven Development' - Research-first approach",
                "🔗 Technical writing and documentation best practices"
            ]
        }
        
        return resources.get(pattern_type, [])
    
    def _get_best_practices(self, pattern_type: str, detail_level: DetailLevel) -> List[str]:
        """Get best practices to prevent the pattern"""
        
        if detail_level == DetailLevel.BRIEF:
            return []
        
        best_practices = {
            "infrastructure_without_implementation": [
                "Always test standard approaches with realistic data before custom development",
                "Document specific requirements that standard solutions don't meet",
                "Create proof-of-concepts with 10-20 lines of code using standard APIs",
                "Get peer review before deciding to build custom infrastructure",
                "Consider maintenance costs and team expertise when evaluating custom vs standard"
            ],
            "symptom_driven_development": [
                "Use systematic root cause analysis techniques (5 Whys, Fishbone diagrams)",
                "Map all symptoms to underlying causes before implementing solutions",
                "Design solutions that eliminate entire classes of problems",
                "Include monitoring to verify root cause resolution",
                "Document problem analysis process for future reference"
            ],
            "complexity_escalation": [
                "Start with the simplest solution that could possibly work",
                "Add complexity incrementally only when requirements demand it",
                "Document clear justification for each layer of abstraction",
                "Regularly review if complex solutions can be simplified",
                "Measure and monitor the true cost of complexity"
            ],
            "documentation_neglect": [
                "Allocate dedicated time for documentation research in project planning",
                "Create shared knowledge base of research findings",
                "Establish team review process for technical decisions",
                "Document decision rationale, not just implementation details",
                "Regular knowledge sharing sessions on discovered best practices"
            ]
        }
        
        return best_practices.get(pattern_type, [])
    
    def _parse_case_studies(self, case_study_data: Dict[str, Any]) -> Dict[str, CaseStudy]:
        """Parse case study data into structured format"""
        case_studies = {}
        
        if "case_study" in case_study_data:
            study_data = case_study_data["case_study"]
            case_study = CaseStudy(
                title=study_data["title"],
                pattern_type=study_data["pattern_type"],
                timeline=study_data["timeline"],
                outcome=study_data["outcome"],
                impact=study_data["impact"],
                root_cause=study_data["root_cause"],
                lesson=study_data["lesson"],
                prevention_checklist=study_data["prevention_checklist"]
            )
            case_studies[study_data["pattern_type"]] = case_study
        
        return case_studies
    
    def _load_educational_extensions(self):
        """Load additional educational content extensions"""
        # This method can be extended to load additional educational content
        # from other files or sources as the system grows
        pass
    
    def get_supported_patterns(self) -> List[str]:
        """Get list of supported pattern types"""
        return list(self.patterns.keys())
    
    def get_available_detail_levels(self) -> List[str]:
        """Get available detail levels"""
        return [level.value for level in DetailLevel]