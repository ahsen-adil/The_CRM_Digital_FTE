"""
Database connection pool and session management using asyncpg.
Follows FastAPI async patterns for optimal performance.
"""
import asyncpg
from typing import Optional
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

load_dotenv()

class DatabasePool:
    """Database connection pool manager using asyncpg."""
    
    def __init__(self):
        self._pool: Optional[asyncpg.Pool] = None
    
    async def create_pool(self, database_url: Optional[str] = None):
        """
        Create connection pool with optimized settings.
        
        Uses connection pooling for efficient resource management.
        Pool size tuned for serverless/async workloads.
        """
        if self._pool is not None:
            return self._pool
        
        database_url = database_url or os.getenv("DATABASE_URL")
        if not database_url:
            # Fallback to individual connection params
            database_url = (
                f"postgresql://{os.getenv('POSTGRES_USER', 'user')}:"
                f"{os.getenv('POSTGRES_PASSWORD', 'password')}@"
                f"{os.getenv('POSTGRES_HOST', 'localhost')}:"
                f"{os.getenv('POSTGRES_PORT', '5432')}/"
                f"{os.getenv('POSTGRES_DB', 'crm_fte_db')}"
            )
        
        self._pool = await asyncpg.create_pool(
            database_url,
            min_size=5,  # Minimum connections
            max_size=20,  # Maximum connections
            command_timeout=60,  # Query timeout in seconds
            max_inactive_connection_lifetime=300,  # 5 minutes
        )
        
        return self._pool
    
    async def close_pool(self):
        """Close all connections in the pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None
    
    @asynccontextmanager
    async def acquire(self):
        """
        Acquire a connection from the pool.
        
        Usage:
            async with db_pool.acquire() as conn:
                rows = await conn.fetch("SELECT * FROM customers")
        """
        if self._pool is None:
            raise RuntimeError("Database pool not initialized. Call create_pool() first.")
        
        async with self._pool.acquire() as connection:
            yield connection
    
    async def fetch(self, query: str, *args):
        """Execute query and return all rows."""
        async with self.acquire() as conn:
            return await conn.fetch(query, *args)
    
    async def fetchrow(self, query: str, *args):
        """Execute query and return single row."""
        async with self.acquire() as conn:
            return await conn.fetchrow(query, *args)
    
    async def fetchval(self, query: str, *args):
        """Execute query and return single value."""
        async with self.acquire() as conn:
            return await conn.fetchval(query, *args)
    
    async def execute(self, query: str, *args):
        """Execute query and return status."""
        async with self.acquire() as conn:
            return await conn.execute(query, *args)
    
    async def fetchmany(self, query: str, args: list, size: int = 100):
        """Execute query with multiple parameter sets."""
        async with self.acquire() as conn:
            return await conn.fetchmany(query, args, size=size)


# Global database pool instance
db_pool = DatabasePool()


async def get_db_pool() -> DatabasePool:
    """Get or create the database pool."""
    if db_pool._pool is None:
        await db_pool.create_pool()
    return db_pool


async def init_db():
    """Initialize database connection on startup."""
    await db_pool.create_pool()
    print("✅ Database pool initialized")


async def close_db():
    """Close database connections on shutdown."""
    await db_pool.close_pool()
    print("🔒 Database pool closed")
