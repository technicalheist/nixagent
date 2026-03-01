# Multi-Agent Collaboration

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
    # Launch sequence
    response = coordinator.run("Ask the researcher for 3 facts about black holes, then send them to the writer to write an intro paragraph.")
    
    print("\n--- Final Output ---")
    print(response)
```

**How it Works:** 
When `coordinator` needs information from `researcher`, the framework stalls `coordinator`'s request context, boots up `researcher`, streams all prompts and native tool iterations internally through the researcher, and finally takes the resulting string answer and routes it right back securely into `coordinator`'s history.
