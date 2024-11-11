import os
from dotenv import load_dotenv
from groq import Groq
from typing import List

# Initialization

load_dotenv()
os.environ['GROQ_API_KEY'] = os.getenv('GROQ_API_KEY')
groq = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

from microagent.core import Microagent
from microagent.types import Agent

# Check if GROQ_API_KEY is set in the environment
if "GROQ_API_KEY" not in os.environ:
    raise ValueError("GROQ_API_KEY environment variable is not set. Please set it before running this script.")

# Initialize Microagent with Groq as the LLM provider
client = Microagent(llm_type='groq')

# Start of agent section

def process_refund(item_id, reason="NOT SPECIFIED"):
    """Refund an item. Refund an item. Make sure you have the item_id of the form item_... Ask for user confirmation before processing the refund."""
    print(f"[mock] Refunding item {item_id} because {reason}...")
    return "Success!"

def apply_discount():
    """Apply a discount to the user's cart."""
    print("[mock] Applying discount...")
    return "Applied discount of 11%"

triage_agent = Agent(
    model="llama-3.1-70b-versatile",
    tool_choice="auto",
    name="Triage Agent",
    instructions="Determine which agent is best suited to handle the user's request, and transfer the conversation to that agent.",
)
sales_agent = Agent(
    model="llama-3.1-70b-versatile",
    tool_choice="auto",
    name="Sales Agent",
    instructions="Be super enthusiastic about selling bees.",
)
refunds_agent = Agent(
    model="llama-3.1-70b-versatile",
    tool_choice="auto",
    name="Refunds Agent",
    instructions="Help the user with a refund. If the reason is that it was too expensive, offer the user a refund code. If they insist, then process the refund.",
    functions=[process_refund, apply_discount],
)

def transfer_back_to_triage():
    """Call this function if a user is asking about a topic that is not handled by the current agent."""
    return triage_agent

def transfer_to_sales():
    return sales_agent

def transfer_to_refunds():
    return refunds_agent

triage_agent.functions = [transfer_to_sales, transfer_to_refunds] # add transfer functions to the supervisor for all other agents
sales_agent.functions.append(transfer_back_to_triage) # add a transfer back to triage function to all other agents
refunds_agent.functions.append(transfer_back_to_triage) # ...

async def get_agent_response(message: str) -> List[str]:
    """
    Get response from the triage agent and return it as a list of chunks.
    """
    client = Microagent(llm_type='groq')
    
    response = client.run(
        agent=triage_agent,
        messages=[{"role": "user", "content": message}],
        context_variables={},
        stream=True,
        debug=False
    )
    
    chunks = []
    current_chunk = ""
    
    for chunk in response:
        if "content" in chunk and chunk["content"] is not None:
            current_chunk += chunk["content"]
        elif "delim" in chunk and chunk["delim"] == "end" and current_chunk:
            chunks.append(current_chunk)
            current_chunk = ""
            
        # Handle tool calls as separate chunks
        if "tool_calls" in chunk and chunk["tool_calls"] is not None:
            for tool_call in chunk["tool_calls"]:
                f = tool_call["function"]
                name = f["name"]
                if name:
                    chunks.append(f"Using {name}...")
    
    if current_chunk:
        chunks.append(current_chunk)
        
    return chunks