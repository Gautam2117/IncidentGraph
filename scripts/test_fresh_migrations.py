#!/usr/bin/env python3
"""Prove that Alembic can build the schema in a fresh temporary database."""

import asyncio
import os
import re
import subprocess
import uuid

import asyncpg
from sqlalchemy.engine import make_url

from app.core.config import settings

SAFE_DB_NAME = re.compile(r"^incidentgraph_migration_verify_[0-9a-f]{12}$")


async def main() -> None:
    source_url = make_url(str(settings.DATABASE_URL))
    database_name = f"incidentgraph_migration_verify_{uuid.uuid4().hex[:12]}"
    if not SAFE_DB_NAME.fullmatch(database_name):
        raise RuntimeError("Refusing to operate on an unsafe temporary database name")

    connection_args = {
        "host": source_url.host or "localhost",
        "port": source_url.port or 5432,
        "user": source_url.username,
        "password": source_url.password,
    }
    # Use the configured database role against the configured server. The role
    # needs CREATE DATABASE only for this isolated verification command.
    admin = await asyncpg.connect(database="postgres", **connection_args)
    created = False
    try:
        exists = await admin.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", database_name)
        if exists:
            raise RuntimeError("Randomly selected verification database already exists")
        owner = source_url.username or "incidentgraph"
        if not re.fullmatch(r"[a-zA-Z_][a-zA-Z0-9_]{0,62}", owner):
            raise RuntimeError("Refusing to use an unsafe database owner")
        await admin.execute(f'CREATE DATABASE "{database_name}" OWNER "{owner}"')
        created = True

        extension_admin = await asyncpg.connect(database=database_name, **connection_args)
        try:
            await extension_admin.execute("CREATE EXTENSION IF NOT EXISTS vector")
        finally:
            await extension_admin.close()

        migration_url = source_url.set(database=database_name)
        process_env = os.environ.copy()
        process_env["DATABASE_URL"] = migration_url.render_as_string(hide_password=False)
        process_env["PYTHONPATH"] = ".:services/control-plane"
        subprocess.run(  # noqa: S603
            [
                "./.venv/bin/alembic",
                "-c",
                "services/control-plane/alembic.ini",
                "upgrade",
                "head",
            ],
            check=True,
            env=process_env,
        )

        verification = await asyncpg.connect(
            host=source_url.host or "localhost",
            port=source_url.port or 5432,
            user=source_url.username,
            password=source_url.password,
            database=database_name,
        )
        try:
            tables = {
                row["tablename"]
                for row in await verification.fetch(
                    "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
                )
            }
            required = {
                "alembic_version",
                "incidents",
                "investigations",
                "knowledge_chunks",
                "evaluation_runs",
                "remediation_executions",
            }
            missing = required - tables
            if missing:
                raise RuntimeError(f"Fresh migration is missing tables: {sorted(missing)}")
        finally:
            await verification.close()
        print(f"Fresh migration verified ({len(tables)} public tables).")
    finally:
        if created:
            await admin.execute(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = $1 AND pid <> pg_backend_pid()",
                database_name,
            )
            await admin.execute(f'DROP DATABASE "{database_name}"')
        await admin.close()


if __name__ == "__main__":
    asyncio.run(main())
