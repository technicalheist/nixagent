import os
import json
from dotenv import load_dotenv

# Import the core Nixagent
from nixagent import Agent

# 1. Load API keys from your .env file
load_dotenv()
PROVIDER = os.getenv("PROVIDER", "openai")

def main():
    print(f"--- Running Structured Output Example via {PROVIDER.upper()} ---")

    # 2. Define exactly what JSON you want back using standard JSON schema
    pizza_schema = {
        "type": "object",
        "properties": {
            "pizzas_ordered": {
                "type": "integer",
                "description": "Total number of pizzas mentioned"
            },
            "toppings": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of requested toppings"
            },
            "is_delivery": {
                "type": "boolean"
            }
        },
        "required": ["pizzas_ordered", "toppings", "is_delivery"]
    }

    # 3. Create a normal agent
    agent = Agent(
        name="PizzaBot",
        system_prompt="Extract the pizza order details perfectly.",
        provider=PROVIDER,
        use_builtin_tools=False
    )
    
    # 4. Give the agent messy text, but pass the schema!
    messy_text = "Yeah hi, I'd like to get 3 large pizzas. Please put pepperoni and mushrooms on them. I'll come pick them up in 20 minutes."
    
    print("\nSending Messy Text:", messy_text)
    print("Wait for LLM response...\n")
    
    # Notice we pass `output_schema` here. 
    # `result` natively becomes a Python dictionary!
    result = agent.run(messy_text, output_schema=pizza_schema)
    
    # 5. Boom! It's a real dictionary, not a string.
    print("✅ Parsed Dictionary Result:")
    print(json.dumps(result, indent=2))
    
    if type(result) == dict:
        print(f"\nAwesome! Total pizzas we need to cook: {result['pizzas_ordered']}")
        print(f"Do we need a driver? {'Yes' if result['is_delivery'] else 'No, pick-up!'}")

if __name__ == "__main__":
    main()
