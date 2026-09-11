import type {
  AuditEvent,
  EvaluationSummary,
  Incident,
  IncidentEvent,
  KnowledgeDocument,
  ModelsOverview,
  Scenario,
  TopologyGraph,
} from '@/lib/api';

export const DEMO_INCIDENT_ID = 'inc-payments-042';

const now = '2026-08-13T15:36:19.000Z';

export const demoIncidents: Incident[] = [
  {
    id: DEMO_INCIDENT_ID,
    title: 'Checkout latency spike after payments deploy',
    severity: 'critical',
    status: 'rca_ready',
    target_service: 'payments',
    scenario_id: 'payment-pool-exhaustion',
    summary: 'Payment authorization p95 crossed 2.4s after connection-pool saturation propagated into checkout.',
    created_at: '2026-08-13T15:18:02.000Z',
    updated_at: now,
  },
  {
    id: 'inc-orders-041',
    title: 'Orders retry storm amplifying gateway load',
    severity: 'high',
    status: 'investigating',
    target_service: 'orders',
    scenario_id: 'retry-storm',
    summary: 'Correlated retry amplification across gateway and orders telemetry.',
    created_at: '2026-08-13T14:41:12.000Z',
    updated_at: '2026-08-13T15:12:44.000Z',
  },
  {
    id: 'inc-inventory-039',
    title: 'Inventory cache inconsistency recovered',
    severity: 'medium',
    status: 'resolved',
    target_service: 'inventory',
    summary: 'Bounded cache invalidation restored consistency; post-change probes passed.',
    created_at: '2026-08-13T12:09:32.000Z',
    updated_at: '2026-08-13T12:31:18.000Z',
  },
];

export const demoTimeline: IncidentEvent[] = [
  { id: 'evt-1', incident_id: DEMO_INCIDENT_ID, event_type: 'alert', actor: 'prometheus', title: 'SLO burn-rate alert received', payload: { p95_ms: 2460, error_rate: 0.087, window: '5m' }, created_at: '2026-08-13T15:18:02.000Z' },
  { id: 'evt-2', incident_id: DEMO_INCIDENT_ID, event_type: 'evidence', actor: 'triage-agent', title: 'Payments isolated as primary service', payload: { confidence: 0.94, correlated_signals: ['trace latency', 'pool wait time', 'deploy marker'] }, created_at: '2026-08-13T15:20:19.000Z' },
  { id: 'evt-3', incident_id: DEMO_INCIDENT_ID, event_type: 'hypothesis', actor: 'skeptic-agent', title: 'Network regression contradicted', payload: { finding: 'Inter-service RTT remained below 8ms', verdict: 'rejected' }, created_at: '2026-08-13T15:23:47.000Z' },
  { id: 'evt-4', incident_id: DEMO_INCIDENT_ID, event_type: 'rca', actor: 'rca-agent', title: 'Evidence-backed RCA synthesized', payload: { root_cause: 'Connection pool limit regressed from 40 to 8 in deploy 7f99382', confidence: 0.91, unsupported_claims: 0 }, created_at: now },
];

export const demoTopology: TopologyGraph = {
  nodes: [
    { id: 'gateway', name: 'API Gateway', type: 'service', version: '1.8.2' },
    { id: 'auth', name: 'Auth', type: 'service', version: '1.4.0' },
    { id: 'orders', name: 'Orders', type: 'service', version: '2.1.3' },
    { id: 'payments', name: 'Payments', type: 'service', version: '3.2.1' },
    { id: 'inventory', name: 'Inventory', type: 'service', version: '1.7.6' },
    { id: 'notifications', name: 'Notifications', type: 'service', version: '1.2.4' },
    { id: 'postgres', name: 'PostgreSQL + pgvector', type: 'database', version: '16' },
    { id: 'redis', name: 'Redis', type: 'cache', version: '7' },
  ],
  edges: [
    { source: 'gateway', target: 'auth', protocol: 'HTTP', description: 'identity verification' },
    { source: 'gateway', target: 'orders', protocol: 'HTTP', description: 'checkout orchestration' },
    { source: 'orders', target: 'payments', protocol: 'HTTP', description: 'payment authorization' },
    { source: 'orders', target: 'inventory', protocol: 'HTTP', description: 'stock reservation' },
    { source: 'orders', target: 'notifications', protocol: 'AMQP', description: 'order events' },
    { source: 'payments', target: 'postgres', protocol: 'TCP', description: 'transaction state' },
    { source: 'orders', target: 'redis', protocol: 'TCP', description: 'idempotency cache' },
  ],
};

