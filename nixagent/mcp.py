import os
import json
import subprocess
import threading
from typing import Dict, Any, List
from .logger import logger

class MCPClient:
    """
    A simple JSON-RPC over STDIO client for Model Context Protocol.
    """
    def __init__(self, command: str, args: List[str]):
        self.command = command
        self.args = args
        self.process = None
        self._message_id = 1
        self._lock = threading.Lock()
        self.tools_cache = []

    def start(self):
        self.process = subprocess.Popen(
            [self.command] + self.args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Send initialize request as required by MCP
        init_req = {
            "jsonrpc": "2.0",
            "id": self._get_next_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05", # recent version
                "capabilities": {},
                "clientInfo": {"name": "python-agent-client", "version": "1.0"}
            }
        }
        self.send_request(init_req)
        # We need to send initialized notification as well
        init_notif = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        self.send_notification(init_notif)

    def _get_next_id(self):
        with self._lock:
            val = self._message_id
            self._message_id += 1
            return val

    def send_notification(self, payload: Dict[Any, Any]):
        if not self.process:
            return
        self.process.stdin.write(json.dumps(payload) + "\n")
        self.process.stdin.flush()

    def send_request(self, payload: Dict[Any, Any]) -> Any:
        if not self.process:
            return {"error": "Process not started"}
            
        self.process.stdin.write(json.dumps(payload) + "\n")
        self.process.stdin.flush()
        
        while True:
            line = self.process.stdout.readline()
            if not line:
                break
            try:
                resp = json.loads(line)
                if "id" in resp and resp["id"] == payload["id"]:
                    return resp
            except json.JSONDecodeError:
                continue

    def get_tools(self):
        req = {
            "jsonrpc": "2.0",
            "id": self._get_next_id(),
            "method": "tools/list",
            "params": {}
        }
        resp = self.send_request(req)
        if "result" in resp and "tools" in resp["result"]:
            self.tools_cache = resp["result"]["tools"]
            return self.tools_cache
        return []

    def call_tool(self, name: str, arguments: Dict[str, Any]):
        req = {
            "jsonrpc": "2.0",
            "id": self._get_next_id(),
            "method": "tools/call",
            "params": {
                "name": name,
                "arguments": arguments
            }
        }
        resp = self.send_request(req)
        return resp.get("result", resp.get("error"))

    def stop(self):
        if self.process:
            self.process.terminate()

class MCPManager:
    """
    Parses mcp.json and dynamically activates marked servers.
    """
    def __init__(self, config_path="mcp.json"):
        self.config_path = config_path
        self.servers: Dict[str, MCPClient] = {}

    def load_and_activate(self):
        if not os.path.exists(self.config_path):
            return
        
        with open(self.config_path, "r") as f:
            config = json.load(f)
            
        mcp_servers = config.get("mcpServers", {})
        for name, details in mcp_servers.items():
            if details.get("active", True):
                client = MCPClient(details.get("command"), details.get("args", []))
                try:
                    client.start()
                    self.servers[name] = client
                    logger.info(f"[MCP] Activated server '{name}'")
                except Exception as e:
                    logger.error(f"[MCP] Failed to activate server '{name}': {e}")
                    
    def get_all_tools(self) -> List[Dict]:
        all_tools = []
        for name, client in self.servers.items():
            tools = client.get_tools()
            for t in tools:
                # Add server prefix to avoid tool name collisions
                formatted_tool = {
                    "type": "function",
                    "function": {
                        "name": f"mcp__{name}__{t['name']}",
                        "description": t.get("description", ""),
                        "parameters": t.get("inputSchema", {})
                    }
                }
                all_tools.append(formatted_tool)
        return all_tools
        
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]):
        if tool_name.startswith("mcp__"):
            parts = tool_name.split("__", 2)
            if len(parts) == 3:
                server_name = parts[1]
                t_name = parts[2]
                if server_name in self.servers:
                    return self.servers[server_name].call_tool(t_name, arguments)
        return {"error": "Tool not found"}

    def stop_all(self):
        for client in self.servers.values():
            client.stop()
