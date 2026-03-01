import os
import json
from typing import List, Dict, Any, Callable
from .llm import call_llm
from .tools import AVAILABLE_TOOLS, TOOL_DEFINITIONS
from .mcp import MCPManager

_global_mcp_managers = {}

def get_mcp_manager(config_path="mcp.json"):
    global _global_mcp_managers
    if config_path not in _global_mcp_managers:
        manager = MCPManager(config_path)
        manager.load_and_activate()
        _global_mcp_managers[config_path] = manager
    return _global_mcp_managers[config_path]

class Agent:
    def __init__(self, name: str, system_prompt: str, model: str = None, 
                 custom_tools: dict = None, custom_tool_defs: list = None,
                 mcp_config_path: str = "mcp.json",
                 use_builtin_tools: bool = True,
                 disabled_tools: list = None):
        self.name = name
        self.system_prompt = system_prompt
        self.model = model or os.getenv("MODEL", "gpt-4o")
        self.messages = [{"role": "system", "content": system_prompt}]
        
        if use_builtin_tools:
            self.tools = AVAILABLE_TOOLS.copy()
            self.tool_defs = TOOL_DEFINITIONS.copy()
        else:
            self.tools = {}
            self.tool_defs = []
            
        if disabled_tools:
            for d_tool in disabled_tools:
                self.tools.pop(d_tool, None)
            self.tool_defs = [td for td in self.tool_defs if td["function"]["name"] not in disabled_tools]
        
        if custom_tools:
            self.tools.update(custom_tools)
        if custom_tool_defs:
            self.tool_defs.extend(custom_tool_defs)
            
        # Load MCP tools
        mcp = get_mcp_manager(mcp_config_path)
        mcp_tools = mcp.get_all_tools()
        if mcp_tools:
            self.tool_defs.extend(mcp_tools)
            for mcp_tool in mcp_tools:
                mcp_name = mcp_tool["function"]["name"]
                
                # Use a factory function to capture the correct mcp_name for the closure
                def make_mcp_caller(n):
                    return lambda **kwargs: mcp.call_tool(n, kwargs)
                    
                self.tools[mcp_name] = make_mcp_caller(mcp_name)

        self.agents_in_network = {}

    def register_collaborator(self, agent_instance):
        """Allows agents to talk to each other."""
        self.agents_in_network[agent_instance.name] = agent_instance
        # Add a tool to communicate with this agent
        def communicate_with_agent(message: str) -> str:
            # Note: We run a sub-agent non-streaming and isolated iterations
            return agent_instance.run(message, max_iterations=10, stream=False)
            
        tool_name = f"ask_agent_{agent_instance.name}"
        self.tools[tool_name] = communicate_with_agent
        self.tool_defs.append({
            "type": "function",
            "function": {
                "name": tool_name,
                "description": f"Ask the {agent_instance.name} agent to perform a task.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "message": {"type": "string", "description": "The task or question for the agent."}
                    },
                    "required": ["message"]
                }
            }
        })

    def _run_stream(self, user_prompt: str, max_iterations: int = 15):
        self.messages.append({"role": "user", "content": user_prompt})
        
        for i in range(max_iterations):
            print(f"[{self.name}] Iteration {i+1} (Streaming)")
            try:
                response = call_llm(
                    messages=self.messages,
                    tools=self.tool_defs if self.tool_defs else None,
                    model=self.model,
                    stream=True
                )
                
                text_content = ""
                tool_calls_dict = {}
                role = "assistant"
                
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str.strip() == "[DONE]":
                                break
                            try:
                                data = json.loads(data_str)
                                if "choices" not in data or not data["choices"]:
                                    continue
                                delta = data["choices"][0].get("delta", {})
                                
                                if "role" in delta:
                                    role = delta["role"]
                                
                                if "content" in delta and delta["content"] is not None:
                                    chunk = delta["content"]
                                    text_content += chunk
                                    yield chunk
                                
                                if "tool_calls" in delta:
                                    for tc in delta["tool_calls"]:
                                        idx = tc["index"]
                                        if idx not in tool_calls_dict:
                                            tool_calls_dict[idx] = {"id": tc.get("id", ""), "type": "function", "function": {"name": "", "arguments": ""}}
                                        
                                        if "id" in tc and tc["id"]:
                                            tool_calls_dict[idx]["id"] = tc["id"]
                                        
                                        if "function" in tc:
                                            fn = tc["function"]
                                            if "name" in fn and fn["name"]:
                                                tool_calls_dict[idx]["function"]["name"] += fn["name"]
                                            if "arguments" in fn and fn["arguments"]:
                                                tool_calls_dict[idx]["function"]["arguments"] += fn["arguments"]
                                                
                            except json.JSONDecodeError:
                                pass
                
                assistant_msg = {"role": role}
                if text_content:
                    assistant_msg["content"] = text_content
                
                tool_calls_list = [tool_calls_dict[k] for k in sorted(tool_calls_dict.keys())]
                if tool_calls_list:
                    assistant_msg["tool_calls"] = tool_calls_list
                else:
                    if "content" not in assistant_msg:
                        assistant_msg["content"] = ""
                        
                self.messages.append(assistant_msg)
                
                if not tool_calls_list:
                    return
                    
                for tool_call in tool_calls_list:
                    tool_name = tool_call["function"]["name"]
                    tool_args_str = tool_call["function"]["arguments"]
                    try:
                        tool_args = json.loads(tool_args_str)
                    except json.JSONDecodeError:
                        tool_args = {}
                    
                    if tool_name not in self.tools:
                        print(f"[{self.name}] Tool '{tool_name}' not found.")
                        self.messages.append({
                            "role": "tool",
                            "name": tool_name,
                            "content": f"Error: Tool '{tool_name}' not found.",
                            "tool_call_id": tool_call["id"]
                        })
                        continue
                        
                    print(f"[{self.name}] Calling {tool_name}")
                    try:
                        tool_output = self.tools[tool_name](**tool_args)
                        self.messages.append({
                            "role": "tool",
                            "name": tool_name,
                            "content": str(tool_output),
                            "tool_call_id": tool_call["id"]
                        })
                    except Exception as e:
                        print(f"[{self.name}] Error executing tool '{tool_name}': {e}")
                        self.messages.append({
                            "role": "tool",
                            "name": tool_name,
                            "content": f"Error executing tool '{tool_name}': {e}",
                            "tool_call_id": tool_call["id"]
                        })
                        
            except Exception as e:
                print(f"API error: {e}")
                yield f"\nAPI error: {e}"
                return

    def run(self, user_prompt: str, max_iterations: int = 15, stream: bool = False):
        if stream:
            return self._run_stream(user_prompt, max_iterations)
            
        self.messages.append({"role": "user", "content": user_prompt})
        
        for i in range(max_iterations):
            print(f"[{self.name}] Iteration {i+1}")
            try:
                # Assuming call_llm handles streaming internally. 
                # For this generic implementation we use standard sync response parsing.
                # Since task says 'Direct HTTP Requests over SDKs' and 'agnostic to specific use cases'.
                response = call_llm(
                    messages=self.messages,
                    tools=self.tool_defs if self.tool_defs else None,
                    model=self.model,
                    stream=False
                )
                
                message = response['choices'][0]['message']
                
                # Append assistant message
                self.messages.append(message)
                
                if not message.get("tool_calls"):
                    return message.get("content", "")
                    
                for tool_call in message["tool_calls"]:
                    tool_name = tool_call["function"]["name"]
                    tool_args_str = tool_call["function"]["arguments"]
                    try:
                        tool_args = json.loads(tool_args_str)
                    except json.JSONDecodeError:
                        tool_args = {}
                    
                    if tool_name not in self.tools:
                        print(f"[{self.name}] Tool '{tool_name}' not found.")
                        self.messages.append({
                            "role": "tool",
                            "name": tool_name,
                            "content": f"Error: Tool '{tool_name}' not found.",
                            "tool_call_id": tool_call["id"]
                        })
                        continue
                        
                    print(f"[{self.name}] Calling {tool_name}")
                    try:
                        tool_output = self.tools[tool_name](**tool_args)
                        self.messages.append({
                            "role": "tool",
                            "name": tool_name,
                            "content": str(tool_output),
                            "tool_call_id": tool_call["id"]
                        })
                    except Exception as e:
                        print(f"[{self.name}] Error executing tool '{tool_name}': {e}")
                        self.messages.append({
                            "role": "tool",
                            "name": tool_name,
                            "content": f"Error executing tool '{tool_name}': {e}",
                            "tool_call_id": tool_call["id"]
                        })
                        
            except Exception as e:
                print(f"API error: {e}")
                return f"API error: {e}"
                
        return "Agent could not complete task within limits."
