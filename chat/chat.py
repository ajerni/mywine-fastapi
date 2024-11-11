from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse
import asyncio
from typing import AsyncGenerator

app = FastAPI()

async def generate_response(message: str) -> AsyncGenerator[bytes, None]:
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
        # Encode the chunk as bytes
        yield chunk.encode('utf-8')

