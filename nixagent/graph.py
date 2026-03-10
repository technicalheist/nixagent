"""
nixagent/graph.py
─────────────────
A lightweight LangGraph-inspired routing system for building
stateful, multi-agent workflows.
"""
from typing import Dict, Any, Callable, Union, Optional
from .agent import Agent
from .logger import logger

END = "__END__"

class AgentGraph:
    """
    State machine for routing context between multiple Agents or functions.
    
    Nodes can be:
      1. A custom Callable: `fn(state_dict) -> dict` (returns state updates)
      2. A Nixagent `Agent`: Automatically runs `agent.run(state['task'])`
         and stores the result back into `state[f"{node_name}_result"]`.
    
    Edges can be:
      1. Unconditional: `from_node -> to_node`
      2. Conditional: `from_node -> condition_fn(state) -> next_node_name`
    """
    def __init__(self):
        self.nodes: Dict[str, Union[Agent, Callable]] = {}
        self.edges: Dict[str, Callable[[Dict[str, Any]], str]] = {}
        self.entry_point: Optional[str] = None

    def add_node(self, name: str, node: Union[Agent, Callable]) -> None:
        self.nodes[name] = node

    def add_edge(self, from_node: str, to_node: str) -> None:
        """Add an unconditional edge."""
        self.edges[from_node] = lambda _: to_node

    def add_conditional_edges(
        self, 
        from_node: str, 
        condition_fn: Callable[[Dict[str, Any]], str]
    ) -> None:
        """
        Add a dynamic edge. 
        `condition_fn` must take the current State dict and return the name 
        of the next node (or END).
        """
        self.edges[from_node] = condition_fn

    def set_entry_point(self, name: str) -> None:
        self.entry_point = name

    def run(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Traverse the graph start to finish.
        
        Args:
            initial_state: The starting global state (e.g. {"task": "do math"}).
            
        Returns:
            The final state dict when the END node is reached.
        """
        if not self.entry_point:
            raise ValueError("Entry point not set. Call set_entry_point() first.")
        
        current_node = self.entry_point
        state = dict(initial_state)

        logger.info(f"[Graph] Starting execution at '{current_node}'")

        while current_node != END:
            if current_node not in self.nodes:
                raise ValueError(f"Node '{current_node}' not found in graph.")

            node = self.nodes[current_node]
            logger.info(f"[Graph] Executing node '{current_node}'")

            # ── Execute the node ──
            if isinstance(node, Agent):
                # Magic handling for bare Nixagents
                task = state.get("task", str(state))
                result = node.run(task)
                state[f"{current_node}_result"] = result
            else:
                # Custom callable node
                state_updates = node(state)
                if state_updates and isinstance(state_updates, dict):
                    state.update(state_updates)

            # ── Determine next node ──
            if current_node not in self.edges:
                logger.info(f"[Graph] No outbound edge for '{current_node}', defaulting to END.")
                current_node = END
            else:
                edge_fn = self.edges[current_node]
                next_node = edge_fn(state)
                logger.info(f"[Graph] Transition: {current_node} ──> {next_node}")
                current_node = next_node

        logger.info("[Graph] Execution reached END.")
        return state
