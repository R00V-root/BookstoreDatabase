# Performance Metrics

| Operation | p95 Latency | Notes |
|-----------|-------------|-------|
| Full-text search | ≤150ms | Measured with EXPLAIN ANALYZE using GIN index |
| Checkout | ≤300ms | Serializable transaction with row-level locking |
