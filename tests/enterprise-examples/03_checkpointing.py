import os
import tempfile
from dotenv import load_dotenv

# Import the Agent
from nixagent import Agent

# Load API keys
load_dotenv()

def main():
    print("--- State Checkpointing & Resume Demo ---")
    
    # We will use a temporary folder on your computer to save the agent's brain 
    # (checkpoint JSON files) so we don't clutter your project.
    with tempfile.TemporaryDirectory() as brain_folder:
        
        # ---------------------------------------------------------
        # PHASE 1: Create our first agent
        # ---------------------------------------------------------
        print(f"\n1. Booting up Agent 1. It saves data to: {brain_folder}")
        agent1 = Agent(
            name="MemoryBot",
            system_prompt="You remember things.",
            provider=os.getenv("PROVIDER", "openai"),
            checkpoint_dir=brain_folder, # <-- THIS ENABLES SAVING!
            use_builtin_tools=False
        )
        
        # We tell it some random facts
        print("User: My favorite color is Neon Green and my dog's name is Bark Twain.")
        agent1.run("My favorite color is Neon Green and my dog's name is Bark Twain.")
        
        # Get the exact file path where it just saved its brain
        saved_brain_file = agent1._state_manager.latest_checkpoint_path()
        print(f"Agent 1 automatically saved its brain to -> {saved_brain_file}")
        
        # ---------------------------------------------------------
        # PHASE 2: Kill Agent 1
        # ---------------------------------------------------------
        print("\n2. Oh no! Agent 1 crashed or was destroyed!")
        del agent1
        
        # ---------------------------------------------------------
        # PHASE 3: Boot a brand new Agent from that saved brain
        # ---------------------------------------------------------
        print("\n3. Booting up Agent 2, but pointing it at Agent 1's brain file...")
        agent2 = Agent(
            name="ResurrectedBot",
            system_prompt="You remember things.",
            provider=os.getenv("PROVIDER", "openai"),
            resume_from_checkpoint=saved_brain_file, # <-- THIS LOADS THE BRAIN!
            use_builtin_tools=False
        )
        
        # Ask it things only Agent 1 would know
        print("\nUser: What is my favorite color and my dog's name?")
        answer = agent2.run("What is my favorite color and my dog's name?")
        
        print("\nAgent 2 Answers:")
        print(answer)

if __name__ == "__main__":
    main()
