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
    
    def extract_metadata_parallel(
        self,
        file_paths: List[Path]
    ) -> Dict[Path, Dict[str, Any]]:
        """Extract metadata from multiple files in parallel.
        
        Args:
            file_paths: List of file paths
            
        Returns:
            Dictionary mapping file paths to metadata
        """
        def extract_with_hash(file_path: Path) -> Dict[str, Any]:
            """Extract metadata and compute hash."""
            try:
                # Extract basic metadata
                metadata = self._extract_file_metadata(file_path)
                
                return metadata
            except Exception as e:
                logger.error(f"Failed to extract metadata from {file_path}: {e}")
                return {}
        
        results = self.process_files_parallel(file_paths, extract_with_hash)
        return {path: metadata for path, metadata in results if metadata}
    
    def _extract_file_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract basic metadata from a file."""
        try:
            stat = file_path.stat()
            
            # Compute content hash
            with open(file_path, 'rb') as f:
                content_hash = hashlib.sha256(f.read()).hexdigest()
            
            return {
                'content_hash': content_hash,
                'size': stat.st_size,
                'modified': stat.st_mtime,
                'exists': True,
            }
        except Exception as e:
            return {
                'exists': False,
                'error': str(e)
            }
    
    def analyze_files_parallel(
        self,
        file_paths: List[Path],
        analyzer_func: Callable[[Path], AnalysisResult]
    ) -> Dict[Path, AnalysisResult]:
        """Analyze multiple files in parallel.
        
        Args:
            file_paths: List of file paths
            analyzer_func: Function to analyze each file
            
        Returns:
            Dictionary mapping file paths to analysis results
        """
        results = self.process_files_parallel(file_paths, analyzer_func)
        return {path: analysis for path, analysis in results if analysis}
    
    async def process_files_async(
        self,
        file_paths: List[Path],
        async_process_func: Callable[[Path], Any],
        max_concurrent: int = 10
    ) -> List[Tuple[Path, Any]]:
        """Process files asynchronously with concurrency limit.
        
        Args:
            file_paths: List of file paths
            async_process_func: Async function to process each file
            max_concurrent: Maximum concurrent operations
            
        Returns:
            List of (file_path, result) tuples
        """
        results = []
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_with_semaphore(path: Path) -> Tuple[Path, Any]:
            async with semaphore:
                try:
                    result = await async_process_func(path)
                    return (path, result)
                except Exception as e:
                    logger.error(f"Error processing {path}: {e}")
                    return (path, None)
        
        # Process all files concurrently
        tasks = [process_with_semaphore(path) for path in file_paths]
        results = await asyncio.gather(*tasks)
        
        return results
    
    def compute_hashes_parallel(
        self,
        file_paths: List[Path],
        hash_types: List[str] = ["sha256"]
    ) -> Dict[Path, Dict[str, str]]:
        """Compute multiple hash types for files in parallel.
        
        Args:
            file_paths: List of file paths
            hash_types: Types of hashes to compute
            
        Returns:
            Dictionary mapping paths to hash values
        """
        def compute_file_hashes(file_path: Path) -> Dict[str, str]:
            """Compute all requested hashes for a file."""
            hashes = {}
            
            try:
                # Read file once
                with open(file_path, 'rb') as f:
                    content = f.read()
                
                # Compute each hash type
                for hash_type in hash_types:
                    if hash_type == "sha256":
                        hashes["sha256"] = hashlib.sha256(content).hexdigest()
                    elif hash_type == "md5":
                        hashes["md5"] = hashlib.md5(content).hexdigest()
                    elif hash_type == "sha1":
                        hashes["sha1"] = hashlib.sha1(content).hexdigest()
                    
            except Exception as e:
                logger.error(f"Failed to compute hashes for {file_path}: {e}")
            
            return hashes
        
        results = self.process_files_parallel(file_paths, compute_file_hashes)
        return {path: hashes for path, hashes in results if hashes}
    
    def shutdown(self):
        """Shutdown the thread pool executor."""
        self.executor.shutdown(wait=True)
    
    def __enter__(self):
        """Enter context manager."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        self.shutdown()


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
        else:
            return batch_results
    
    def _create_batches(self, items: List[Any], batch_size: int) -> List[List[Any]]:
        """Create batches from a list of items."""
        for i in range(0, len(items), batch_size):
            yield items[i:i + batch_size]
    
    def shutdown(self):
        """Shutdown the underlying parallel processor."""
        self.parallel_processor.shutdown()