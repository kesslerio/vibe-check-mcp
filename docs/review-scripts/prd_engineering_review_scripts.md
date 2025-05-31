# PRD & Engineering Plan Review Scripts
## Systematic Document Validation for Anti-Pattern Prevention

**Purpose**: Extend the proven `review-issue.sh` and `review-pr.sh` methodology to systematically review Product Requirements Documents (PRDs) and Engineering Plans before implementation, preventing systematic failures at the planning stage.

---

## Research Findings & Anti-Pattern Analysis

### PRD Failure Modes (Research-Based)

Based on research into PRD best practices and failure patterns, common anti-patterns include:

1. **Solution-First Requirements**: Starting with implementation details instead of problem definition
2. **Scope Creep Enablers**: Vague success criteria and poorly defined boundaries  
3. **Resource Reality Disconnect**: Technical requirements without implementation feasibility
4. **Stakeholder Assumption Gaps**: Missing critical user validation and market assumptions
5. **Metrics Manipulation**: Vanity metrics instead of business impact measurements

### Engineering Plan Failure Modes (Research-Based)

Research into technical design document failures reveals:

1. **Architecture Without Validation**: Complex designs without proof-of-concept validation
2. **Integration Assumption Failures**: Third-party dependencies without API verification
3. **Scale Premature Optimization**: Over-engineering for theoretical future scale
4. **Technology Selection Bias**: Choosing trendy tech over proven, standard solutions
5. **Risk Assessment Blindness**: Missing failure mode analysis and contingency planning

---

## Proposed Script Architecture

### Two Complementary Scripts

Following the proven pattern of `review-issue.sh` and `review-pr.sh`, we propose:

1. **`review-prd.sh`**: Product Requirements Document validation
2. **`review-engineering-plan.sh`**: Technical design document validation

Both scripts follow the established systematic review methodology:
- **Claude-powered analysis** via `claude -p` integration
- **Anti-pattern detection** using documented failure modes
- **Educational feedback** with clear explanations and alternatives
- **Systematic validation** checklists based on industry best practices

---

## Script 1: `review-prd.sh`

### Purpose
Systematic PRD validation to prevent product development anti-patterns before engineering begins.

### Usage
```bash
./scripts/review-prd.sh <PRD_FILE_PATH>
./scripts/review-prd.sh docs/PRD.md
./scripts/review-prd.sh --url https://github.com/org/repo/blob/main/docs/PRD.md
```

### Core Validation Framework

**Anti-Pattern Detection Categories:**

#### 1. Solution-First Requirements Detection
**Indicators to Scan For:**
- Technical implementation details in problem statement
- Architecture decisions before user needs validation
- Technology choices before requirements finalization
- UI mockups before user journey analysis

**Example Detection Logic:**
```bash
# Search for premature technical decisions
TECH_PREMATURE=$(grep -iE "(microservices|kubernetes|react|database|API)" "$PRD_CONTENT" | head -5)
SOLUTION_FIRST=$(grep -iE "(we will build|implementation will use|technology stack)" "$PRD_CONTENT" | head -3)
```

#### 2. Scope Creep Enabler Analysis
**Indicators to Scan For:**
- Vague success metrics ("improve user experience")
- Missing "out of scope" sections
- Ambiguous acceptance criteria
- Feature lists without prioritization

#### 3. Resource Reality Disconnect
**Indicators to Scan For:**
- No technical feasibility validation
- Missing development timeline estimates
- Complex features without complexity assessment
- Third-party dependencies without verification

#### 4. Stakeholder Assumption Gaps
**Indicators to Scan For:**
- Missing user research validation
- Assumptions stated as facts
- No market validation evidence
- Missing competitive analysis

#### 5. Metrics Manipulation Prevention
**Indicators to Scan For:**
- Vanity metrics (page views, signups) without business impact
- No baseline measurements
- Success criteria without measurement methodology
- Growth targets without historical data

### Claude Integration Prompt Template

