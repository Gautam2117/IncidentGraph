POSTMORTEMS: list[dict[str, str]] = [
    {
        "id": "pm_001",
        "title": "Postmortem: Inventory Database Pool Starvation Outage",
        "content": "On 2026-05-10, the inventory microservice failed to handle peak order volume due to connection pool starvation (MAX_CONNECTIONS=5). Resolution: Increased connection pool size to 20 and added PgBouncer.",
    },
    {
        "id": "pm_002",
        "title": "Postmortem: Payments Service Latency Spike Outage",
        "content": "On 2026-06-01, payments service experienced 5000ms latency spikes caused by external payment provider throttling. Resolution: Added retry circuit breaker and exponential backoff.",
    },
    {
        "id": "pm_003",
        "title": "Postmortem: Auth Token Invalid Secret Deployment Incident",
        "content": "On 2026-06-15, deployment v1.0.3 contained an invalid JWT_SECRET environment variable causing 100% auth failure. Resolution: Added pre-flight config validation test.",
    },
    {
        "id": "pm_004",
        "title": "Postmortem: Orders Microservice N+1 Database Query Regression",
        "content": "On 2026-07-02, orders list endpoint latency degraded to 4000ms due to N+1 ORM query fetching user profiles in a loop. Resolution: Refactored query to use joinedload().",
    },
    {
        "id": "pm_005",
        "title": "Postmortem: Redis Memory Exhaustion Outage",
        "content": "On 2026-07-20, Redis instance crashed due to unbounded key growth without TTLs. Resolution: Configured `allkeys-lru` eviction policy and standard 600s TTLs.",
    },
    {
        "id": "pm_006",
        "title": "Postmortem: Gateway Rate Limit Lockout",
        "content": "On 2026-08-01, a misconfigured rate limit on gateway blocked all valid client traffic. Resolution: Updated token bucket capacity and added rate limit bypass for internal traffic.",
    },
    {
        "id": "pm_007",
        "title": "Postmortem: Notification Queue Worker Starvation Incident",
        "content": "On 2026-08-05, notifications queue backed up to 50,000 pending items due to worker thread crashes. Resolution: Added auto-restarting worker processes and DLQ monitoring.",
    },
    {
        "id": "pm_008",
        "title": "Postmortem: Row Lock Contention on Product Stock",
        "content": "On 2026-08-10, flash sale caused high database lock contention on inventory row updates. Resolution: Implemented Redis optimistic lock for stock reservations.",
    },
]
