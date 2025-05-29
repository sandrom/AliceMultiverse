# Prometheus Metrics Guide

AliceMultiverse exports Prometheus metrics for monitoring API calls, performance, and system health.

## Quick Start

### Running the Metrics Server

```bash
# Start metrics server on default port 9090
alice metrics-server

# Custom host and port
alice metrics-server --host 0.0.0.0 --port 8080

# Access metrics
curl http://localhost:9090/metrics
```

### Docker Compose Setup

```yaml
services:
  alice-metrics:
    image: alicemultiverse:latest
    command: ["alice", "metrics-server"]
    ports:
      - "9090:9090"
  
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9091:9090"
```

### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'alice'
    static_configs:
      - targets: ['alice-metrics:9090']
```

## Available Metrics

### API Metrics

#### `alice_api_requests_total`
Total number of API requests

Labels:
- `provider`: Provider name (e.g., "openai", "anthropic", "fal.ai")
- `model`: Model used (e.g., "gpt-4", "claude-3", "flux-schnell")
- `operation`: Operation type (e.g., "image", "video", "audio", "text")
- `status`: Request status ("success" or "error")

Example queries:
```promql
# Request rate by provider
rate(alice_api_requests_total[5m])

# Error rate percentage
100 * rate(alice_api_requests_total{status="error"}[5m]) 
/ rate(alice_api_requests_total[5m])

# Requests by model
sum by (model) (rate(alice_api_requests_total[5m]))
```

#### `alice_api_request_duration_seconds`
API request duration histogram

Labels: `provider`, `model`, `operation`

Example queries:
```promql
# Average request duration
rate(alice_api_request_duration_seconds_sum[5m])
/ rate(alice_api_request_duration_seconds_count[5m])

# 95th percentile latency
histogram_quantile(0.95, rate(alice_api_request_duration_seconds_bucket[5m]))

# Slow requests (> 5 seconds)
alice_api_request_duration_seconds_bucket{le="5.0"}
```

#### `alice_api_request_cost_dollars`
API request cost summary

Labels: `provider`, `model`

Example queries:
```promql
# Total cost per hour
rate(alice_api_request_cost_dollars_sum[1h]) * 3600

# Average cost per request
alice_api_request_cost_dollars_sum / alice_api_request_cost_dollars_count

# Cost by provider
sum by (provider) (rate(alice_api_request_cost_dollars_sum[1h]) * 3600)
```

### Provider Health Metrics

#### `alice_provider_health_status`
Provider health status gauge (1=healthy, 0=unhealthy)

Labels: `provider`

Example queries:
```promql
# Unhealthy providers
alice_provider_health_status == 0

# Provider availability percentage
avg_over_time(alice_provider_health_status[1h]) * 100
```

#### `alice_provider_circuit_breaker_state`
Circuit breaker state (0=closed, 1=open, 2=half-open)

Labels: `provider`

Example queries:
```promql
# Open circuit breakers
alice_provider_circuit_breaker_state == 1

# Circuit breaker state changes
changes(alice_provider_circuit_breaker_state[1h])
```

#### `alice_provider_error_rate`
Provider error rate ratio

Labels: `provider`

Example queries:
```promql
# Providers with > 10% error rate
alice_provider_error_rate > 0.1

# Average error rate across all providers
avg(alice_provider_error_rate)
```

### Database Metrics

#### `alice_db_connections_active`
Active database connections gauge

Example queries:
```promql
# Connection usage percentage (assuming pool size of 20)
alice_db_connections_active / 20 * 100

# Connection spikes
max_over_time(alice_db_connections_active[5m])
```

#### `alice_db_query_duration_seconds`
Database query duration histogram

Labels: `query_type` (select, insert, update, delete)

Example queries:
```promql
# Slow queries (> 1 second)
rate(alice_db_query_duration_seconds_bucket{le="1.0"}[5m])

# Query performance by type
avg by (query_type) (
  rate(alice_db_query_duration_seconds_sum[5m])
  / rate(alice_db_query_duration_seconds_count[5m])
)
```

### Asset Processing Metrics

#### `alice_assets_processed_total`
Total assets processed

Labels:
- `media_type`: Type of media (image, video)
- `source`: Source provider
- `status`: Processing status (success, error)

Example queries:
```promql
# Processing rate
rate(alice_assets_processed_total[5m]) * 60

# Success rate
alice_assets_processed_total{status="success"} 
/ alice_assets_processed_total
```

#### `alice_asset_quality_score`
Asset quality score distribution histogram

Labels:
- `media_type`: Type of media
- `quality_type`: Quality assessment type (brisque, sightengine, claude)

Example queries:
```promql
# Average quality score
alice_asset_quality_score_sum / alice_asset_quality_score_count

