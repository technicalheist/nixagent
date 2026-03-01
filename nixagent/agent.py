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
                 mcp_config_path: str = "mcp.json"):
        self.name = name
        self.system_prompt = system_prompt
        self.model = model or os.getenv("MODEL", "gpt-4o")
        self.messages = [{"role": "system", "content": system_prompt}]
        self.tools = AVAILABLE_TOOLS.copy()
        self.tool_defs = TOOL_DEFINITIONS.copy()
        
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

    def run(self, user_prompt: str, max_iterations: int = 15, stream: bool = False):
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
                    stream=False # Stream logic parsing over standard HTTP is complex, focusing on standard payload first
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
