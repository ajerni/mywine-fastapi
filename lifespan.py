from contextlib import asynccontextmanager
from fastapi import FastAPI
import logging
from database_connection import init_db_pool, close_db_pool

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        await init_db_pool()
        logging.info("Application startup complete")
    except Exception as e:
        logging.error(f"Startup error: {str(e)}")
    
    yield
    
    # Shutdown
    try:
        await close_db_pool()
        logging.info("Application shutdown complete")
    except Exception as e:
        logging.error(f"Shutdown error: {str(e)}") 