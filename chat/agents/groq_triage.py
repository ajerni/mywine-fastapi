import os
from dotenv import load_dotenv
from groq import Groq
from typing import List, Dict, Any
from database_connection.wine_queries import get_user_wine_collection, analyze_wine_collection
from decimal import Decimal

# Load environment variables
load_dotenv()
os.environ['GROQ_API_KEY'] = os.getenv('GROQ_API_KEY')

if "GROQ_API_KEY" not in os.environ:
    raise ValueError("GROQ_API_KEY environment variable is not set")

# Initialize Groq client
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

async def get_wine_collection_summary(user_id: int) -> str:
    """Create a summary of the user's wine collection for the agent's context."""
    wines = await get_user_wine_collection(user_id)
    if not wines:
        return "No wines found in collection."
    
    # Get analytics
    stats = await analyze_wine_collection(wines)
    
    summary = f"""Wine Collection Summary:
Total bottles: {stats['total_bottles']}
Unique wines: {stats['total_unique_wines']}
Total collection value: ${stats['total_value']:,.2f}
Average bottle value: ${stats['average_bottle_value']:,.2f}

Most expensive wine: {stats['most_expensive']['wine']} ({stats['most_expensive']['year']}) 
by {stats['most_expensive']['producer']} - ${stats['most_expensive']['price']:,.2f}

Value by country:
{chr(10).join(f'- {country}: ${value:,.2f}' for country, value in stats['value_by_country'].items())}

Bottles by country:
{chr(10).join(f'- {country}: {count} bottles' for country, count in stats['countries'].most_common())}

Individual Wines:
"""
    
    for wine in wines:
        wine_value = Decimal(str(wine['price'])) * Decimal(str(wine['quantity']))
        summary += f"- {wine['wine_name']} ({wine['year']}) by {wine['producer']}\n"
        summary += f"  Region: {wine['country']}, {wine['region']}\n"
        summary += f"  Grapes: {wine['grapes']}\n"
        summary += f"  Quantity: {wine['quantity']} x {wine['bottle_size']}\n"
        summary += f"  Value: ${wine_value:,.2f} (${wine['price']:,.2f} per bottle)\n"
        if wine['note_text']:
            summary += f"  Notes: {wine['note_text']}\n"
        summary += "\n"
    
    return summary

async def get_agent_response(message: str, user_id: int) -> List[str]:
    """
    Get response from Groq about the user's wine collection.
    """
    # Get the user's wine collection
    wine_collection = await get_wine_collection_summary(user_id)
    
    # Create the system prompt
    system_prompt = """You are a knowledgeable wine sommelier. Your responsibilities include:
    - Answering questions about wines in the user's collection
    - Providing wine pairing recommendations
    - Sharing insights about wine regions, vintages, and varietals
    
    Base your recommendations on the user's actual wine collection when possible.
    If asked about wines not in the collection, provide general expert advice.
    
    Always reference specific wines from the collection when answering questions.
    Be concise but informative in your responses."""
    
    # Create the complete context
    user_prompt = f"""Here is the user's current wine collection:

{wine_collection}

User question: {message}"""

    # Get completion from Groq
    completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        #model="llama-3.1-70b-versatile",
        model="llama-3.1-8b-instant",
        temperature=0.7,
        max_tokens=1000,
        top_p=1,
        stream=True
    )
    
    # Process the streaming response
    chunks = []
    current_chunk = ""
    
    for chunk in completion:
        if chunk.choices[0].delta.content:
            current_chunk += chunk.choices[0].delta.content
            if len(current_chunk) >= 80:  # Send chunks of reasonable size
                chunks.append(current_chunk)
                current_chunk = ""
    
    if current_chunk:  # Don't forget the last chunk
        chunks.append(current_chunk)
        
    return chunks