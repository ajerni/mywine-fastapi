import os
from typing import Optional
from groq import AsyncGroq
from fastapi import HTTPException
import logging
from .database_structure import export_schema

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

async def generate_sql(question: str) -> str:
    try:
        logger.info(f"Starting SQL generation for question: {question}")
        
        system_prompt = f"""
        You are a SQL expert (PostgreSQL). Generate SQL statements to get data from the database.
        Here is the complete database structure:

        {export_schema}

        Important instructions:
        1. Return ONLY the SQL statement, nothing else
        2. Use proper table joins where needed
        3. Follow PostgreSQL syntax
        4. Ensure the statement is complete and executable
        5. Include appropriate WHERE clauses for filtering
        """
        
        user_prompt = f"Generate a SQL statement to: {question}"
        
        logger.info("Sending request to Groq API")
        response = await client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt,
                }
            ],
            model="llama-3.1-8b-instant",
            max_tokens=500,
            temperature=0.1
        )
        
        if not response or not hasattr(response, 'choices') or not response.choices:
            logger.error("No response received from Groq API")
            raise HTTPException(
                status_code=500,
                detail="No response received from AI service"
            )

        # Extract the SQL statement from the response
        sql_statement = response.choices[0].message.content.strip()
        
        # Remove any markdown formatting if present
        sql_statement = sql_statement.replace('```sql', '').replace('```', '').strip()
        
        logger.info(f"Successfully generated SQL statement")
        return sql_statement

    except Exception as e:
        logger.error(f"Error generating SQL statement: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate SQL statement: {str(e)}"
        )
