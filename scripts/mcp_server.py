#!/usr/bin/env python3
import asyncio
import sys

from mcp.server.stdio import stdio_server

from app.mcp.server import server


async def main() -> None:
    """Runs the MCP server over stdio using the official SDK."""
    sys.stderr.write("IncidentGraph MCP Server running over stdio...\n")
    sys.stderr.flush()

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
