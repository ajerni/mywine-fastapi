import asyncio
from typing import AsyncGenerator
from .agents.groq_triage import get_agent_response

async def generate_response(message: str, user_id: int) -> AsyncGenerator[str, None]:
    """
    Generate streaming response chunks using the sommelier agent.
    
    Args:
        message: The user's input message
        user_id: The ID of the user whose wine collection to reference
        
    Yields:
        str: Response chunks from the sommelier
    """
    # Get response chunks from the agent with the specific user_id
    chunks = await get_agent_response(message, user_id)
    
    for chunk in chunks:
        # Add a small delay to simulate processing
        await asyncio.sleep(0.5)
        yield chunk

