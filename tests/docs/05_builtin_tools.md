# Built-In Tools

`nixagent` ships directly with deep, robust native tools focused heavily around File System Mechanics and Subprocess secure shell implementations out of the box. Unless overridden via parameters, these tools are **enabled by default** for any agent you initialize.

### Core System Tools Available:

1. **`list_files(directory: str, recursive: bool)`**
   * *Description:* Scans the directory and lists out localized hierarchy mapping structurally to identify structure logic inside unknown repositories.
   
2. **`list_files_by_pattern(directory: str, pattern: str, recursive: bool)`**
   * *Description:* Deep Regex matching for identifying specific source files via system names (e.g., `*.py`).
   
3. **`read_file(filepath: str)`**
   * *Description:* Pulls direct source string content of targeted local documents directly into LLM sequence buffers.
   
4. **`write_file(filepath: str, content: str)`**
   * *Description:* Directly creates or wholly overwrites localized structures via standard OS hooks with strict encoding standards. Secure text rendering logic payload.
   
5. **`delete_file(filepath: str)`**
   * *Description:* Removes specific files or directory structures off the active filesystem context natively.

6. **`search_file_contents(directory: str, pattern: str, use_regex: bool, recursive: bool)`**
   * *Description:* Very robust grep-style internal searching mechanism. Used specifically by agents trying to traverse deep architectural scopes to look for specific variable or function bindings inside unmapped legacy architectures.

7. **`execute_shell_command(command: str, working_directory: str)`**
   * *Description:* Harnesses secure isolated `subprocess` execution sequences directly onto the hosted terminal environment and streams the standard text error code results logically back to the central logic controller.

### Restricting Default Tools
If you want an agent to operate *without* the built-in system tools (for example, a restricted writer agent), you can use the `use_builtin_tools=False` flag natively when instantiating your Agent. 

```python
restricted_agent = Agent(
    name="Chatter",
    system_prompt="You only talk, you cannot act.",
    use_builtin_tools=False
)
```

Additionally, if you want *most* tools but want to explicitly disable a few dangerous ones (like subprocess execution), you can supply the `disabled_tools` array flag:

```python
safe_agent = Agent(
    name="SafeAgent",
    system_prompt="You can read and list files, but you cannot execute scripts or delete files.",
    disabled_tools=["execute_shell_command", "delete_file"]
)
```
