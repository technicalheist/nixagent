import os
import time
import json
import requests
from typing import List, Dict, Any, Optional
from ..logger import logger

class QwenStreamWrapper:
    def __init__(self, response, tools):
        self.response = response
        self.tools = tools

    def iter_lines(self):
        full_content = ""
        for line in self.response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data_str = line_str[6:]
                    if data_str.strip() == '[DONE]':
                        continue
                    try:
                        data = json.loads(data_str)
                        choices = data.get("choices", [])
                        if choices:
                            delta = choices[0].get("delta", {})
                            if "content" in delta:
                                chunk = delta["content"]
                                full_content += chunk
                                # We yield standard OpenAI delta format
                                fake_openai = {"choices": [{"delta": {"content": chunk}}]}
                                yield f"data: {json.dumps(fake_openai)}\n".encode('utf-8')
                    except json.JSONDecodeError:
                        pass
        
        # Intercept tool calls cleanly from the completed stream text
        if self.tools and "tool_calls" in full_content and "{" in full_content:
            try:
                json_str = full_content[full_content.find("{") : full_content.rfind("}")+1]
                parsed = json.loads(json_str)
                if "tool_calls" in parsed:
                    # Emit matching tool format that standard agent parser expects
                    for i, call in enumerate(parsed["tool_calls"]):
                        fake_tool_delta = {
                            "choices": [{
                                "delta": {
                                    "tool_calls": [{
                                        "index": i,
                                        "id": f"call_{int(time.time()*1000)}_{i}",
                                        "type": "function",
                                        "function": {
                                            "name": call.get("name", ""),
                                            "arguments": json.dumps(call.get("arguments", {}))
                                        }
                                    }]
                                }
                            }]
                        }
                        yield f"data: {json.dumps(fake_tool_delta)}\n".encode('utf-8')
            except json.JSONDecodeError:
                pass
                
        yield b"data: [DONE]\n"


class QwenInternalClient:
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self.token_file = os.path.join(os.path.dirname(__file__), "qwen_token.txt")
        self.access_token = self._load_token()
        
        self.base_headers = {
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
            'Origin': 'https://chat.qwen.ai'
        }

    def _load_token(self):
        try:
            if os.path.exists(self.token_file):
                with open(self.token_file, "r") as f:
                    return f.read().strip()
        except:
            pass
        return None

    def _save_token(self, token: str):
        try:
            with open(self.token_file, "w") as f:
                f.write(token)
        except Exception as e:
            logger.warning(f"Failed to save Qwen token: {e}")

    def login(self):
        url = "https://chat.qwen.ai/api/v1/auths/signin"
        payload = {"email": self.email, "password": self.password}
        response = requests.post(url, headers=self.base_headers, json=payload)
        response.raise_for_status()
        self.access_token = response.json().get("token")
        if not self.access_token:
            raise Exception("Login succeeded but no token was returned in the response.")
        self._save_token(self.access_token)
        return self.access_token

    def _get_auth_headers(self):
        if not self.access_token:
            self.login()
        headers = self.base_headers.copy()
        headers['Authorization'] = f"Bearer {self.access_token}"
        headers['Cookie'] = f"token={self.access_token}"
        return headers

    def create_chat(self, model: str) -> str:
        url = "https://chat.qwen.ai/api/v2/chats/new"
        payload = {
            "title": "New Chat",
            "models": [model],
            "chat_mode": "normal",
            "chat_type": "t2t",
            "timestamp": int(time.time() * 1000),
            "project_id": ""
        }
        headers = self._get_auth_headers()
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code in [401, 403]:
            self.login()
            headers = self._get_auth_headers()
            response = requests.post(url, headers=headers, json=payload)
            
        response.raise_for_status()
        chat_id = response.json().get("data", {}).get("id")
        return chat_id


_global_qwen_client = None

def get_qwen_client():
    global _global_qwen_client
    if not _global_qwen_client:
        email = os.getenv("QWEN_EMAIL")
        password = os.getenv("QWEN_PASSWORD")
        if not email or not password:
            raise ValueError("QWEN_EMAIL and QWEN_PASSWORD environment variables are required to use the qwen provider.")
        _global_qwen_client = QwenInternalClient(email, password)
    return _global_qwen_client


