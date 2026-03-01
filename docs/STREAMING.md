# Streaming Usage

The `nixagent` framework supports streaming responses directly from the LLM provider to your console or client application.

## How it works

When you pass `stream=True` to the `Agent.run()` method, the framework delegates the streaming request down to the underlying LLM via Server-Sent Events (SSE). 

Instead of blocking and returning a single string at the end of the final iteration, `Agent.run()` returns a Python **Generator** that yields text chunks as they arrive over the network. 

Tool calls are still handled seamlessly during a streamed response:
1. If the model decides to use a tool, the framework quietly accumulates the tool call chunks.
2. Once the tool call is completely received, the framework executes the tool locally.
3. The framework creates a new iteration and transparently begins streaming the text chunk responses from that subsequent call to you.

## Example

```python
import sys
from nixagent import Agent

agent = Agent(
    name="StreamingAgent",
    system_prompt="You are a poetic assistant."
)

stream = agent.run("Write a beautiful poem about the stars.", stream=True)

for chunk in stream:
    sys.stdout.write(chunk)
    sys.stdout.flush()
```

By leveraging `stream=True`, you can dramatically reduce perceived latency for end-users, especially for long-form content generation tasks.
