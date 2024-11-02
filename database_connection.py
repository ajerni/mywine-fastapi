import asyncpg
from os import getenv
import logging

pool = None

async def init_db_pool():
    global pool
    
    try:
        # If pool already exists and is not closed, return it
        if pool is not None and not pool.is_closed():
            return pool
        
        # Check if we're in Vercel environment
        if getenv('VERCEL_ENV'):
            logging.info("Running in Vercel environment - deferring database connection")
            return None
        
        # Validate environment variables first
        required_env_vars = ['DATABASE', 'DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT']
        missing_vars = [var for var in required_env_vars if not getenv(var)]
        
        if missing_vars:
            error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
            logging.warning(error_msg)
            return None

        pool = await asyncpg.create_pool(
            database=getenv('DATABASE'),
            user=getenv('DB_USER'),
            password=getenv('DB_PASSWORD'),
            host=getenv('DB_HOST'),
            port=getenv('DB_PORT'),
            min_size=1,
            max_size=10,
            command_timeout=60,
            max_inactive_connection_lifetime=300.0
        )
        return pool
    except Exception as e:
        logging.error(f"Database connection error: {str(e)}")
        return None

async def get_db_connection():
    global pool
    
    if pool is None or pool.is_closed():
        pool = await init_db_pool()
    
    return pool 