# nixagent

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A generic, multipurpose nixagent library in Python. This framework is completely agnostic to specific use cases and architectures, serving as a robust foundation for building autonomous, collaborative AI agents that can manage their own context, interface with each other, and securely use external tools. 

## 🚀 Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Command Line Usage

First, set up your environment configuration by copying `.env.example` to `.env` and adding your API keys.

```bash
# Ask a question directly
python app.py "What files are in the current directory?"

# Interactive mode
python app.py

# With custom settings
python app.py "Analyze the code structure" --no-save
```

### Python Library Usage

```python
from nixagent import Agent

# Initialize the core agent
agent = Agent(
    name="MainAgent",
    system_prompt="You are a highly capable AI assistant that uses available tools to accomplish goals."
)

result = agent.run(user_prompt="List all Python files in the project")
print(result)
```

## ✨ Features

- **🌐 Standardized API Interface**: Uses pure `requests` following the OpenAI native JSON structure. Compatible with OpenAI, Vertex, Local LLMs (via Ollama/vLLM), Groq, and more.
- **🤖 Autonomous Agents**: Agents maintain independent conversation histories and automatically delegate sub-tasks when needed.
- **🔌 Model Context Protocol (MCP)**: Dynamic tool extension via MCP Servers via `.mcp.json`.
- **🛠️ Rich Built-In Tools**: Deep system-level tools covering regex-based file searching, exact content mapping, disk manipulation, and secure subprocess execution.
- **🗣️ Inter-Agent Collaboration**: Support for multiple sub-agents operating concurrently under the same framework via `.register_collaborator(agent)`.

## 📦 Project Structure

```text
framework/
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
│   │   ├── vertex.py
│   │   └── qwen.py
│   └── tools/            # Default Native Tools
│       ├── __init__.py   # Tool bindings & descriptions
│       ├── cmd.py        # Subprocess shell extensions
│       └── fs.py         # File system native operations
├── mcp.json              # Model Context Protocol Server mapping
├── docs/                 # Additional Documentation
├── requirements.txt      # Python dependencies
├── .env                  # Operational mapping variables
└── README.md             # This file
```

## ⚙️ Configuration

Create a `.env` file in your project root:

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

# Qwen Configuration
QWEN_EMAIL=your_email_here
QWEN_PASSWORD=your_password_here
QWEN_MODEL=qwen3.5-plus

# Tool and Processing Configuration
MAX_ITERATIONS=25

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=agent.log  # (Optional) Route all agent tool execution traces to this file instead of stdout
```

## 🔌 Using MCP Servers

Add server definitions to your `mcp.json` file in the root directory:

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

The framework's `MCPManager` automatically bootstraps all active MCP servers, parses their schemas, and loads their tools natively alongside standard tools upon Agent initialization.

## 🤝 Collaborative Agents

Agents can securely establish communication networks.

```python
from nixagent import Agent

research_agent = Agent("Researcher", "You perform file system research.")
writer_agent = Agent("Writer", "You answer questions accurately.")

writer_agent.register_collaborator(research_agent)

writer_agent.run("Ask the Researcher to find all text files and read them to me.")
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
