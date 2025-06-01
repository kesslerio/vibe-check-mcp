# Pattern Definition Guide

## Overview

This document provides comprehensive guidance for defining anti-patterns in the Vibe Check MCP detection system. All pattern definitions are stored in `data/anti_patterns.json` and must conform to the JSON schema defined in `data/pattern_schema.json`.

## Schema Structure

### Required Fields

#### `id` (string)
- **Format**: snake_case (e.g., `infrastructure_without_implementation`)
- **Pattern**: `^[a-z][a-z0-9_]*[a-z0-9]$`
- **Purpose**: Unique identifier for the pattern
- **Usage**: Must match the JSON property key

#### `name` (string)
- **Format**: Title Case (e.g., "Infrastructure Without Implementation")
- **Length**: 3-100 characters
- **Purpose**: Human-readable display name
- **Usage**: Used in detection reports and educational content

#### `description` (string)
- **Length**: 10-500 characters
- **Purpose**: Clear explanation of what the anti-pattern represents
- **Guidelines**: Should explain WHY this pattern is problematic, not just what it is

#### `detection_threshold` (number)
- **Range**: 0.1 - 1.0
- **Purpose**: Minimum confidence score required to trigger detection
- **Guidelines**: 
  - 0.3-0.4: High sensitivity (more false positives, catches subtle cases)
  - 0.5-0.6: Balanced approach (recommended for most patterns)
  - 0.7-0.8: High precision (fewer false positives, only clear cases)

#### `indicators` (array)
- **Required**: At least 1 indicator
- **Maximum**: 20 indicators (to prevent overly complex patterns)
- **Purpose**: Positive signals that suggest the presence of this anti-pattern

### Optional Fields

#### `severity` (string)
- **Values**: `"low"`, `"medium"`, `"high"`, `"critical"`
- **Default**: `"medium"`
- **Purpose**: Impact classification for prioritization

#### `category` (string)
- **Values**: `"architectural"`, `"process"`, `"design"`, `"security"`, `"performance"`
- **Default**: `"process"`
- **Purpose**: Classification for organization and filtering

#### `negative_indicators` (array)
- **Maximum**: 10 indicators
- **Purpose**: Signals that reduce confidence in pattern detection
- **Usage**: Evidence that contradicts the anti-pattern (e.g., mentions of official documentation)

## Indicator Structure

### Positive Indicators

```json
{
  "regex": "\\b(?:custom|build|implement)\\s+(?:our\\s+own|new)",
  "description": "mentions building custom infrastructure",
  "weight": 0.4,
  "text": "custom infrastructure"
}
```

#### Fields:

- **`regex`**: Regular expression pattern (case-insensitive matching)
- **`description`**: Human-readable explanation of what this detects
- **`weight`**: Confidence contribution (0.1-0.5 range)
- **`text`**: Short label for reporting

### Negative Indicators

```json
{
  "regex": "\\bofficial\\s+(?:sdk|api|documentation)",
  "description": "mentions official SDK research",
  "weight": -0.3
}
```

#### Fields:

- **`regex`**: Regular expression pattern
- **`description`**: Explanation of the negative evidence
- **`weight`**: Negative confidence contribution (-0.5 to -0.1)

## Weight Calibration Guidelines

### Weight Ranges and Meanings

| Weight Range | Strength | Use Cases |
|--------------|----------|-----------|
| 0.1 - 0.2 | Weak | Suggestive language, mild indicators |
| 0.2 - 0.3 | Moderate | Clear indicators but context-dependent |
| 0.3 - 0.4 | Strong | Direct statements, obvious anti-patterns |
| 0.4 - 0.5 | Very Strong | Explicit anti-pattern language |

### Calibration Process

1. **Start with baseline weights**: 0.2 for moderate indicators, 0.3 for strong ones
2. **Test against validation cases**: Use `validation/comprehensive_test.py`
3. **Adjust based on results**:
   - If too many false positives: reduce weights or increase threshold
   - If missing clear cases: increase weights for key indicators
4. **Validate accuracy**: Target 80%+ detection accuracy with <10% false positive rate

### Weight Distribution Strategy

For effective pattern detection:
- **Primary indicators** (core anti-pattern signals): 0.3-0.4 weight
- **Supporting indicators** (contextual clues): 0.2-0.3 weight  
- **Weak indicators** (suggestive language): 0.1-0.2 weight
- **Negative indicators**: -0.2 to -0.4 weight

## Pattern Examples

### Well-Formed Pattern Example

