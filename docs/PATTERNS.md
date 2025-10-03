# Pattern Detection Reference

This document summarizes the anti-patterns detected by the Vibe Check MCP pattern engine.

## Infrastructure Without Implementation
- **Summary:** Building custom infrastructure without validating official SDKs or APIs.
- **Detection Signals:** Mentions of custom servers, wrappers, or manual integrations when official solutions exist.
- **Severity:** Typically `critical` due to extreme risk of wasted engineering effort.

## Symptom-Driven Development
- **Summary:** Applying workarounds rather than addressing root causes.
- **Detection Signals:** Language about "quick fixes", hot patches, or suppressing errors.
- **Severity:** Usually `warning` because long-term stability is threatened.

## Complexity Escalation
- **Summary:** Introducing unnecessary architectural layers or abstractions.
- **Detection Signals:** Descriptions of elaborate patterns for simple requirements.
- **Severity:** `warning` unless paired with high confidence evidence.

## Documentation Neglect
- **Summary:** Skipping official documentation or research before building custom solutions.
- **Detection Signals:** Lack of research notes, uncertainty about existing tooling, or assumptions about missing features.
- **Severity:** Starts at `caution` but escalates with repeated indicators.

## God Object
- **Summary:** Classes that accumulate too many responsibilities (500+ lines and 50+ methods).
- **Detection Signals:** Oversized classes identified via the source analysis engine.
- **Severity:** `critical` because maintainability is severely impacted.

## Copy-Paste Programming
- **Summary:** Large blocks of duplicated code maintained in parallel.
- **Detection Signals:** Repeated sequences of five or more lines outside of generated code.
- **Severity:** `warning`; duplication increases bug risk and maintenance cost.

## Magic Numbers and Strings
- **Summary:** Unexplained literals embedded in logic without descriptive constants.
- **Detection Signals:** Frequent numeric or string literals that are not declared as named constants.
- **Severity:** Ranges from `caution` to `warning` depending on density.

## Long Method
- **Summary:** Functions that exceed maintainability thresholds for size or complexity.
- **Detection Signals:** Functions longer than 80 lines or with cyclomatic complexity above 10.
- **Severity:** `warning`, escalated to `critical` for extremely complex routines.

## Detection Optimizations
- **AST-Aware Analysis:** Python sources are parsed once per file, allowing precise detection of class and function spans while skipping docstrings for literal analysis.
- **Cached Line Processing:** Normalized line views are cached so repeated invocations (e.g., during batch reviews) avoid redundant string work.
- **Early Exits:** Lightweight checks skip duplicate and magic literal analysis when files are too small to trigger the configured thresholds, keeping benchmark performance within limits.

---
Use these references when triaging pattern detection output or writing educational guidance.