```bash
# PRD Review Prompt Template
cat > /tmp/prd_review_prompt.md << EOF
You are a senior product strategy advisor with expertise in preventing systematic product failures.

Analyze this PRD and provide systematic validation using this framework:

## ANTI-PATTERN DETECTION FRAMEWORK

### 1. SOLUTION-FIRST REQUIREMENTS CHECK
- [ ] Are technical implementation details mentioned before user problems are fully defined?
- [ ] Are architecture decisions made before requirements are validated?
- [ ] Are technology choices specified before feasibility assessment?
- [ ] Are implementation approaches detailed before user needs confirmation?

### 2. SCOPE CREEP ENABLER ANALYSIS  
- [ ] Are success criteria specific and measurable?
- [ ] Is there a clear "out of scope" section?
- [ ] Are acceptance criteria unambiguous?
- [ ] Are features prioritized with clear trade-offs?

### 3. RESOURCE REALITY DISCONNECT CHECK
- [ ] Is technical feasibility validated with proof-of-concepts?
- [ ] Are development estimates realistic and evidence-based?
- [ ] Are complex features assessed for implementation complexity?
- [ ] Are third-party dependencies verified (APIs tested, SDKs evaluated)?

### 4. STAKEHOLDER ASSUMPTION GAPS
- [ ] Are user needs validated with actual user research?
- [ ] Are assumptions clearly identified vs. stated as facts?
- [ ] Is market validation evidence provided?
- [ ] Is competitive analysis thorough and recent?

### 5. METRICS MANIPULATION PREVENTION
- [ ] Do success metrics connect to actual business impact?
- [ ] Are baseline measurements established?
- [ ] Is measurement methodology defined?
- [ ] Are growth targets based on historical evidence?

## SYSTEMATIC REVIEW OUTPUT FORMAT

🎯 **PRD Overview**
[Brief summary of what this PRD proposes]

🚨 **Anti-Pattern Risk Assessment**
[Detailed analysis of detected failure patterns]

🔍 **Critical Validation Requirements**
[Specific validation work needed before implementation]

⚖️ **Resource Reality Check**
[Technical feasibility and timeline assessment]

🎯 **Success Criteria Evaluation**
[Analysis of measurability and business alignment]

⚠️ **Red Flags & Blockers**
[Issues that must be resolved before development begins]

💡 **Recommendations**
[Specific actions to strengthen the PRD]

**Overall Assessment**: [APPROVE / NEEDS REVISION / NEEDS USER VALIDATION / REJECT]

Focus on preventing the systematic failures that lead to months/years of wasted development effort.
EOF
```

### Key Features

**Systematic Validation Checklist:**
- Problem definition clarity and user validation
- Success criteria measurability and business alignment
- Technical feasibility and third-party dependency verification
- Scope boundaries and feature prioritization
- Resource estimation reality and timeline feasibility

**Educational Feedback:**
- Explains WHY each anti-pattern is problematic
- Provides specific examples of PRD failure modes
- Suggests concrete improvements with templates
- References industry best practices and case studies

**Integration Points:**
- File-based analysis (local PRD files)
- URL-based analysis (GitHub, Notion, etc.)
- GitHub integration for comment posting
- Template generation for missing sections

---

## Script 2: `review-engineering-plan.sh`

### Purpose
Systematic technical design document validation to prevent engineering anti-patterns before implementation.

### Usage
```bash
./scripts/review-engineering-plan.sh <PLAN_FILE_PATH>
./scripts/review-engineering-plan.sh docs/technical-design.md
./scripts/review-engineering-plan.sh --prd docs/PRD.md --plan docs/engineering-plan.md
```

### Core Validation Framework

**Anti-Pattern Detection Categories:**

#### 1. Architecture Without Validation
**Indicators to Scan For:**
- Complex system designs without proof-of-concept validation
- Microservices architecture for simple applications
- Custom solutions without evaluating existing alternatives
- Distributed systems without proven need for scale

#### 2. Integration Assumption Failures  
**Indicators to Scan For:**
- Third-party APIs without actual testing
- SDK integration without version compatibility verification
- Database choices without performance validation
- External service dependencies without SLA verification

#### 3. Scale Premature Optimization
**Indicators to Scan For:**
- Performance optimizations before measuring bottlenecks
- Horizontal scaling before vertical scaling exploration
- Caching strategies without traffic analysis
- Load balancing before traffic requirements validation

#### 4. Technology Selection Bias
**Indicators to Scan For:**
- New technology adoption without proven stability
- Complex frameworks for simple requirements
- Custom implementations when standard solutions exist
- Technology choices without team skill assessment

#### 5. Risk Assessment Blindness
**Indicators to Scan For:**
- Missing failure mode and effects analysis (FMEA)
- No rollback/contingency planning
- Single points of failure without mitigation
- Missing monitoring and observability strategy

### Claude Integration Prompt Template

