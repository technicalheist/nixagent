import json
import os
from dotenv import load_dotenv
from nixagent import Agent

load_dotenv()

# We will create a dummy mcp.json in the current directory if it doesn't exist just to test loading logic
mcp_config = {
  "mcpServers": {} # No active MCP servers for the safety of this isolated test loop!
}
with open("mcp.json", "w") as f:
    json.dump(mcp_config, f)

agent = Agent(
    name="DB_Agent",
    system_prompt="You are a helpful SQL assistant.",
    mcp_config_path="mcp.json"  
)

if __name__ == "__main__":
    print("Running Test 04 - MCP JSON Dynamic Path Loading")
    result = agent.run("Acknowledge that your MCP config loaded successfully, even if it has 0 active servers right now.")
    print("\n--- Output ---")
    print(result)
