import os
import requests
from typing import List, Dict, Any, Optional

def call_openai(messages: List[Dict], tools: Optional[List[Dict]] = None, 
                model: Optional[str] = None, api_base: Optional[str] = None, 
                api_key: Optional[str] = None, stream: bool = False) -> Any:
    """
    OpenAI-compatible caller (works for OpenAI, Groq, Ollama, vLLM, etc.)
    """
    api_key = api_key or os.getenv("OPENAI_API_KEY", "")
    api_base = api_base or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    model = model or os.getenv("OPENAI_MODEL", "gpt-4o")

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
    
    if stream:
        response = requests.post(url, headers=headers, json=payload, stream=True)
        response.raise_for_status()
        return response
    else:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