export const demoScenarios: Scenario[] = [
  ['payment-pool-exhaustion', 'Payments connection pool exhaustion', 'database', 'Reduce the available connection pool and observe queueing propagation.', 'payments', ['orders', 'gateway']],
  ['retry-storm', 'Orders retry amplification', 'resilience', 'Inject transient failures that expose an unsafe retry policy.', 'orders', ['gateway', 'payments']],
  ['inventory-cache-stale', 'Stale inventory cache', 'data-integrity', 'Serve an outdated stock snapshot and trace consistency impact.', 'inventory', ['orders']],
  ['auth-jwks-latency', 'JWKS endpoint latency', 'dependency', 'Delay signing-key refresh and measure authentication degradation.', 'auth', ['gateway']],
  ['notification-backlog', 'Notification queue backlog', 'messaging', 'Throttle consumers while preserving core checkout availability.', 'notifications', ['orders']],
  ['gateway-memory-pressure', 'Gateway memory pressure', 'resource', 'Apply bounded memory pressure and validate early warning signals.', 'gateway', ['auth', 'orders']],
].map(([id, title, category, summary, target, affected]) => ({
  id: id as string,
  title: title as string,
  category: category as string,
  summary: summary as string,
  target_service: target as string,
  affected_services: affected as string[],
  tags: ['verified-scenario', category as string],
}));

const demoMetric = (id: string, title: string, passed = true) => ({
  scenario_id: id,
  scenario_title: title,
  primary_service_match: passed,
  root_cause_match: passed,
  causal_chain_precision: passed ? 0.94 : 0.72,
  causal_chain_recall: passed ? 1 : 0.8,
  unsupported_claim_rate: passed ? 0 : 0.08,
  tool_choice_accuracy: passed ? 1 : 0.75,
  tool_parameter_accuracy: passed ? 1 : 0.8,
  remediation_match: passed,
  latency_seconds: passed ? 1.34 : 2.16,
  total_tokens: 0,
  cost_usd: 0,
  passed,
});

export const demoEvaluation: EvaluationSummary = {
  eval_id: 'eval-proof-20260813',
  benchmark_mode: 'offline',
  scenario_count: 5,
  primary_service_accuracy: 1,
  root_cause_accuracy: 1,
  mean_causal_chain_precision: 0.95,
  mean_causal_chain_recall: 1,
  mean_unsupported_claim_rate: 0,
  mean_tool_choice_accuracy: 1,
  mean_tool_parameter_accuracy: 1,
  remediation_accuracy: 1,
  safe_uncertainty_rate: 1,
  overall_pass_rate: 1,
  mean_latency_seconds: 1.52,
  p50_latency_seconds: 1.34,
  p95_latency_seconds: 2.16,
  total_tokens: 0,
  total_cost_usd: 0,
  metrics: demoScenarios.slice(0, 5).map((scenario) => demoMetric(scenario.id, scenario.title)),
  created_at: now,
};

