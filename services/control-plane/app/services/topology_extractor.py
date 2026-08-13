from pydantic import BaseModel


class ServiceNode(BaseModel):
    id: str
    name: str
    type: str  # service, database, cache, queue
    version: str = "0.1.0"
    health_url: str | None = None
    metrics_url: str | None = None


class ServiceEdge(BaseModel):
    source: str
    target: str
    protocol: str = "HTTP"
    description: str | None = None


class TopologyGraph(BaseModel):
    nodes: list[ServiceNode]
    edges: list[ServiceEdge]


def extract_system_topology() -> TopologyGraph:
    """Returns the dependency topology map of the IncidentGraph demo system."""
    nodes = [
        ServiceNode(
            id="gateway",
            name="Gateway Service",
            type="service",
            health_url="http://gateway:8001/health/ready",
            metrics_url="http://gateway:8001/metrics",
        ),
        ServiceNode(
            id="auth",
            name="Auth Service",
            type="service",
            health_url="http://auth:8002/health/ready",
            metrics_url="http://auth:8002/metrics",
        ),
        ServiceNode(
            id="orders",
            name="Orders Service",
            type="service",
            health_url="http://orders:8003/health/ready",
            metrics_url="http://orders:8003/metrics",
        ),
        ServiceNode(
            id="payments",
            name="Payments Service",
            type="service",
            health_url="http://payments:8004/health/ready",
            metrics_url="http://payments:8004/metrics",
        ),
        ServiceNode(
            id="inventory",
            name="Inventory Service",
            type="service",
            health_url="http://inventory:8005/health/ready",
            metrics_url="http://inventory:8005/metrics",
        ),
        ServiceNode(
            id="notifications",
            name="Notifications Service",
            type="service",
            health_url="http://notifications:8006/health/ready",
            metrics_url="http://notifications:8006/metrics",
        ),
        ServiceNode(id="postgres", name="PostgreSQL Database", type="database"),
        ServiceNode(id="redis", name="Redis Cache & Queue", type="cache"),
    ]

    edges = [
        ServiceEdge(source="gateway", target="auth", description="Token validation"),
        ServiceEdge(source="gateway", target="orders", description="Order dispatch"),
        ServiceEdge(source="orders", target="inventory", description="Stock reservation"),
        ServiceEdge(source="orders", target="payments", description="Payment charging"),
        ServiceEdge(
            source="orders", target="notifications", description="Order confirmation notification"
        ),
        ServiceEdge(
            source="inventory",
            target="postgres",
            protocol="PostgreSQL",
            description="Inventory records",
        ),
        ServiceEdge(
            source="notifications", target="redis", protocol="Redis", description="Message queue"
        ),
    ]

    return TopologyGraph(nodes=nodes, edges=edges)
