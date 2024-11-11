from os import getenv
from fastapi import HTTPException
import asyncpg
import logging
from typing import Optional
import asyncio
from dotenv import load_dotenv
from contextlib import asynccontextmanager

load_dotenv()

# Global pool variable
pool: Optional[asyncpg.Pool] = None

async def init_db_pool():
    global pool
    
    # If pool already exists and is active, return it
    if pool is not None:
        try:
            # Test the connection with a simple query
            async with pool.acquire() as conn:
                await conn.fetchval('SELECT 1')
            return pool
        except Exception as e:
            logging.error(f"Pool test failed: {str(e)}")
            # If the test fails, the pool is not usable
            try:
                await pool.close()
            except Exception:
                pass
            pool = None
    
    # Validate environment variables first
    required_env_vars = ['DATABASE', 'DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT']
    missing_vars = [var for var in required_env_vars if not getenv(var)]
    
    if missing_vars:
        error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
        logging.error(error_msg)
        raise RuntimeError(error_msg)

    try:
        pool = await asyncpg.create_pool(
            database=getenv('DATABASE'),
            user=getenv('DB_USER'),
            password=getenv('DB_PASSWORD'),
            host=getenv('DB_HOST'),
            port=getenv('DB_PORT'),
            min_size=1,
            max_size=10,
            command_timeout=60,
            max_inactive_connection_lifetime=300.0,  # 5 minutes
            server_settings={'application_name': 'mywine_fastapi'}
        )
        return pool
    except asyncpg.PostgresError as e:
        logging.error(f"PostgreSQL error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Database connection failed - PostgreSQL error"
        )
    except Exception as e:
        logging.error(f"Unexpected database connection error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Database connection failed - unexpected error"
        )

@asynccontextmanager
async def get_db_connection():
    """
    Async context manager for database connections.
    """
    conn = await asyncpg.connect(
        user=getenv('DB_USER'),
        password=getenv('DB_PASSWORD'),
        database=getenv('DB_NAME'),
        host=getenv('DB_HOST'),
        port=getenv('DB_PORT')
    )
    try:
        yield conn
    finally:
        await conn.close()

async def close_db_pool():
    global pool
    if pool is not None:
        try:
            await pool.close()
        except Exception as e:
            logging.error(f"Error closing pool: {str(e)}")
        finally:
            pool = None