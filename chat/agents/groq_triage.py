import os
from dotenv import load_dotenv
from groq import Groq
from typing import List, Dict, Any
from .microagent import Microagent, Agent
from database_connection.wine_queries import get_user_wine_collection, analyze_wine_collection

# Load environment variables
load_dotenv()
os.environ['GROQ_API_KEY'] = os.getenv('GROQ_API_KEY')

if "GROQ_API_KEY" not in os.environ:
    raise ValueError("GROQ_API_KEY environment variable is not set")

# Initialize Groq client
groq = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
    default_params={"tool_choice": "auto"}
)

async def get_wine_collection_summary(user_id: int) -> str:
    """
    Create a summary of the user's wine collection for the agent's context.
    """
    wines = await get_user_wine_collection(user_id)
    if not wines:
        return "No wines found in collection."
    
    # Get analytics
    stats = await analyze_wine_collection(wines)
    
    summary = f"""Wine Collection Summary:
Total bottles: {stats['total_bottles']}
Unique wines: {stats['total_unique_wines']}

Most expensive wine: {stats['most_expensive']['wine']} ({stats['most_expensive']['year']}) 
by {stats['most_expensive']['producer']} - ${stats['most_expensive']['price']}

Wines by country:
{chr(10).join(f'- {country}: {count} bottles' for country, count in stats['countries'].most_common())}

Individual Wines:
"""
    
    for wine in wines:
        summary += f"- {wine['wine_name']} ({wine['year']}) by {wine['producer']}\n"
        summary += f"  Region: {wine['country']}, {wine['region']}\n"
        summary += f"  Grapes: {wine['grapes']}\n"
        summary += f"  Quantity: {wine['quantity']} x {wine['bottle_size']}\n"
        if wine['note_text']:
            summary += f"  Notes: {wine['note_text']}\n"
        summary += "\n"
    
    return summary

# Initialize single Sommelier agent
sommelier_agent = Agent(
    model="llama-3.1-70b-versatile",
    name="Sommelier",
    tool_choice="auto",
    instructions="""
    You are a knowledgeable wine sommelier. Your responsibilities include:
    - Answering questions about wines in the user's collection
    - Providing wine pairing recommendations
    - Providing wine and food pairing recommendations
    - Sharing insights about wine regions, vintages, and varietals
    
    You can answer analytical questions about the collection such as:
    - Number of wines from specific countries/regions
    - Most expensive wines
    - Wines from specific vintages
    - Wines made from specific grape varieties
    - Total bottle counts and values
    
    Base your recommendations on the user's actual wine collection when possible.
    If asked about wines not in the collection, provide general expert advice.
    
    When making recommendations, consider:
    - The user's existing collection
    - Wine regions and vintages
    - Grape varieties and their characteristics
    - Food pairing compatibility
    
    Always reference specific wines from the collection when answering questions.
    """
)

async def get_agent_response(message: str, user_id: int) -> List[str]:
    """
    Get response from the sommelier agent and return it as a list of chunks.
    """
    client = Microagent(
        llm_type='groq',
        default_params={"tool_choice": "auto"}
    )
    
    # Get the user's wine collection
    wine_collection = await get_wine_collection_summary(user_id)
    
    # Add wine collection context to the message
    context_message = f"""
    Here is the user's current wine collection:
    
    {wine_collection}
    
    User question: {message}
    """
    
    response = client.run(
        agent=sommelier_agent,
        messages=[{"role": "user", "content": context_message}],
        context_variables={},
        stream=True,
        debug=False,
        tool_choice="auto"
    )
    
    chunks = []
    current_chunk = ""
    
    for chunk in response:
        if "content" in chunk and chunk["content"] is not None:
            current_chunk += chunk["content"]
        elif "delim" in chunk and chunk["delim"] == "end" and current_chunk:
            chunks.append(current_chunk)
            current_chunk = ""
    
    if current_chunk:
        chunks.append(current_chunk)
        
    return chunks