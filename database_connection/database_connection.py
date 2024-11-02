from os import getenv
from fastapi import HTTPException
import asyncpg
import logging
from typing import Optional

# Global pool variable
pool: Optional[asyncpg.Pool] = None

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
        pool = await asyncpg.create_pool(
            database=getenv('DATABASE'),
            user=getenv('DB_USER'),
            password=getenv('DB_PASSWORD'),
            host=getenv('DB_HOST'),
            port=getenv('DB_PORT'),
            min_size=1,
            max_size=10
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

async def get_db_connection():
    if pool is None:
        await init_db_pool()
    return pool