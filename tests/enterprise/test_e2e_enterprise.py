import os
import json
import pytest
import tempfile
from dotenv import load_dotenv

from nixagent import Agent, AgentGraph, END, StateManager
from nixagent.integrations.langchain_bridge import from_langchain_tool

# Load real environment variables to allow real API calls
load_dotenv()

# We only want to run these tests if a valid provider is configured
# and we have an API key available to avoid failing CI pipelines randomly.
HAS_API_KEY = any(
    os.getenv(k) for k in [
        "OPENAI_API_KEY", 
        "ANTHROPIC_API_KEY", 
        "GEMINI_API_KEY", 
        "VERTEX_API_KEY", 
        "QWEN_PASSWORD"
    ]
)

pytestmark = pytest.mark.skipif(
    not HAS_API_KEY, 
    reason="Skipping real E2E enterprise tests because no API key is set in the environment (.env)."
)

# Use whatever provider is set in .env, fallback to whatever works
PROVIDER = os.getenv("PROVIDER", "openai")

def test_real_structured_output():
    """
    E2E Test: Ask the real LLM to extract data and return only proper JSON,
    matching our output_schema.
    """
    schema = {
        "type": "object",
        "properties": {
            "cities": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of city names mentioned in the text."
            },
            "sentiment": {
                "type": "string",
                "enum": ["positive", "neutral", "negative"]
            }
        },
        "required": ["cities", "sentiment"]
    }

    agent = Agent(
        name="Extractor",
        system_prompt="You are a data extraction bot. You strictly follow instructions.",
        provider=PROVIDER,
        use_builtin_tools=False
    )
    
    text_to_analyze = "I had a wonderful time visiting Tokyo last spring, but the train in Kyoto was terrible!"
    
    # This will hit the real API
    result = agent.run(
        user_prompt=f"Analyze this text: '{text_to_analyze}'",
        output_schema=schema
    )
    
    if isinstance(result, str) and ("API error: 429" in result or "LLM error after retries" in result):
        pytest.skip("Provider API is rate limiting (429). Skipping test gracefully.")
        
    assert isinstance(result, dict), f"Expected dict, got {type(result)}: {result}"
    assert "cities" in result
    assert "sentiment" in result
    
    cities_lower = [c.lower() for c in result["cities"]]
    assert "tokyo" in cities_lower
    assert "kyoto" in cities_lower


def test_real_agent_graph_workflow():
    """
    E2E Test: Create a real graph workflow with 2 actual Agents.
    Agent 1 (Researcher) generates a fact.
    Agent 2 (Reviewer) evaluates the fact.
    """
    research_agent = Agent(
        name="Researcher",
        system_prompt="You are a trivia bot. Provide exactly one random fun fact about space. Be brief.",
        provider=PROVIDER,
        use_builtin_tools=False
    )
    
    review_agent = Agent(
        name="Reviewer",
        system_prompt="You review facts. Say 'LGTM' if the fact sounds plausible, or 'REJECT' if it's nonsense.",
        provider=PROVIDER,
        use_builtin_tools=False
    )

    graph = AgentGraph()

    # Define Node 1
    def research_node(state):
        fact = research_agent.run("Give me a space fact.")
        return {"fact": fact}
    
    # Define Node 2
    def review_node(state):
        fact = state.get("fact", "")
        review = review_agent.run(f"Review this fact: {fact}")
        return {"review": review}

    graph.add_node("research", research_node)
    graph.add_node("review", review_node)
    
    graph.add_edge("research", "review")
    graph.add_edge("review", END)
    
    graph.set_entry_point("research")
    
    # Run the real graph
    final_state = graph.run({})
    
    if "fact" in final_state and isinstance(final_state["fact"], str) and "API error: 429" in final_state["fact"]:
         pytest.skip("Provider API is rate limiting (429). Skipping test gracefully.")
         
    if "review" in final_state and isinstance(final_state["review"], str) and "API error: 429" in final_state["review"]:
         pytest.skip("Provider API is rate limiting (429). Skipping test gracefully.")
         
    assert "fact" in final_state
    assert "review" in final_state
    assert len(final_state["fact"]) > 5
    assert len(final_state["review"]) > 2


def test_real_state_checkpointing_resume():
    """
    E2E Test: Run a real interaction, save to disk via StateManager, 
    reinstantiate a totally new Agent pointing to that checkpoint, 
    and ask it what the first message was.
    """
    with tempfile.TemporaryDirectory() as tempdir:
        # 1. First agent talks to the LLM
        agent1 = Agent(
            name="StateBot",
            system_prompt="You are a helpful assistant.",
            provider=PROVIDER,
            checkpoint_dir=tempdir,
            use_builtin_tools=False
        )
        
        reply1 = agent1.run("My secret passcode is 887766.")
        
        if "API error: 429" in reply1 or "LLM error after retries" in reply1:
            pytest.skip("Provider API is rate limiting (429). Skipping test gracefully.")
            
        # Determine the latest checkpoint path
        sm = agent1._state_manager
        latest_file = sm.latest_checkpoint_path()
        assert os.path.exists(latest_file)
        
        # 2. Second agent resumes from that exact state
        agent2 = Agent(
            name="StateBotResumed",
            system_prompt="You are a helpful assistant.",
            provider=PROVIDER,
            resume_from_checkpoint=latest_file,
            use_builtin_tools=False
        )
        
        # It should know the secret passcode because the message list was restored!
        reply2 = agent2.run("What is my secret passcode?")
        
        if "API error: 429" in reply2 or "LLM error after retries" in reply2:
            pytest.skip("Provider API is rate limiting (429). Skipping test gracefully.")
            
        assert "887766" in reply2


def test_real_langchain_bridge():
    """
    E2E Test: Build a real LangChain basic tool, bridge it, and have the
    real LLM decide to call it.
    """
    # We create a dummy langchain tool class to simulate without needing the whole library
    class MockCalculatorTool:
        name = "custom_calculator"
        description = "Adds two numbers together. Usage: pass arg 'expr' like '5+5'"
        
        def run(self, query: str) -> str:
            # simple mock execution
            if "5" in query and "5" in query:
                return "10"
            return "42"
            
    # Bridge it
    name, fn, schema = from_langchain_tool(MockCalculatorTool())
    
    # Give it to the agent
    agent = Agent(
        name="MathBot",
        system_prompt="You have a calculator tool. Use it to answer the user's math question.",
        provider=PROVIDER,
        custom_tools={name: fn},
        custom_tool_defs=[schema],
        use_builtin_tools=False
    )
    
    # LLM should figure out it needs to call the custom_calculator tool
    try:
        result = agent.run("What is 5 plus 5? Use your calculator.")
        
        # We know the tool returns 10, so the LLM should incorporate that into the final string
        if "API error: 429" in result or "LLM error after retries" in result:
            pytest.skip("Provider API is rate limiting (429). Skipping test gracefully.")
            
        assert "10" in result
    except Exception as e:
        if "429" in str(e):
            pytest.skip("Provider API is rate limiting (429). Skipping test gracefully.")
        raise