export const demoKnowledge: KnowledgeDocument[] = [
  { id: 'doc-runbook-pool', source_uri: 'runbook://payments/connection-pool', title: 'Payments connection pool saturation', content: 'When pool wait time rises with stable database CPU, compare the deployed pool limit with the service baseline. Prefer a bounded configuration rollback, then verify authorization p95 and error rate before resolving.', category: 'runbook', status: 'active', version: 4, chunk_count: 7, metadata: { owner: 'payments-sre', reviewed: true }, created_at: now, updated_at: now },
  { id: 'doc-postmortem-retry', source_uri: 'postmortem://orders/retry-amplification', title: 'Orders retry amplification — 2026-07', content: 'An uncapped retry policy amplified a transient payments fault. The lasting fix added exponential backoff, jitter, a retry budget, and circuit-breaker telemetry.', category: 'postmortem', status: 'active', version: 2, chunk_count: 9, metadata: { severity: 'SEV-1' }, created_at: now, updated_at: now },
  { id: 'doc-architecture-checkout', source_uri: 'architecture://checkout/topology', title: 'Checkout service topology', content: 'Gateway delegates identity to Auth and checkout orchestration to Orders. Orders synchronously calls Payments and Inventory, then publishes notification events asynchronously.', category: 'architecture', status: 'active', version: 6, chunk_count: 5, metadata: { domain: 'checkout' }, created_at: now, updated_at: now },
];

export const demoAuditEvents: AuditEvent[] = demoTimeline.map((event, index) => ({
  id: `audit-${index + 1}`,
  actor: event.actor,
  action: event.event_type === 'rca' ? 'investigation.rca.completed' : `investigation.${event.event_type}.recorded`,
  resource_type: 'incident',
  resource_id: DEMO_INCIDENT_ID,
  details: event.payload,
  created_at: event.created_at,
}));

export const demoModels: ModelsOverview = {
  providers: [
    { name: 'openai', configured: false, reachable: false, is_active: false, default_model: 'gpt-4o', supported_models: ['gpt-4o'], detail: 'Live credentials intentionally absent in public showcase.' },
    { name: 'offline evaluation adapter', configured: true, reachable: true, is_active: true, default_model: 'deterministic-proof-v1', supported_models: ['deterministic-proof-v1'], detail: 'Deterministic adapter for reproducible evaluation plumbing—not a live AI quality claim.' },
  ],
  routing_policy: { showcase: 'deterministic-proof-v1', live_primary: 'credential required', fallback: 'credential required' },
  accounting: { total_tokens: 0, total_cost_usd: 0 },
};

export const demoInvestigation = {
  incident_id: DEMO_INCIDENT_ID,
  status: 'awaiting_human_review',
  primary_service: 'payments',
  confidence: 0.91,
  root_cause: 'Connection pool limit regressed from 40 to 8 in the latest payments deployment.',
  causal_chain: ['pool limit regression', 'connection queue saturation', 'authorization latency', 'checkout SLO burn'],
  contradicted_hypotheses: ['database CPU exhaustion', 'inter-service network regression'],
  remediation_plan: {
    plan_id: 'plan-payments-042',
    risk_level: 'medium',
    requires_human_approval: true,
    approved: true,
    steps: [{ step_number: 1, action_type: 'config_rollback', description: 'Restore the last verified payments pool configuration.', target_service: 'payments', parameters: { connection_pool_size: 40, rollout: 'canary', max_unavailable: 0 } }],
  },
};

export const demoPostmortem = {
  title: 'SEV-1: Payments connection pool regression',
  markdown_content: `# SEV-1: Payments connection pool regression\n\n## Summary\nA deployment reduced the payments connection pool from 40 to 8, causing authorization queueing and checkout latency.\n\n## Evidence\n- Pool wait time rose 18× immediately after deploy 7f99382.\n- Database CPU and network RTT remained healthy, contradicting two alternate hypotheses.\n- Trace fan-out localized the first material latency increase to payments.\n\n## Controlled remediation\nA human-approved canary rollback restored the pool limit. Post-change probes verified p95 latency and error-rate recovery before resolution.\n\n## Prevention\nAdd configuration regression checks, pool saturation alerts, and a deployment-time SLO gate.`,
};

