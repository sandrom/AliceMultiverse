# Database Connection Pool Management

This guide covers the enhanced database connection pool management system designed to prevent pool exhaustion and detect connection leaks.

## Overview

The enhanced pool management system provides:
- **Connection leak detection** with automatic cleanup
- **Pool exhaustion prevention** through queue management
- **Session timeout enforcement** to prevent long-held connections
- **Comprehensive diagnostics** for troubleshooting
- **Monitoring and alerting** capabilities

## Configuration

Pool settings are configured in `settings.yaml`:

```yaml
providers:
  database:
    # Base pool size - number of persistent connections
    pool_size: 20  # Increased from 10 for better concurrency
    
    # Maximum overflow - temporary connections when pool exhausted
    max_overflow: 40  # Increased from 20 to handle spikes
    
    # Timeout waiting for connection from pool (seconds)
    pool_timeout: 30
    
    # Recycle connections after this many seconds
    pool_recycle: 1800  # Reduced from 3600 to prevent stale connections
    
    # Check connection health before use
    pool_pre_ping: true
```

## Using Managed Sessions

### Basic Usage

Always use `get_managed_session()` instead of `get_session()`:

```python
from alicemultiverse.database.pool_manager import get_managed_session

# Synchronous usage
with get_managed_session() as session:
    asset = session.query(Asset).filter_by(content_hash=hash).first()
    # Session automatically cleaned up
```

### Async Usage

```python
from alicemultiverse.database.pool_manager import get_managed_session_async

# Asynchronous usage
async with get_managed_session_async() as session:
    result = await session.execute(query)
```

### Custom Timeouts

Set session-specific timeouts for long operations:

```python
# 10 minute timeout for batch operations
with get_managed_session(timeout=600) as session:
    for item in large_dataset:
        process_item(session, item)
```

## Connection Leak Detection

The system automatically detects connections held longer than 30 seconds:

```python
# This will trigger a warning after 30 seconds
with get_managed_session() as session:
    # Long-running operation
    time.sleep(60)  # Warning logged with stack trace
```

### Leak Detection Features

1. **Automatic tracking** of all connection checkouts
2. **Stack trace capture** for debugging
3. **Periodic monitoring** with configurable intervals
4. **Automatic cleanup** of expired sessions

## Pool Exhaustion Prevention

The system prevents pool exhaustion through:

1. **Increased pool size** (20 base + 40 overflow)
2. **Connection queuing** with timeouts
3. **Health checks** before connection use
4. **Automatic recycling** of stale connections

## Diagnostics CLI

Use the diagnostics tool to monitor pool health:

```bash
# Show current pool status
python -m alicemultiverse.database.diagnostics status

# Run comprehensive diagnostics
python -m alicemultiverse.database.diagnostics diagnose

# Live monitor (updates every 5 seconds)
python -m alicemultiverse.database.diagnostics monitor

# Health check with auto-fix
python -m alicemultiverse.database.diagnostics health-check --fix

# Export statistics as JSON
python -m alicemultiverse.database.diagnostics export > pool_stats.json
```

### Example Output

```
Database Pool Status
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┓
┃ Metric              ┃ Value  ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━┩
│ Pool Size           │ 20     │
│ Active Connections  │ 5/20   │
│ Overflow in Use     │ 0      │
│ Avg Checkout Time   │ 0.234s │
│ Health Status       │ healthy│
└─────────────────────┴────────┘
```

## Best Practices

### 1. Always Use Context Managers

```python
# Good
with get_managed_session() as session:
    do_work(session)

# Bad - manual session management
session = SessionLocal()
try:
    do_work(session)
finally:
    session.close()  # Easy to forget!
```

### 2. Keep Sessions Short-Lived

```python
# Good - multiple short sessions
for batch in batches:
    with get_managed_session() as session:
        process_batch(session, batch)

# Bad - one long session
with get_managed_session() as session:
    for batch in batches:  # Session held for entire loop
        process_batch(session, batch)
```

### 3. Set Appropriate Timeouts

```python
# Quick operations (default 5 minutes)
with get_managed_session() as session:
    result = session.query(Asset).first()

# Batch operations (custom timeout)
with get_managed_session(timeout=1800) as session:  # 30 minutes
    migrate_large_dataset(session)
```

### 4. Handle Pool Exhaustion Gracefully

```python
from alicemultiverse.database.pool_manager import get_managed_session

try:
    with get_managed_session() as session:
        # Do work
        pass
except TimeoutError:
    logger.error("Database pool exhausted - consider increasing pool_size")
    # Implement fallback or retry logic
```

## Monitoring Integration

### Prometheus Metrics

Export pool metrics for monitoring:

```python
from prometheus_client import Gauge
from alicemultiverse.database.config import get_pool_monitor

# Create metrics
db_pool_size = Gauge('alice_db_pool_size', 'Database pool size')
db_pool_used = Gauge('alice_db_pool_used', 'Active database connections')
db_pool_overflow = Gauge('alice_db_pool_overflow', 'Overflow connections in use')

# Update metrics
monitor = get_pool_monitor()
if monitor:
    stats = monitor.get_stats()
    pool_status = stats['pool_status']
    
    db_pool_size.set(pool_status['size'])
    db_pool_used.set(pool_status['checked_out'])
    db_pool_overflow.set(pool_status['overflow'])
```

### Health Checks

Include pool health in application health checks:

```python
from alicemultiverse.database.pool_manager import get_pool_diagnostics

@app.get("/health/database")
async def database_health():
    diag = get_pool_diagnostics()
    
    # Determine health status
    is_healthy = (
        diag['potential_leaks'] == 0 and
        len(diag['recommendations']) == 0
    )
    
    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "details": diag
    }
```

## Troubleshooting

### Pool Exhaustion

**Symptoms:**
- `TimeoutError: Failed to acquire database connection`
- Slow response times
- Application hangs

**Solutions:**
1. Increase `pool_size` and `max_overflow` in settings
2. Review code for connection leaks
3. Optimize long-running queries
4. Use connection pooling middleware

### Connection Leaks

**Symptoms:**
- Warning logs about long-held connections
- Gradual performance degradation
- Pool exhaustion despite low load

**Solutions:**
1. Review stack traces in leak warnings
2. Ensure all sessions use context managers
3. Set appropriate timeouts
4. Enable automatic cleanup

### Stale Connections

**Symptoms:**
- `OperationalError: server closed the connection`
- Random connection failures

**Solutions:**
1. Enable `pool_pre_ping: true`
2. Reduce `pool_recycle` time
3. Handle connection errors gracefully

## Performance Tuning

### Pool Size Calculation

Recommended pool size:
```
pool_size = (number_of_workers × average_connections_per_worker) + buffer
```

For Alice:
- Workers: 4-8 (typical deployment)
- Connections per worker: 2-3
- Buffer: 20-50%
- **Result**: pool_size=20, max_overflow=40

### Connection Recycling

Balance between performance and reliability:
- **Shorter recycle** (1800s): More overhead, fewer stale connections
- **Longer recycle** (3600s): Better performance, risk of stale connections

### Monitoring Recommendations

1. **Alert on pool exhaustion**: > 80% usage
2. **Alert on connection leaks**: > 5 potential leaks
3. **Track average checkout time**: Baseline for performance
4. **Monitor error rates**: Connection failures indicate issues

## Future Enhancements

Planned improvements:
- Read/write splitting for scalability
- Connection pooling per service
- Automatic pool size adjustment
- Advanced leak detection heuristics
- Integration with APM tools