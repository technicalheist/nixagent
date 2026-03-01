from dotenv import load_dotenv
from nixagent import Agent

load_dotenv()

safe_agent = Agent(
    name="SafeAgent",
    system_prompt="You are a restricted agent. Check the files in the current dir using list_files.",
    disabled_tools=["execute_shell_command", "delete_file", "write_file"] # Specifically disabling deep native dangerous functions!
)

if __name__ == "__main__":
    print("Running Test 05 - Built-in Tools (Safe Mode Filter Disable Test)")
    print(f"Tools loaded natively for {safe_agent.name}: {list(safe_agent.tools.keys())}")
    
    result = safe_agent.run("What files are in the current directory? List them.")
    print("\n--- Output ---")
    print(result)
