"""
nixagent/integrations/langchain_bridge.py
──────────────────────────────────────────
Bridges LangChain BaseTool instances into native Nixagent tool format.

Works WITHOUT requiring LangChain to be installed project-wide.
Import only happens when `from_langchain_tool()` is actually called.

Supports:
  • LangChain community / core tools (BaseTool subclasses)
  • Pydantic v1 and v2 schemas (args_schema.schema() / model_json_schema())
  • Tools with no args_schema (falls back to a free-form string input)
"""
from __future__ import annotations

from typing import Any, Callable, Dict, Optional, Tuple


# ──────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ──────────────────────────────────────────────────────────────────────────────

def _pydantic_schema(model_class) -> Dict:
    """
    Extract a JSON Schema dict from a Pydantic model class.
    Handles both Pydantic v1 (.schema()) and v2 (.model_json_schema()).
    """
    # Pydantic v2
    if hasattr(model_class, "model_json_schema"):
        schema = model_class.model_json_schema()
    # Pydantic v1
    elif hasattr(model_class, "schema"):
        schema = model_class.schema()
    else:
        schema = {}

    # Strip $defs / $ref resolution noise — LLMs don't need it
    schema.pop("title", None)
    schema.pop("$defs", None)
    schema.pop("definitions", None)
    return schema


def _make_nixagent_tool_def(name: str, description: str, parameters: Dict) -> Dict:
    """Return an OpenAI-format function-call schema dict."""
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description or f"Run the {name} tool.",
            "parameters": parameters,
        },
    }


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────

def from_langchain_tool(
    lc_tool: Any,
    tool_name_override: Optional[str] = None,
) -> Tuple[str, Callable, Dict]:
    """
    Convert a LangChain ``BaseTool`` instance into a Nixagent-compatible triple.

    Args:
        lc_tool:              Any LangChain BaseTool instance.
        tool_name_override:   Optional custom name for the tool. Defaults to
                              the tool's own ``.name`` attribute.

    Returns:
        A tuple of ``(tool_name, callable, tool_def_dict)`` ready to be
        passed into ``Agent(custom_tools={...}, custom_tool_defs=[...])``.

    Raises:
        TypeError:  If ``lc_tool`` does not look like a LangChain BaseTool
                    (i.e. has no ``.run()`` or ``.invoke()`` method).

    Example::

        from langchain_community.tools import WikipediaQueryRun
        from langchain_community.utilities import WikipediaAPIWrapper
        from nixagent.integrations.langchain_bridge import from_langchain_tool
        from nixagent import Agent

        wiki_tool = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
        name, fn, schema = from_langchain_tool(wiki_tool)

        agent = Agent(
            name="ResearchAgent",
            system_prompt="You are a research assistant.",
            custom_tools={name: fn},
            custom_tool_defs=[schema],
        )
    """
    # ── Validate the object looks like a LangChain tool ───────────────────
    has_run = hasattr(lc_tool, "run") and callable(lc_tool.run)
    has_invoke = hasattr(lc_tool, "invoke") and callable(lc_tool.invoke)
    if not (has_run or has_invoke):
        raise TypeError(
            f"Expected a LangChain BaseTool (with .run() or .invoke()), "
            f"got {type(lc_tool).__name__}"
        )

    # ── Name ──────────────────────────────────────────────────────────────
    raw_name = tool_name_override or getattr(lc_tool, "name", type(lc_tool).__name__)
    # Normalise to valid function name: spaces/hyphens → underscores
    tool_name = raw_name.replace(" ", "_").replace("-", "_").lower()

    # ── Description ───────────────────────────────────────────────────────
    description = getattr(lc_tool, "description", "") or f"Run the {tool_name} tool."

    # ── Parameter schema ──────────────────────────────────────────────────
    args_schema = getattr(lc_tool, "args_schema", None)
    if args_schema is not None and isinstance(args_schema, type):
        # args_schema is a Pydantic model class
        parameters = _pydantic_schema(args_schema)
        # Ensure it has the minimum required fields
        if "type" not in parameters:
            parameters["type"] = "object"
        if "properties" not in parameters:
            parameters["properties"] = {}
    else:
        # Fallback: a single 'query' string input (works for most simple tools)
        parameters = {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The input query for the tool.",
                }
            },
            "required": ["query"],
        }

    # ── Callable wrapper ───────────────────────────────────────────────────
    # Prefer .invoke() (newer LangChain API), fall back to .run()
    if has_invoke:
        def _callable(**kwargs) -> str:
            result = lc_tool.invoke(kwargs)
            return str(result)
    else:
        def _callable(**kwargs) -> str:
            # Old-style .run() usually takes a single string
            query = kwargs.get("query", "") or " ".join(str(v) for v in kwargs.values())
            result = lc_tool.run(query)
            return str(result)

    # ── Tool def ──────────────────────────────────────────────────────────
    tool_def = _make_nixagent_tool_def(tool_name, description, parameters)

    return tool_name, _callable, tool_def


def from_langchain_tools(lc_tools: list) -> Tuple[Dict, list]:
    """
    Batch-convert a list of LangChain tools.

    Returns:
        ``(custom_tools_dict, custom_tool_defs_list)`` — pass both directly
        into ``Agent(custom_tools=..., custom_tool_defs=...)``.

    Example::

        tools_dict, defs = from_langchain_tools([wiki_tool, search_tool])
        agent = Agent(
            name="ResearchAgent",
            system_prompt="...",
            custom_tools=tools_dict,
            custom_tool_defs=defs,
        )
    """
    tools_dict: Dict[str, Callable] = {}
    defs_list: list = []
    for lc_tool in lc_tools:
        name, fn, schema = from_langchain_tool(lc_tool)
        tools_dict[name] = fn
        defs_list.append(schema)
    return tools_dict, defs_list
