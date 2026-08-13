import asyncio

from app.db.base import Base
from app.db.session import engine


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


asyncio.run(main())
