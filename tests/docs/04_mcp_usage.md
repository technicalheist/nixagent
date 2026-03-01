# Using Model Context Protocol (MCP)

`nixagent` natively integrates with **Model Context Protocol (MCP)**, allowing you to ingest and harness highly specialized tools exposed by standard MCP process servers completely autonomously. 

### 1. Define your Server File
At the root configuration directory of the consumer's execution script, define a `mcp.json` file pointing to remote MCP executable engines.

```json
{
  "mcpServers": {
    "sqlite": {
      "command": "uvx",
      "args": ["mcp-server-sqlite", "--db-path", "./database.db"],
      "active": true
    }
  }
}
```

### 2. Connecting the MCP Context to an Agent
You can selectively harness MCP configurations inside certain agents by defining the path pointer to the JSON payload via the parameter `mcp_config_path`:

```python
from dotenv import load_dotenv
from nixagent import Agent

load_dotenv()

# Example Agent loading local schema mapping pointing to MCP definitions natively
agent = Agent(
    name="DB_Agent",
    system_prompt="You are a helpful SQL assistant.",
    mcp_config_path="mcp.json"  # Overrides defaults natively dynamically
)

if __name__ == "__main__":
    # If the SQLite MCP server is valid, it will natively route standard SQL tools!
    agent.run("Read the tables from the sqlite database.")
```

### How MCP works Internally
When an Agent initializes with an MCP configuration path:
1. It reads `mcp.json` and evaluates standard nodes marked with `"active": true`.
2. Utilizing STDIN/STDOUT processes, it hooks securely into those local shell domains and downloads the `tools/list` schema from that subsystem.
3. Automatically translates them to `mcp__{server_name}__{tool_name}` internally to avoid local tool collisions (for example, `mcp__sqlite__query`).
4. Injects them transparently inside standard LLM execution logic!
