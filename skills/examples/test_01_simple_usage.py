import os
from dotenv import load_dotenv
from nixagent import Agent

load_dotenv()

agent = Agent(
    name="MainAgent",
    system_prompt="You are a highly capable AI assistant that uses available tools to accomplish goals."
)

if __name__ == "__main__":
    print("Running Test 01 - Simple Usage")
    reply = agent.run(user_prompt="Who are you and what time is it? Don't use tools for this, just answer directly.")
    print("\n--- Output ---")
    print(reply)
