# Nixagent — Enterprise Features Guide

> **Introduced in:** Sprint 1 (v1.14+)  
> Covers: Retry Logic (E9), Context Window Management (E3), State Checkpointing (E1), Human-in-the-Loop (E2)

---

## Quick Start — All Enterprise Features

```python
from nixagent import Agent

agent = Agent(
    name="EnterpriseAgent",
    system_prompt="You are a powerful enterprise AI assistant.",

    # E9 — Retry: survive transient API hiccups
    max_retries=3,
    retry_delay=1.0,

    # E3 — Context: stop context window exhaustion
    max_context_messages=40,

    # E1 — Checkpointing: survive crashes
    checkpoint_dir="./runs/task_001",

    # E2 — HITL: require human approval for shell commands
    hitl_mode=True,
    hitl_tools=["execute_shell_command", "delete_file"],
)

result = agent.run("Analyze the repository and generate a test report.")
```

---

## E9 — Retry Logic with Exponential Backoff

Wraps every LLM API call with configurable retry behaviour.

### Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `max_retries` | `int` | `3` | Max retry attempts after first failure |
| `retry_delay` | `float` | `1.0` | Initial delay (seconds) between retries |

### Retry Strategy

| Error Type | Behaviour |
|---|---|
| HTTP 429 (Rate Limit) | ✅ Retried with backoff |
| HTTP 503 / 502 / 504 (Server Error) | ✅ Retried with backoff |
| Connection timeout | ✅ Retried with backoff |
| HTTP 401 (Unauthorized) | ❌ Raised immediately — retrying won't help |
| HTTP 400 / 404 | ❌ Raised immediately |

### Standalone Usage

The `call_with_retry` utility can be used independently:

```python
from nixagent.retry import call_with_retry

result = call_with_retry(
    my_api_function,
    max_retries=5,
    retry_delay=2.0,
    arg1="value"
)
```

---

## E3 — Context Window Management

Prevents the agent's message history from growing indefinitely and exhausting the LLM's context window.

### Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `max_context_messages` | `int` | `None` (unlimited) | Sliding window size for message history |
| `context_summarizer` | `Callable` | `None` | Optional function to summarize evicted messages |

### How It Works

1. Before each iteration, the manager checks if `len(messages) - 1` (excluding the system prompt) exceeds `max_context_messages`.
2. If exceeded, the oldest messages are **evicted** from the front of the list.
3. The **system prompt is always preserved**.
4. If a `context_summarizer` is provided, the evicted messages are passed to it and the returned summary is injected back as a context note.

### With a Summarizer

```python
def my_summarizer(evicted_messages: list) -> str:
    # You could call a cheap/fast LLM here to compress old context
    return "Earlier the agent searched for files and found 3 Python modules."

agent = Agent(
    name="CodeAgent",
    system_prompt="...",
    max_context_messages=20,
    context_summarizer=my_summarizer,
)
```

### Standalone Usage

```python
from nixagent import ContextWindowManager

manager = ContextWindowManager(max_messages=20)
messages = manager.maybe_trim(messages)
```

---

## E1 — State Persistence & Checkpointing

Saves the full agent message history to disk after every iteration. If the process crashes, the agent can be resumed exactly where it left off.

### Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `checkpoint_dir` | `str` | `None` (disabled) | Directory to write checkpoint JSON files |
| `resume_from_checkpoint` | `str` | `None` | Path to a checkpoint file to restore from |

### Checkpoint Files

Two files are written on every iteration:

```
./runs/task_001/
├── checkpoint_0001.json   ← Iteration 1 (permanent, for time-travel)
├── checkpoint_0002.json   ← Iteration 2
├── checkpoint_0003.json   ← Iteration 3
└── checkpoint_latest.json ← Always points to most recent state
```

Each checkpoint JSON contains:
```json
{
  "run_id": "67d32a7b-...",
  "agent_name": "EnterpriseAgent",
  "iteration": 3,
  "saved_at": "2026-03-10T05:07:09+00:00",
  "messages": [...],
  "extra": {}
}
```

### Resuming a Crashed Run

```python
# Original run — was killed at iteration 7
agent = Agent(
    name="DataAgent",
    system_prompt="You are a data analyst.",
    checkpoint_dir="./runs/analysis_task",
)
agent.run("Analyze Q1 sales data and write a report.")

# --- Process crashed ---

# Resumed run — picks up from last saved checkpoint
agent = Agent(
    name="DataAgent",
    system_prompt="You are a data analyst.",
    checkpoint_dir="./runs/analysis_task",
    resume_from_checkpoint="./runs/analysis_task/checkpoint_latest.json",
)
agent.run("Continue from where you stopped.")
```

### Standalone Usage

```python
from nixagent import StateManager

sm = StateManager(checkpoint_dir="./my_run", agent_name="MyAgent")
sm.save(messages=agent.messages)

# Later...
checkpoint = StateManager.load("./my_run/checkpoint_latest.json")
restored_messages = checkpoint["messages"]
```

---

## E2 — Human-in-the-Loop (HITL)

Pauses execution before executing specific tools and asks a human operator to approve, reject, or edit the call.

### Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `hitl_mode` | `bool` | `False` | Enable HITL globally |
| `hitl_tools` | `List[str]` | `["execute_shell_command"]` | Tools that require human approval |

### Interactive Prompt

When a guarded tool is about to be called, the agent pauses and shows:

