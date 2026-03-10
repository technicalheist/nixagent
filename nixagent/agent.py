import os
import json
from typing import List, Dict, Any, Callable, Optional
from .llm import call_llm
from .tools import AVAILABLE_TOOLS, TOOL_DEFINITIONS
from .mcp import MCPManager
from .logger import logger
from .retry import call_with_retry, RetryError
from .memory import ContextWindowManager
from .state import StateManager

_global_mcp_managers = {}

def get_mcp_manager(config_path="mcp.json"):
    global _global_mcp_managers
    if config_path not in _global_mcp_managers:
        manager = MCPManager(config_path)
        manager.load_and_activate()
        _global_mcp_managers[config_path] = manager
    return _global_mcp_managers[config_path]


class Agent:
    def __init__(
        self,
        name: str,
        system_prompt: str,
        model: str = None,
        custom_tools: dict = None,
        custom_tool_defs: list = None,
        mcp_config_path: str = "mcp.json",
        use_builtin_tools: bool = True,
        disabled_tools: list = None,
        provider: str = None,
        verbose: bool = False,
        # ── E9: Retry ─────────────────────────────────────────────────
        max_retries: int = 3,
        retry_delay: float = 1.0,
        # ── E3: Context Window Management ─────────────────────────────
        max_context_messages: Optional[int] = None,
        context_summarizer: Optional[Callable[[List[Dict]], str]] = None,
        # ── E1: State / Checkpointing ──────────────────────────────────
        checkpoint_dir: Optional[str] = None,
        resume_from_checkpoint: Optional[str] = None,
        # ── E2: Human-in-the-Loop ─────────────────────────────────────
        hitl_mode: bool = False,
        hitl_tools: Optional[List[str]] = None,
    ):
        """
        Create a Nixagent Agent.

        Args:
            name:                    Unique display name for this agent.
            system_prompt:           The LLM's system instruction.
            model:                   Override the model name (falls back to env var).
            custom_tools:            Dict of {tool_name: callable} to merge with built-ins.
            custom_tool_defs:        List of OpenAI-format function schemas for custom_tools.
            mcp_config_path:         Path to mcp.json for MCP server config.
            use_builtin_tools:       If False, starts with zero tools (no fs/cmd).
            disabled_tools:          List of built-in tool names to disable selectively.
            provider:                LLM provider: "openai" | "anthropic" | "gemini" |
                                     "vertex" | "qwen".
            verbose:                 Print detailed iteration/tool logs to stdout.

            max_retries:             Max retry attempts on transient LLM API errors (E9).
            retry_delay:             Initial backoff delay in seconds between retries (E9).

            max_context_messages:    Sliding window size for the message history.
                                     Old messages are evicted when limit is exceeded (E3).
            context_summarizer:      Optional callable(evicted_msgs) -> str that
                                     produces a summary of evicted messages (E3).

            checkpoint_dir:          Directory to write per-iteration JSON checkpoints.
                                     Enables crash recovery and time-travel (E1).
            resume_from_checkpoint:  Path to a checkpoint JSON file to restore from.
                                     The agent resumes exactly where it left off (E1).

            hitl_mode:               When True, pauses before executing any tool whose
                                     name appears in hitl_tools and asks for approval (E2).
            hitl_tools:              List of tool names requiring human approval.
                                     Defaults to ["execute_shell_command"] (E2).
        """
        self.name = name
        self.system_prompt = system_prompt
        self.verbose = verbose
        self.provider = provider or os.getenv("PROVIDER", "openai")

        # ── Provider / Model resolution ────────────────────────────────────
        if self.provider.lower() == "anthropic":
            self.model = model or os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229")
        elif self.provider.lower() == "gemini":
            self.model = model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        elif self.provider.lower() == "vertex":
            self.model = model or os.getenv("VERTEX_MODEL", "gemini-2.5-flash-lite")
        elif self.provider.lower() == "qwen":
            self.model = model or os.getenv("QWEN_MODEL", "qwen3.5-plus")
        else:
            self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o")

        # ── E9: Retry config ───────────────────────────────────────────────
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # ── E2: HITL config ────────────────────────────────────────────────
        self.hitl_mode = hitl_mode
        self.hitl_tools = set(hitl_tools) if hitl_tools else {"execute_shell_command"}

        # ── E3: Context window manager ─────────────────────────────────────
        self._context_manager: Optional[ContextWindowManager] = None
        if max_context_messages is not None:
            self._context_manager = ContextWindowManager(
                max_messages=max_context_messages,
                summarizer=context_summarizer,
            )

        # ── E1: State / Checkpoint manager ────────────────────────────────
        self._state_manager: Optional[StateManager] = None
        if checkpoint_dir:
            self._state_manager = StateManager(
                checkpoint_dir=checkpoint_dir,
                agent_name=name,
            )

        # ── Message history ────────────────────────────────────────────────
        if resume_from_checkpoint:
            checkpoint_data = StateManager.load(resume_from_checkpoint)
            self.messages = checkpoint_data["messages"]
            # Sync StateManager iteration counter if possible
            if self._state_manager:
                self._state_manager._iteration_count = checkpoint_data.get("iteration", 0)
            logger.info(
                f"[{name}] Resumed from checkpoint: {resume_from_checkpoint} "
                f"({len(self.messages)} messages restored)"
            )
        else:
            self.messages = [{"role": "system", "content": system_prompt}]

        # ── Tool setup ─────────────────────────────────────────────────────
        if use_builtin_tools:
            self.tools = AVAILABLE_TOOLS.copy()
            self.tool_defs = TOOL_DEFINITIONS.copy()
        else:
            self.tools = {}
            self.tool_defs = []

        if disabled_tools:
            for d_tool in disabled_tools:
                self.tools.pop(d_tool, None)
            self.tool_defs = [
                td for td in self.tool_defs
                if td["function"]["name"] not in disabled_tools
            ]

        if custom_tools:
            self.tools.update(custom_tools)
        if custom_tool_defs:
            self.tool_defs.extend(custom_tool_defs)

        # Load MCP tools
        mcp = get_mcp_manager(mcp_config_path)
        mcp_tools = mcp.get_all_tools()
        if mcp_tools:
            self.tool_defs.extend(mcp_tools)
            for mcp_tool in mcp_tools:
                mcp_name = mcp_tool["function"]["name"]

                def make_mcp_caller(n):
                    return lambda **kwargs: mcp.call_tool(n, kwargs)

                self.tools[mcp_name] = make_mcp_caller(mcp_name)

        self.agents_in_network = {}

    # ──────────────────────────────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────────────────────────────

    def _vprint(self, *args, **kwargs):
        """Print only when verbose mode is enabled."""
        if self.verbose:
            print(*args, **kwargs)

    def _print_iteration(self, i: int, mode: str = ""):
        label = f"[{self.name}] ── Iteration {i+1}"
        if mode:
            label += f" ({mode})"
        self._vprint(f"\n{'─' * 60}")
        self._vprint(label)
        self._vprint(f"{'─' * 60}")

    def _print_llm_message(self, content: str):
        if content and content.strip():
            self._vprint("\n💬 Assistant:")
            self._vprint(content.strip())

    def _print_tool_call(self, tool_name: str, tool_args: dict):
        self._vprint(f"\n🔧 Tool Call  → {tool_name}")
        if tool_args:
            try:
                self._vprint(f"   Args: {json.dumps(tool_args, indent=6, ensure_ascii=False)}")
            except Exception:
                self._vprint(f"   Args: {tool_args}")

    def _print_tool_result(self, tool_name: str, result: str):
        self._vprint(f"\n📤 Tool Result ← {tool_name}")
        display = result if len(result) <= 1000 else result[:1000] + "\n   ... (truncated)"
        for line in display.splitlines():
            self._vprint(f"   {line}")

    # ──────────────────────────────────────────────────────────────────────
    # E2: Human-in-the-Loop gating
    # ──────────────────────────────────────────────────────────────────────

    def _hitl_approve(self, tool_name: str, tool_args: dict) -> bool:
        """
        Pause execution and ask the human whether to proceed.

        Returns:
            True  → proceed normally
            False → skip this tool call (agent receives a "skipped" message)
        """
        print("\n" + "═" * 60)
        print(f"🛑  HUMAN-IN-THE-LOOP APPROVAL REQUIRED")
        print(f"    Agent : {self.name}")
        print(f"    Tool  : {tool_name}")
        try:
            print(f"    Args  : {json.dumps(tool_args, indent=4, ensure_ascii=False)}")
        except Exception:
            print(f"    Args  : {tool_args}")
        print("═" * 60)
        while True:
            choice = input("    Approve? [y]es / [n]o / [e]dit args : ").strip().lower()
            if choice in ("y", "yes"):
                print("    ✅ Approved.\n")
                return True, tool_args
            elif choice in ("n", "no"):
                print("    ❌ Skipped by human.\n")
                return False, tool_args
            elif choice in ("e", "edit"):
                print("    Paste the new args as JSON (single line) and press Enter:")
                raw = input("    > ").strip()
                try:
                    new_args = json.loads(raw)
                    print("    ✅ Args updated and approved.\n")
                    return True, new_args
                except json.JSONDecodeError:
                    print("    ⚠️  Invalid JSON — please try again.")
            else:
                print("    Please enter 'y', 'n', or 'e'.")

    # ──────────────────────────────────────────────────────────────────────
    # E9: Wrapped LLM call with retry
    # ──────────────────────────────────────────────────────────────────────

    def _call_llm_with_retry(self, **kwargs):
        """Call call_llm with the agent's configured retry settings."""
        return call_with_retry(
            call_llm,
            max_retries=self.max_retries,
            retry_delay=self.retry_delay,
            **kwargs,
        )

    # ──────────────────────────────────────────────────────────────────────
    # E3 / E1: Shared pre-iteration housekeeping
    # ──────────────────────────────────────────────────────────────────────

    def _pre_iteration_hooks(self, iteration_index: int):
        """Apply context trimming and save a checkpoint before each LLM call."""
        # E3 — trim context window if configured
        if self._context_manager:
            self.messages = self._context_manager.maybe_trim(self.messages)

        # E1 — save checkpoint after every iteration
        if self._state_manager:
            self._state_manager.save(
                messages=self.messages,
                extra={"iteration": iteration_index},
            )

    # ──────────────────────────────────────────────────────────────────────
    # Shared tool execution (used by both run and _run_stream)
    # ──────────────────────────────────────────────────────────────────────

    def _execute_tool(self, tool_call: dict) -> str:
        """
        Execute a single tool call dict, applying HITL gate if configured.

        Returns the string result to append as a tool message.
        """
        tool_name = tool_call["function"]["name"].strip()
        tool_args_str = tool_call["function"]["arguments"]
        try:
            tool_args = json.loads(tool_args_str)
        except json.JSONDecodeError:
            tool_args = {}

        self._print_tool_call(tool_name, tool_args)

        if tool_name not in self.tools:
            logger.warning(f"[{self.name}] Tool '{tool_name}' not found.")
            err_msg = f"Error: Tool '{tool_name}' not found."
            self._print_tool_result(tool_name, err_msg)
            return tool_name, tool_args, err_msg

        # ── E2: HITL Gate ──────────────────────────────────────────────
        if self.hitl_mode and tool_name in self.hitl_tools:
            approved, tool_args = self._hitl_approve(tool_name, tool_args)
            if not approved:
                skip_msg = f"Tool '{tool_name}' was skipped by the human operator."
                logger.info(f"[{self.name}] HITL: {skip_msg}")
                self._print_tool_result(tool_name, skip_msg)
                return tool_name, tool_args, skip_msg

        logger.info(f"[{self.name}] Calling {tool_name}")
        try:
            tool_output = self.tools[tool_name](**tool_args)
            result_str = str(tool_output)
            self._print_tool_result(tool_name, result_str)
            return tool_name, tool_args, result_str
        except Exception as e:
            logger.error(f"[{self.name}] Error executing tool '{tool_name}': {e}")
            err_msg = f"Error executing tool '{tool_name}': {e}"
            self._print_tool_result(tool_name, err_msg)
            return tool_name, tool_args, err_msg

    # ──────────────────────────────────────────────────────────────────────
    # Agent network
    # ──────────────────────────────────────────────────────────────────────

    def register_collaborator(self, agent_instance, max_iterations: int = 10):
        """Allows agents to talk to each other."""
        self.agents_in_network[agent_instance.name] = agent_instance

        def communicate_with_agent(message: str) -> str:
            return agent_instance.run(message, max_iterations=max_iterations, stream=False)

        tool_name = f"ask_agent_{agent_instance.name}"
        self.tools[tool_name] = communicate_with_agent
        self.tool_defs.append({
            "type": "function",
            "function": {
                "name": tool_name,
                "description": f"Ask the {agent_instance.name} agent to perform a task.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "message": {"type": "string", "description": "The task or question for the agent."}
                    },
                    "required": ["message"]
                }
            }
        })

    # ──────────────────────────────────────────────────────────────────────
    # Streaming run
    # ──────────────────────────────────────────────────────────────────────

    def _run_stream(self, user_prompt: str, max_iterations: int = 15):
        self.messages.append({"role": "user", "content": user_prompt})

        for i in range(max_iterations):
            logger.info(f"[{self.name}] Iteration {i+1} (Streaming)")
            self._print_iteration(i, mode="Streaming")

            # ── E3 / E1 hooks ──────────────────────────────────────────
            self._pre_iteration_hooks(i)

            try:
                response = self._call_llm_with_retry(
                    messages=self.messages,
                    tools=self.tool_defs if self.tool_defs else None,
                    model=self.model,
                    provider=self.provider,
                    stream=True,
                )

                text_content = ""
                tool_calls_dict = {}
                role = "assistant"

                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str.strip() == "[DONE]":
                                break
                            try:
                                data = json.loads(data_str)
                                if "choices" not in data or not data["choices"]:
                                    continue
                                delta = data["choices"][0].get("delta", {})

                                if "role" in delta:
                                    role = delta["role"]

                                if "content" in delta and delta["content"] is not None:
                                    chunk = delta["content"]
                                    text_content += chunk
                                    yield chunk

                                if "tool_calls" in delta:
                                    for tc in delta["tool_calls"]:
                                        idx = tc["index"]
                                        if idx not in tool_calls_dict:
                                            tool_calls_dict[idx] = {
                                                "id": tc.get("id", ""),
                                                "type": "function",
                                                "function": {"name": "", "arguments": ""}
                                            }
                                        if "id" in tc and tc["id"]:
                                            tool_calls_dict[idx]["id"] = tc["id"]
                                        if "function" in tc:
                                            fn = tc["function"]
                                            if "name" in fn and fn["name"]:
                                                tool_calls_dict[idx]["function"]["name"] += fn["name"]
                                            if "arguments" in fn and fn["arguments"]:
                                                tool_calls_dict[idx]["function"]["arguments"] += fn["arguments"]

                            except json.JSONDecodeError:
                                pass

                assistant_msg = {"role": role}
                if text_content:
                    assistant_msg["content"] = text_content

                tool_calls_list = [tool_calls_dict[k] for k in sorted(tool_calls_dict.keys())]
                if tool_calls_list:
                    assistant_msg["tool_calls"] = tool_calls_list
                else:
                    if "content" not in assistant_msg:
                        assistant_msg["content"] = ""

                self.messages.append(assistant_msg)

                if text_content and self.verbose:
                    self._vprint("\n💬 Assistant: (streamed above)")

                if not tool_calls_list:
                    return

                for tool_call in tool_calls_list:
                    t_name, _, result_str = self._execute_tool(tool_call)
                    self.messages.append({
                        "role": "tool",
                        "name": t_name,
                        "content": result_str,
                        "tool_call_id": tool_call["id"],
                    })

            except RetryError as e:
                logger.error(f"[{self.name}] LLM call failed after retries: {e}")
                yield f"\nLLM error after retries: {e}"
                return
            except Exception as e:
                logger.error(f"API error: {e}")
                yield f"\nAPI error: {e}"
                return

    # ──────────────────────────────────────────────────────────────────────
    # Standard (non-streaming) run
    # ──────────────────────────────────────────────────────────────────────

    def run(self, user_prompt: str, max_iterations: int = 15, stream: bool = False, output_schema: dict = None):
        """
        Execute the agent on a user prompt.

        Args:
            user_prompt:    The task or question for the agent.
            max_iterations: Maximum agentic loop iterations before giving up.
            stream:         If True, returns a generator that yields text chunks.
            output_schema:  JSON schema dict. If provided, instructs the LLM
                            to return JSON matching this schema and parses it.

        Returns:
            str  — the final LLM response text (non-streaming).
            generator — yields text chunks as they arrive (streaming).
        """
        if stream:
            return self._run_stream(user_prompt, max_iterations)

        prompt = user_prompt
        if output_schema:
            schema_str = json.dumps(output_schema, indent=2)
            prompt = (f"{user_prompt}\n\nIMPORTANT: You must return your final response "
                      f"as a valid JSON object matching this schema:\n```json\n{schema_str}\n```")

        self.messages.append({"role": "user", "content": prompt})
        final_content = "Agent could not complete task within limits."

        for i in range(max_iterations):
            logger.info(f"[{self.name}] Iteration {i+1}")
            self._print_iteration(i)

            # ── E3 / E1 hooks ──────────────────────────────────────────
            self._pre_iteration_hooks(i)

            try:
                response = self._call_llm_with_retry(
                    messages=self.messages,
                    tools=self.tool_defs if self.tool_defs else None,
                    model=self.model,
                    provider=self.provider,
                    stream=False,
                )

                message = response['choices'][0]['message']
                self.messages.append(message)
                self._print_llm_message(message.get("content", ""))

                if not message.get("tool_calls"):
                    final_content = message.get("content", "")
                    break

                for tool_call in message["tool_calls"]:
                    t_name, _, result_str = self._execute_tool(tool_call)
                    self.messages.append({
                        "role": "tool",
                        "name": t_name,
                        "content": result_str,
                        "tool_call_id": tool_call["id"],
                    })

            except RetryError as e:
                logger.error(f"[{self.name}] LLM call failed after retries: {e}")
                final_content = f"LLM error after retries: {e}"
                break
            except Exception as e:
                logger.error(f"API error: {e}")
                final_content = f"API error: {e}"
                break

        # ── E7: Structured Output Parsing ──
        if output_schema and final_content and not final_content.startswith(("Agent could", "API error", "LLM error")):
            try:
                import re
                cleaned = re.sub(r"^```json\s*", "", final_content.strip(), flags=re.IGNORECASE)
                cleaned = re.sub(r"\s*```$", "", cleaned)
                data = json.loads(cleaned)
                
                # Strict jsonschema check if library is available
                try:
                    import jsonschema
                    jsonschema.validate(instance=data, schema=output_schema)
                except ImportError:
                    logger.debug("[Structured Output] jsonschema not installed, skipping strict validation.")
                
                return data
            except Exception as e:
                logger.error(f"[Structured Output] Failed to parse/validate JSON: {e}")
                # Fall back to returning string if parsing fails
                return final_content

        return final_content
