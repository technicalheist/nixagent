# Simple Usage of nixagent

The `nixagent` library makes it incredibly easy to configure and deploy autonomous AI agents capable of contextual reasoning. All you need is an environment configuration and standard Python integration.

### Setting Up Your Environment
`nixagent` bypasses heavy provider-specific SDKs and uses pure HTTP requests (following standard OpenAI JSON format payload schemas). To set it up, create a `.env` file where your python script executes:

```bash
API_KEY=your_api_key_here
API_BASE_URL=https://api.openai.com/v1
MODEL=gpt-4o
```

*Note: You can route this to Ollama, Groq, Vertex AI or any other API that speaks the OpenAI schema standard by simply updating the `API_BASE_URL`.*

### Basic Agent Invocation
Once your environment variables are set, you can interact programmatically with your agent:

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
