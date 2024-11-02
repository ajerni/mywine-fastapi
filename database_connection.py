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
            logging.warning(f"Missing required environment variables: {', '.join(missing_vars)}")
            return None

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
                max_inactive_connection_lifetime=300.0
            )
            return pool
        except asyncpg.PostgresError as e:
            logging.error(f"PostgreSQL connection error: {str(e)}")
            return None
            
    except Exception as e:
        logging.error(f"Unexpected database initialization error: {str(e)}")
        return None

async def get_db_connection():
    global pool
    
    try:
        if pool is None or pool.is_closed():
            pool = await init_db_pool()
        return pool
    except Exception as e:
        logging.error(f"Error getting database connection: {str(e)}")
        return None

async def close_db_pool():
    """Close the database connection pool if it exists."""
    global pool
    try:
        if pool and not pool.is_closed():
            await pool.close()
            logging.info("Database pool closed successfully")
    except Exception as e:
        logging.error(f"Error closing database pool: {str(e)}")