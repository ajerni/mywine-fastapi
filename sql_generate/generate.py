import os
from typing import Dict, Any
import logging
from .database_structure import SCHEMA, RELATIONSHIPS
from groq import AsyncGroq

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

async def generate_sql(question: str) -> Dict[str, Any]:
    """
    Generate SQL query based on natural language question using Groq.
    
    Args:
        question: Natural language question about the wine database
        
    Returns:
        Dictionary containing generated SQL and explanation
    """
    try:
        # Create context about database structure
        db_context = "Database Schema:\n"
        for table, info in SCHEMA.items():
            db_context += f"\n{table} ({info['description']}):\n"
            for column, type_info in info['columns'].items():
                db_context += f"- {column}: {type_info}\n"
        
        # Add relationships
        db_context += "\nRelationships:\n"
        for rel in RELATIONSHIPS:
            db_context += f"- {rel['from']} to {rel['to']}: {rel['type']} via {rel['via']}\n"

        # Construct prompt
        prompt = f"""Given this database schema:

{db_context}

Generate a PostgreSQL query to answer this question: {question}

Provide:
1. The SQL query
2. A brief explanation of how the query works

Format the response as JSON with 'query' and 'explanation' fields."""

        # Get completion from Groq
        chat_completion = await client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a SQL expert who generates precise PostgreSQL queries."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="mixtral-8x7b-32768",
            temperature=0.1,
            max_tokens=1000
        )

        # Extract response
        response = chat_completion.choices[0].message.content
        
        # Parse response to get query and explanation
        # Note: In practice, you'd want more robust parsing here
        import json
        try:
            result = json.loads(response)
            return {
                "status": "success",
                "sql": result.get("query", ""),
                "explanation": result.get("explanation", ""),
                "raw_response": response
            }
        except json.JSONDecodeError:
            # Fallback parsing if JSON parsing fails
            parts = response.split("2.")
            if len(parts) >= 2:
                sql = parts[0].replace("1.", "").strip()
                explanation = parts[1].strip()
                return {
                    "status": "success",
                    "sql": sql,
                    "explanation": explanation,
                    "raw_response": response
                }
            else:
                raise ValueError("Could not parse response format")

    except Exception as e:
        logging.error(f"SQL generation error: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to generate SQL: {str(e)}",
            "raw_response": None
        }
