import os
import json
import re
from typing import Dict, Any, Optional
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

# Prefer a current Groq model; llama-3.1-8b-instant is deprecated.
GROQ_SQL_MODEL = os.environ.get("GROQ_SQL_MODEL", "openai/gpt-oss-20b")

_SQL_START = re.compile(
    r"(?is)\b(WITH|SELECT|INSERT|UPDATE|DELETE|EXPLAIN)\b"
)


def _coerce_query(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        for key in ("query", "sql", "sql_query", "statement"):
            nested = _coerce_query(value.get(key))
            if nested:
                return nested
    return ""


def _extract_sql_text(text: str) -> str:
    """Best-effort extraction when the model returns SQL instead of JSON."""
    if not text or not text.strip():
        return ""

    sql_fence = re.search(r"```(?:sql)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if sql_fence:
        candidate = sql_fence.group(1).strip()
        if _SQL_START.search(candidate):
            return candidate.rstrip(";").strip() + ";"

    match = _SQL_START.search(text)
    if not match:
        return ""

    sql = text[match.start():].strip()
    # Drop trailing prose after the first statement when possible
    sql = re.split(r"\n\s*\n", sql, maxsplit=1)[0].strip()
    sql = sql.rstrip("`").strip()
    if not sql.endswith(";"):
        sql += ";"
    return sql


def _parse_response(response: Optional[str]) -> Dict[str, str]:
    """Extract the query/explanation pair from a model response.

    JSON mode should give us a bare object, but models occasionally wrap it in a
    markdown fence, trail prose after it, nest the SQL, or return bare SQL.
    """
    if response is None or not str(response).strip():
        raise ValueError("Empty model response")

    text = str(response)
    candidates = [text]

    for fence in re.finditer(r"```(?:json)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE):
        candidates.append(fence.group(1))

    decoder = json.JSONDecoder()
    for candidate in candidates:
        candidate = candidate.strip()
        start = candidate.find("{")
        if start == -1:
            continue
        try:
            parsed, _ = decoder.raw_decode(candidate[start:])
        except json.JSONDecodeError:
            continue
        if not isinstance(parsed, dict):
            continue

        query = (
            _coerce_query(parsed.get("query"))
            or _coerce_query(parsed.get("sql"))
            or _coerce_query(parsed.get("sql_query"))
            or _coerce_query(parsed.get("statement"))
        )
        if query:
            explanation = parsed.get("explanation") or parsed.get("reason") or ""
            if not isinstance(explanation, str):
                explanation = str(explanation)
            return {
                "query": query,
                "explanation": explanation.strip(),
            }

    # Legacy numbered format: "1. <sql> 2. <explanation>"
    parts = re.split(r"\n\s*2\.\s*", text, maxsplit=1)
    if len(parts) == 2:
        sql = _extract_sql_text(parts[0]) or parts[0].replace("1.", "", 1).strip()
        if sql:
            return {"query": sql, "explanation": parts[1].strip()}

    sql = _extract_sql_text(text)
    if sql:
        return {"query": sql, "explanation": ""}

    raise ValueError("Could not parse response format")


async def generate_sql(question: str) -> Dict[str, Any]:
    """
    Generate SQL query based on natural language question using Groq.
    
    Args:
        question: Natural language question about the wine database
        
    Returns:
        Dictionary containing generated SQL and explanation
    """
    response = None
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

Generate a single PostgreSQL query to answer this question: {question}

Respond with one JSON object containing exactly two fields:
- "query": the PostgreSQL query as a string
- "explanation": a brief explanation of how the query works"""

        # Get completion from Groq
        chat_completion = await client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a SQL expert who generates precise PostgreSQL queries. "
                        "Always answer with a single JSON object with the keys "
                        "'query' and 'explanation', and nothing else."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model=GROQ_SQL_MODEL,
            temperature=0.1,
            max_tokens=1000,
            response_format={"type": "json_object"}
        )

        message = chat_completion.choices[0].message
        response = message.content
        # Some models put usable text only in refusal / secondary fields
        if not response and getattr(message, "refusal", None):
            response = message.refusal

        result = _parse_response(response)
        return {
            "status": "success",
            "sql": result["query"],
            "explanation": result["explanation"],
            "raw_response": response
        }

    except Exception as e:
        logging.error(f"SQL generation error: {str(e)}; raw_response={response!r}")
        return {
            "status": "error",
            "message": f"Failed to generate SQL: {str(e)}",
            "raw_response": response
        }
