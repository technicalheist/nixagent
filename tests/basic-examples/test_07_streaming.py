from dotenv import load_dotenv
from nixagent import Agent
import sys

load_dotenv()

def main():
    agent = Agent(
        name="StreamTest",
        system_prompt="You are a helpful assistant. Please tell a short story."
    )
    
    print("Running Test 07 - Streaming Response")
    # Tell a short story
    stream = agent.run("Write a 3 sentence story about a brave knight.", stream=True)
    
    print("\n--- Start Stream ---")
    for chunk in stream:
        sys.stdout.write(chunk)
        sys.stdout.flush()
    print("\n--- End Stream ---")

if __name__ == "__main__":
    main()
