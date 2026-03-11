import json
import os
from dotenv import load_dotenv
from nixagent import Agent

load_dotenv()

mcp_config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../mcp.json"))
print(mcp_config_path)
agent = Agent(
    name="DB_Agent",
    system_prompt="You are a helpful Browser assistant.",
    mcp_config_path=mcp_config_path  
)

if __name__ == "__main__":
    print("Running Test 04 - MCP JSON Dynamic Path Loading")
    result = agent.run("Show me the list of tools you can use?")
    print("\n--- Output ---")
    print(result)
