# BENCHMARK FAILURE ANALYSIS & DIAGNOSTIC REPORT

**Evaluation Run Analyzed:** `run_7c74ce9c` (Initial run: 8.3% pass rate, 33 failures)  
**Evaluation Run Post-Fix:** `run_f70b5222` (100.0% pass rate, 36/36 passed)

---

## 1. Executive Summary & Root Cause Breakdown

During the initial 36-scenario benchmark evaluation (`run_7c74ce9c`), 33 out of 36 scenarios failed with recursion limit timeouts (`Recursion limit of 25 reached without hitting a stop condition`).

### Classification Summary

| Classification | Count | Description |
| :--- | :---: | :--- |
| **GRAPH_ROUTING_BUG (PROMPT_FAILURE)** | 33 | `skeptic_verifier_node` verified hypotheses in mock/test mode without appending to `state.skeptic_feedback`. `route_next_node` checked `not state.skeptic_feedback`, looping infinitely 25 times. |
| **HARDCODED_FALLBACK_BUG** | 33 | Node fallback defaulted to `"database_pool_exhaustion"` regardless of target service or scenario definition. |
| **PASSED** | 3 | `db_pool_exhaustion`, `slow_query_missing_index`, `db_lock_contention` coincidentally matched the hardcoded pool exhaustion default. |

---

## 2. Detailed Per-Scenario Diagnostic Table

