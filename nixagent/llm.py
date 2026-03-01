import os
import json
import requests
from typing import List, Dict, Any, Optional

def call_llm(messages: List[Dict], tools: Optional[List[Dict]] = None, 
             model: Optional[str] = None, api_base: Optional[str] = None, 
             api_key: Optional[str] = None, provider: str = "openai",
             stream: bool = False) -> Any:
    """
    Execute LLM calls via raw HTTP requests.
    Supports OpenAI standard format. Many platforms including Ollama support this format.
    Vertex API support can be routed here as well.
    """
    api_key = api_key or os.getenv("API_KEY", "")
    api_base = api_base or os.getenv("API_BASE_URL", "https://api.openai.com/v1")
    model = model or os.getenv("MODEL", "gpt-4o")
    
    headers = {
        "Content-Type": "application/json"
    }
    
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
        
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 1,
        "top_p": 1,
        "max_tokens": 4096,
        "stream": stream
    }
    
    if tools:
        payload["tools"] = tools

    url = f"{api_base.rstrip('/')}/chat/completions"
    
    # Custom logic for Vertex if provider == "vertex" might be added here, 
    # but the task states we standardize exclusively on the OpenAI format for all request structures.
    
    if stream:
        response = requests.post(url, headers=headers, json=payload, stream=True)
        response.raise_for_status()
        return response # Return the raw response for iterating lines
    else:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
