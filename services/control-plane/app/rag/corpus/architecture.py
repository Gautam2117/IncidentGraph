ARCHITECTURE_DOCS: list[dict[str, str]] = [
    {
        "id": "arch_system_overview",
        "title": "Architecture: IncidentGraph System Overview",
        "content": "IncidentGraph features an observable demo distributed system comprising 6 microservices: Gateway (8001), Auth (8002), Orders (8003), Payments (8004), Inventory (8005), and Notifications (8006). Telemetry is captured via OpenTelemetry SDK and scraped into Prometheus, Tempo, and Loki.",
    },
    {
        "id": "arch_telemetry_flow",
        "title": "Architecture: OpenTelemetry Tracing & Context Propagation",
        "content": "All HTTP requests propagate W3C traceparent headers across service boundaries via TracedHTTPClient. Spans record service attributes, HTTP status codes, and error events exported to Tempo collector at otel-collector:4317.",
    },
]
