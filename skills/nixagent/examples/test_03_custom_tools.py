from dotenv import load_dotenv
from nixagent import Agent

load_dotenv()

def check_inventory(item_name: str) -> str:
    """Mock database check"""
    database = {"apples": 14, "oranges": 0}
    if item_name.lower() in database:
        return f"We have {database[item_name.lower()]} {item_name} in stock."
    return f"Item '{item_name}' is not carried in our system."

custom_tools = {
    "check_inventory": check_inventory
}

custom_tool_defs = [
    {
        "type": "function",
        "function": {
            "name": "check_inventory",
            "description": "Checks the database for the current inventory stock of a given item.",
            "parameters": {
                "type": "object",
                "properties": {
                    "item_name": {"type": "string", "description": "The name of the item to look up."}
                },
                "required": ["item_name"]
            }
        }
    }
]

agent = Agent(
    name="InventoryAgent",
    system_prompt="You are a helpful warehouse AI.",
    custom_tools=custom_tools,
    custom_tool_defs=custom_tool_defs
)

if __name__ == "__main__":
    print("Running Test 03 - Custom Tools (Injection Merge)")
    result = agent.run("Do we have any apples or oranges in stock?")
    print("\n--- Output ---")
    print(result)
