import asyncio
from typing import AsyncGenerator

async def generate_response(message: str) -> AsyncGenerator[str, None]:
    """
    Generate streaming response chunks.
    Each chunk must be a complete piece of text that can be displayed.
    """
    # Example response generation
    responses = [
        "I'm analyzing your wine collection...",
        "Based on your collection, ",
        "I notice you have several wines from the Bordeaux region. ",
        "Would you like specific recommendations for similar wines?"
    ]
    
    for chunk in responses:
        # Add a small delay to simulate processing
        await asyncio.sleep(0.5)
        # Return string directly, no need to encode
        yield chunk