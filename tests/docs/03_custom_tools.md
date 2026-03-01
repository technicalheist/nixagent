# Custom Tools and Functions

While `nixagent` provides deep internal access to the system via its built-in toolkit, you can securely pass in your own Python logic using the `custom_tools` dictionaries. These functions act as an overlay and do not destruct or overwrite standard built-in abilities.

### 1. Define the Python Logic
First, create the raw python function you want your AI to use:

```python
def check_inventory(item_name: str) -> str:
    """Mock database check"""
    database = {"apples": 14, "oranges": 0}
    if item_name.lower() in database:
        return f"We have {database[item_name.lower()]} {item_name} in stock."
    return f"Item '{item_name}' is not carried in our system."
```

### 2. Define the Mapping Object and JSON Schema (Tool Def)
To pass this function into the LLM context, create a `custom_tools` dictionary for the execution bindings, and a `custom_tool_defs` list matching the strict OpenAI JSON Schema:

```python
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
```

### 3. Initialize the Agent
Inject them directly via keyword arguments inside the main instantiation sequence:

```python
from dotenv import load_dotenv
from nixagent import Agent

load_dotenv()

agent = Agent(
    name="InventoryAgent",
    system_prompt="You are a helpful warehouse AI.",
    custom_tools=custom_tools,
    custom_tool_defs=custom_tool_defs
)

if __name__ == "__main__":
    result = agent.run("Do we have any apples or oranges in stock?")
    print(result)
```

The system will now autonomously trigger your python method whenever the language model requests the lookup schema!
