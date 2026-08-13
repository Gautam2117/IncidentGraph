export interface HealthLiveResponse { status: string; timestamp: string; service: string }
export interface ComponentHealth { status: string; message?: string }
export interface HealthReadyResponse { status: string; timestamp: string; components: Record<string, ComponentHealth> }
export interface HealthVersionResponse { name: string; version: string; environment: string; git_sha: string }

export interface Incident {
  id: string;
  title: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  status: 'open' | 'investigating' | 'rca_ready' | 'remediating' | 'resolved' | 'closed';
  target_service?: string;
  scenario_id?: string;
  summary?: string;
  created_at: string;
  updated_at: string;
}

export interface IncidentEvent {
  id: string;
  incident_id: string;
  event_type: string;
  actor: string;
  title: string;
  payload: Record<string, unknown>;
  created_at: string;
}

export interface ServiceNode { id: string; name: string; type: string; version: string; health_url?: string; metrics_url?: string }
export interface ServiceEdge { source: string; target: string; protocol: string; description?: string }
export interface TopologyGraph { nodes: ServiceNode[]; edges: ServiceEdge[] }

export interface Scenario {
  id: string;
  title: string;
  category: string;
  summary: string;
  target_service: string;
  affected_services: string[];
  tags: string[];
}

export interface ScenarioRun {
  run_id: string;
  scenario_id: string;
  state: string;
  fault_ack?: boolean;
  probe_status_code?: number;
  probe_latency_ms?: number;
  error_message?: string;
}

export interface ScenarioMetric {
  scenario_id: string;
  scenario_title: string;
  primary_service_match: boolean;
  root_cause_match: boolean;
  causal_chain_precision: number;
  causal_chain_recall: number;
  unsupported_claim_rate: number;
  tool_choice_accuracy: number;
  tool_parameter_accuracy: number;
  remediation_match: boolean;
  latency_seconds: number;
  total_tokens: number;
  cost_usd: number;
  passed: boolean;
}

export interface EvaluationSummary {
  eval_id: string;
  benchmark_mode: 'offline' | 'live';
  scenario_count: number;
  primary_service_accuracy: number;
  root_cause_accuracy: number;
  mean_causal_chain_precision: number;
  mean_causal_chain_recall: number;
  mean_unsupported_claim_rate: number;
  mean_tool_choice_accuracy: number;
  mean_tool_parameter_accuracy: number;
  remediation_accuracy: number;
  safe_uncertainty_rate: number;
  overall_pass_rate: number;
  mean_latency_seconds: number;
  p50_latency_seconds: number;
  p95_latency_seconds: number;
  total_tokens: number;
  total_cost_usd: number;
  metrics: ScenarioMetric[];
  created_at: string;
}

export interface KnowledgeDocument {
  id: string;
  source_uri?: string;
  title: string;
  content: string;
  category: string;
  status: string;
  version: number;
  chunk_count: number;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface AuditEvent {
  id: string;
  actor: string;
  action: string;
  resource_type: string;
  resource_id: string;
  details: Record<string, unknown>;
  created_at: string;
}

export interface ProviderStatus { name: string; configured: boolean; reachable: boolean; is_active: boolean; default_model: string; supported_models: string[]; detail: string }
export interface ModelsOverview { providers: ProviderStatus[]; routing_policy: Record<string, string>; accounting: Record<string, number> }
export interface KnowledgeSearchResult { chunk_id: string; document_id: string; content: string; score: number; metadata: Record<string, unknown> }

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api/proxy/${path.replace(/^\//, '')}`, {
    ...init,
    headers: { 'content-type': 'application/json', ...(init?.headers || {}) },
    cache: 'no-store',
  });
  if (response.status === 401 && typeof window !== 'undefined') {
    window.dispatchEvent(new Event('incidentgraph:unauthorized'));
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.message || body.detail || `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export const fetchHealthLive = () => apiFetch<HealthLiveResponse>('health/live');
export const fetchHealthReady = () => apiFetch<HealthReadyResponse>('health/ready');
export const fetchHealthVersion = () => apiFetch<HealthVersionResponse>('health/version');
export const fetchIncidents = () => apiFetch<Incident[]>('incidents');
export const fetchIncidentDetail = (id: string) => apiFetch<Incident>(`incidents/${id}`);
export const fetchIncidentTimeline = (id: string) => apiFetch<IncidentEvent[]>(`incidents/${id}/timeline`);
export const fetchTopology = () => apiFetch<TopologyGraph>('topology');
export const fetchScenarios = () => apiFetch<Scenario[]>('scenarios');
export const triggerScenario = (id: string) => apiFetch<ScenarioRun>(`scenarios/${id}/trigger`, { method: 'POST' });
export const resetScenario = (id: string) => apiFetch<ScenarioRun>(`scenarios/${id}/reset`, { method: 'POST' });
export const fetchLatestEvaluation = () => apiFetch<EvaluationSummary>('evals/latest');
export const fetchEvaluations = () => apiFetch<EvaluationSummary[]>('evals?limit=30');
export const fetchEvaluation = (id: string) => apiFetch<EvaluationSummary>(`evals/${id}`);
export const runEvaluation = (mode: 'offline' | 'live', scenarios?: string[]) => apiFetch<EvaluationSummary>('evals/run', {
  method: 'POST',
  body: JSON.stringify({ benchmark_mode: mode, scenarios: scenarios || null, export_json: true }),
});
export const fetchKnowledge = (includeArchived = false) => apiFetch<KnowledgeDocument[]>(`knowledge?include_archived=${includeArchived}`);
export const fetchKnowledgeDocument = (id: string) => apiFetch<KnowledgeDocument>(`knowledge/${id}`);
export const reindexKnowledgeDocument = (id: string) => apiFetch<KnowledgeDocument>(`knowledge/${id}/reindex`, { method: 'POST' });
export const archiveKnowledgeDocument = (id: string) => apiFetch<KnowledgeDocument>(`knowledge/${id}`, { method: 'DELETE' });
export const fetchAuditEvents = () => apiFetch<AuditEvent[]>('audit/events?limit=200');
export const fetchModelProviders = () => apiFetch<ModelsOverview>('models/providers');
export const searchKnowledge = (query: string, mode: 'vector' | 'lexical' | 'hybrid') => apiFetch<KnowledgeSearchResult[]>('knowledge/search', { method: 'POST', body: JSON.stringify({ query, mode, top_k: 10 }) });
export const fetchScenarioRun = (id: string) => apiFetch<ScenarioRun>(`scenarios/${id}/run`);
