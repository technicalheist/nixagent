import os
import subprocess

def execute_shell_command(command, working_directory=None):
    """
    Execute a shell command and return the output.
    """
    try:
        if working_directory and not os.path.isdir(working_directory):
            return {
                "stdout": "",
                "stderr": f"Error: Directory '{working_directory}' not found.",
                "return_code": 1,
                "success": False,
            }

        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=working_directory,
            timeout=30,
        )

        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode,
            "success": result.returncode == 0,
        }

    except subprocess.TimeoutExpired:
        return {
            "stdout": "",
            "stderr": "Error: Command timed out after 30 seconds.",
            "return_code": 124,
            "success": False,
        }
    except Exception as e:
        return {
            "stdout": "",
            "stderr": f"Error executing command: {e}",
            "return_code": 1,
            "success": False,
        }
