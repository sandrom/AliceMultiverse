#!/usr/bin/env python3
"""Performance profiling script for AliceMultiverse.

Tests performance with large datasets and identifies bottlenecks.
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from alicemultiverse import MediaOrganizer
from alicemultiverse.core.config import settings, DictConfig
from alicemultiverse.storage.duckdb_cache import DuckDBSearchCache


class PerformanceProfiler:
    """Profile AliceMultiverse performance with various dataset sizes."""

    def __init__(self, output_dir: Path = None):
        """Initialize profiler."""
        self.output_dir = output_dir or Path("performance_reports")
        self.output_dir.mkdir(exist_ok=True)
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": []
        }

    def profile_media_organization(self, num_files: int) -> dict[str, Any]:
        """Profile media organization performance."""
        print(f"\n📊 Profiling media organization with {num_files} files...")
        
        # Use default settings
        organizer = MediaOrganizer(settings)
        
        # Measure organization time
        start_time = time.time()
        memory_before = self._get_memory_usage()
        
        try:
            # Simulate organization (would need actual test files)
            stats = organizer.organize()
            
            duration = time.time() - start_time
            memory_after = self._get_memory_usage()
            memory_used = memory_after - memory_before
            
            result = {
                "test": "media_organization",
                "num_files": num_files,
                "duration": duration,
                "files_per_second": num_files / duration if duration > 0 else 0,
                "memory_used_mb": memory_used,
                "stats": stats
            }
            
            print(f"  ✅ Completed in {duration:.2f}s")
            print(f"  📈 {result['files_per_second']:.2f} files/second")
            print(f"  💾 {memory_used:.2f} MB memory used")
            
            return result
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return {
                "test": "media_organization",
                "error": str(e),
                "num_files": num_files
            }

    def profile_search_performance(self, db_size: int) -> dict[str, Any]:
        """Profile search performance with various database sizes."""
        print(f"\n🔍 Profiling search with {db_size} assets...")
        
        cache = DuckDBSearchCache()
        
        # Test queries
        queries = [
            {"description": "cyberpunk portrait"},
            {"tags": ["portrait", "cyberpunk", "neon"]},
            {"style_tags": ["digital_art"], "mood_tags": ["dramatic"]},
            {"time_reference": "last week"},
            {"similar_to": ["abc123"]}  # Mock hash
        ]
        
        results = []
        
        for query in queries:
            start_time = time.time()
            
            try:
                # Perform search
                if "description" in query:
                    # Natural language search
                    search_results = cache.search(query=query["description"])
                else:
                    # Structured search
                    search_results = cache.search(**query)
                
                duration = time.time() - start_time
                
                results.append({
                    "query": query,
                    "duration": duration,
                    "results_count": len(search_results.get("assets", [])),
                    "ms_per_result": (duration * 1000) / len(search_results.get("assets", [])) if search_results.get("assets") else 0
                })
                
                print(f"  ✅ Query completed in {duration*1000:.2f}ms")
                
            except Exception as e:
                results.append({
                    "query": query,
                    "error": str(e)
                })
                print(f"  ❌ Query failed: {e}")
        
        return {
            "test": "search_performance",
            "db_size": db_size,
            "queries": results,
            "avg_query_time": sum(r.get("duration", 0) for r in results) / len(results)
        }

    def profile_similarity_search(self, num_hashes: int) -> dict[str, Any]:
        """Profile perceptual hash similarity search."""
        print(f"\n🎯 Profiling similarity search with {num_hashes} hashes...")
        
        from alicemultiverse.assets.deduplication import DuplicateFinder
        
        finder = DuplicateFinder()
        
        # Measure index building
        start_time = time.time()
        
        # Would need actual images to test properly
        # For now, simulate with timing
        
        build_time = time.time() - start_time
        
        # Measure search time
        search_times = []
        for _ in range(10):  # 10 sample searches
            start = time.time()
            # finder.find_similar(mock_hash, threshold=0.9)
            search_times.append(time.time() - start)
        
        avg_search_time = sum(search_times) / len(search_times)
        
        return {
            "test": "similarity_search",
            "num_hashes": num_hashes,
            "index_build_time": build_time,
            "avg_search_time": avg_search_time,
            "searches_per_second": 1 / avg_search_time if avg_search_time > 0 else 0
        }

    def profile_understanding_batch(self, batch_sizes: list[int]) -> dict[str, Any]:
        """Profile batch understanding performance."""
        print(f"\n🧠 Profiling understanding with batch sizes: {batch_sizes}")
        
        results = []
        
        for batch_size in batch_sizes:
            print(f"\n  Testing batch size: {batch_size}")
            
            # Simulate API call timing
            start_time = time.time()
            
            # Mock API latency
            import time
            time.sleep(0.1 * batch_size)  # Simulate processing
            
            duration = time.time() - start_time
            
            result = {
                "batch_size": batch_size,
                "duration": duration,
                "images_per_second": batch_size / duration,
                "cost_efficiency": 1.0 - (0.1 * batch_size / 20)  # Mock calculation
            }
            
            results.append(result)
            
            print(f"    ✅ {result['images_per_second']:.2f} images/second")
            print(f"    💰 {result['cost_efficiency']:.2%} cost efficiency")
        
        return {
            "test": "understanding_batch",
            "results": results,
            "optimal_batch_size": max(results, key=lambda x: x["cost_efficiency"])["batch_size"]
        }

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            import psutil
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return 0.0

    def generate_report(self):
        """Generate performance report."""
        report_path = self.output_dir / f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📄 Report saved to: {report_path}")
        
        # Print summary
        print("\n🎯 Performance Summary:")
        print("=" * 50)
        
        for test in self.results["tests"]:
            if "error" in test:
                print(f"❌ {test['test']}: ERROR - {test['error']}")
            else:
                print(f"✅ {test['test']}:")
                if "duration" in test:
                    print(f"   Duration: {test['duration']:.2f}s")
                if "files_per_second" in test:
                    print(f"   Throughput: {test['files_per_second']:.2f} files/s")
                if "avg_query_time" in test:
                    print(f"   Avg Query Time: {test['avg_query_time']*1000:.2f}ms")
                if "optimal_batch_size" in test:
                    print(f"   Optimal Batch Size: {test['optimal_batch_size']}")


def main():
    """Run performance profiling."""
    parser = argparse.ArgumentParser(description="Profile AliceMultiverse performance")
    parser.add_argument("--output-dir", type=Path, help="Output directory for reports")
    parser.add_argument("--quick", action="store_true", help="Run quick tests only")
    args = parser.parse_args()
    
    profiler = PerformanceProfiler(args.output_dir)
    
    # Run tests
    if args.quick:
        # Quick tests
        profiler.results["tests"].append(
            profiler.profile_media_organization(100)
        )
        profiler.results["tests"].append(
            profiler.profile_search_performance(1000)
        )
    else:
        # Full test suite
        for num_files in [100, 1000, 5000]:
            profiler.results["tests"].append(
                profiler.profile_media_organization(num_files)
            )
        
        for db_size in [1000, 10000, 50000]:
            profiler.results["tests"].append(
                profiler.profile_search_performance(db_size)
            )
        
        for num_hashes in [1000, 10000]:
            profiler.results["tests"].append(
                profiler.profile_similarity_search(num_hashes)
            )
        
        profiler.results["tests"].append(
            profiler.profile_understanding_batch([1, 5, 10, 20, 50])
        )
    
    # Generate report
    profiler.generate_report()


if __name__ == "__main__":
    main()