```
════════════════════════════════════════════════════════════
🛑  HUMAN-IN-THE-LOOP APPROVAL REQUIRED
    Agent : DevAgent
    Tool  : execute_shell_command
    Args  : {
        "command": "rm -rf ./temp_build",
        "working_directory": "/home/user/project"
    }
════════════════════════════════════════════════════════════
    Approve? [y]es / [n]o / [e]dit args :
```

**Options:**
- **`y`** — Proceed with the original arguments
- **`n`** — Skip the tool call; agent receives a "skipped by human operator" message
- **`e`** — Edit the arguments as JSON inline before approving

### Example

```python
agent = Agent(
    name="DevAgent",
    system_prompt="You are a DevOps automation agent.",
    hitl_mode=True,
    # Require approval for ALL dangerous built-in tools
    hitl_tools=["execute_shell_command", "delete_file", "write_file"],
)

agent.run("Clean up the build artifacts and redeploy the service.")
```

---

## Combining All Features

```python
from nixagent import Agent

def lightweight_summarizer(msgs):
    """Compress old messages into a brief summary."""
    n = len(msgs)
    return f"[Earlier context: {n} messages covering initial research and file analysis.]"

agent = Agent(
    name="EnterpriseAutomationAgent",
    system_prompt=(
        "You are an enterprise automation agent. You analyze repositories, "
        "run tests, and generate reports. Always be careful with destructive operations."
    ),
    provider="openai",

    # E9 — Retry: survive rate limits during long tasks
    max_retries=5,
    retry_delay=2.0,

    # E3 — Context: keep last 30 messages, auto-summarize older ones
    max_context_messages=30,
    context_summarizer=lightweight_summarizer,

    # E1 — Checkpointing: save state after every iteration
    checkpoint_dir="./runs/repo_analysis_2026_03_10",

    # E2 — HITL: human approval for shell commands only
    hitl_mode=True,
    hitl_tools=["execute_shell_command"],

    verbose=True,
)

result = agent.run("Analyze the entire codebase and generate a comprehensive test coverage report.")
print(result)
```

---

## Feature Matrix

| Feature | New Param(s) | Module | Default (off) |
|---|---|---|---|
| **Retry Logic** | `max_retries`, `retry_delay` | `nixagent/retry.py` | `max_retries=3` (always on) |
| **Context Window** | `max_context_messages`, `context_summarizer` | `nixagent/memory.py` | Disabled unless set |
| **Checkpointing** | `checkpoint_dir`, `resume_from_checkpoint` | `nixagent/state.py` | Disabled unless set |
| **HITL** | `hitl_mode`, `hitl_tools` | `nixagent/agent.py` | Disabled (`hitl_mode=False`) |
| **Graph Routing** | `AgentGraph`, `add_node`, `add_edge` | `nixagent/graph.py` | N/A |
| **LangChain Bridge** | `from_langchain_tool` | `nixagent/integrations/` | N/A |
| **Structured Output** | `output_schema` param on `Agent.run()` | `nixagent/agent.py` | Disabled unless set |

---

## E5 — Graph-Based Routing (LangGraph Alternative)

An included declarative graph orchestration system to direct workflow between agents or functions cleanly.

### Getting Started

```python
from nixagent import AgentGraph, END

graph = AgentGraph()

# Nodes can be lambdas/functions or Agent instances!
graph.add_node("step_1", lambda state: {"count": state.get("count", 0) + 1})
graph.add_node("step_2", lambda state: {"count": state.get("count", 0) * 10})

# Unconditional edges
graph.add_edge("step_1", "step_2")

# Conditional edges (must return name of the next node)
graph.add_conditional_edges("step_2", lambda state: END if state["count"] >= 50 else "step_1")

graph.set_entry_point("step_1")
final_state = graph.run({"count": 5})

print(final_state) # {"count": 60}
```

---

## E4 — LangChain Tool Bridge

Unlock 1000+ pre-built integrations from the LangChain ecosystem without needing to write your own endpoints or load LangChain as a heavy global dependency.

### Getting Started

```python
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from nixagent.integrations.langchain_bridge import from_langchain_tool
from nixagent import Agent

# Create the LangChain BaseTool
wiki_lc_tool = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())

# Convert to native Nixagent primitives (name, callable, OpenAI-style schema)
name, fn, schema = from_langchain_tool(wiki_lc_tool)

agent = Agent(
    name="Researcher",
    system_prompt="You have access to Wikipedia.",
    custom_tools={name: fn},
    custom_tool_defs=[schema],
)

agent.run("Who discovered penecillin?")
```

### Batch Conversion

```python
from nixagent.integrations.langchain_bridge import from_langchain_tools

tools_dict, tools_defs = from_langchain_tools([wiki_lc_tool, another_lc_tool])

agent = Agent(
    name="SuperAgent",
    system_prompt="...",
    custom_tools=tools_dict,
    custom_tool_defs=tools_defs,
)
```

---

## E7 — Structured Output Schema

Enterprise apps often need robust typed and structured data coming back from the agent. `output_schema` ensures the LLM replies in valid JSON and auto-parses it.

### Getting Started

Provide a JSON Schema dictionary to `Agent.run()`. Nixagent will instruct the LLM and attempt to validate/extract the result automatically.

```python
schema = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "sentiment_score": {"type": "number", "minimum": 0, "maximum": 100},
        "tags": {
            "type": "array",
            "items": {"type": "string"}
        }
    },
    "required": ["summary", "sentiment_score", "tags"]
}

# The agent parses and returns a Python dictionary natively!
result_dict = agent.run("Analyze the user review: 'I absolutely love this!'", output_schema=schema)

print(result_dict["sentiment_score"]) # e.g. 98.5
print(result_dict["tags"]) # e.g. ["positive", "happy"]
```
