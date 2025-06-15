#!/usr/bin/env python3
"""
Performance Benchmarking for AliceMultiverse
Tests system performance with large-scale collections.
"""
import json
import random
import shutil
import sys
import tempfile
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

import psutil

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from alicemultiverse.core.metrics import Metrics
from alicemultiverse.metadata.search import MetadataSearch
from alicemultiverse.organizer.media_organizer import MediaOrganizer
from alicemultiverse.storage.unified_duckdb import UnifiedDuckDB


@dataclass
class BenchmarkResult:
    """Stores results from a benchmark run."""
    operation: str
    item_count: int
    duration_seconds: float
    items_per_second: float
    memory_mb: float
    cpu_percent: float
    success: bool
    error: str = None


class PerformanceBenchmark:
    """Performance testing for AliceMultiverse with large collections."""

    def __init__(self):
        self.results: list[BenchmarkResult] = []
        self.temp_dir = None

    def setup(self):
        """Create temporary test environment."""
        self.temp_dir = tempfile.mkdtemp(prefix="alice_benchmark_")
        self.inbox = Path(self.temp_dir) / "inbox"
        self.organized = Path(self.temp_dir) / "organized"
        self.inbox.mkdir(parents=True)
        self.organized.mkdir(parents=True)

        # Initialize components
        self.db = UnifiedDuckDB(Path(self.temp_dir) / "test.duckdb")
        self.search = MetadataSearch(self.db)
        self.metrics = Metrics()

        print(f"✅ Created test environment in {self.temp_dir}")

    def cleanup(self):
        """Clean up temporary files."""
        if self.temp_dir:
            shutil.rmtree(self.temp_dir)
            print("✅ Cleaned up test environment")

    def generate_test_images(self, count: int) -> list[Path]:
        """Generate test image files with metadata."""
        print(f"🎨 Generating {count} test images...")

        images = []
        sources = ["midjourney", "dall-e-3", "stable-diffusion", "firefly", "ideogram"]
        styles = ["cyberpunk", "minimalist", "surreal", "photorealistic", "abstract"]
        subjects = ["portrait", "landscape", "urban", "nature", "fantasy"]

        for i in range(count):
            # Create dummy image file
            img_path = self.inbox / f"test_image_{i:06d}.png"
            img_path.write_text(f"dummy image {i}")

            # Create metadata
            metadata = {
                "source": random.choice(sources),
                "prompt": f"A {random.choice(styles)} {random.choice(subjects)} scene",
                "seed": random.randint(1000000, 9999999),
                "timestamp": datetime.now().isoformat(),
                "tags": random.sample(styles + subjects, 3),
                "width": 1024,
                "height": 1024,
                "model": f"model_v{random.randint(1, 5)}"
            }

            # Save metadata
            meta_path = self.inbox / ".metadata" / f"{img_path.stem}.json"
            meta_path.parent.mkdir(exist_ok=True)
            meta_path.write_text(json.dumps(metadata, indent=2))

            images.append(img_path)

            if (i + 1) % 100 == 0:
                print(f"  Generated {i + 1}/{count} images...")

        return images

    def benchmark_operation(self, operation: str, func, *args, **kwargs) -> BenchmarkResult:
        """Benchmark a single operation."""
        print(f"\n⏱️  Benchmarking: {operation}")

        # Get initial system state
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Run operation
        start_time = time.time()
        success = True
        error = None
        result = None

        try:
            result = func(*args, **kwargs)
        except Exception as e:
            success = False
            error = str(e)
            print(f"❌ Error: {error}")

        duration = time.time() - start_time

        # Get final system state
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_used = final_memory - initial_memory
        cpu_percent = process.cpu_percent(interval=0.1)

        # Calculate metrics
        item_count = kwargs.get('item_count', len(args[0]) if args and hasattr(args[0], '__len__') else 1)
        items_per_second = item_count / duration if duration > 0 else 0

        benchmark = BenchmarkResult(
            operation=operation,
            item_count=item_count,
            duration_seconds=round(duration, 2),
            items_per_second=round(items_per_second, 2),
            memory_mb=round(memory_used, 2),
            cpu_percent=round(cpu_percent, 2),
            success=success,
            error=error
        )

        self.results.append(benchmark)

        if success:
            print(f"✅ Completed in {benchmark.duration_seconds}s")
            print(f"   • {benchmark.items_per_second} items/second")
            print(f"   • Memory: {benchmark.memory_mb} MB")
            print(f"   • CPU: {benchmark.cpu_percent}%")

        return benchmark

    def benchmark_indexing(self, images: list[Path]):
        """Benchmark database indexing performance."""
        def index_images():
            for img in images:
                # Read metadata
                meta_path = self.inbox / ".metadata" / f"{img.stem}.json"
                metadata = json.loads(meta_path.read_text()) if meta_path.exists() else {}

                # Index in database
                self.db.add_file(
                    path=str(img),
                    file_hash=f"hash_{img.stem}",
                    size=img.stat().st_size,
                    metadata=metadata
                )
            self.db.commit()

        return self.benchmark_operation(
            "Database Indexing",
            index_images,
            item_count=len(images)
        )

    def benchmark_search(self, query_count: int = 100):
        """Benchmark search performance."""
        queries = [
            "cyberpunk portrait",
            "minimalist landscape",
            "surreal urban",
            "photorealistic nature",
            "abstract fantasy",
            "source:midjourney",
            "source:dall-e-3 AND style:cyberpunk",
            "tags:portrait OR tags:landscape"
        ]

        def run_searches():
            results = []
            for i in range(query_count):
                query = random.choice(queries)
                result = self.search.search(query, limit=50)
                results.append(len(result))
            return results

        return self.benchmark_operation(
            "Search Queries",
            run_searches,
            item_count=query_count
        )

    def benchmark_similarity_search(self, sample_count: int = 50):
        """Benchmark similarity search performance."""
        def run_similarity():
            # Get random sample images
            all_files = list(self.db.get_all_files())
            if not all_files:
                return []

            samples = random.sample(all_files, min(sample_count, len(all_files)))
            results = []

            for file_data in samples:
                # Simulate similarity search
                similar = self.search.find_similar(
                    reference_hash=file_data.get('file_hash'),
                    limit=20
                )
                results.append(len(similar))

            return results

        return self.benchmark_operation(
            "Similarity Search",
            run_similarity,
            item_count=sample_count
        )

    def benchmark_organization(self, images: list[Path]):
        """Benchmark file organization performance."""
        organizer = MediaOrganizer(
            inbox_path=self.inbox,
            organized_path=self.organized,
            move_files=False
        )

        def organize_files():
            results = []
            for img in images:
                result = organizer.organize_file(img)
                results.append(result)
            return results

        return self.benchmark_operation(
            "File Organization",
            organize_files,
            item_count=len(images)
        )

    def benchmark_batch_operations(self, batch_size: int = 100):
        """Benchmark batch processing performance."""
        all_files = list(self.inbox.glob("*.png"))
        batches = [all_files[i:i+batch_size] for i in range(0, len(all_files), batch_size)]

        def process_batches():
            results = []
            for batch in batches:
                # Simulate batch processing
                batch_results = []
                for file in batch:
                    # Read file
                    content = file.read_text()
                    # Process (simulate)
                    result = len(content)
                    batch_results.append(result)
                results.extend(batch_results)
            return results

        return self.benchmark_operation(
            f"Batch Processing (size={batch_size})",
            process_batches,
            item_count=len(all_files)
        )

    def generate_report(self):
        """Generate performance report."""
        print("\n" + "="*60)
        print("📊 PERFORMANCE BENCHMARK REPORT")
        print("="*60)

        # Summary statistics
        total_duration = sum(r.duration_seconds for r in self.results)
        total_items = sum(r.item_count for r in self.results)
        successful = sum(1 for r in self.results if r.success)

        print("\n📈 Summary:")
        print(f"   • Total operations: {len(self.results)}")
        print(f"   • Successful: {successful}/{len(self.results)}")
        print(f"   • Total duration: {total_duration:.2f}s")
        print(f"   • Total items processed: {total_items}")

        # Detailed results
        print("\n📊 Detailed Results:")
        print(f"{'Operation':<30} {'Items':<10} {'Time (s)':<10} {'Items/s':<10} {'Memory (MB)':<12} {'CPU %':<8}")
        print("-" * 90)

        for result in self.results:
            status = "✓" if result.success else "✗"
            print(f"{status} {result.operation:<28} {result.item_count:<10} "
                  f"{result.duration_seconds:<10.2f} {result.items_per_second:<10.2f} "
                  f"{result.memory_mb:<12.2f} {result.cpu_percent:<8.2f}")

        # Performance insights
        print("\n💡 Performance Insights:")

        # Find bottlenecks
        slowest = max(self.results, key=lambda r: r.duration_seconds)
        print(f"   • Slowest operation: {slowest.operation} ({slowest.duration_seconds}s)")

        # Memory usage
        highest_memory = max(self.results, key=lambda r: r.memory_mb)
        print(f"   • Highest memory usage: {highest_memory.operation} ({highest_memory.memory_mb} MB)")

        # Throughput
        if self.results:
            avg_throughput = total_items / total_duration
            print(f"   • Average throughput: {avg_throughput:.2f} items/second")

        # Save detailed report
        report_path = Path("benchmark_report.json")
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_operations": len(self.results),
                "successful": successful,
                "total_duration": total_duration,
                "total_items": total_items
            },
            "results": [asdict(r) for r in self.results]
        }

        report_path.write_text(json.dumps(report_data, indent=2))
        print(f"\n📄 Detailed report saved to: {report_path}")

    def run_benchmarks(self, image_counts: list[int] = None):
        """Run complete benchmark suite."""
        if image_counts is None:
            image_counts = [100, 1000, 5000]

        print("🚀 Starting AliceMultiverse Performance Benchmarks")
        print(f"   Testing with collection sizes: {image_counts}")

        try:
            self.setup()

            for count in image_counts:
                print(f"\n{'='*60}")
                print(f"📦 Testing with {count} images")
                print(f"{'='*60}")

                # Generate test data
                images = self.generate_test_images(count)

                # Run benchmarks
                self.benchmark_indexing(images)
                self.benchmark_search()
                self.benchmark_similarity_search()
                self.benchmark_organization(images[:100])  # Organize subset
                self.benchmark_batch_operations()

                # Clean up between runs
                self.db.close()
                self.db = UnifiedDuckDB(Path(self.temp_dir) / f"test_{count}.duckdb")
                self.search = MetadataSearch(self.db)

            # Generate final report
            self.generate_report()

        finally:
            self.cleanup()


def main():
    """Run performance benchmarks."""
    import argparse

    parser = argparse.ArgumentParser(description="AliceMultiverse Performance Benchmarks")
    parser.add_argument(
        "--sizes",
        type=int,
        nargs="+",
        default=[100, 1000],
        help="Collection sizes to test (default: 100 1000)"
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run full benchmark suite including 10k+ images"
    )

    args = parser.parse_args()

    if args.full:
        sizes = [100, 1000, 5000, 10000]
    else:
        sizes = args.sizes

    benchmark = PerformanceBenchmark()
    benchmark.run_benchmarks(sizes)


if __name__ == "__main__":
    main()
