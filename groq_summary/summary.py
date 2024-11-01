import os
from typing import Optional
from groq import Groq

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

async def generate_wine_summary(wine_name: str, wine_producer: str) -> Optional[str]:
    system_prompt = """You are a knowledgeable wine expert. Provide concise, engaging 2-3 sentence summaries of wines. 
    Focus on the wine's key characteristics, notable features, and what makes it special. Keep responses brief but informative."""
    
    user_prompt = f"Please provide a brief summary of {wine_name} from {wine_producer}."
    
    chat_completion = await client.chat.completions.create(
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
        model="llama3.1-8b-instant",
    )

    return chat_completion.choices[0].message.content
