from dotenv import load_dotenv
from nixagent import Agent

load_dotenv()

coordinator = Agent(
    name="Coordinator",
    system_prompt="You are a project manager. Coordinate tasks with your sub-agents."
)

researcher = Agent(
    name="Researcher",
    system_prompt="You perform deep academic research and only return factual bullet points."
)

writer = Agent(
    name="Writer",
    system_prompt="You are a creative writer. You take bullet points and produce engaging articles."
)

coordinator.register_collaborator(researcher)
coordinator.register_collaborator(writer)

if __name__ == "__main__":
    print("Running Test 02 - Multi-Agent Collaboration")
    response = coordinator.run("Ask the researcher for 3 facts about black holes, then send them to the writer to write an intro paragraph.")
    print("\n--- Final Output ---")
    print(response)