```bash
# Engineering Plan Review Prompt Template  
cat > /tmp/engineering_review_prompt.md << EOF
You are a senior technical architect with expertise in preventing systematic engineering failures.

Based on the Cognee retrospective lessons (2+ years of technical debt from infrastructure-without-implementation), analyze this engineering plan:

## ENGINEERING ANTI-PATTERN DETECTION FRAMEWORK

### 1. ARCHITECTURE WITHOUT VALIDATION CHECK
- [ ] Are complex designs validated with working proof-of-concepts?
- [ ] Are microservices justified with specific scalability requirements?
- [ ] Are custom solutions compared against existing alternatives?
- [ ] Are distributed system decisions backed by actual scale needs?

### 2. INTEGRATION ASSUMPTION FAILURES
- [ ] Are third-party APIs tested with actual integration code?
- [ ] Are SDK versions and compatibility verified?
- [ ] Are database performance requirements validated with realistic data?
- [ ] Are external service SLAs and reliability confirmed?

### 3. SCALE PREMATURE OPTIMIZATION
- [ ] Are performance optimizations based on measured bottlenecks?
- [ ] Is vertical scaling explored before horizontal scaling?
- [ ] Are caching strategies based on actual traffic patterns?
- [ ] Are scaling decisions backed by traffic growth projections?

### 4. TECHNOLOGY SELECTION BIAS  
- [ ] Are new technologies proven stable for production use?
- [ ] Are framework choices proportional to application complexity?
- [ ] Are standard solutions evaluated before custom implementation?
- [ ] Does team have expertise in chosen technologies?

### 5. RISK ASSESSMENT BLINDNESS
- [ ] Is failure mode and effects analysis (FMEA) included?
- [ ] Are rollback and contingency plans defined?
- [ ] Are single points of failure identified and mitigated?
- [ ] Is monitoring and observability strategy comprehensive?

## COGNEE RETROSPECTIVE LESSONS APPLICATION

**Infrastructure-Without-Implementation Prevention:**
- [ ] Are basic API integrations tested before architecture planning?
- [ ] Are standard approaches (like cognee.add() → cognee.cognify() → cognee.search()) researched?
- [ ] Is custom infrastructure justified over documented standard approaches?
- [ ] Are working examples demonstrated before complex implementation?

## SYSTEMATIC REVIEW OUTPUT FORMAT

🎯 **Engineering Plan Overview**
[Brief summary of proposed technical approach]

🚨 **Anti-Pattern Risk Assessment**
[Detailed analysis of detected engineering failure patterns]

🔧 **Technical Validation Requirements**
[Specific POCs and validations needed before implementation]

⚖️ **Complexity Appropriateness**
[Assessment of solution complexity vs. actual requirements]

🛡️ **Risk Analysis & Mitigation**
[Failure modes and contingency planning evaluation]

🎯 **Implementation Feasibility**
[Timeline, resource, and skill assessment]

⚠️ **Critical Blockers**
[Issues that must be resolved before development]

💡 **Recommendations**
[Specific actions to strengthen the engineering plan]

**Overall Assessment**: [APPROVE / NEEDS POC / NEEDS SIMPLIFICATION / REJECT]

Focus on preventing infrastructure-without-implementation patterns that led to the Cognee technical debt.
EOF
```

### Key Features

**Technical Validation Framework:**
- Proof-of-concept requirements for complex designs
- Third-party integration verification checklists
- Technology selection justification analysis
- Risk assessment and failure mode analysis

**Cognee Retrospective Integration:**
- Specific checks for infrastructure-without-implementation patterns
- Validation that basic APIs are tested before complex architecture
- Standard approach research requirements
- Working example demonstration before custom solutions

**PRD Alignment Verification** (when both provided):
- Technical approach alignment with PRD requirements
- Implementation complexity vs. business value assessment
- Timeline feasibility vs. PRD deadlines
- Resource requirements vs. available team capacity

---

## Integration with Existing Script Ecosystem

### Unified Review Workflow

Building on the proven `review-issue.sh` and `review-pr.sh` patterns:

```bash
# Complete systematic review workflow
./scripts/review-prd.sh docs/PRD.md
./scripts/review-engineering-plan.sh docs/technical-design.md --prd docs/PRD.md  
./scripts/review-issue.sh 123  # Implementation issue validation
./scripts/review-pr.sh 456     # Code review validation
```

### Shared Components

**Common Utilities** (`scripts/shared/`):
- `claude-integration.sh`: Shared Claude CLI wrapper
- `validation-framework.sh`: Common anti-pattern detection logic
- `output-formatting.sh`: Consistent educational response formatting
- `github-integration.sh`: Shared GitHub API utilities

**Knowledge Base Integration:**
- Shared anti-pattern definitions and examples
- Common Cognee retrospective lessons
- Consistent validation criteria across all scripts
- Educational content templates and examples

### Script Relationships

```
review-prd.sh           → Validates product requirements
    ↓
review-engineering-plan.sh → Validates technical approach  
    ↓
review-issue.sh         → Validates implementation issues
    ↓  
review-pr.sh           → Validates actual code changes
```

Each script builds on the previous validation layer, creating a comprehensive systematic review process from concept to code.

