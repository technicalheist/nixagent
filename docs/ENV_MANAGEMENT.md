# Environment Management Guide

This guide explains how to manage environment variables for your autonomous Agent Framework.

## 🎯 Overview

The `nixagent` package utilizes pure `requests` and a unified JSON configuration layer to power agnostic capabilities across providers (OpenAI, Gemini, Vertex AI, Groq, Ollama). 

All configurations start at your project's `.env` or system environment flags.

## 🔧 Configuration Options

### Core Connection Methods

We rely on identifying the provider `PROVIDER` alongside configuring the specific `BASE_URL`, `API_KEY`, and `MODEL` fields for that provider. 

Place this `.env` inside your working directory alongside `app.py`:

```bash
# LLM Provider (openai, anthropic, gemini, or vertex)
PROVIDER=openai

# OpenAI Configuration
OPENAI_API_KEY=your_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o

# Anthropic Configuration
ANTHROPIC_API_KEY=your_anthropic_key_here
ANTHROPIC_BASE_URL=https://api.anthropic.com/v1
ANTHROPIC_MODEL=claude-3-opus-20240229

# Gemini Configuration
GEMINI_API_KEY=your_gemini_key_here
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

# Tool call safety depth
MAX_ITERATIONS=25
```

If you are using **Ollama** locally, your setup looks like this:

```bash
# Core API Key
OPENAI_API_KEY="ollama" 

# Base URL pointing to Ollama
OPENAI_BASE_URL=http://localhost:11434/v1

# The model name downloaded
OPENAI_MODEL=llama3.2
```

### Extending System Configuration

You can also rely entirely on system flags dynamically in Linux/Mac or in CI/CD chains by skipping files completely:

```bash
export OPENAI_API_KEY="sk-..."
export OPENAI_BASE_URL="https://api.groq.com/openai/v1"
export OPENAI_MODEL="llama3-groq-70b-8192-tool-use-preview"
```

Then boot your application normally: `python app.py "What is 2+2?"`.

## 🐳 Docker Deployment Setup

For containerized agent clusters, environment files are naturally preferred via Docker or Kubernetes configurations:

```dockerfile
# Dockerfile Example
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

# Set defaults
ENV OPENAI_BASE_URL=https://api.openai.com/v1
ENV OPENAI_MODEL=gpt-4o

CMD ["python", "app.py"]
```

## 🔐 Security Best Practices

### 1. Ignore Credentials
Always ensure your `.env` goes into `.gitignore`. Do not commit keys.

```bash
echo ".env" >> .gitignore
echo "mcp.json" >> .gitignore # Hide proprietary tool connections 
```

### 2. AWS Lambda and Secret Clouds
Connect the `OPENAI_API_KEY` straight out of Secure Stores via direct code injections instead of relying entirely on `dotenv`:

```python
import os
import boto3
import json

client = boto3.client('secretsmanager')
secret = client.get_secret_value(SecretId='core-agent-config')

os.environ['OPENAI_API_KEY'] = json.loads(secret['SecretString'])['api_key']

from lib import Agent
agent = Agent("ProductionAgent", "You help users.")
```

## 📋 Complete Variable Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `PROVIDER` | The LLM provider (openai, anthropic, gemini, vertex, qwen) | `openai` |
| `OPENAI_API_KEY` | OpenAI API Key | `sk-proj-...` |
| `OPENAI_BASE_URL` | Provider Base URL for OpenAI compatible APIs | `https://api.openai.com/v1` |
| `OPENAI_MODEL` | Name of the hosted Model | `gpt-4o` |
| `ANTHROPIC_...` | Standard Anthropic environment credentials | `sk-ant-...` |
| `GEMINI_...` | Standard Gemini environment credentials | `AIza...` |
| `VERTEX_...` | Standard Vertex AI API environment credentials | `AQ.Ab...` |
| `QWEN_...` | Standard Qwen Web UI credentials | `user@email...` |
| `MAX_ITERATIONS` | Safety Loop Interrupter | `25` |
| `LOG_LEVEL` | Application logging depth | `INFO` / `DEBUG` |
| `LOG_FILE` | Default stdout capture log | `agent.log` |
