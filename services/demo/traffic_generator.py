import argparse
import asyncio
import random

import httpx

DEFAULT_GATEWAY_URL = "http://localhost:8001"


async def generate_order_request(client: httpx.AsyncClient, gateway_url: str) -> bool:
    user_ids = [f"usr_demo_{i}" for i in range(1001, 1020)]
    sample_items = [
        {"item_id": "item_cpu_sku", "quantity": 1, "price": 49.99},
        {"item_id": "item_mem_sku", "quantity": 2, "price": 19.99},
        {"item_id": "item_ssd_sku", "quantity": 1, "price": 89.99},
    ]

    payload = {
        "user_id": random.choice(user_ids),
        "items": random.sample(sample_items, k=random.randint(1, 3)),
        "total_amount": round(random.uniform(20.0, 250.0), 2),
    }

    try:
        response = await client.post(
            f"{gateway_url}/orders",
            json=payload,
            timeout=5.0,
        )
        return response.status_code == 200
    except Exception as e:
        print(f"[TrafficGenerator] Error sending request: {e}")
        return False


async def run_traffic_generator(
    gateway_url: str, rate_per_sec: float, count: int | None = None
) -> None:
    print(
        f"[TrafficGenerator] Starting synthetic load against {gateway_url} at ~{rate_per_sec} req/s..."
    )
    async with httpx.AsyncClient() as client:
        sent = 0
        success = 0

        while count is None or sent < count:
            ok = await generate_order_request(client, gateway_url)
            sent += 1
            if ok:
                success += 1

            if sent % 10 == 0:
                print(f"[TrafficGenerator] Sent: {sent}, Successful: {success}")

            await asyncio.sleep(1.0 / rate_per_sec)

        print(f"[TrafficGenerator] Complete. Sent: {sent}, Successful: {success}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="IncidentGraph Demo System Traffic Generator")
    parser.add_argument("--gateway-url", default=DEFAULT_GATEWAY_URL, help="Gateway URL")
    parser.add_argument("--rate", type=float, default=2.0, help="Requests per second")
    parser.add_argument(
        "--count", type=int, default=None, help="Number of requests (None = run forever)"
    )
    args = parser.parse_args()

    asyncio.run(run_traffic_generator(args.gateway_url, args.rate, args.count))
