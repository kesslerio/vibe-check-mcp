# Comprehensive Testing Suite for Vibe Check MCP

This directory contains the comprehensive testing suite for the vibe-check-mcp project, implementing all testing requirements from Issue #197.

## 📋 Test Architecture Overview

The testing suite is organized into 7 main categories, each targeting different aspects of the system:

### 1. Unit Tests (`tests/unit/`)
Tests individual components in isolation:
- **Pattern Detector** (`test_pattern_detector.py`) - Core anti-pattern detection engine
- **Educational Content** (`test_educational_content.py`) - Content generation and formatting
- **Analyze Text Tool** (`test_analyze_text_tool.py`) - Main MCP tool functionality
- **MCP Server Tools** (`test_mcp_server_tools.py`) - Tool registration and execution

### 2. Integration Tests (`tests/integration/`)
Tests component interactions and external integrations:
- **MCP Protocol Integration** (`test_mcp_protocol_integration.py`) - FastMCP compliance and tool execution
- **GitHub API Workflows** - Integration with GitHub API for issue/PR analysis
- **Claude CLI Integration** - External Claude CLI tool interactions

### 3. Security Tests (`tests/security/`)
Tests security measures and vulnerability prevention:
- **Input Validation** (`test_input_validation.py`) - Comprehensive security testing including:
  - ReDoS attack prevention
  - XSS prevention 
  - Injection attack prevention
  - URL sanitization
  - Memory exhaustion prevention
  - Path traversal prevention
  - Command injection prevention

### 4. Performance Tests (`tests/performance/`)
Performance benchmarks and resource usage validation:
- **Performance Benchmarks** (`test_performance_benchmarks.py`) - Including:
  - Response time benchmarks (small, medium, large inputs)
  - Memory usage monitoring
  - Concurrent request performance
  - CPU usage monitoring
  - Throughput measurement
  - Memory leak detection

### 5. Edge Case Tests (`tests/edge_cases/`)
Boundary conditions and unusual scenarios:
- **Boundary Conditions** (`test_boundary_conditions.py`) - Including:
  - Extreme input sizes
  - Malformed Unicode
  - Special characters
  - Resource contention
  - File system edge cases
  - Threading edge cases

### 6. Novel Query Tests (`tests/novel_queries/`)
Complex scenarios and stress testing:
- **Complex Scenarios** (`test_complex_scenarios.py`) - Including:
  - Enterprise development scenarios
  - Startup MVP patterns
  - Microservices over-engineering
  - AI/ML infrastructure scenarios
  - Multi-language projects
  - Cascading complexity patterns

### 7. End-to-End Tests (`tests/e2e/`)
Complete workflow validation:
- **Complete Workflows** (`test_complete_workflows.py`) - Including:
  - Full analysis pipeline
  - MCP tool registration to execution
  - Error recovery workflows
  - Context-aware analysis
  - Concurrent workflow execution

## 🚀 Quick Start

### Prerequisites
```bash
# Install test dependencies
pip install -r requirements-test.txt

# Install development dependencies  
pip install -r requirements.txt
```

### Running Tests

#### Run All Tests
```bash
# Complete test suite with coverage
python -m pytest --cov=src --cov-report=html --cov-report=term

# Using the test runner
python tests/test_runner.py --category all --verbose --coverage
```

#### Run Specific Categories
```bash
# Unit tests only
python tests/test_runner.py --category unit --verbose

# Security tests
python tests/test_runner.py --category security --verbose

# Performance benchmarks
python tests/test_runner.py --category performance --verbose

# End-to-end workflows
python tests/test_runner.py --category e2e --verbose
```

#### Run by Test Markers
```bash
# Security-focused tests
python -m pytest -m security -v

# Performance tests with benchmarking
python -m pytest -m performance --benchmark-only

# Quick unit tests
python -m pytest -m unit -v

# Integration tests (may require external services)
python -m pytest -m integration -v
```

## 📊 Coverage and Reporting

### Coverage Requirements
- **Target Coverage**: >90% for critical paths
- **Minimum Coverage**: >80% overall
- **Security Code**: 100% coverage required

### Generate Coverage Reports
```bash
# HTML coverage report
python -m pytest --cov=src --cov-report=html
open htmlcov/index.html

# JSON coverage report
python -m pytest --cov=src --cov-report=json
cat coverage.json

# Terminal coverage report
python -m pytest --cov=src --cov-report=term-missing
```

### Performance Benchmarks
```bash
# Run performance tests with JSON output
python -m pytest tests/performance/ --benchmark-json=benchmark_results.json

# View benchmark results
cat benchmark_results.json | jq '.benchmarks[] | {name: .name, mean: .stats.mean}'
```

## 🏗️ Test Configuration

### pytest.ini Configuration
Located at project root, defines:
- Test discovery patterns
- Coverage settings
- Test markers
- Timeout configurations
- Output formatting

### conftest.py Fixtures
Provides shared test fixtures:
- **Mock GitHub API** - For GitHub integration tests
- **Mock Claude API** - For AI service tests  
- **Temporary files/directories** - For file system tests
- **Security test inputs** - Malicious input patterns
- **Performance test data** - Various data sizes
- **Anti-pattern examples** - Test patterns and good examples

## 🔧 Writing New Tests

### Test Organization Guidelines

1. **File Naming**: `test_<component_name>.py`
2. **Class Naming**: `Test<ComponentName>`
3. **Method Naming**: `test_<functionality>_<scenario>`
4. **Markers**: Add appropriate pytest markers

