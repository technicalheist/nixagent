import os
import json
import requests
from typing import List, Dict, Any, Optional

class VertexStreamWrapper:
    def __init__(self, response):
        self.response = response

    def iter_lines(self):
        for line in self.response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith("data: "):
                    data_str = line_str[6:]
                    try:
                        data = json.loads(data_str)
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            text = ""
                            for p in parts:
                                if "text" in p:
                                    text += p["text"]
                            if text:
                                fake_openai = {"choices": [{"delta": {"content": text}}]}
                                yield f"data: {json.dumps(fake_openai)}\n".encode('utf-8')
                    except ValueError:
                        pass
        yield b"data: [DONE]\n"

def call_vertex(messages: List[Dict], tools: Optional[List[Dict]] = None, 
                model: Optional[str] = None, api_base: Optional[str] = None, 
                api_key: Optional[str] = None, stream: bool = False) -> Any:
    """
    Vertex API calling logic mapping OpenAI standard formats to Vertex GenerateContent API.
    """
    api_key = api_key or os.getenv("VERTEX_API_KEY", "")
    api_base = api_base or os.getenv("VERTEX_BASE_URL", "https://aiplatform.googleapis.com/v1")
    model = model or os.getenv("VERTEX_MODEL", "gemini-2.5-flash-lite")

    headers = {
        "Content-Type": "application/json"
    }
    
    vertex_messages = []
    system_instruction = None
    
    for m in messages:
        role = m.get("role")
        if role == "system":
            if system_instruction is None:
                system_instruction = {"parts": [{"text": m.get("content", "")}]}
            else:
                system_instruction["parts"][0]["text"] += "\n" + m.get("content", "")
        elif role == "user":
            vertex_messages.append({"role": "user", "parts": [{"text": m.get("content", "")}]})
        elif role == "assistant":
            parts = []
            if m.get("content"):
                parts.append({"text": m.get("content")})
            if m.get("tool_calls"):
                for tc in m["tool_calls"]:
                    fn = tc["function"]
                    try:
                        args = json.loads(fn["arguments"]) if isinstance(fn["arguments"], str) else fn["arguments"]
                    except json.JSONDecodeError:
                        args = {}
                    parts.append({
                        "functionCall": {
                            "name": fn["name"],
                            "args": args
                        }
                    })
            if not parts:
                parts.append({"text": ""})
            vertex_messages.append({"role": "model", "parts": parts})
        elif role == "tool":
            vertex_messages.append({
                "role": "function",
                "parts": [{
                    "functionResponse": {
                        "name": m.get("name", "unknown_tool"),
                        "response": {"result": m.get("content", "")}
                    }
                }]
            })
            
    vertex_tools = []
    if tools:
        function_declarations = []
        for t in tools:
            fn = t.get("function", {})
            params = fn.get("parameters", {"type": "OBJECT", "properties": {}})
            # Ensure "type" is uppercase to align with Vertex standards if provided
            if params.get("type", "").lower() == "object":
                params["type"] = "OBJECT"
                
            function_declarations.append({
                "name": fn.get("name", ""),
                "description": fn.get("description", ""),
                "parameters": params
            })
        if function_declarations:
            vertex_tools = [{"functionDeclarations": function_declarations}]
    
    payload = {
        "contents": vertex_messages
    }
    if system_instruction:
        payload["systemInstruction"] = system_instruction
    if vertex_tools:
        payload["tools"] = vertex_tools
        
    action = "streamGenerateContent" if stream else "generateContent"
    
    url = f"{api_base.rstrip('/')}/publishers/google/models/{model}:{action}?key={api_key}"
    if stream:
        url += "&alt=sse"
    
    if stream:
        response = requests.post(url, headers=headers, json=payload, stream=True)
        try:
            response.raise_for_status()
        except Exception as e:
            print("Vertex API Error details:", response.text)
            raise e
        return VertexStreamWrapper(response)
    else:
        response = requests.post(url, headers=headers, json=payload)
        try:
            response.raise_for_status()
        except Exception as e:
            print("Vertex API Error details:", response.text)
            raise e
            
        data = response.json()
        
        candidates = data.get("candidates", [])
        if not candidates:
            return {"choices": [{"message": {"role": "assistant", "content": "No content generated. Feedback: " + json.dumps(data)}}]}
            
        first_candidate = candidates[0]
        content = first_candidate.get("content", {})
        parts = content.get("parts", [])
        
        assistant_content = ""
        tool_calls = []
        
        for part in parts:
            if "text" in part:
                assistant_content += part["text"]
            if "functionCall" in part:
                fc = part["functionCall"]
                tool_calls.append({
                    "id": f"call_{fc['name']}",
                    "type": "function",
                    "function": {
                        "name": fc["name"],
                        "arguments": json.dumps(fc.get("args", {}))
                    }
                })
        
        message_info = {
            "role": "assistant",
            "content": assistant_content if assistant_content else None
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
