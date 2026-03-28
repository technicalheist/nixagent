import subprocess

def run_cli_test():
    print("Running Test 06 - CLI & Config Wrapper Test")
    print("Simulating local-agent CLI proxy interaction via python subprocess:")

    command = ["python", "../app.py", "Test if CLI operates successfully and tell me.", "--no-save"]
    try:
        result = subprocess.run(command, capture_output=True, text=True)
        print("--- Subprocess STD OUT: ---")
        print(result.stdout)
    except Exception as e:
        print(f"CLI proxy run error: {e}")

if __name__ == "__main__":
    run_cli_test()