export function isDemoMode() {
  return process.env.INCIDENTGRAPH_DEMO_MODE === 'true';
}

export function demoResponse(method: string, segments: string[], searchParams: URLSearchParams): Response {
  const path = segments.join('/');
  if (path === 'auth/me') return Response.json({ email: 'recruiter@showcase.demo', username: 'Portfolio Guest', role: 'viewer' });
  if (path === 'health/live') return Response.json({ status: 'healthy', timestamp: now, service: 'incidentgraph-showcase' });
  if (path === 'health/ready') return Response.json({ status: 'ready', timestamp: now, components: { showcase: { status: 'healthy', message: 'Verified artifact replay' }, deployment: { status: 'healthy', message: 'Vercel serverless' } } });
  if (path === 'health/version') return Response.json({ name: 'IncidentGraph', version: '1.0.1', environment: 'public-showcase', git_sha: '7f99382' });
  if (path === 'incidents') return Response.json(demoIncidents);
  if (/^incidents\/[^/]+\/timeline$/.test(path)) return Response.json(demoTimeline);
  if (/^incidents\/[^/]+$/.test(path)) return Response.json(demoIncidents.find((item) => item.id === segments[1]) ?? demoIncidents[0]);
  if (path === 'topology') return Response.json(demoTopology);
  if (path === 'scenarios') return Response.json(demoScenarios);
  if (/^scenarios\/[^/]+\/trigger$/.test(path)) return Response.json({ run_id: `demo-${segments[1]}`, scenario_id: segments[1], state: 'fault_verified', fault_ack: true, probe_status_code: 503, probe_latency_ms: 2460 });
  if (/^scenarios\/[^/]+\/reset$/.test(path)) return Response.json({ run_id: `demo-${segments[1]}`, scenario_id: segments[1], state: 'baseline_restored', fault_ack: false, probe_status_code: 200, probe_latency_ms: 18 });
  if (/^scenarios\/[^/]+\/run$/.test(path)) return Response.json({ run_id: `demo-${segments[1]}`, scenario_id: segments[1], state: 'fault_verified', fault_ack: true, probe_status_code: 503, probe_latency_ms: 2460 });
  if (path === 'evals/latest' || path === 'evals/run' || /^evals\/[^/]+$/.test(path)) return Response.json(demoEvaluation);
  if (path === 'evals') return Response.json([demoEvaluation]);
  if (path === 'knowledge') return Response.json(demoKnowledge.filter((doc) => searchParams.get('include_archived') === 'true' || doc.status === 'active'));
  if (path === 'knowledge/search') return Response.json(demoKnowledge.map((doc, index) => ({ chunk_id: `chunk-${index + 1}`, document_id: doc.id, content: doc.content, score: 0.032 - index * 0.004, metadata: doc.metadata })));
  if (/^knowledge\/[^/]+/.test(path)) return Response.json(demoKnowledge.find((doc) => doc.id === segments[1]) ?? demoKnowledge[0]);
  if (path === 'audit/events') return Response.json(demoAuditEvents);
  if (path === 'models/providers') return Response.json(demoModels);
  if (path === 'investigations/trigger' || /^investigations\/[^/]+$/.test(path)) return Response.json(demoInvestigation);
  if (/^remediations\/[^/]+\/review$/.test(path)) return Response.json({ status: 'approved', demo: true });
  if (/^remediations\/[^/]+\/execute$/.test(path)) return Response.json({ status: 'verified', dry_run: method === 'POST', actions_executed: 1, post_change_health: { payments_p95_ms: 82, error_rate: 0.001 }, demo: true });
  if (path === 'postmortems/generate' || /^postmortems\/[^/]+$/.test(path)) return Response.json(demoPostmortem);
  return Response.json({ message: `Showcase fixture unavailable for ${method} ${path}` }, { status: 404 });
}
