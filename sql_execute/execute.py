import logging
from typing import Dict, Any, List
from fastapi import HTTPException
from database_connection.database_connection import get_db_connection

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
