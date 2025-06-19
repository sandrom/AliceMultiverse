# Integration Testing Guide

This guide covers the comprehensive integration testing suite for AliceMultiverse, including performance benchmarking, memory profiling, and stress testing.

## Overview

The integration testing suite provides:

- **Large-scale performance testing** with collections up to 100K files
- **Memory profiling** to detect leaks and optimize usage
- **Stress testing** with chaos engineering and failure injection
- **Concurrent operation testing** for thread safety
- **Data integrity verification** for batch operations

## Test Categories

### 1. Performance Testing

Tests system performance with large file collections:

```python
# Run performance tests
pytest -m slow tests/integration/test_large_scale_performance.py

# Specific test for 50K files
pytest -k "test_large_collection_processing[50000-300]"
```

#### Key Tests:
- **Large Collection Processing**: Tests 10K, 50K, and 100K file collections
- **Memory Stability**: Monitors memory usage during large operations
- **Concurrent Operations**: Tests multiple organizers running in parallel
- **Performance Benchmarks**: Compares different performance profiles

### 2. Memory Profiling

Detects memory leaks and analyzes usage patterns:

```python
# Run memory profiling tests
pytest -m slow tests/integration/test_memory_profiling.py

# Generate memory usage plots
python -m pytest tests/integration/test_memory_profiling.py::TestMemoryLeaks::test_organizer_memory_leak
```

#### Key Features:
- **Leak Detection**: Tracks memory growth over multiple iterations
- **Resource Usage**: Monitors file handles and thread cleanup
- **Memory Optimization**: Tests impact of different batch sizes
- **Visual Reports**: Generates memory usage plots

### 3. Stress & Resilience Testing

Tests system behavior under extreme conditions:

```python
# Run resilience tests
pytest -m slow tests/integration/test_stress_resilience.py

# Test with chaos injection
pytest -k "test_random_failures"
```

#### Chaos Engineering:
- **Random Failure Injection**: 20-30% failure rates
- **Cascading Failures**: Tests graceful degradation
- **Resource Exhaustion**: Simulates low memory/CPU
- **Network Issues**: Tests timeout and intermittent failures

## Running Integration Tests

### Quick Test Run

For a quick validation (runs only first 2 tests per suite):

```bash
python tests/integration/run_integration_tests.py --quick
```

### Full Test Suite

Run all integration tests (may take 30+ minutes):

```bash
python tests/integration/run_integration_tests.py
```

### Specific Test Suites

Run only specific test categories:

```bash
# Performance tests only
python tests/integration/run_integration_tests.py --suites performance

# Memory and resilience tests
python tests/integration/run_integration_tests.py --suites memory resilience
```

### Verbose Output

For detailed test output:

```bash
python tests/integration/run_integration_tests.py --verbose
```

## Test Reports

The test runner generates comprehensive reports:

### JSON Report
```json
{
  "start_time": "2025-06-18T10:00:00",
  "suites": {
    "performance": {
      "tests": {
        "TestLargeScalePerformance::test_large_collection_processing": {
          "status": "passed",
          "duration": 45.2
        }
      },
      "summary": {
        "total": 9,
        "passed": 8,
        "failed": 1
      }
    }
  }
}
```

### Markdown Report
- Test summary with pass/fail rates
- Failed test details with error messages
- Performance metrics and recommendations
- Memory analysis results

Reports are saved to `test_results/` directory.

## Performance Benchmarking

### Running Benchmarks

Compare different performance profiles:

```python
from tests.integration.test_large_scale_performance import TestPerformanceBenchmarks

benchmarker = TestPerformanceBenchmarks()
benchmarker.test_profile_comparison()
```

### Benchmark Results

Results include:
- Files processed per second
- Memory usage per profile
- Optimal settings for different scenarios

### Custom Benchmarks

Create custom benchmarks:

```python
def run_custom_benchmark():
    config = AliceMultiverseConfig(
        performance={
            'profile': 'custom',
            'max_workers': 16,
            'batch_size': 1000
        }
    )
    
    results = benchmarker.run_benchmark(config, file_count=10000)
    print(f"Rate: {results['files_per_second']:.2f} files/s")
```

## Memory Profiling

### Using the Memory Profiler

```python
from tests.integration.test_memory_profiling import MemoryProfiler

profiler = MemoryProfiler()
profiler.start()

# Your code here
organizer = ResilientMediaOrganizer(config)
results = organizer.organize()

profiler.stop()
profiler.plot_memory_usage("memory_analysis.png")
```

### Memory Reports

The profiler generates:
- Memory usage over time plots
- Top memory consumers by line
- Growth analysis between snapshots
- Statistical summaries

## Chaos Testing

### Chaos Monkey Configuration

```python
from tests.integration.test_stress_resilience import ChaosMonkey

# 30% failure rate
chaos = ChaosMonkey(failure_rate=0.3)

# Custom failure types
chaos.failure_types = [
    FileOperationError,
    DatabaseOperationError,
    TimeoutError
]
```

### Failure Scenarios

Test different failure patterns:

1. **Random Failures**: Uniform distribution
2. **Cascading Failures**: Increasing failure rate
3. **Burst Failures**: Concentrated failure periods
4. **Component Failures**: Target specific components

## CI/CD Integration

### GitHub Actions

```yaml
name: Integration Tests

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  workflow_dispatch:

jobs:
  integration-tests:
    runs-on: ubuntu-latest
    timeout-minutes: 60
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run integration tests
      run: |
        python tests/integration/run_integration_tests.py \
          --output-dir ${{ github.workspace }}/test-results
    
    - name: Upload test results
      uses: actions/upload-artifact@v3
      with:
        name: integration-test-results
        path: test-results/
```

### Local Development

For faster iteration during development:

```bash
# Run specific test with debugging
pytest -xvs --pdb tests/integration/test_large_scale_performance.py::TestLargeScalePerformance::test_memory_usage_stability

# Run with coverage
pytest --cov=alicemultiverse tests/integration/
```

## Best Practices

### 1. Test Data Management

- Use `create_test_files()` helper for consistent test data
- Clean up temporary directories after tests
- Consider file size impact on test duration

### 2. Resource Management

- Reset singletons between tests (`reset_metrics` fixture)
- Force garbage collection for memory tests
- Monitor system resources during tests

### 3. Failure Injection

- Start with low failure rates (10-20%)
- Gradually increase to find breaking points
- Test recovery mechanisms separately

### 4. Performance Baselines

- Establish baseline metrics for comparison
- Track performance over time
- Alert on significant regressions

## Troubleshooting

### Common Issues

1. **Tests timing out**
   - Reduce file counts for initial runs
   - Check system resource availability
   - Use `--quick` flag for faster validation

2. **Memory errors**
   - Ensure sufficient RAM (8GB+ recommended)
   - Use memory_constrained profile
   - Run memory tests in isolation

3. **Flaky tests**
   - Check for race conditions
   - Ensure proper cleanup between tests
   - Use deterministic chaos seeds

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Run with debug output
pytest -xvs --log-cli-level=DEBUG tests/integration/
```

## Demo Script

Try the interactive demo:

```bash
python examples/integration_testing_demo.py
```

This demonstrates:
- Performance testing with different file counts
- Memory profiling with visual output
- Chaos engineering with failure injection
- Concurrent operations testing

## Next Steps

1. **Extend test coverage** for new features
2. **Add custom chaos scenarios** for your use cases
3. **Create performance regression tests**
4. **Integrate with monitoring systems**