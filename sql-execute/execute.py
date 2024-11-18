import os
from typing import Optional
from groq import AsyncGroq
from fastapi import HTTPException
import logging
from database_connection.database_connection import get_db_connection
from typing import Dict, Any, List

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check for API key at module level
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if not GROQ_API_KEY:
    logger.error("GROQ_API_KEY is not set in environment variables")
    raise RuntimeError("GROQ_API_KEY environment variable is required")

# Initialize Groq client
try:
    client = AsyncGroq(api_key=GROQ_API_KEY)
except Exception as e:
    logger.error(f"Failed to initialize Groq client: {str(e)}")
    raise RuntimeError(f"Failed to initialize Groq client: {str(e)}")

async def execute_sql(sql_query: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Execute an SQL query and return the results in JSON format.
    
    Args:
        sql_query (str): The SQL query to execute
        
    Returns:
        Dict[str, List[Dict[str, Any]]]: Dictionary with "result" key containing the query results
        
    Raises:
        HTTPException: If there's an error executing the query
    """
    try:
        # Get database pool
        pool = await get_db_connection()
        
        async with pool.acquire() as connection:
            # Execute query and fetch results
            rows = await connection.fetch(sql_query)
            
            # Convert rows to list of dictionaries
            results = [dict(row) for row in rows]
            
            return {"result": results}
            
    except Exception as e:
        logging.error(f"Error executing SQL query: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error executing SQL query: {str(e)}"
        )
