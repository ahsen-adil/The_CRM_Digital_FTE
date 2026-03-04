import asyncio
from production.database.queries import db_pool

async def test():
    await db_pool.create_pool()
    r = await db_pool.fetchval('SELECT 1')
    print(f'Database OK: {r}')
    await db_pool.close_pool()

asyncio.run(test())
