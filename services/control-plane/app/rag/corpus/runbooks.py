RUNBOOKS: list[dict[str, str]] = [
    {
        "id": "rb_db_pool_exhaustion",
        "title": "Runbook: Database Connection Pool Exhaustion Remediation",
        "content": "When services log PostgreSQL connection pool timeouts (active connections == max pool size), increase MAX_CONNECTIONS in service environment variables or configure PgBouncer connection pooling. Check for unclosed DB sessions or missing async context managers in inventory and orders microservices.",
    },
    {
        "id": "rb_slow_query_index",
        "title": "Runbook: Slow Query & Missing Index Diagnosis",
        "content": "Analyze slow query logs (>1000ms execution time). Execute EXPLAIN ANALYZE on PostgreSQL queries. Identify missing indexes on foreign key columns (e.g. orders.user_id, inventory.product_id). Add B-Tree indexes via Alembic migration.",
    },
    {
        "id": "rb_n_plus_one_query",
        "title": "Runbook: N+1 Query Pattern Resolution",
        "content": "High DB query volume proportional to HTTP request count indicates N+1 query patterns. Update SQLAlchemy ORM queries to use joinedload() or selectinload() eager loading options.",
    },
    {
        "id": "rb_db_lock_contention",
        "title": "Runbook: Database Row Lock Contention Mitigation",
        "content": "Row lock contention occurs when concurrent transactions execute SELECT FOR UPDATE on inventory stock items. Implement optimistic locking with version numbers or Redis distributed locking.",
    },
    {
        "id": "rb_bad_deployment_rollback",
        "title": "Runbook: Failed Deployment Rollback Standard Operating Procedure",
        "content": "If 5xx HTTP error rates spike after a deployment, immediately trigger deployment rollback via CI/CD pipeline or update Kubernetes deployment image tag to previous stable git SHA.",
    },
    {
        "id": "rb_payment_gateway_latency",
        "title": "Runbook: Payment Gateway High Latency Response Procedure",
        "content": "When payment processing latency exceeds 3000ms, inspect external payment provider API metrics. Enable circuit breaker to fail fast or switch to fallback payment provider endpoint.",
    },
    {
        "id": "rb_payment_5xx_burst",
        "title": "Runbook: Payment Service 5xx Burst Handling",
        "content": "Spikes in 5xx errors from the payment microservice indicate HTTP 500/502 downstream errors. Verify payment gateway credentials, SSL certificates, and downstream retry exponential backoff settings.",
    },
    {
        "id": "rb_payment_throttling",
        "title": "Runbook: Payment Rate Limiting & Throttling Mitigation",
        "content": "HTTP 429 Too Many Requests from payment provider requires dynamic client rate-limiting on gateway and queuing payment processing tasks in Redis background queue.",
    },
    {
        "id": "rb_auth_latency",
        "title": "Runbook: Auth Token Validation Latency Optimization",
        "content": "High latency in auth token validation affects all downstream endpoints. Enable Redis caching for JWT token verification public keys and session tokens.",
    },
    {
        "id": "rb_auth_errors",
        "title": "Runbook: Auth Invalid Signature & Token Failure Resolution",
        "content": "A high rate of HTTP 401 Unauthorized errors indicates token secret mismatch, clock drift between services, or expired JWT tokens. Verify JWT_SECRET configuration across all microservices.",
    },
    {
        "id": "rb_auth_config_failure",
        "title": "Runbook: Auth Missing Config & Service Start Failure",
        "content": "Auth service crashes on startup when JWT_SECRET or AUTH_DOMAIN environment variables are missing. Ensure all required environment variables are populated in docker-compose.yml or Kubernetes Secret.",
    },
    {
        "id": "rb_inventory_timeout",
        "title": "Runbook: Inventory Reservation Timeout Mitigation",
        "content": "HTTP 504 Gateway Timeout during inventory stock reservation. Increase HTTP client timeout from 2s to 5s, or scale inventory service deployment replicas.",
    },
    {
        "id": "rb_inventory_stale",
        "title": "Runbook: Inventory Stale Cache Invalidation",
        "content": "Discrepancies between cached inventory count and actual database stock level require flushing Redis stock keys `inventory:stock:*` and setting cache TTL to max 60 seconds.",
    },
    {
        "id": "rb_gateway_ratelimit",
        "title": "Runbook: API Gateway Rate Limit Tuning",
        "content": "Gateway HTTP 429 errors under heavy synthetic load. Adjust rate limiter token bucket capacity in gateway config from 100 req/s to 500 req/s.",
    },
    {
        "id": "rb_retry_storm",
        "title": "Runbook: Downstream Retry Storm Prevention",
        "content": "Unbounded retries without exponential backoff cause downstream service collapse. Configure full jitter exponential backoff with max 3 retry attempts on HTTP clients.",
    },
    {
        "id": "rb_cpu_saturation",
        "title": "Runbook: High CPU Saturation Troubleshooting",
        "content": "CPU usage > 90% across worker nodes. Profile Python process using py-spy or cProfile. Identify inefficient regex matching or sync blocking loops in request handler thread pools.",
    },
    {
        "id": "rb_memory_pressure",
        "title": "Runbook: Memory Leak & OOM Killer Remediation",
        "content": "Continuous memory growth leading to container OOMKilled events. Inspect heap snapshots, check for unclosed HTTP response bodies or global array leaks.",
    },
    {
        "id": "rb_redis_unavailable",
        "title": "Runbook: Redis Cache Outage Failover",
        "content": "Redis connection refused or cluster failover. Ensure applications implement graceful fallback to PostgreSQL read replicas when Redis cache is unreachable.",
    },
    {
        "id": "rb_redis_latency",
        "title": "Runbook: Redis High Latency & Slow Command Audit",
        "content": "Execute `SLOWLOG GET 10` on Redis to identify blocking O(N) commands like `KEYS *`. Replace with `SCAN` iterations and set maxmemory-policy to `allkeys-lru`.",
    },
    {
        "id": "rb_queue_backlog",
        "title": "Runbook: Notification Message Queue Backlog Resolution",
        "content": "High queue depth gauge on notifications queue indicates worker starvation. Increase concurrency worker process count or scale notification service replicas.",
    },
    {
        "id": "rb_notification_worker_failure",
        "title": "Runbook: Notification Worker Crash & DLQ Recovery",
        "content": "Dead Letter Queue (DLQ) accumulation due to unhandled message parsing exceptions. Inspect worker error logs, patch message payload schema, and replay DLQ messages.",
    },
    {
        "id": "rb_dns_network_simulation",
        "title": "Runbook: Inter-Service DNS & Network Latency Recovery",
        "content": "DNS resolution failures between microservices. Check CoreDNS pod status, verify local `/etc/hosts` aliases, and configure HTTP client socket reuse.",
    },
    {
        "id": "rb_partial_dependency",
        "title": "Runbook: Partial Dependency Failure Degraded Mode",
        "content": "When non-critical downstream microservices fail (e.g. notifications), ensure gateway serves degraded HTTP 200 responses with empty notification metadata.",
    },
    {
        "id": "rb_cascading_failure",
        "title": "Runbook: Cascading Microservice Failure Isolation",
        "content": "Chain-reaction failures across gateway -> orders -> inventory -> database. Implement bulkheads and circuit breakers to isolate failing downstream components.",
    },
    {
        "id": "rb_timeout_regression",
        "title": "Runbook: Service Timeout Regression Audit",
        "content": "Latencies increasing following a library update. Audit HTTP client connection timeout configurations and socket read timeouts across all services.",
    },
    {
        "id": "rb_circuit_breaker",
        "title": "Runbook: Circuit Breaker Open State Recovery",
        "content": "Circuit breaker trips to OPEN state after 5 consecutive downstream errors. Monitor half-open health probe checks before resetting circuit breaker state to CLOSED.",
    },
    {
        "id": "rb_correlated_signals",
        "title": "Runbook: Misleading Correlated Telemetry Signals Analysis",
        "content": "High CPU on gateway caused by retry loop from payments service error. Root cause is downstream payments service, not gateway CPU performance.",
    },
    {
        "id": "rb_multi_weak_signals",
        "title": "Runbook: Multi-Weak Signal Correlation Analysis",
        "content": "Slight memory increase + 5% latency increase + minor pool count growth indicate slow DB queries without explicit error logs. Correlate traces with slow query logs.",
    },
    {
        "id": "rb_insufficient_evidence",
        "title": "Runbook: Insufficient Telemetry Evidence Action Plan",
        "content": "When metrics and logs are ambiguous, enable DEBUG level logging on target service and capture trace samples with 100% sampling rate.",
    },
    {
        "id": "rb_historical_repeat",
        "title": "Runbook: Historical Postmortem Incident Pattern Matching",
        "content": "Search historical postmortem database for matching root causes when experiencing repeated DB connection pool exhaustion or memory leaks.",
    },
]
