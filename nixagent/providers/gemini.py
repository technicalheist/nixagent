import os
import requests
from typing import List, Dict, Any, Optional

def call_gemini(messages: List[Dict], tools: Optional[List[Dict]] = None, 
                model: Optional[str] = None, api_base: Optional[str] = None, 
                api_key: Optional[str] = None, stream: bool = False) -> Any:
    """
    Gemini API calling logic. We use Gemini's OpenAI-compatible endpoint.
    Reference: https://developers.google.com/workspace/chat/authenticate-authorize-chat-app
    """
    api_key = api_key or os.getenv("GEMINI_API_KEY", "")
    api_base = api_base or os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai")
    model = model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

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