```json
{
  "example_pattern": {
    "id": "example_pattern",
    "name": "Example Anti-Pattern",
    "description": "Clear description of why this pattern is problematic and what it represents",
    "severity": "medium",
    "category": "process",
    "detection_threshold": 0.5,
    "indicators": [
      {
        "regex": "\\bprimary\\s+indicator\\s+pattern",
        "description": "main signal of the anti-pattern",
        "weight": 0.4,
        "text": "primary indicator"
      },
      {
        "regex": "\\bsupporting\\s+evidence",
        "description": "additional evidence for the pattern",
        "weight": 0.2,
        "text": "supporting evidence"
      }
    ],
    "negative_indicators": [
      {
        "regex": "\\bpositive\\s+counter-evidence",
        "description": "evidence against the anti-pattern",
        "weight": -0.3
      }
    ]
  }
}
```

### Common Regex Patterns

#### Language Indicators
- Future plans: `\\b(?:planning|going)\\s+to\\s+(?:build|implement)`
- Assumptions: `\\b(?:might|could|probably)\\s+(?:be|won't)`
- Custom solutions: `\\b(?:custom|our\\s+own|build\\s+our\\s+own)`

#### Intensity Modifiers
- Strong negative: `\\bwon't\\s+work\\b|\\bcan't\\s+use\\b`
- Uncertainty: `\\bmight\\s+not\\b|\\bmay\\s+not\\b`
- Dismissal: `\\btoo\\s+(?:limiting|simple|basic)\\b`

## Validation and Testing

### Schema Validation

Validate your pattern definitions against the schema:

```bash
# Install JSON schema validator
pip install jsonschema

# Validate patterns
python -c "
import json
from jsonschema import validate
with open('data/pattern_schema.json') as f:
    schema = json.load(f)
with open('data/anti_patterns.json') as f:
    patterns = json.load(f)
validate(patterns, schema)
print('✅ Schema validation passed')
"
```

### Detection Testing

Test your patterns against validation cases:

```bash
# Run comprehensive validation
python validation/comprehensive_test.py

# Test specific pattern
python validation/detect_patterns.py --pattern your_pattern_id
```

### Performance Guidelines

- **Target accuracy**: 80%+ detection rate
- **False positive rate**: <10%
- **Pattern complexity**: Max 20 indicators per pattern
- **Regex performance**: Avoid catastrophic backtracking

## Adding New Patterns

### Step-by-Step Process

1. **Identify the anti-pattern**: Clearly define what makes it problematic
2. **Research indicators**: Collect examples of language that signals this pattern
3. **Create initial definition**: Start with 3-5 core indicators
4. **Set initial weights**: Use guidelines above for weight assignment
5. **Test against examples**: Validate with positive and negative test cases
6. **Calibrate threshold**: Adjust detection_threshold for optimal accuracy
7. **Add negative indicators**: Include counter-evidence to reduce false positives
8. **Validate schema**: Ensure JSON conforms to schema
9. **Run comprehensive tests**: Verify overall system accuracy isn't degraded

### Testing Checklist

- [ ] Schema validation passes
- [ ] Pattern detects positive test cases
- [ ] Pattern doesn't trigger on negative test cases  
- [ ] Weights sum appropriately for threshold
- [ ] Regex patterns don't cause performance issues
- [ ] Overall system accuracy remains >80%
- [ ] Documentation updated with pattern rationale

## Maintenance Guidelines

### Regular Review Process

1. **Quarterly accuracy review**: Test against expanding validation set
2. **Weight adjustment**: Fine-tune based on real-world usage
3. **Indicator updates**: Add new indicators based on discovered cases
4. **Threshold optimization**: Adjust for changing accuracy requirements

### Version Control

When making significant changes to patterns:
1. Document the rationale in commit messages
2. Update test cases to reflect changes
3. Consider backward compatibility for detection results
4. Update this documentation if new patterns or fields are added

### Performance Monitoring

Monitor these metrics:
- Detection accuracy per pattern
- False positive rate
- Processing time per analysis
- Memory usage for large text analysis

## Troubleshooting

### Common Issues

**Pattern not triggering**: 
- Check if weights sum to threshold
- Verify regex patterns match expected text
- Test individual indicators separately

**Too many false positives**:
- Add negative indicators
- Increase detection threshold
- Reduce indicator weights

**Poor performance**:
- Simplify complex regex patterns
- Reduce number of indicators
- Avoid nested quantifiers in regex

### Debug Commands

```bash
# Test specific text against pattern
python -c "
from src.vibe_check.core.pattern_detector import PatternDetector
detector = PatternDetector()
results = detector.analyze_text_for_patterns('your test text here')
print(results)
"

# Analyze pattern weights
python validation/debug_pattern_weights.py pattern_id
```

## References

- [JSON Schema Specification](https://json-schema.org/)
- [Python Regex Documentation](https://docs.python.org/3/library/re.html)
- [Vibe Check MCP Core Documentation](Technical_Implementation_Guide.md)
- [Validation Results](../validation/README.md)