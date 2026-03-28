import os
import sys
from dotenv import load_dotenv
from nixagent import Agent

os.environ["PROVIDER"] = "gemini"
load_dotenv()

agent = Agent(
    name="GeminiAgent",
    system_prompt="You are a highly capable AI assistant that uses available tools to accomplish goals.",
    provider="gemini"
)

if __name__ == "__main__":
    print("Running Test - Gemini API Usage")
    print("Using Provider:", agent.provider)
    print("Using Model:", agent.model)
    print("\n--- Testing Direct Answer ---")
    reply = agent.run(user_prompt="Who are you? Please answer in 1 sentence.")
    print("Agent Reply:", reply)

    print("\n--- Testing Tool Usage ---")
    tool_reply = agent.run(user_prompt="List the contents of the current directory using your tools. Be concise.")
    print("Agent Tool Reply:", tool_reply)

    print("\n--- Testing Streaming ---")
    stream_response = agent.run(user_prompt="Count from 1 to 5.", stream=True)
    print("Agent Streaming Reply: ", end="", flush=True)
    for chunk in stream_response:
        sys.stdout.write(chunk)
        sys.stdout.flush()
    print()