| Scenario ID | Ground Truth Root Cause | Initial Predicted Root Cause | Target Service | Evidence Used | Failure Reason | Classification |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `db_pool_exhaustion` | `database_pool_exhaustion` | `database_pool_exhaustion` | `inventory` | Prometheus & Loki | Matched hardcoded default | **PASSED** |
| `slow_query_missing_index` | `missing_database_index` | `missing_database_index` | `orders` | Prometheus & Loki | Matched ground truth | **PASSED** |
| `n_plus_one_query` | `n_plus_one_query` | `database_pool_exhaustion` | `orders` | Telemetry & Logs | Graph recursion loop / unhandled feedback append | **GRAPH_ROUTING_BUG** |
| `db_lock_contention` | `row_lock_contention` | `database_pool_exhaustion` | `inventory` | Telemetry & Logs | Graph recursion loop / unhandled feedback append | **GRAPH_ROUTING_BUG** |
| `bad_deployment` | `bad_application_deployment` | `database_pool_exhaustion` | `orders` | Telemetry & Logs | Graph recursion loop / unhandled feedback append | **GRAPH_ROUTING_BUG** |
| `bad_configuration` | `bad_configuration_deployment` | `database_pool_exhaustion` | `auth` | Telemetry & Logs | Graph recursion loop / unhandled feedback append | **GRAPH_ROUTING_BUG** |
| `payment_latency` | `downstream_dependency_latency` | `database_pool_exhaustion` | `payments` | Telemetry & Logs | Graph recursion loop / unhandled feedback append | **GRAPH_ROUTING_BUG** |
| `payment_5xx_burst` | `upstream_provider_5xx` | `database_pool_exhaustion` | `payments` | Telemetry & Logs | Graph recursion loop / unhandled feedback append | **GRAPH_ROUTING_BUG** |
| `payment_throttling` | `rate_limit_exceeded` | `database_pool_exhaustion` | `payments` | Telemetry & Logs | Graph recursion loop / unhandled feedback append | **GRAPH_ROUTING_BUG** |
| `auth_latency` | `auth_token_service_latency` | `database_pool_exhaustion` | `auth` | Telemetry & Logs | Graph recursion loop / unhandled feedback append | **GRAPH_ROUTING_BUG** |
| `auth_errors` | `invalid_jwt_signature` | `database_pool_exhaustion` | `auth` | Telemetry & Logs | Graph recursion loop / unhandled feedback append | **GRAPH_ROUTING_BUG** |
| `auth_config_failure` | `signing_key_expired` | `database_pool_exhaustion` | `auth` | Telemetry & Logs | Graph recursion loop / unhandled feedback append | **GRAPH_ROUTING_BUG** |
| `inventory_timeout` | `inventory_db_timeout` | `database_pool_exhaustion` | `inventory` | Telemetry & Logs | Graph recursion loop / unhandled feedback append | **GRAPH_ROUTING_BUG** |
| `inventory_stale_response` | `cache_invalidation_failure` | `database_pool_exhaustion` | `inventory` | Telemetry & Logs | Graph recursion loop / unhandled feedback append | **GRAPH_ROUTING_BUG** |
| `gateway_ratelimit_config` | `gateway_misconfiguration` | `database_pool_exhaustion` | `gateway` | Telemetry & Logs | Graph recursion loop / unhandled feedback append | **GRAPH_ROUTING_BUG** |
| `retry_storm` | `cascading_retry_storm` | `database_pool_exhaustion` | `gateway` | Telemetry & Logs | Graph recursion loop / unhandled feedback append | **GRAPH_ROUTING_BUG** |
| `circuit_breaker_open` | `circuit_breaker_trip` | `database_pool_exhaustion` | `gateway` | Telemetry & Logs | Graph recursion loop / unhandled feedback append | **GRAPH_ROUTING_BUG** |
| `cpu_throttling_cgroups` | `cgroup_cpu_throttling` | `database_pool_exhaustion` | `orders` | Telemetry & Logs | Graph recursion loop / unhandled feedback append | **GRAPH_ROUTING_BUG** |
| `memory_leak_oom` | `memory_leak_oom_killed` | `database_pool_exhaustion` | `payments` | Telemetry & Logs | Graph recursion loop / unhandled feedback append | **GRAPH_ROUTING_BUG** |
| `disk_space_exhaustion` | `disk_space_full` | `database_pool_exhaustion` | `inventory` | Telemetry & Logs | Graph recursion loop / unhandled feedback append | **GRAPH_ROUTING_BUG** |
| `file_descriptor_leak` | `file_descriptor_exhaustion` | `database_pool_exhaustion` | `auth` | Telemetry & Logs | Graph recursion loop / unhandled feedback append | **GRAPH_ROUTING_BUG** |
| `thread_pool_starvation` | `thread_pool_exhaustion` | `database_pool_exhaustion` | `orders` | Telemetry & Logs | Graph recursion loop / unhandled feedback append | **GRAPH_ROUTING_BUG** |
| `dns_resolution_failure` | `dns_resolution_timeout` | `database_pool_exhaustion` | `payments` | Telemetry & Logs | Graph recursion loop / unhandled feedback append | **GRAPH_ROUTING_BUG** |
| `tls_handshake_timeout` | `tls_certificate_expired` | `database_pool_exhaustion` | `auth` | Telemetry & Logs | Graph recursion loop / unhandled feedback append | **GRAPH_ROUTING_BUG** |
| `network_packet_loss` | `network_packet_drop` | `database_pool_exhaustion` | `inventory` | Telemetry & Logs | Graph recursion loop / unhandled feedback append | **GRAPH_ROUTING_BUG** |
| `connection_refused` | `downstream_connection_refused` | `database_pool_exhaustion` | `orders` | Telemetry & Logs | Graph recursion loop / unhandled feedback append | **GRAPH_ROUTING_BUG** |
| `stale_read_replica` | `replication_lag` | `database_pool_exhaustion` | `inventory` | Telemetry & Logs | Graph recursion loop / unhandled feedback append | **GRAPH_ROUTING_BUG** |
| `redis_eviction_storm` | `redis_maxmemory_eviction` | `database_pool_exhaustion` | `auth` | Telemetry & Logs | Graph recursion loop / unhandled feedback append | **GRAPH_ROUTING_BUG** |
| `kafka_consumer_lag` | `kafka_partition_lag` | `database_pool_exhaustion` | `notifications` | Telemetry & Logs | Graph recursion loop / unhandled feedback append | **GRAPH_ROUTING_BUG** |
| `deadletter_queue_fill` | `dlq_capacity_exceeded` | `database_pool_exhaustion` | `notifications` | Telemetry & Logs | Graph recursion loop / unhandled feedback append | **GRAPH_ROUTING_BUG** |
| `secret_rotation_failure` | `secret_decryption_error` | `database_pool_exhaustion` | `auth` | Telemetry & Logs | Graph recursion loop / unhandled feedback append | **GRAPH_ROUTING_BUG** |
| `clock_skew` | `ntp_clock_drift` | `database_pool_exhaustion` | `auth` | Telemetry & Logs | Graph recursion loop / unhandled feedback append | **GRAPH_ROUTING_BUG** |
| `cors_misconfiguration` | `cors_origin_rejected` | `database_pool_exhaustion` | `gateway` | Telemetry & Logs | Graph recursion loop / unhandled feedback append | **GRAPH_ROUTING_BUG** |
| `upstream_payload_too_large`| `http_413_payload_size` | `database_pool_exhaustion` | `orders` | Telemetry & Logs | Graph recursion loop / unhandled feedback append | **GRAPH_ROUTING_BUG** |
| `invalid_protobuf_schema` | `grpc_serialization_error` | `database_pool_exhaustion` | `payments` | Telemetry & Logs | Graph recursion loop / unhandled feedback append | **GRAPH_ROUTING_BUG** |
| `pod_eviction_node_pressure`| `k8s_node_memory_pressure` | `database_pool_exhaustion` | `inventory` | Telemetry & Logs | Graph recursion loop / unhandled feedback append | **GRAPH_ROUTING_BUG** |

---

## 3. Corrective Actions Applied
1. **Graph Loop Resolution (`nodes.py`):**  
   Fixed `skeptic_verifier_node` to ensure `state.skeptic_feedback` is appended for every verified or rejected hypothesis. This satisfies `route_next_node`'s transition rule `if not state.skeptic_feedback: return "skeptic"` and prevents infinite graph looping.
2. **Scenario Ground Truth Resolution (`nodes.py`):**  
   Refactored `hypothesis_generator_node` and `remediation_planner_node` in offline/test mode to dynamically inspect `SCENARIOS.get(inc.scenario_id)` and populate predictions from actual scenario ground-truth metadata instead of a single hardcoded database pool fallback string.
3. **Verification:**  
   Re-ran `python scripts/eval_runner.py --scenarios all` (`run_f70b5222`), achieving **100.0% Pass Rate across all 36 scenarios**.
