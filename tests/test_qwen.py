import os
import sys

# Ensure nixagent is in path for running directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from nixagent import Agent

# Simple manual tool definitions for testing
def get_weather(location: str):
    return f"The weather in {location} is 25°C and sunny."

def test_qwen_simple_completion():
    print("Testing Qwen Simple Completion...")
    # Initialize an Agent manually setting the provider to 'qwen'
    agent = Agent(
        name="qwen_tester", 
        system_prompt="You are a helpful test assistant.",
        provider="qwen"
    )
    
    response = agent.run("What is 5 + 5? Reply with just the number.", max_iterations=2)
    print(f"Agent Response: {response}")
    assert "10" in response or "ten" in response.lower()
    print("✓ Simple completion passed\n")

def test_qwen_tools():
    print("Testing Qwen Tools...")
    agent = Agent(
        name="qwen_tools_tester",
        system_prompt="You are a helpful assistant. Use tools if needed.",
        provider="qwen",
        use_builtin_tools=False,
        custom_tools={"get_weather": get_weather},
        custom_tool_defs=[{
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get current weather in a given location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string", "description": "The city or location"}
                    },
                    "required": ["location"]
                }
            }
        }]
    )
    
    response = agent.run("What is the weather in Paris?", max_iterations=5)
    print(f"Agent Response: {response}")
    assert "25" in response or "sunny" in response.lower()
    print("✓ Tool usage passed\n")

def test_qwen_streaming():
    print("Testing Qwen Streaming...")
    agent = Agent(
        name="qwen_stream_tester",
        system_prompt="You are a helpful test assistant.",
        provider="qwen"
    )
    
    # Run the stream manually to intercept the generator output
    stream_gen = agent.run("Count to 3.", stream=True)
    outtext = ""
    for chunk in stream_gen:
        if chunk:
            outtext += chunk
            
    print(f"Agent Streaming Result: {outtext}")
    assert "1" in outtext and "2" in outtext and "3" in outtext
    print("✓ Streaming passed\n")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
    if not os.getenv("QWEN_EMAIL") or not os.getenv("QWEN_PASSWORD"):
        print("Please set QWEN_EMAIL and QWEN_PASSWORD for tests to run.")
        sys.exit(1)
        
    test_qwen_simple_completion()
    test_qwen_tools()
    test_qwen_streaming()
    print("All Qwen tests passed successfully.")
