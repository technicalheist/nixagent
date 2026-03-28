---
name: nixagent
description: A sophisticated, provider-agnostic AI agent framework in Python. Supports OpenAI, Anthropic, Gemini, and Vertex AI. Features autonomous agents with built-in file/shell tools, multi-agent collaboration, custom tool injection, MCP server integration, and streaming responses.
---

## Installation

### 1. Install the nixagent Python Package

```bash
pip install nixagent
```

### 2. Set Up Your Environment

Create a `.env` file in the root directory of your project:

```bash
# LLM Provider (openai, anthropic, gemini, or vertex)
PROVIDER=openai

# OpenAI Configuration
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o

# Anthropic Configuration
ANTHROPIC_API_KEY=your_anthropic_api_key_here
ANTHROPIC_BASE_URL=https://api.anthropic.com/v1
ANTHROPIC_MODEL=claude-3-opus-20240229

# Gemini Configuration
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
GEMINI_MODEL=gemini-2.5-flash

# Vertex AI Configuration
VERTEX_API_KEY=your_vertex_api_key_here
VERTEX_BASE_URL=https://aiplatform.googleapis.com/v1
VERTEX_MODEL=gemini-2.5-flash-lite

# Tool and Processing Configuration
MAX_ITERATIONS=25

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=agent.log  # (Optional) Route all agent tool execution traces to this file instead of stdout
```

---

## Overview

`nixagent` is a generic, multipurpose AI agent framework in Python. It is completely agnostic to specific use cases and architectures, serving as a robust foundation for building autonomous, collaborative AI agents that can:

- Manage their own conversation context
- Interface with each other via a collaborator network
- Use file system tools, shell execution, and custom functions
- Dynamically extend with external MCP (Model Context Protocol) servers
- Stream responses in real-time

It bypasses heavy provider-specific SDKs and uses **pure HTTP requests** following the standard OpenAI JSON format payload schema — making it compatible with OpenAI, Anthropic, Gemini, Vertex AI, local LLMs (via Ollama/vLLM), Groq, and more.

---

## 1. Simple Usage

The `nixagent` library makes it incredibly easy to configure and deploy autonomous AI agents capable of contextual reasoning. All you need is an environment configuration and standard Python integration.

### Setting Up Your Environment

`nixagent` uses pure HTTP requests following the standard OpenAI JSON format. Create a `.env` file where your python script executes:

```bash
PROVIDER=openai
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o
```

You can switch to `PROVIDER=anthropic`, `PROVIDER=gemini`, or `PROVIDER=vertex` and configure their respective variables. The framework seamlessly understands all providers.

### Basic Agent Invocation

```python
import os
from dotenv import load_dotenv
from nixagent import Agent

# Load variables from .env
load_dotenv()

# Initialize the core agent
agent = Agent(
    name="MainAgent",
    system_prompt="You are a highly capable AI assistant that uses available tools to accomplish goals."
)

if __name__ == "__main__":
    reply = agent.run(user_prompt="Who are you and what time is it?")
    print(reply)
```

The system will automatically log the iteration steps sequentially as the AI loops and checks its context.

> **Code Reference:** [`examples/test_01_simple_usage.py`](./examples/test_01_simple_usage.py)

---

## 2. Multi-Agent Collaboration

One of the most powerful features of `nixagent` is its ability to natively cluster multiple agents together. Each agent runs contextually independent, utilizing its own system prompts to accomplish tasks, but they can be allowed to delegate requests dynamically by registering each other as "collaborators."

### Registering Sub-Agents

By using `.register_collaborator(agent)`, you map a secondary agent directly into the primary agent's payload context as a native standard tool.

```python
from dotenv import load_dotenv
from nixagent import Agent

load_dotenv()

# Initialize primary agent
coordinator = Agent(
    name="Coordinator",
    system_prompt="You are a project manager. Coordinate tasks with your sub-agents."
)

# Initialize specialized sub-agents
researcher = Agent(
    name="Researcher",
    system_prompt="You perform deep academic research and only return factual bullet points."
)

writer = Agent(
    name="Writer",
    system_prompt="You are a creative writer. You take bullet points and produce engaging articles."
)

# Connect the network:
# The Coordinator now has standard tools exposed to query "ask_agent_Researcher" and "ask_agent_Writer"
coordinator.register_collaborator(researcher)
coordinator.register_collaborator(writer)

if __name__ == "__main__":
    response = coordinator.run("Ask the researcher for 3 facts about black holes, then send them to the writer to write an intro paragraph.")
    
    print("\n--- Final Output ---")
    print(response)
```