---

## Implementation Plan

### Phase 1: Core Script Development (Week 1)
- **`review-prd.sh`**: Basic PRD validation with anti-pattern detection
- **Claude integration**: Prompt engineering and response parsing
- **File analysis**: Local markdown file processing
- **Educational feedback**: Structured output with explanations

### Phase 2: Engineering Plan Integration (Week 2)  
- **`review-engineering-plan.sh`**: Technical design validation
- **PRD alignment**: Cross-document consistency checking
- **Cognee retrospective**: Infrastructure-without-implementation prevention
- **Technical validation**: POC requirements and complexity assessment

### Phase 3: Workflow Integration (Week 3)
- **Shared utilities**: Extract common functionality
- **GitHub integration**: URL-based document analysis
- **Template generation**: Missing section recommendations
- **Documentation**: Comprehensive usage guides and examples

### Phase 4: Validation & Refinement (Week 4)
- **Real-world testing**: Use scripts on actual PRDs and engineering plans
- **Prompt optimization**: Refine Claude integration for accuracy
- **Error handling**: Robust failure modes and recovery
- **Community feedback**: Prepare for open source release

---

## Success Criteria

### Technical Validation
- ✅ Successfully detect solution-first requirements in PRDs
- ✅ Identify infrastructure-without-implementation patterns in engineering plans  
- ✅ Generate educational feedback explaining why patterns are problematic
- ✅ Integrate seamlessly with existing `review-*.sh` script ecosystem
- ✅ Process documents within reasonable time limits (2-5 minutes)

### Anti-Pattern Prevention
- ✅ Catch PRD scope creep enablers before development begins
- ✅ Prevent premature technology selection without validation
- ✅ Require proof-of-concept validation for complex architectures  
- ✅ Ensure third-party integrations are tested before planning
- ✅ Validate success criteria are measurable and business-aligned

### Workflow Integration
- ✅ Scripts work with local files and GitHub URLs
- ✅ Educational output helps improve document quality
- ✅ Integration with Claude CLI workflow via `claude -p`
- ✅ Consistent with existing script patterns and conventions
- ✅ Comprehensive validation from PRD to code review

---

## Risk Mitigation

### Document Format Variations
- **Risk**: PRDs and engineering plans vary widely in format
- **Mitigation**: Flexible parsing with multiple format support
- **Mitigation**: Template suggestions for missing standard sections

### Complex Document Analysis
- **Risk**: Large documents may hit Claude CLI limits
- **Mitigation**: Document chunking and section-based analysis
- **Mitigation**: Progressive analysis with summary generation

### False Positive Management
- **Risk**: Over-flagging minor issues reduces tool credibility
- **Mitigation**: Conservative detection thresholds with confidence scoring
- **Mitigation**: Clear explanations of why each issue is flagged

### Integration Complexity
- **Risk**: Scripts become too complex for maintenance
- **Mitigation**: Shared utility extraction and modular design
- **Mitigation**: Comprehensive testing and documentation

---

## Future Enhancements

### Advanced Analysis
- **Cross-document consistency**: PRD ↔ Engineering Plan alignment validation
- **Historical analysis**: Learn from past PRD/plan success patterns
- **Stakeholder validation**: Integration with user research requirements
- **Competitive analysis**: Market positioning and differentiation validation

### Workflow Integration
- **CI/CD integration**: Automated document validation in development pipeline
- **Template generation**: Smart PRD and engineering plan templates
- **Collaboration features**: Multi-stakeholder review and approval workflows
- **Metrics tracking**: Document quality improvements over time

### AI Enhancement
- **Custom model training**: Fine-tuned anti-pattern detection
- **Context learning**: Adaptation to team-specific patterns and preferences  
- **Predictive analysis**: Early warning for project risk factors
- **Integration recommendations**: Automated suggestion of standard approaches

---

## Conclusion

The proposed `review-prd.sh` and `review-engineering-plan.sh` scripts extend the proven systematic review methodology to the critical planning phases of development. By catching anti-patterns before implementation begins, these scripts can prevent the months or years of technical debt that result from poor initial planning.

The scripts build naturally on the existing `review-issue.sh` and `review-pr.sh` foundation, creating a comprehensive validation pipeline from initial product concept through final code review. This systematic approach, powered by Claude's analytical capabilities and grounded in real-world failure patterns, provides the systematic prevention methodology needed to avoid repeating costly mistakes like the Cognee integration experience.

**Next Steps**: Begin implementation with `review-prd.sh`, focusing on the most critical anti-patterns that lead to systematic project failures, then extend to engineering plan validation with specific emphasis on preventing infrastructure-without-implementation patterns.