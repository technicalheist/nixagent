"""
Test 08 - Verbose Output Control
=================================
Demonstrates the `verbose` flag on Agent. When verbose=True, the agent prints
a structured trace to stdout in real-time:
  - Iteration headers
  - LLM assistant messages
  - Tool call name + arguments
  - Tool result content

This is fully opt-in — setting verbose=False (the default) produces zero extra
output, keeping existing behaviour unchanged.
"""

import sys
import os

# Ensure the project root (parent of this file's directory) is on the path
# so the nixagent package is importable when running from any working directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from nixagent import Agent

load_dotenv()


# ---------------------------------------------------------------------------
# Example 1: Simple Q&A — verbose shows iteration + final assistant message
# ---------------------------------------------------------------------------
def test_simple_verbose():
    print("=" * 60)
    print("Test 08a — Simple Q&A with verbose=True")
    print("=" * 60)

    agent = Agent(
        name="VerboseAgent",
        system_prompt="You are a concise, helpful assistant. Answer in one sentence.",
        verbose=True,          # <-- user-controlled output
    )

    result = agent.run("What is the capital of France?")
    print("\n--- Final Result ---")
    print(result)


# ---------------------------------------------------------------------------
# Example 2: Tool-using agent — verbose shows full tool call / result trace
# ---------------------------------------------------------------------------
def test_tool_verbose():
    print("\n" + "=" * 60)
    print("Test 08b — Tool Usage with verbose=True")
    print("=" * 60)

    # Custom mock tool so we don't need real filesystem side effects
    def get_weather(city: str) -> str:
        """Returns a fake weather report."""
        return f"It is sunny and 24°C in {city}."

    custom_tools = {"get_weather": get_weather}
    custom_tool_defs = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Returns the current weather for a given city.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "Name of the city to get weather for.",
                        }
                    },
                    "required": ["city"],
                },
            },
        }
    ]

    agent = Agent(
        name="WeatherAgent",
        system_prompt="You are a weather assistant. Use the get_weather tool to answer questions.",
        custom_tools=custom_tools,
        custom_tool_defs=custom_tool_defs,
        use_builtin_tools=False,   # only our custom tool
        verbose=True,              # show full execution trace
    )

    result = agent.run("What is the weather in Tokyo?")
    print("\n--- Final Result ---")
    print(result)


# ---------------------------------------------------------------------------
# Example 3: Same scenario, verbose=False — no extra output
# ---------------------------------------------------------------------------
def test_silent_default():
    print("\n" + "=" * 60)
    print("Test 08c — Same Tool Agent with verbose=False (silent, default)")
    print("=" * 60)

    def get_weather(city: str) -> str:
        return f"It is cloudy and 18°C in {city}."

    custom_tools = {"get_weather": get_weather}
    custom_tool_defs = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Returns the current weather for a given city.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string", "description": "Name of the city."}
                    },
                    "required": ["city"],
                },
            },
        }
    ]

    agent = Agent(
        name="SilentWeatherAgent",
        system_prompt="You are a weather assistant. Use the get_weather tool to answer questions.",
        custom_tools=custom_tools,
        custom_tool_defs=custom_tool_defs,
        use_builtin_tools=False,
        verbose=False,   # default — no trace output printed
    )

    result = agent.run("What is the weather in London?")
    print("(No verbose trace above — only the final result below)")
    print("\n--- Final Result ---")
    print(result)


# ---------------------------------------------------------------------------
# Example 4: Streaming mode with verbose=True
# ---------------------------------------------------------------------------
def test_stream_verbose():
    print("\n" + "=" * 60)
    print("Test 08d — Streaming with verbose=True")
    print("=" * 60)

    agent = Agent(
        name="StreamVerboseAgent",
        system_prompt="You are a storyteller. Tell a very short story (2-3 sentences).",
        verbose=True,
    )

    stream = agent.run("Tell me a story about a robot who learns to paint.", stream=True)

    print("\n--- Streaming Output ---")
    for chunk in stream:
        sys.stdout.write(chunk)
        sys.stdout.flush()
    print("\n--- End Stream ---")


if __name__ == "__main__":
    test_simple_verbose()
    test_tool_verbose()
    test_silent_default()
    test_stream_verbose()
