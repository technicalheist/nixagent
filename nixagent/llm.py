from typing import List, Dict, Any, Optional
from .providers import get_provider_caller

def call_llm(messages: List[Dict], tools: Optional[List[Dict]] = None, 
             model: Optional[str] = None, api_base: Optional[str] = None, 
             api_key: Optional[str] = None, provider: str = "openai",
             stream: bool = False) -> Any:
    """
    Execute LLM calls via raw HTTP requests by delegating to the right provider logic.
    Supports OpenAI, Anthropic, Gemini formats and structures seamlessly.
    """
    caller = get_provider_caller(provider)
    
    return caller(
        messages=messages,
        tools=tools,
        model=model,
        api_base=api_base,
        api_key=api_key,
        stream=stream
    )

