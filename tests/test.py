import os
from dotenv import load_dotenv

load_dotenv()

from nixagent.agent import Agent

def calculate_sqrt(number: float) -> float:
    return number ** 0.5

custom_tools = {
    "calculate_sqrt": calculate_sqrt
}
custom_tool_defs = [
    {
        "type": "function",
        "function": {
            "name": "calculate_sqrt",
            "description": "Calculates the square root of a number.",
            "parameters": {
                "type": "object",
                "properties": {
                    "number": {"type": "number", "description": "The number to find the square root of."}
                },
                "required": ["number"]
            }
        }
    }
]

agent = Agent(
    name="TestAgent",
    system_prompt="You are a helpful AI assistant testing the generic framework.",
    custom_tools=custom_tools,
    custom_tool_defs=custom_tool_defs,
    mcp_config_path="mcp.json" # Will point to local user dir, if it exists
)

if __name__ == "__main__":
    result = agent.run("Show me the list of all files in current directory and then calculate the square root of 144.")
    print("\n--- Agent Result ---")
    print(result)
