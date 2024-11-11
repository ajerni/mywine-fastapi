from os import getenv
from fastapi import HTTPException
import asyncpg
import logging
from typing import Optional
import asyncio
from contextlib import asynccontextmanager

# Global pool variable
pool: Optional[asyncpg.Pool] = None
pool_lock = asyncio.Lock()  # Add lock for thread safety

async def init_db_pool():
    global pool
    
    # Validate environment variables first
    required_env_vars = ['DATABASE', 'DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT']
    missing_vars = [var for var in required_env_vars if not getenv(var)]
    
    if missing_vars:
        error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
        logging.error(error_msg)
        raise RuntimeError(error_msg)

    try:
        new_pool = await asyncpg.create_pool(
            database=getenv('DATABASE'),
            user=getenv('DB_USER'),
            password=getenv('DB_PASSWORD'),
            host=getenv('DB_HOST'),
            port=getenv('DB_PORT'),
            min_size=2,  # Increased min size
            max_size=20,  # Increased max size
            command_timeout=60,
            max_inactive_connection_lifetime=300.0,
            server_settings={'application_name': 'mywine_fastapi'}
        )
        return new_pool
    except Exception as e:
        logging.error(f"Pool creation error: {str(e)}")
        raise

@asynccontextmanager
async def get_db_connection():
    global pool
    async with pool_lock:  # Use lock to prevent concurrent pool creation/recreation
        try:
            if pool is None:
                pool = await init_db_pool()
            
            # Get connection from pool
            async with pool.acquire() as connection:
                try:
                    # Test connection
                    await connection.fetchval('SELECT 1')
                    yield connection
                except Exception as e:
                    logging.error(f"Connection test failed: {str(e)}")
                    # If connection test fails, recreate pool
                    if pool:
                        await pool.close()
                    pool = await init_db_pool()
                    # Try one more time with new pool
                    async with pool.acquire() as new_connection:
                        yield new_connection
                        
        except Exception as e:
            logging.error(f"Database connection error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Database connection failed"
            )

async def close_db_pool():
    global pool
    if pool is not None:
        try:
            await pool.close()
        except Exception as e:
            logging.error(f"Error closing pool: {str(e)}")
        finally:
            pool = None