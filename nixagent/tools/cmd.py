import os
import sys
import subprocess

def execute_shell_command(command, working_directory=None):
    """
    Execute a shell command and return the output.
    On Windows, uses PowerShell so that single-quoted paths, semicolons,
    and Set-Location all work correctly.
    On Linux/macOS, uses the default shell (sh).
    """
    try:
        if working_directory and not os.path.isdir(working_directory):
            return {
                "stdout": "",
                "stderr": f"Error: Directory '{working_directory}' not found.",
                "return_code": 1,
                "success": False,
            }

        if sys.platform == "win32":
            # Use PowerShell on Windows to support single-quoted paths,
            # semicolons for command chaining, and modern shell features.
            cmd_args = ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command]
            result = subprocess.run(
                cmd_args,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                cwd=working_directory,
                timeout=120,
            )
        else:
            # On Linux/macOS use shell=True which defaults to /bin/sh
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                cwd=working_directory,
                timeout=120,
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
            "stderr": "Error: Command timed out after 120 seconds.",
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
