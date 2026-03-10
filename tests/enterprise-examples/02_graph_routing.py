import os
from dotenv import load_dotenv

# Import the Agent and the Graph tools
from nixagent import Agent, AgentGraph, END

# Load API keys
load_dotenv()

def main():
    # 1. We create two completely separate agents with different jobs
    writer = Agent(
        name="Writer",
        system_prompt="You are a funny joke writer. Write exactly ONE short joke about programmers.",
        provider=os.getenv("PROVIDER", "openai"),
        use_builtin_tools=False
    )
    
    critic = Agent(
        name="Critic",
        system_prompt="You review jokes. Rate the joke from 1-10 and say why.",
        provider=os.getenv("PROVIDER", "openai"),
        use_builtin_tools=False
    )

    # 2. We initialize the orchestration graph
    graph = AgentGraph()

    # 3. Define the nodes (what happens at each step)
    def writer_node(state):
        print(">> [Writer] is thinking...")
        joke = writer.run("Tell me a programmer joke.")
        print(f"JOKE: {joke}\n")
        return {"current_joke": joke}
        
    def critic_node(state):
        print(">> [Critic] is reviewing...")
        joke_to_review = state.get("current_joke")
        review = critic.run(f"Review this joke: {joke_to_review}")
        print(f"REVIEW: {review}\n")
        return {"final_review": review}

    # 4. Mount the nodes into the graph
    graph.add_node("writer", writer_node)
    graph.add_node("critic", critic_node)
    
    # 5. Connect the nodes together (Edges)
    graph.add_edge("writer", "critic")     # Unconditionally go Writer -> Critic
    graph.add_edge("critic", END)          # Unconditionally go Critic -> Finished
    
    # 6. Set where the graph starts
    graph.set_entry_point("writer")
    
    # 7. Execute the entire multi-agent pipeline!
    print("--- Starting Pipeline ---")
    final_output = graph.run({})
    print("Pipeline Complete! Final state dictionary keys:", final_output.keys())


if __name__ == "__main__":
    main()
