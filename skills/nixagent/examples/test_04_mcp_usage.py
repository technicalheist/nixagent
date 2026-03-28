import json
from dotenv import load_dotenv
from nixagent import Agent

load_dotenv()

mcp_config = {
  "mcpServers": {}
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
