from .fs import list_files, read_file, write_file, delete_file, list_files_by_pattern, search_file_contents
from .cmd import execute_shell_command

# Expose available tools
AVAILABLE_TOOLS = {
    "list_files": list_files,
    "read_file": read_file,
    "write_file": write_file,
    "delete_file": delete_file,
    "list_files_by_pattern": list_files_by_pattern,
    "search_file_contents": search_file_contents,
    "execute_shell_command": execute_shell_command,
}

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "Lists all files in a given directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "The path to the directory."},
                    "recursive": {"type": "boolean", "description": "If true, lists files in subdirectories."}
                },
                "required": ["directory"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Reads the content of a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "The path to the file."}
                },
                "required": ["filepath"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Writes content to a file. Overwrites if it exists.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "The path to the file."},
                    "content": {"type": "string", "description": "The content to write."}
                },
                "required": ["filepath", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_file",
            "description": "Deletes a file or directory at the specified path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "The path to the file or directory."}
                },
                "required": ["filepath"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files_by_pattern",
            "description": "Lists files in a given directory that match a regex pattern.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "The path to the directory."},
                    "pattern": {"type": "string", "description": "The regex pattern."},
                    "recursive": {"type": "boolean", "description": "If true, searches recursively."}
                },
                "required": ["directory", "pattern"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_file_contents",
            "description": "Searches within file contents iteratively.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "The dir to search."},
                    "pattern": {"type": "string", "description": "The exact string or regex pattern."},
                    "use_regex": {"type": "boolean", "description": "If true, treats pattern as regular expression."},
                    "recursive": {"type": "boolean", "description": "If true, searches recursively."}
                },
                "required": ["directory", "pattern", "use_regex"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_shell_command",
            "description": "Execute a shell command. IMPORTANT: To run in a specific directory, ALWAYS use the 'working_directory' argument instead of chaining a 'cd' command. Use double quotes (\") for file paths. For command chaining use '&&' on Windows and ';' on Linux/Mac.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The shell command to execute."},
                    "working_directory": {"type": "string", "description": "Dir to run the command in. Default is current dir."}
                },
                "required": ["command"]
            }
        }
    }
]