# Quality distribution
histogram_quantile(0.5, alice_asset_quality_score_bucket)
```

### Event System Metrics

#### `alice_events_published_total`
Total events published

Labels: `event_type`

Example queries:
```promql
# Event rate by type
rate(alice_events_published_total[5m])

# Most common events
topk(10, sum by (event_type) (alice_events_published_total))
```

## Grafana Dashboard

Import the provided dashboard for comprehensive monitoring:

```json
{
  "dashboard": {
    "title": "AliceMultiverse Monitoring",
    "panels": [
      {
        "title": "API Request Rate",
        "targets": [{
          "expr": "rate(alice_api_requests_total[5m])"
        }]
      },
      {
        "title": "API Error Rate",
        "targets": [{
          "expr": "rate(alice_api_requests_total{status='error'}[5m])"
        }]
      },
      {
        "title": "API Latency (p95)",
        "targets": [{
          "expr": "histogram_quantile(0.95, rate(alice_api_request_duration_seconds_bucket[5m]))"
        }]
      },
      {
        "title": "Cost per Hour",
        "targets": [{
          "expr": "rate(alice_api_request_cost_dollars_sum[1h]) * 3600"
        }]
      }
    ]
  }
}
```

## Alerting Rules

Example Prometheus alerting rules:

```yaml
groups:
  - name: alice_alerts
    rules:
      - alert: HighErrorRate
        expr: |
          100 * rate(alice_api_requests_total{status="error"}[5m]) 
          / rate(alice_api_requests_total[5m]) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High API error rate ({{ $value }}%)"
      
      - alert: ProviderDown
        expr: alice_provider_health_status == 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Provider {{ $labels.provider }} is down"
      
      - alert: DatabasePoolExhausted
        expr: alice_db_connections_active / 20 > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Database pool nearly exhausted ({{ $value }}% used)"
      
      - alert: HighAPICost
        expr: rate(alice_api_request_cost_dollars_sum[1h]) * 3600 > 10
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "High API costs (${{ $value }}/hour)"
```

## Custom Metrics

### Adding New Metrics

```python
from prometheus_client import Counter, Histogram, Gauge

# Define metric
my_custom_metric = Counter(
    'alice_my_custom_total',
    'Description of my metric',
    ['label1', 'label2']
)

# Use in code
my_custom_metric.labels(label1='value1', label2='value2').inc()
```

### Decorating Functions

```python
from alicemultiverse.core.metrics import track_api_metrics

@track_api_metrics(provider="custom", model="my-model", operation="process")
async def my_function():
    # Automatically tracks duration, success/error, cost
    result = await do_work()
    result.cost = 0.05  # Will be tracked
    return result
```

## Performance Considerations

### Metric Cardinality

Keep label cardinality low:
```python
# Good - bounded labels
api_requests_total.labels(
    provider="openai",  # ~10 providers
    model="gpt-4",      # ~50 models
    status="success"    # 2 values
)

# Bad - unbounded labels
api_requests_total.labels(
    user_id=user_id,    # Unlimited users!
    request_id=uuid4()  # Unique per request!
)
```

### Metric Collection Overhead

- Counter increment: ~50ns
- Histogram observation: ~200ns
- Gauge set: ~50ns
- Label lookup: ~100ns

Keep metrics out of tight loops.

### Scrape Performance

Default settings handle ~100k metrics:
- Scrape interval: 15s
- Scrape timeout: 10s
- Compression: enabled

## Troubleshooting

### Missing Metrics

1. Check metrics server is running:
   ```bash
   curl http://localhost:9090/health
   ```

2. Verify metric is registered:
   ```bash
   curl http://localhost:9090/metrics | grep metric_name
   ```

3. Check for errors in logs:
   ```bash
   alice --log-level DEBUG metrics-server
   ```

### High Memory Usage

Reduce metric cardinality:
- Fewer label combinations
- Remove unused metrics
- Increase scrape interval

### Prometheus Connection Issues

1. Verify network connectivity
2. Check firewall rules
3. Confirm Prometheus configuration
4. Review Prometheus logs

## Integration Examples

### Kubernetes

```yaml
apiVersion: v1
kind: Service
metadata:
  name: alice-metrics
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "9090"
spec:
  ports:
    - port: 9090
      name: metrics
```

### Docker

```dockerfile
# Expose metrics port
EXPOSE 9090

# Health check
HEALTHCHECK CMD curl -f http://localhost:9090/health || exit 1
```

### CI/CD

```yaml
# GitHub Actions example
- name: Check metrics endpoint
  run: |
    alice metrics-server &
    sleep 5
    curl -f http://localhost:9090/metrics
```