import os
import json
import requests
from typing import List, Dict, Any, Optional

class AnthropicStreamWrapper:
    def __init__(self, response):
        self.response = response

    def iter_lines(self):
        for line in self.response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith("data: "):
                    data_str = line_str[6:]
                    if data_str.strip() == "[DONE]":
                        yield b"data: [DONE]\n"
                        continue
                    try:
                        data = json.loads(data_str)
                        if data.get("type") == "content_block_delta":
                            text = data.get("delta", {}).get("text", "")
                            if text:
                                fake_openai = {"choices": [{"delta": {"content": text}}]}
                                yield f"data: {json.dumps(fake_openai)}\n".encode('utf-8')
                        elif data.get("type") == "message_stop":
                            yield b"data: [DONE]\n"
                    except ValueError:
                        pass

def call_anthropic(messages: List[Dict], tools: Optional[List[Dict]] = None, 
                   model: Optional[str] = None, api_base: Optional[str] = None, 
                   api_key: Optional[str] = None, stream: bool = False) -> Any:
    """
    Anthropic API calling logic mapping OpenAI standard formats to Anthropic Messages API.
    """
    api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
    api_base = api_base or os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com/v1")
    model = model or os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229")

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    system_message = ""
    anthropic_messages = []
    
    for m in messages:
        role = m.get("role")
        if role == "system":
            system_message += m.get("content", "") + "\n"
        elif role == "user":
            anthropic_messages.append({"role": "user", "content": m.get("content", "")})
        elif role == "assistant":
            content = []
            if m.get("content"):
                content.append({"type": "text", "text": m.get("content")})
            if m.get("tool_calls"):
                for tc in m["tool_calls"]:
                    fn = tc["function"]
                    try:
                        args = json.loads(fn["arguments"]) if isinstance(fn["arguments"], str) else fn["arguments"]
                    except json.JSONDecodeError:
                        args = {}
                    content.append({
                        "type": "tool_use",
                        "id": tc["id"],
                        "name": fn["name"],
                        "input": args
                    })
            if not content:
                content = [{"type": "text", "text": ""}]
            anthropic_messages.append({"role": "assistant", "content": content})
        elif role == "tool":
            tool_result_content = {
                "type": "tool_result",
                "tool_use_id": m.get("tool_call_id", ""),
                "content": str(m.get("content", ""))
            }
            if anthropic_messages and anthropic_messages[-1]["role"] == "user" and isinstance(anthropic_messages[-1]["content"], list):
                anthropic_messages[-1]["content"].append(tool_result_content)
            else:
                anthropic_messages.append({"role": "user", "content": [tool_result_content]})
                
    anthropic_tools = []
    if tools:
        for t in tools:
            fn = t.get("function", {})
            anthropic_tools.append({
                "name": fn.get("name", ""),
                "description": fn.get("description", ""),
                "input_schema": fn.get("parameters", {"type": "object", "properties": {}})
            })
    
    payload = {
        "model": model,
        "max_tokens": 4096,
        "messages": anthropic_messages,
        "stream": stream
    }
    if system_message.strip():
        payload["system"] = system_message.strip()
    if anthropic_tools:
        payload["tools"] = anthropic_tools
        
    url = f"{api_base.rstrip('/')}/messages"
    
    if stream:
        response = requests.post(url, headers=headers, json=payload, stream=True)
        response.raise_for_status()
        return AnthropicStreamWrapper(response)
    else:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        
        assistant_content = ""
        tool_calls = []
        
        for block in data.get("content", []):
            if block["type"] == "text":
                assistant_content += block["text"]
            elif block["type"] == "tool_use":
                tool_calls.append({
                    "id": block["id"],
                    "type": "function",
                    "function": {
                        "name": block["name"],
                        "arguments": json.dumps(block["input"])
                    }
                })
        
        message_info = {
            "role": "assistant",
            "content": assistant_content or None
        }
        if tool_calls:
            message_info["tool_calls"] = tool_calls
            
        return {
            "choices": [
                {
                    "message": message_info
                }
            ]
        }