### Example Test Structure
```python
import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

@pytest.mark.unit
class TestComponentName:
    """Test component functionality"""
    
    @pytest.fixture
    def component(self):
        """Create component instance for testing"""
        return ComponentClass()
    
    def test_basic_functionality(self, component):
        """Test basic functionality works"""
        result = component.method_under_test("input")
        
        assert isinstance(result, dict)
        assert 'expected_key' in result
        assert result['status'] == 'success'
    
    def test_error_handling(self, component):
        """Test error scenarios"""
        with pytest.raises(ValueError):
            component.method_under_test(None)
    
    @pytest.mark.slow
    def test_performance_sensitive(self, component):
        """Test performance-sensitive functionality"""
        import time
        
        start = time.time()
        result = component.heavy_operation()
        duration = time.time() - start
        
        assert duration < 5.0, f"Operation too slow: {duration}s"
```

### Security Test Guidelines
```python
@pytest.mark.security
def test_input_sanitization(self):
    """Test input sanitization security"""
    malicious_inputs = [
        "<script>alert('xss')</script>",
        "'; DROP TABLE users; --",
        "../../../etc/passwd"
    ]
    
    for malicious_input in malicious_inputs:
        result = analyze_text_demo(malicious_input)
        
        assert isinstance(result, dict)
        assert 'status' in result
        
        # Response should not contain dangerous content
        response_str = str(result)
        assert "<script>" not in response_str
```

### Performance Test Guidelines
```python
@pytest.mark.performance
def test_response_time_benchmark(self, benchmark):
    """Benchmark response time"""
    def analyze_text():
        return analyze_text_demo("Performance test input")
    
    result = benchmark(analyze_text)
    assert isinstance(result, dict)
    # Benchmark automatically measures timing
```

## 🎯 Test Markers Reference

| Marker | Purpose | Usage |
|--------|---------|-------|
| `unit` | Unit tests | `@pytest.mark.unit` |
| `integration` | Integration tests | `@pytest.mark.integration` |
| `security` | Security tests | `@pytest.mark.security` |
| `performance` | Performance tests | `@pytest.mark.performance` |
| `edge_case` | Edge case tests | `@pytest.mark.edge_case` |
| `novel_query` | Novel query tests | `@pytest.mark.novel_query` |
| `e2e` | End-to-end tests | `@pytest.mark.e2e` |
| `slow` | Slow-running tests | `@pytest.mark.slow` |
| `external` | Requires external services | `@pytest.mark.external` |
| `mcp` | MCP-specific tests | `@pytest.mark.mcp` |
| `github` | GitHub API tests | `@pytest.mark.github` |
| `claude` | Claude API tests | `@pytest.mark.claude` |

## 🐛 Debugging Tests

### Running Individual Tests
```bash
# Single test method
python -m pytest tests/unit/test_pattern_detector.py::TestPatternDetector::test_detector_initialization -v

# Single test file
python -m pytest tests/unit/test_pattern_detector.py -v

# Tests matching pattern
python -m pytest -k "test_detector" -v
```

### Debug Mode
```bash
# Run with pdb on failure
python -m pytest --pdb

# Run with verbose output and no capture
python -m pytest -v -s

# Run with detailed traceback
python -m pytest --tb=long
```

### Test Logs
```bash
# Enable logging output
python -m pytest --log-cli-level=DEBUG

# Capture logs in reports
python -m pytest --log-file=test.log
```

## 🔄 Continuous Integration

### GitHub Actions Integration
The test suite integrates with CI/CD pipelines:

```yaml
# Example CI configuration
- name: Run Comprehensive Tests
  run: |
    python tests/test_runner.py --category all --coverage --quality
    
- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

### Pre-commit Hooks
```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

## 📈 Performance Baselines

### Response Time Targets
- **Small input (<1KB)**: <100ms
- **Medium input (~10KB)**: <500ms  
- **Large input (~100KB)**: <2s

### Memory Usage Targets
- **Base usage**: <50MB increase
- **Large input**: <200MB peak
- **Concurrent (10 requests)**: <500MB total

### Throughput Targets
- **Sequential**: >10 requests/second
- **Concurrent**: >50 requests/second (10 workers)

## 🛠️ Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Ensure src is in Python path
   export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
   ```

2. **Coverage Issues**
   ```bash
   # Clean coverage data
   rm .coverage coverage.json
   rm -rf htmlcov/
   ```

3. **Performance Test Failures**
   ```bash
   # Run with relaxed timeouts
   python -m pytest tests/performance/ --timeout=60
   ```

4. **Memory Issues**
   ```bash
   # Increase available memory for tests
   python -m pytest --maxfail=1
   ```

### Debug Environment
```bash
# Check test environment
python tests/test_runner.py --quality

# Validate test dependencies
pip check

# Test configuration validation
python -m pytest --collect-only --quiet
```

## 📚 Related Documentation

- [Project README](../README.md) - Project overview
- [Technical Documentation](../docs/TECHNICAL.md) - Architecture details
- [Contributing Guidelines](../CONTRIBUTING.md) - Development workflow
- [Security Documentation](../docs/SECURITY.md) - Security considerations

## 🆘 Support and Maintenance

### Updating Tests
When adding new features:
1. Add unit tests for new components
2. Update integration tests for new workflows
3. Add security tests for new inputs
4. Update performance baselines if needed
5. Add edge cases for new functionality

### Test Maintenance Schedule
- **Weekly**: Run full test suite
- **Monthly**: Review performance baselines  
- **Quarterly**: Update security test patterns
- **Per release**: Full coverage and quality check

### Getting Help
- Create an issue for test failures
- Consult the test runner output
- Check coverage reports for gaps
- Review security test results for vulnerabilities