#!/usr/bin/env python3
"""Run comprehensive integration tests and generate reports."""

import sys
import time
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import argparse

# Test suites to run
TEST_SUITES = {
    'performance': {
        'module': 'test_large_scale_performance',
        'description': 'Large-scale performance tests',
        'slow': True,
        'tests': [
            'TestLargeScalePerformance::test_large_collection_processing',
            'TestLargeScalePerformance::test_memory_usage_stability',
            'TestLargeScalePerformance::test_concurrent_operations',
            'TestDataIntegrity::test_batch_operation_integrity',
            'TestDataIntegrity::test_transaction_rollback',
            'TestStressScenarios::test_cascading_failures',
            'TestStressScenarios::test_resource_exhaustion',
            'TestStressScenarios::test_long_running_stability',
            'TestPerformanceBenchmarks::test_profile_comparison'
        ]
    },
    'memory': {
        'module': 'test_memory_profiling',
        'description': 'Memory profiling and leak detection',
        'slow': True,
        'tests': [
            'TestMemoryLeaks::test_organizer_memory_leak',
            'TestMemoryLeaks::test_cache_memory_leak',
            'TestMemoryLeaks::test_metrics_memory_leak',
            'TestMemoryLeaks::test_circular_references',
            'TestResourceUsage::test_file_handle_management',
            'TestResourceUsage::test_thread_cleanup',
            'TestMemoryOptimization::test_batch_size_memory_impact'
        ]
    },
    'resilience': {
        'module': 'test_stress_resilience',
        'description': 'Stress and resilience testing',
        'slow': True,
        'tests': [
            'TestChaosEngineering::test_random_failures',
            'TestChaosEngineering::test_cascading_failures',
            'TestChaosEngineering::test_circuit_breaker_activation',
            'TestChaosEngineering::test_resource_exhaustion',
            'TestNetworkResilience::test_network_timeout_handling',
            'TestNetworkResilience::test_intermittent_network',
            'TestConcurrentFailures::test_concurrent_failure_handling',
            'TestConcurrentFailures::test_deadlock_prevention',
            'TestRecoveryMechanisms::test_checkpoint_recovery',
            'TestRecoveryMechanisms::test_state_persistence'
        ]
    }
}


