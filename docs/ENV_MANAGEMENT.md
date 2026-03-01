# Environment Management Guide

This guide explains how to manage environment variables for your autonomous Agent Framework.

## 🎯 Overview

The Local Agent Toolkit utilizes pure `requests` and a unified JSON configuration layer to power agnostic capabilities across providers (OpenAI, Gemini, Vertex AI, Groq, Ollama). 

All configurations start at your project's `.env` or system environment flags.

## 🔧 Configuration Options

### Core Connection Methods

We rely on three primary fields: `API_BASE_URL`, `API_KEY`, and `MODEL`. This conforms automatically to the wide ecosystem of standard APIs.

Place this `.env` inside your working directory alongside `app.py`:

```bash
# Core API Key for the desired AI provider
API_KEY=your_key_here

# Base URL for the OpenAI compatible endpoint
API_BASE_URL=https://api.openai.com/v1

# The model name to use for generating responses
MODEL=gpt-4o

# Tool call safety depth
MAX_ITERATIONS=25
```

If you are using **Ollama** locally, your setup looks like this:

```bash
# Core API Key
API_KEY="ollama" 

# Base URL pointing to Ollama
API_BASE_URL=http://localhost:11434/v1

# The model name downloaded
MODEL=llama3.2
```

### Extending System Configuration

You can also rely entirely on system flags dynamically in Linux/Mac or in CI/CD chains by skipping files completely:

```bash
export API_KEY="sk-..."
export API_BASE_URL="https://api.groq.com/openai/v1"
export MODEL="llama3-groq-70b-8192-tool-use-preview"
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
ENV API_BASE_URL=https://api.openai.com/v1
ENV MODEL=gpt-4o

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
Connect the `API_KEY` straight out of Secure Stores via direct code injections instead of relying entirely on `dotenv`:

```python
import os
import boto3
import json

client = boto3.client('secretsmanager')
secret = client.get_secret_value(SecretId='core-agent-config')

os.environ['API_KEY'] = json.loads(secret['SecretString'])['api_key']

from lib import Agent
agent = Agent("ProductionAgent", "You help users.")
```

## 📋 Complete Variable Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `API_KEY` | Provider API Key | `sk-proj-...` |
| `API_BASE_URL` | Provider Base URL | `https://api.openai.com/v1` |
| `MODEL` | Name of the hosted Model | `gpt-4o` |
| `MAX_ITERATIONS` | Safety Loop Interrupter | `25` |
| `LOG_LEVEL` | Application logging depth | `INFO` / `DEBUG` |
| `LOG_FILE` | Default stdout capture log | `agent.log` |
