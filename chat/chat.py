import asyncio
from typing import AsyncGenerator
from .agents.groq_triage import get_agent_response

async def generate_response(message: str) -> AsyncGenerator[str, None]:
    """
    Generate streaming response chunks using the triage agent.
    Each chunk must be a complete piece of text that can be displayed.
    """
    # Get response chunks from the agent
    chunks = await get_agent_response(message)
    
    for chunk in chunks:
        # Add a small delay to simulate processing
        await asyncio.sleep(0.5)
        # Return string directly, no need to encode
        yield chunk