**How it Works:**
When `coordinator` needs information from `researcher`, the framework stalls `coordinator`'s request context, boots up `researcher`, streams all prompts and native tool iterations internally through the researcher, and finally takes the resulting string answer and routes it right back securely into `coordinator`'s history.

> **Code Reference:** [`examples/test_02_multi_agent.py`](./examples/test_02_multi_agent.py)

---

## 3. Custom Tools and Functions

While `nixagent` provides deep internal access to the system via its built-in toolkit, you can securely pass in your own Python logic using the `custom_tools` dictionaries. These functions act as an overlay and do not destruct or overwrite standard built-in abilities.

### Step 1: Define the Python Logic

```python
def check_inventory(item_name: str) -> str:
    """Mock database check"""
    database = {"apples": 14, "oranges": 0}
    if item_name.lower() in database:
        return f"We have {database[item_name.lower()]} {item_name} in stock."
    return f"Item '{item_name}' is not carried in our system."
```

### Step 2: Define the Mapping Object and JSON Schema (Tool Def)

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

### Step 3: Initialize the Agent

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

> **Code Reference:** [`examples/test_03_custom_tools.py`](./examples/test_03_custom_tools.py)

---

## 4. Using Model Context Protocol (MCP)

`nixagent` natively integrates with **Model Context Protocol (MCP)**, allowing you to ingest and harness highly specialized tools exposed by standard MCP process servers completely autonomously.

### Step 1: Define your Server File

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

### Step 2: Connecting the MCP Context to an Agent

You can selectively harness MCP configurations inside certain agents by defining the path pointer to the JSON payload via the parameter `mcp_config_path`:

```python
from dotenv import load_dotenv
from nixagent import Agent

load_dotenv()

agent = Agent(
    name="DB_Agent",
    system_prompt="You are a helpful SQL assistant.",
    mcp_config_path="mcp.json"  # Overrides defaults natively dynamically
)

if __name__ == "__main__":
    agent.run("Read the tables from the sqlite database.")
```

### How MCP Works Internally

When an Agent initializes with an MCP configuration path:
1. It reads `mcp.json` and evaluates standard nodes marked with `"active": true`.
2. Utilizing STDIN/STDOUT processes, it hooks securely into those local shell domains and downloads the `tools/list` schema from that subsystem.
3. Automatically translates them to `mcp__{server_name}__{tool_name}` internally to avoid local tool collisions (for example, `mcp__sqlite__query`).
4. Injects them transparently inside standard LLM execution logic!

> **Code Reference:** [`examples/test_04_mcp_usage.py`](./examples/test_04_mcp_usage.py)

---

## 5. Built-In Tools

`nixagent` ships directly with deep, robust native tools focused heavily around File System Mechanics and Subprocess secure shell implementations out of the box. Unless overridden via parameters, these tools are **enabled by default** for any agent you initialize.

### Core System Tools Available

| Tool | Description |
|------|-------------|
| `list_files(directory, recursive)` | Scans the directory and lists out localized hierarchy mapping structurally to identify structure logic inside unknown repositories. |
| `list_files_by_pattern(directory, pattern, recursive)` | Deep Regex matching for identifying specific source files via system names (e.g., `*.py`). |
| `read_file(filepath)` | Pulls direct source string content of targeted local documents directly into LLM sequence buffers. |
| `write_file(filepath, content)` | Directly creates or wholly overwrites localized structures via standard OS hooks with strict encoding standards. |
| `delete_file(filepath)` | Removes specific files or directory structures off the active filesystem context natively. |
| `search_file_contents(directory, pattern, use_regex, recursive)` | Very robust grep-style internal searching mechanism. Used specifically by agents trying to traverse deep architectural scopes. |
| `execute_shell_command(command, working_directory)` | Harnesses secure isolated `subprocess` execution sequences directly onto the hosted terminal environment. |

### Restricting Default Tools

If you want an agent to operate *without* the built-in system tools (for example, a restricted writer agent), use the `use_builtin_tools=False` flag:

```python
restricted_agent = Agent(
    name="Chatter",
    system_prompt="You only talk, you cannot act.",
    use_builtin_tools=False
)
```

To disable only specific dangerous tools, supply the `disabled_tools` array flag:

```python
safe_agent = Agent(
    name="SafeAgent",
    system_prompt="You can read and list files, but you cannot execute scripts or delete files.",
    disabled_tools=["execute_shell_command", "delete_file"]
)
```

> **Code Reference:** [`examples/test_05_builtin_tools.py`](./examples/test_05_builtin_tools.py)

---

## 6. Configuration and Command Line Interface

Beyond Python imports, `nixagent` provides an integrated CLI wrapper allowing interactive reasoning loops without building a script.

### Using the CLI (`app.py`)

```bash
# Direct Question
python app.py "What text files exist in the public/ directory?"

# Interactive Mode
python app.py
```

*Note: Interactive Mode boots up a persistent conversational loop that maintains message history recursively until you `exit`.*

### Setting up Logging

`nixagent` relies explicitly on safe environment configurations. You can optionally expose deep execution iteration logs to a specific local file by defining standard logger values inside the `.env`:

```bash
LOG_LEVEL=DEBUG    # Can be INFO, DEBUG, ERROR, WARNING
LOG_FILE=nix_debug.log
```

### Safety Mechanics (`MAX_ITERATIONS`)

The framework operates as an autonomous multi-iteration orchestrator. If the model continually decides to chain functions together recursively, `nixagent` securely stops the logic execution automatically to prevent infinite API billing loops.

You can modify this ceiling explicitly:

```bash
# Default is 15. Set to higher value for extreme file-system operations
MAX_ITERATIONS=50
```

> **Code Reference:** [`examples/test_06_cli_and_config.py`](./examples/test_06_cli_and_config.py)

---

## 7. Streaming Responses

`nixagent` supports real-time streaming responses via the `stream=True` parameter on `agent.run()`.

### Usage

```python
from dotenv import load_dotenv
from nixagent import Agent
import sys

load_dotenv()

agent = Agent(
    name="StreamTest",
    system_prompt="You are a helpful assistant."
)

stream = agent.run("Write a 3 sentence story about a brave knight.", stream=True)

print("\n--- Start Stream ---")
for chunk in stream:
    sys.stdout.write(chunk)
    sys.stdout.flush()
print("\n--- End Stream ---")
```

When `stream=True` is passed, `agent.run()` returns a **generator** that yields text chunks progressively, just like standard LLM chat interfaces.

> **Code Reference:** [`examples/test_07_streaming.py`](./examples/test_07_streaming.py)

---

## Provider-Specific Usage

You can explicitly set the provider at the Agent level, overriding the `.env` configuration:

### Anthropic (Claude)

```python
agent = Agent(
    name="AnthropicAgent",
    system_prompt="You are a highly capable AI assistant.",
    provider="anthropic"
)
```

> **Code Reference:** [`examples/test_anthropic.py`](./examples/test_anthropic.py)

### Google Gemini

```python
agent = Agent(
    name="GeminiAgent",
    system_prompt="You are a highly capable AI assistant.",
    provider="gemini"
)
```

> **Code Reference:** [`examples/test_gemini.py`](./examples/test_gemini.py)

### Google Vertex AI

```python
agent = Agent(
    name="VertexAgent",
    system_prompt="You are a highly capable AI assistant.",
    provider="vertex"
)
```

> **Code Reference:** [`examples/test_vertex.py`](./examples/test_vertex.py)

---

## Project Structure

```text
nixagent/
├── app.py                # Main CLI application
├── nixagent/             # Core Framework Mechanics
│   ├── __init__.py       # Library exports
│   ├── agent.py          # Core contextual autonomous Agent
│   ├── llm.py            # Central HTTP-based LLM orchestration
│   ├── logger.py         # Central system execution logger
│   ├── mcp.py            # Model Context Protocol definition and bindings
│   ├── providers/        # LLM Vendor specific HTTP adapters
│   │   ├── openai.py
│   │   ├── anthropic.py
│   │   ├── gemini.py
│   │   └── vertex.py
│   └── tools/            # Default Native Tools
│       ├── __init__.py   # Tool bindings & descriptions
│       ├── cmd.py        # Subprocess shell extensions
│       └── fs.py         # File system native operations
├── mcp.json              # Model Context Protocol Server mapping
├── requirements.txt      # Python dependencies
└── .env                  # Operational mapping variables
```

---

## Links

- **PyPI:** https://pypi.org/project/nixagent/
- **GitHub:** https://github.com/technicalheist/nixagent
- **Issues:** https://github.com/technicalheist/nixagent/issues
