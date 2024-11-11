from typing import Dict, Any, List, Generator, Optional
from .types import Agent, Response, Result
from .util import debug_print, function_to_json, merge_chunk
import json
import groq

class Microagent:
    def __init__(self, llm_type: str = 'groq'):
        self.llm_type = llm_type
        if llm_type == 'groq':
            self.client = groq.Groq()
        else:
            raise ValueError(f"Unsupported LLM type: {llm_type}")

    def run(
        self,
        agent: Agent,
        messages: List[Dict[str, Any]],
        context_variables: Dict[str, Any] = None,
        stream: bool = False,
        debug: bool = False,
    ) -> Generator[Dict[str, Any], None, None] if stream else Response:
        context_variables = context_variables or {}
        
        # Convert functions to the format expected by the LLM
        functions = [function_to_json(f) for f in agent.functions]
        
        # Prepare the messages
        formatted_messages = []
        for msg in messages:
            formatted_msg = {
                "role": msg["role"],
                "content": msg["content"]
            }
            formatted_messages.append(formatted_msg)
            
        # Add system message with agent instructions
        system_message = {
            "role": "system",
            "content": agent.instructions if isinstance(agent.instructions, str) 
                      else agent.instructions()
        }
        formatted_messages.insert(0, system_message)

        # Make the API call
        try:
            completion = self.client.chat.completions.create(
                model=agent.model,
                messages=formatted_messages,
                tools=functions if functions else None,
                tool_choice="auto" if functions else None,
                stream=stream
            )

            if stream:
                return self._handle_streaming_response(completion, debug)
            else:
                return self._handle_complete_response(completion, agent, context_variables)

        except Exception as e:
            debug_print(debug, f"Error in API call: {str(e)}")
            raise

    def _handle_streaming_response(
        self, completion, debug: bool
    ) -> Generator[Dict[str, Any], None, None]:
        final_response = {"role": "assistant", "content": "", "tool_calls": []}
        
        for chunk in completion:
            delta = chunk.choices[0].delta
            if hasattr(delta, "content") and delta.content:
                yield {"content": delta.content}
            
            if hasattr(delta, "tool_calls") and delta.tool_calls:
                for tool_call in delta.tool_calls:
                    yield {
                        "tool_calls": [{
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments
                            }
                        }]
                    }

            yield {"delim": "end"}

    def _handle_complete_response(
        self, completion, agent: Agent, context_variables: Dict[str, Any]
    ) -> Response:
        message = completion.choices[0].message
        messages = [{"role": "assistant", "content": message.content}]
        
        return Response(
            messages=messages,
            agent=agent,
            context_variables=context_variables
        )