"""Parallel processing for media organization to improve performance."""

import asyncio
import concurrent.futures
import hashlib
import logging
import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from ..core.types import AnalysisResult

logger = logging.getLogger(__name__)


class ParallelProcessor:
    """Process media files in parallel for better performance."""
    
    def __init__(self, max_workers: int = None):
        """Initialize parallel processor.
        
        Args:
            max_workers: Maximum number of worker threads. Defaults to CPU count.
        """
        self.max_workers = max_workers or min(8, (os.cpu_count() or 1) + 4)
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers)
        logger.info(f"Initialized parallel processor with {self.max_workers} workers")
    
    def process_files_parallel(
        self,
        file_paths: List[Path],
        process_func: Callable[[Path], Any],
        batch_size: int = 50
    ) -> List[Tuple[Path, Any]]:
        """Process multiple files in parallel.
        
        Args:
            file_paths: List of file paths to process
            process_func: Function to process each file
            batch_size: Number of files to process before yielding
            
        Returns:
            List of (file_path, result) tuples
        """
        results = []
        
        # Submit all tasks
        future_to_path = {
            self.executor.submit(process_func, path): path 
            for path in file_paths
        }
        
        # Process completed tasks
        for future in concurrent.futures.as_completed(future_to_path):
            path = future_to_path[future]
            try:
                result = future.result()
                results.append((path, result))
                
                # Log progress periodically
                if len(results) % batch_size == 0:
                    logger.info(f"Processed {len(results)}/{len(file_paths)} files")
                    
            except Exception as e:
                logger.error(f"Error processing {path}: {e}")
                results.append((path, None))
        
        return results
    
    # TODO: Review unreachable code - def extract_metadata_parallel(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - file_paths: List[Path]
    # TODO: Review unreachable code - ) -> Dict[Path, Dict[str, Any]]:
    # TODO: Review unreachable code - """Extract metadata from multiple files in parallel.
        
    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - file_paths: List of file paths
            
    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Dictionary mapping file paths to metadata
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - def extract_with_hash(file_path: Path) -> Dict[str, Any]:
    # TODO: Review unreachable code - """Extract metadata and compute hash."""
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - # Extract basic metadata
    # TODO: Review unreachable code - metadata = self._extract_file_metadata(file_path)
                
    # TODO: Review unreachable code - return metadata
    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.error(f"Failed to extract metadata from {file_path}: {e}")
    # TODO: Review unreachable code - return {}
        
    # TODO: Review unreachable code - results = self.process_files_parallel(file_paths, extract_with_hash)
    # TODO: Review unreachable code - return {path: metadata for path, metadata in results if metadata}
    
    # TODO: Review unreachable code - def _extract_file_metadata(self, file_path: Path) -> Dict[str, Any]:
    # TODO: Review unreachable code - """Extract basic metadata from a file."""
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - stat = file_path.stat()
            
    # TODO: Review unreachable code - # Compute content hash
    # TODO: Review unreachable code - with open(file_path, 'rb') as f:
    # TODO: Review unreachable code - content_hash = hashlib.sha256(f.read()).hexdigest()
            
    # TODO: Review unreachable code - return {
    # TODO: Review unreachable code - 'content_hash': content_hash,
    # TODO: Review unreachable code - 'size': stat.st_size,
    # TODO: Review unreachable code - 'modified': stat.st_mtime,
    # TODO: Review unreachable code - 'exists': True,
    # TODO: Review unreachable code - }
    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - return {
    # TODO: Review unreachable code - 'exists': False,
    # TODO: Review unreachable code - 'error': str(e)
    # TODO: Review unreachable code - }
    
    # TODO: Review unreachable code - def analyze_files_parallel(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - file_paths: List[Path],
    # TODO: Review unreachable code - analyzer_func: Callable[[Path], AnalysisResult]
    # TODO: Review unreachable code - ) -> Dict[Path, AnalysisResult]:
    # TODO: Review unreachable code - """Analyze multiple files in parallel.
        
    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - file_paths: List of file paths
    # TODO: Review unreachable code - analyzer_func: Function to analyze each file
            
    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Dictionary mapping file paths to analysis results
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - results = self.process_files_parallel(file_paths, analyzer_func)
    # TODO: Review unreachable code - return {path: analysis for path, analysis in results if analysis}
    
    # TODO: Review unreachable code - async def process_files_async(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - file_paths: List[Path],
    # TODO: Review unreachable code - async_process_func: Callable[[Path], Any],
    # TODO: Review unreachable code - max_concurrent: int = 10
    # TODO: Review unreachable code - ) -> List[Tuple[Path, Any]]:
    # TODO: Review unreachable code - """Process files asynchronously with concurrency limit.
        
    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - file_paths: List of file paths
    # TODO: Review unreachable code - async_process_func: Async function to process each file
    # TODO: Review unreachable code - max_concurrent: Maximum concurrent operations
            
    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - List of (file_path, result) tuples
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - results = []
    # TODO: Review unreachable code - semaphore = asyncio.Semaphore(max_concurrent)
        
    # TODO: Review unreachable code - async def process_with_semaphore(path: Path) -> Tuple[Path, Any]:
    # TODO: Review unreachable code - async with semaphore:
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - result = await async_process_func(path)
    # TODO: Review unreachable code - return (path, result)
    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.error(f"Error processing {path}: {e}")
    # TODO: Review unreachable code - return (path, None)
        
    # TODO: Review unreachable code - # Process all files concurrently
    # TODO: Review unreachable code - tasks = [process_with_semaphore(path) for path in file_paths]
    # TODO: Review unreachable code - results = await asyncio.gather(*tasks)
        
    # TODO: Review unreachable code - return results
    
    # TODO: Review unreachable code - def compute_hashes_parallel(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - file_paths: List[Path],
    # TODO: Review unreachable code - hash_types: List[str] = ["sha256"]
    # TODO: Review unreachable code - ) -> Dict[Path, Dict[str, str]]:
    # TODO: Review unreachable code - """Compute multiple hash types for files in parallel.
        
    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - file_paths: List of file paths
    # TODO: Review unreachable code - hash_types: Types of hashes to compute
            
    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Dictionary mapping paths to hash values
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - def compute_file_hashes(file_path: Path) -> Dict[str, str]:
    # TODO: Review unreachable code - """Compute all requested hashes for a file."""
    # TODO: Review unreachable code - hashes = {}
            
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - # Read file once
    # TODO: Review unreachable code - with open(file_path, 'rb') as f:
    # TODO: Review unreachable code - content = f.read()
                
    # TODO: Review unreachable code - # Compute each hash type
    # TODO: Review unreachable code - for hash_type in hash_types:
    # TODO: Review unreachable code - if hash_type == "sha256":
    # TODO: Review unreachable code - hashes["sha256"] = hashlib.sha256(content).hexdigest()
    # TODO: Review unreachable code - elif hash_type == "md5":
    # TODO: Review unreachable code - hashes["md5"] = hashlib.md5(content).hexdigest()
    # TODO: Review unreachable code - elif hash_type == "sha1":
    # TODO: Review unreachable code - hashes["sha1"] = hashlib.sha1(content).hexdigest()
                    
    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.error(f"Failed to compute hashes for {file_path}: {e}")
            
    # TODO: Review unreachable code - return hashes
        
    # TODO: Review unreachable code - results = self.process_files_parallel(file_paths, compute_file_hashes)
    # TODO: Review unreachable code - return {path: hashes for path, hashes in results if hashes}
    
    # TODO: Review unreachable code - def shutdown(self):
    # TODO: Review unreachable code - """Shutdown the thread pool executor."""
    # TODO: Review unreachable code - self.executor.shutdown(wait=True)
    
    # TODO: Review unreachable code - def __enter__(self):
    # TODO: Review unreachable code - """Enter context manager."""
    # TODO: Review unreachable code - return self
    
    # TODO: Review unreachable code - def __exit__(self, exc_type, exc_val, exc_tb):
    # TODO: Review unreachable code - """Exit context manager."""
    # TODO: Review unreachable code - self.shutdown()


class ParallelBatchProcessor:
    """Process files in parallel batches for optimal performance."""
    
    def __init__(self, batch_size: int = 100, max_workers: int = None):
        """Initialize batch processor.
        
        Args:
            batch_size: Number of files per batch
            max_workers: Maximum worker threads
        """
        self.batch_size = batch_size
        self.parallel_processor = ParallelProcessor(max_workers)
    
    def process_in_batches(
        self,
        file_paths: List[Path],
        process_func: Callable[[List[Path]], Any],
        combine_func: Optional[Callable[[List[Any]], Any]] = None
    ) -> Any:
        """Process files in batches with parallel execution.
        
        Args:
            file_paths: All file paths to process
            process_func: Function to process a batch of files
            combine_func: Function to combine batch results
            
        Returns:
            Combined results from all batches
        """
        # Split into batches
        batches = [
            file_paths[i:i + self.batch_size]
            for i in range(0, len(file_paths), self.batch_size)
        ]
        
        logger.info(f"Processing {len(file_paths)} files in {len(batches)} batches")
        
        # Process batches in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.parallel_processor.max_workers) as executor:
            batch_results = list(executor.map(process_func, batches))
        
        # Combine results if function provided
        if combine_func:
            return combine_func(batch_results)
        # TODO: Review unreachable code - else:
        # TODO: Review unreachable code - return batch_results
    
    def _create_batches(self, items: List[Any], batch_size: int) -> List[List[Any]]:
        """Create batches from a list of items."""
        for i in range(0, len(items), batch_size):
            yield items[i:i + batch_size]
    
    def shutdown(self):
        """Shutdown the underlying parallel processor."""
        self.parallel_processor.shutdown()