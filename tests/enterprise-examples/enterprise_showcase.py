import os
import json
import tempfile
from dotenv import load_dotenv

from nixagent import Agent, AgentGraph, END, StateManager
from nixagent.integrations.langchain_bridge import from_langchain_tool

# Ensure environment variables (like OPENAI_API_KEY) are loaded
load_dotenv()
PROVIDER = os.getenv("PROVIDER", "openai")

def separator(title):
    print("\n" + "="*80)
    print(f"🚀 EXECUTING: {title}")
    print("="*80 + "\n")

def example_1_structured_output():
    separator("Example 1: Structured Output (E7)")
    print("Asking the agent to analyze a review and return a strict JSON dictionary...\n")

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
        name="DataExtractor",
        system_prompt="You are a data extraction bot. You strictly follow instructions.",
        provider=PROVIDER,
        use_builtin_tools=False
    )
    
    text_to_analyze = "I had a wonderful time visiting Tokyo last spring, but the train in Kyoto was terrible!"
    
    # This hits the real API and returns a parsed Python dictionary
    result = agent.run(
        user_prompt=f"Analyze this text: '{text_to_analyze}'",
        output_schema=schema
    )
    
    print("\n✅ Final Extracted Dictionary:")
    print(json.dumps(result, indent=2))
    print(f"Type of result: {type(result)}")


def example_2_graph_routing():
    separator("Example 2: Multi-Agent Graph Routing (E5)")
    print("Creating a Research Agent and a Review Agent, orchestrating them via AgentGraph...\n")

    research_agent = Agent(
        name="Researcher",
        system_prompt="You are a trivia bot. Provide exactly one random fun fact about the ocean. Be very brief.",
        provider=PROVIDER,
        use_builtin_tools=False
    )
    
    review_agent = Agent(
        name="Reviewer",
        system_prompt="You review facts. Say 'APPROVED: <reason>' if plausible, or 'REJECTED: <reason>' if nonsense.",
        provider=PROVIDER,
        use_builtin_tools=False
    )

    graph = AgentGraph()

    # Node 1
    def research_node(state):
        print(">> [Researcher Node] Fetching a fact from the LLM...")
        fact = research_agent.run("Give me an ocean fact.")
        print(f"   Fact obtained: {fact}")
        return {"fact": fact}
    
    # Node 2
    def review_node(state):
        fact = state.get("fact", "")
        print(">> [Review Node] Sending the fact to the Reviewer Agent...")
        review = review_agent.run(f"Review this fact: '{fact}'")
        return {"review": review}

    graph.add_node("research", research_node)
    graph.add_node("review", review_node)
    
    graph.add_edge("research", "review")
    graph.add_edge("review", END)
    
    graph.set_entry_point("research")
    
    print("Starting Workflow...\n")
    final_state = graph.run({})
    
    print("\n✅ Final Workflow State:")
    print(f"Fact Generator Output: {final_state['fact']}")
    print(f"Reviewer Output: {final_state['review']}")


def example_3_time_travel_checkpointing():
    separator("Example 3: State Checkpointing & Resume (E1)")
    print("Creating an agent, giving it a secret, crashing it, then resuming from checkpoint...\n")

    # We use a temporary directory to avoid cluttering your project
    with tempfile.TemporaryDirectory() as tempdir:
        
        # --- PHASE 1: Original Run ---
        print(">> Phase 1: Starting Agent A")
        agent_a = Agent(
            name="StateBot",
            system_prompt="You are a helpful assistant. Keep your answers brief.",
            provider=PROVIDER,
            checkpoint_dir=tempdir, # <--- ENABLES CHECKPOINTING
            use_builtin_tools=False
        )
        
        agent_a.run("My secret passcode is: OMEGA-77-DELTA.")
        print("   Agent A has processed the passcode.")
        
        # Get the path to the checkpoint it just saved
        latest_checkpoint = agent_a._state_manager.latest_checkpoint_path()
        print(f"   Checkpoint saved to disk at: {latest_checkpoint}")
        
        # --- PHASE 2: Crash / Restart ---
        print("\n>> Phase 2: Simulating system crash... Agent A is destroyed.")
        del agent_a 
        
        print("\n>> Phase 3: Starting Agent B (Resuming from checkpoint)")
        agent_b = Agent(
            name="StateBot(Resumed)",
            system_prompt="You are a helpful assistant. Keep your answers brief.",
            provider=PROVIDER,
            resume_from_checkpoint=latest_checkpoint, # <--- RESUMES
            use_builtin_tools=False
        )
        
        print("   Agent B is asking the LLM for the passcode...")
        reply = agent_b.run("What was my secret passcode?")
        
        print(f"\n✅ Agent B Reply: {reply}")


if __name__ == "__main__":
    print(f"Using Provider: {PROVIDER.upper()}")
    
    try:
        example_1_structured_output()
        example_2_graph_routing()
        example_3_time_travel_checkpointing()
        
        print("\n" + "="*80)
        print("🎉 ALL EXAMPLES COMPLETED SUCCESSFULLY!")
        print("="*80 + "\n")
        
    except Exception as e:
        if "429" in str(e):
            print(f"\n⚠️ WARNING: Your LLM Provider ({PROVIDER}) is rate-limiting your API key (HTTP 429).")
            print("Try switching to a different provider in your .env file or wait a moment.")
        else:
            raise
