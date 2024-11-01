import os
from typing import Optional
from groq import AsyncGroq
from fastapi import HTTPException
import logging

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

async def generate_wine_summary(wine_name: str, wine_producer: str) -> Optional[str]:
    try:
        logger.info(f"Generating summary for wine: {wine_name} from {wine_producer}")
        
        system_prompt = """You are a knowledgeable wine expert. Provide concise, engaging 2-3 sentence summaries of wines. 
        Focus on the wine's key characteristics, notable features, and what makes it special. Keep responses brief but informative."""
        
        user_prompt = f"Please provide a brief summary of {wine_name} from {wine_producer}."
        
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
            max_tokens=200,
            temperature=0.7
        )

        if not response or not hasattr(response, 'choices') or not response.choices:
            logger.error("No response received from Groq API")
            raise HTTPException(
                status_code=500,
                detail="No response received from AI service"
            )

        summary = response.choices[0].message.content
        logger.info("Successfully generated wine summary")
        return summary

    except Exception as e:
        logger.error(f"Error generating wine summary: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate summary: {str(e)}"
        )
