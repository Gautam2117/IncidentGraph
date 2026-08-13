import argparse
import asyncio
import sys

import httpx

DEFAULT_CONTROL_PLANE_URL = "http://localhost:8000"


async def list_scenarios(base_url: str) -> None:
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{base_url}/api/v1/scenarios")
        if res.status_code != 200:
            print(f"Error fetching scenarios: {res.status_code} {res.text}")
            sys.exit(1)
        scenarios = res.json()
        print("=========================================")
        print(f"Registered Scenarios ({len(scenarios)} total):")
        print("=========================================")
        for sc in scenarios:
            print(
                f" - [{sc['id']}] {sc['title']} ({sc['category']}) -> target: {sc['target_service']}"
            )


async def trigger_scenario_cmd(base_url: str, scenario_id: str) -> None:
    async with httpx.AsyncClient() as client:
        print(f"Triggering scenario '{scenario_id}'...")
        res = await client.post(f"{base_url}/api/v1/scenarios/{scenario_id}/trigger")
        print(f"Response ({res.status_code}): {res.json()}")


async def reset_scenario_cmd(base_url: str, scenario_id: str) -> None:
    async with httpx.AsyncClient() as client:
        print(f"Resetting scenario '{scenario_id}'...")
        res = await client.post(f"{base_url}/api/v1/scenarios/{scenario_id}/reset")
        print(f"Response ({res.status_code}): {res.json()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="IncidentGraph Scenario Runner CLI")
    parser.add_argument("action", choices=["list", "trigger", "reset"], help="Action to perform")
    parser.add_argument("--scenario", help="Scenario ID (required for trigger/reset)")
    parser.add_argument("--url", default=DEFAULT_CONTROL_PLANE_URL, help="Control plane API URL")
    args = parser.parse_args()

    if args.action == "list":
        asyncio.run(list_scenarios(args.url))
    elif args.action == "trigger":
        if not args.scenario:
            print("Error: --scenario is required for trigger action")
            sys.exit(1)
        asyncio.run(trigger_scenario_cmd(args.url, args.scenario))
    elif args.action == "reset":
        if not args.scenario:
            print("Error: --scenario is required for reset action")
            sys.exit(1)
        asyncio.run(reset_scenario_cmd(args.url, args.scenario))