def call_qwen(messages: List[Dict], tools: Optional[List[Dict]] = None, 
              model: Optional[str] = None, api_base: Optional[str] = None, 
              api_key: Optional[str] = None, stream: bool = False) -> Any:
    """
    Qwen-compatible caller utilizing internal UI reverse-engineered endpoints.
    """
    client = get_qwen_client()
    model = model or os.getenv("QWEN_MODEL", "qwen3.5-plus")
    
    # Lazily create a new chat for execution contexts
    chat_id = client.create_chat(model)
    url = f"https://chat.qwen.ai/api/v2/chat/completions?chat_id={chat_id}"

    # Flatten logic to text because qwen UI endpoint primarily accepts sequential history as context
    # or just passing the most recent augmented prompt if we don't have perfect multi-turn struct arrays.
    # The safest bet for UI mappings is rendering the history as a single text block
    conversation_history = ""
    for msg in messages[:-1]:
        conversation_history += f"**{msg['role']}**: {msg['content']}\n\n"
    
    latest_msg = messages[-1]['content']
    
    augmented_message = conversation_history + f"**{messages[-1]['role']}**: {latest_msg}"

    if tools:
        augmented_message = (
            "You have access to the following tools. If you need to use one, you MUST reply EXACTLY with a JSON block formatted like: "
            '{"tool_calls": [{"name": "function_name", "arguments": {"arg1": "value"}}]}\n\n'
            f"Tools available:\n{json.dumps(tools, indent=2)}\n\n"
            f"Conversation Context:\n{augmented_message}"
        )

    payload = {
        "stream": True,  # Force internally for SSE extraction
        "version": "2.1",
        "incremental_output": True,
        "chat_id": chat_id,
        "chat_mode": "normal",
        "model": model,
        "parent_id": None,
        "messages": [
            {
                "role": "user",
                "content": augmented_message,
                "user_action": "chat",
                "timestamp": int(time.time()),
                "models": [model],
                "chat_type": "t2t",
                "feature_config": {
                    "thinking_enabled": False, # Setting False since we don't stream thoughts locally yet
                    "output_schema": "phase",
                    "research_mode": "normal",
                    "auto_thinking": False,
                    "thinking_format": "summary",
                    "auto_search": False
                }
            }
        ],
        "timestamp": int(time.time() * 1000)
    }

    # Force streaming internally to align with UI SSE payload structure
    headers = client._get_auth_headers()
    response = requests.post(url, headers=headers, json=payload, stream=True)
    
    if response.status_code in [401, 403]:
        client.login()
        headers = client._get_auth_headers()
        response = requests.post(url, headers=headers, json=payload, stream=True)
        
    response.raise_for_status()
    
    if stream:
        return QwenStreamWrapper(response, tools)
        
    else:
        # Full sync mode parse
        full_content = ""
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data_str = line_str[6:]
                    if data_str.strip() == '[DONE]':
                        continue
                    try:
                        data = json.loads(data_str)
                        choices = data.get("choices", [])
                        if choices:
                            delta = choices[0].get("delta", {})
                            if "content" in delta:
                                full_content += delta["content"]
                    except json.JSONDecodeError:
                        pass
                        
        response_dict = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": full_content
                }
            }]
        }
        
        if tools and "tool_calls" in full_content and "{" in full_content:
            try:
                json_str = full_content[full_content.find("{") : full_content.rfind("}")+1]
                parsed = json.loads(json_str)
                if "tool_calls" in parsed:
                    # Append strictly standard mock details
                    standard_calls = []
                    for i, call in enumerate(parsed["tool_calls"]):
                        standard_calls.append({
                            "id": f"call_{int(time.time()*1000)}_{i}",
                            "type": "function",
                            "function": {
                                "name": call.get("name", ""),
                                "arguments": json.dumps(call.get("arguments", {}))
                            }
                        })
                    response_dict["choices"][0]["message"]["tool_calls"] = standard_calls
            except json.JSONDecodeError:
                pass
                
        return response_dict
