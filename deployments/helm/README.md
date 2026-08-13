# IncidentGraph Helm deployment

The chart deploys the control plane, Celery worker, console, six demo services,
PostgreSQL/pgvector, Redis, OpenTelemetry Collector, Prometheus, Tempo, Loki,
Promtail, and Grafana. The application service account has no Kubernetes API
permissions and does not mount an API token; sandbox remediation uses only the
allow-listed demo HTTP control surface.

Create the namespace and required Secret before installing:

```bash
kubectl create namespace incidentgraph
kubectl -n incidentgraph create secret generic incidentgraph-secrets \
  --from-literal=postgres-password="$POSTGRES_PASSWORD" \
  --from-literal=database-url="postgresql+asyncpg://incidentgraph:${POSTGRES_PASSWORD}@incidentgraph-postgres:5432/incidentgraph_db" \
  --from-literal=secret-key="$SECRET_KEY" \
  --from-literal=webhook-signing-secret="$WEBHOOK_SIGNING_SECRET" \
  --from-literal=bootstrap-admin-password="$BOOTSTRAP_ADMIN_PASSWORD" \
  --from-literal=grafana-admin-password="$GRAFANA_ADMIN_PASSWORD"
helm upgrade --install incidentgraph deployments/helm/incidentgraph \
  --namespace incidentgraph --wait --timeout 15m
```

For a kind cluster, build the three application image families locally, load
them with `kind load docker-image`, and retain the pinned tags from
`values.yaml`. Never put secret values in a values file or command history.