class IntegrationTestRunner:
    """Run integration tests and collect results."""
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path("test_results")
        self.output_dir.mkdir(exist_ok=True)
        self.results = {
            'start_time': datetime.now().isoformat(),
            'suites': {},
            'summary': {
                'total_tests': 0,
                'passed': 0,
                'failed': 0,
                'skipped': 0,
                'duration': 0
            }
        }
    
    def run_suite(self, suite_name: str, suite_config: Dict[str, Any], 
                  verbose: bool = False) -> Dict[str, Any]:
        """Run a single test suite."""
        print(f"\n{'='*60}")
        print(f"Running {suite_name} tests: {suite_config['description']}")
        print(f"{'='*60}")
        
        suite_results = {
            'description': suite_config['description'],
            'tests': {},
            'summary': {
                'total': 0,
                'passed': 0,
                'failed': 0,
                'duration': 0
            }
        }
        
        module = suite_config['module']
        start_time = time.time()
        
        # Run each test
        for test_name in suite_config['tests']:
            print(f"\n→ Running {test_name}...")
            test_start = time.time()
            
            # Construct pytest command
            cmd = [
                'pytest',
                '-xvs' if verbose else '-x',
                f'tests/integration/{module}.py::{test_name}'
            ]
            
            if suite_config.get('slow'):
                cmd.extend(['-m', 'slow'])
            
            # Run test
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            test_duration = time.time() - test_start
            
            # Parse results
            test_result = {
                'status': 'passed' if result.returncode == 0 else 'failed',
                'duration': test_duration,
                'stdout': result.stdout if verbose else '',
                'stderr': result.stderr if result.returncode != 0 else ''
            }
            
            suite_results['tests'][test_name] = test_result
            suite_results['summary']['total'] += 1
            
            if result.returncode == 0:
                suite_results['summary']['passed'] += 1
                print(f"  ✓ Passed ({test_duration:.2f}s)")
            else:
                suite_results['summary']['failed'] += 1
                print(f"  ✗ Failed ({test_duration:.2f}s)")
                if not verbose:
                    print(f"    Error: {result.stderr.split('FAILED')[0].strip()}")
        
        suite_results['summary']['duration'] = time.time() - start_time
        return suite_results
    
    def run_all(self, suites: List[str] = None, verbose: bool = False):
        """Run all or specified test suites."""
        start_time = time.time()
        
        # Determine which suites to run
        suites_to_run = suites or list(TEST_SUITES.keys())
        
        for suite_name in suites_to_run:
            if suite_name not in TEST_SUITES:
                print(f"Warning: Unknown suite '{suite_name}', skipping")
                continue
            
            suite_config = TEST_SUITES[suite_name]
            suite_results = self.run_suite(suite_name, suite_config, verbose)
            
            self.results['suites'][suite_name] = suite_results
            
            # Update summary
            self.results['summary']['total_tests'] += suite_results['summary']['total']
            self.results['summary']['passed'] += suite_results['summary']['passed']
            self.results['summary']['failed'] += suite_results['summary']['failed']
        
        self.results['summary']['duration'] = time.time() - start_time
        self.results['end_time'] = datetime.now().isoformat()
    
    def generate_report(self):
        """Generate test report."""
        # Save JSON results
        json_path = self.output_dir / f"integration_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(json_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        # Generate markdown report
        report_path = self.output_dir / "integration_test_report.md"
        with open(report_path, 'w') as f:
            f.write("# Integration Test Report\n\n")
            f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Summary
            summary = self.results['summary']
            f.write("## Summary\n\n")
            f.write(f"- **Total Tests**: {summary['total_tests']}\n")
            f.write(f"- **Passed**: {summary['passed']} ")
            f.write(f"({summary['passed']/summary['total_tests']*100:.1f}%)\n")
            f.write(f"- **Failed**: {summary['failed']}\n")
            f.write(f"- **Duration**: {summary['duration']:.2f} seconds\n\n")
            
            # Suite details
            f.write("## Test Suites\n\n")
            
            for suite_name, suite_results in self.results['suites'].items():
                suite_summary = suite_results['summary']
                f.write(f"### {suite_name.title()}\n\n")
                f.write(f"*{suite_results['description']}*\n\n")
                f.write(f"- Tests: {suite_summary['total']}\n")
                f.write(f"- Passed: {suite_summary['passed']}\n")
                f.write(f"- Failed: {suite_summary['failed']}\n")
                f.write(f"- Duration: {suite_summary['duration']:.2f}s\n\n")
                
                # Failed tests details
                failed_tests = [
                    (name, result) for name, result in suite_results['tests'].items()
                    if result['status'] == 'failed'
                ]
                
                if failed_tests:
                    f.write("**Failed Tests:**\n\n")
                    for test_name, test_result in failed_tests:
                        f.write(f"- `{test_name}`\n")
                        if test_result.get('stderr'):
                            f.write(f"  ```\n  {test_result['stderr'][:200]}...\n  ```\n")
                
                f.write("\n")
            
            # Performance metrics if available
            if 'performance' in self.results['suites']:
                f.write("## Performance Metrics\n\n")
                f.write("See generated benchmark files for detailed performance data.\n\n")
            
            # Memory analysis if available
            if 'memory' in self.results['suites']:
                f.write("## Memory Analysis\n\n")
                f.write("See memory profiling plots and reports for detailed analysis.\n\n")
            
            # Recommendations
            f.write("## Recommendations\n\n")
            
            if summary['failed'] > 0:
                f.write("### Failed Tests\n\n")
                f.write("- Review failed test logs for root cause analysis\n")
                f.write("- Check for environmental issues or missing dependencies\n")
                f.write("- Consider re-running failed tests in isolation\n\n")
            
            if summary['duration'] > 3600:  # More than 1 hour
                f.write("### Test Duration\n\n")
                f.write("- Consider parallelizing test execution\n")
                f.write("- Review slow tests for optimization opportunities\n")
                f.write("- Use test markers to separate quick and slow tests\n\n")
        
        print(f"\n{'='*60}")
        print("Test Results:")
        print(f"  Total: {summary['total_tests']}")
        print(f"  Passed: {summary['passed']} ({summary['passed']/summary['total_tests']*100:.1f}%)")
        print(f"  Failed: {summary['failed']}")
        print(f"  Duration: {summary['duration']:.2f}s")
        print(f"\nReports saved to:")
        print(f"  JSON: {json_path}")
        print(f"  Markdown: {report_path}")
        
        return summary['failed'] == 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run AliceMultiverse integration tests"
    )
    parser.add_argument(
        '--suites',
        nargs='+',
        choices=list(TEST_SUITES.keys()),
        help='Test suites to run (default: all)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        help='Output directory for reports (default: test_results)'
    )
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Run only quick tests (skip slow tests)'
    )
    
    args = parser.parse_args()
    
    # Filter out slow tests if --quick
    if args.quick:
        for suite in TEST_SUITES.values():
            if suite.get('slow'):
                suite['tests'] = suite['tests'][:2]  # Run only first 2 tests
    
    # Run tests
    runner = IntegrationTestRunner(output_dir=args.output_dir)
    runner.run_all(suites=args.suites, verbose=args.verbose)
    
    # Generate report
    success = runner.generate_report()
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())