# Performance Guide

This guide covers the performance optimizations available in AliceMultiverse to handle large media collections efficiently.

## Overview

AliceMultiverse includes several performance features designed to handle collections of thousands of media files:

- **Parallel Processing**: Process multiple files concurrently
- **Batch Operations**: Efficient database operations for bulk updates
- **Performance Profiles**: Pre-configured settings for different use cases
- **Memory Management**: Controlled memory usage for large collections

## Performance Profiles

AliceMultiverse provides several pre-configured performance profiles:

### Default Profile
Balanced performance suitable for most use cases:
- 8 parallel workers
- 100 files per batch
- Moderate memory usage

### Fast Profile
Maximum performance for powerful machines:
```bash
export ALICE_PERFORMANCE=fast
alice mcp-server
```
- 16 parallel workers
- 200 files per batch
- Higher memory usage (8GB)
- Ideal for: High-end machines with many CPU cores

### Memory Constrained Profile
For systems with limited RAM:
```bash
export ALICE_PERFORMANCE=memory_constrained
alice mcp-server
```
- 4 parallel workers
- 50 files per batch
- Limited cache size (100MB)
- Ideal for: Older machines or when running alongside other apps

### Large Collection Profile
Optimized for processing thousands of files:
```bash
export ALICE_PERFORMANCE=large_collection
alice mcp-server
```
- 12 parallel workers
- 500 files per batch
- Large transaction sizes
- Ideal for: Initial organization of large collections

## Custom Performance Configuration

You can customize performance settings in `settings.yaml`:

```yaml
performance:
  max_workers: 8              # Number of parallel threads
  batch_size: 100            # Files processed per batch
  enable_batch_operations: true
  parallel_metadata_extraction: true
  
  # Database optimization
  batch_insert_size: 500     # Records per batch insert
  transaction_size: 1000     # Operations per transaction
  
  # Memory management
  max_memory_cache_mb: 500   # Maximum cache size in MB
  cache_ttl_seconds: 3600    # Cache time-to-live
  
  # Understanding system
  understanding_batch_size: 20    # Images per API batch
  max_concurrent_api_calls: 5     # Concurrent API requests
```

## Parallel Processing

The organizer automatically uses parallel processing for large batches:

1. **Small batches (<100 files)**: Sequential processing
2. **Large batches (>100 files)**: Parallel processing with multiple workers

### How It Works

- Files are divided into batches
- Each batch is processed by a separate worker thread
- Results are combined and saved to the database
- Progress is logged periodically

### Monitoring Progress

When processing large collections, you'll see progress updates:
```
Processing 5000 files in 50 batches
Processed 1000/5000 files
Processed 2000/5000 files
...
```

## Batch Database Operations

For storage backends that support it (DuckDB), batch operations provide significant performance improvements:

- **Batch Inserts**: Insert hundreds of records in a single transaction
- **Batch Updates**: Update tags for multiple assets at once
- **Transaction Management**: Automatic rollback on errors

### Performance Comparison

| Operation | Sequential | Batch | Improvement |
|-----------|------------|-------|-------------|
| Insert 1000 assets | ~30s | ~2s | 15x faster |
| Update 500 tags | ~15s | ~1s | 15x faster |
| Search by tags | ~5s | ~0.5s | 10x faster |

## Memory Optimization

### Cache Management

The system uses intelligent caching to reduce repeated operations:

- **Metadata Cache**: Stores file analysis results
- **Search Cache**: Caches frequent search queries
- **Understanding Cache**: Stores AI analysis results

### Memory Limits

Set memory limits to prevent excessive usage:
```yaml
performance:
  max_memory_cache_mb: 500      # Total cache size
  search_cache_size: 1000       # Number of cached queries
  cache_ttl_seconds: 3600       # Cache expiration
```

## Best Practices

### 1. Initial Organization

For first-time organization of large collections:
```bash
# Use large collection profile
export ALICE_PERFORMANCE=large_collection

# Run organization
alice --inbox ~/Pictures/AI-Generated --organized ~/Pictures/AI-Organized
```

### 2. Daily Updates

For regular updates with new files:
```bash
# Use default or fast profile
export ALICE_PERFORMANCE=fast

# Watch mode for continuous processing
alice --watch
```

### 3. Understanding System

When using AI providers for image analysis:
```yaml
performance:
  understanding_batch_size: 20    # Process 20 images per API call
  max_concurrent_api_calls: 5     # 5 parallel API requests
```

### 4. Search Optimization

For better search performance:
- Enable search result caching
- Use batch search operations when possible
- Consider using similarity search for related images

## Monitoring Performance

### Enable Performance Metrics

```yaml
performance:
  enable_performance_monitoring: true
  log_performance_metrics: true
  metrics_interval_seconds: 60
```

This will log performance statistics every minute:
```
Performance metrics:
- Files processed: 1250
- Average processing time: 0.15s/file
- Memory usage: 245MB
- Cache hit rate: 85%
```

### Troubleshooting Performance Issues

1. **Slow Processing**
   - Check CPU usage - increase max_workers if CPU is underutilized
   - Verify batch operations are enabled
   - Consider using a faster performance profile

2. **High Memory Usage**
   - Reduce batch_size
   - Lower max_memory_cache_mb
   - Use memory_constrained profile

3. **Database Errors**
   - Reduce batch_insert_size
   - Lower transaction_size
   - Check disk space

## Performance Tips

1. **SSD Storage**: Use SSD for both media files and database
2. **Sufficient RAM**: At least 4GB for default profile, 8GB for fast profile
3. **Multi-core CPU**: Performance scales with CPU cores
4. **Network Storage**: Avoid processing files over slow network connections
5. **API Rate Limits**: Configure understanding batch size based on provider limits

## Future Optimizations

Planned performance improvements:
- GPU acceleration for similarity search
- Distributed processing across multiple machines
- Incremental indexing for faster updates
- Smart prefetching for predicted operations