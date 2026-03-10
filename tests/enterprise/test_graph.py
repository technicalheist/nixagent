import pytest
from nixagent.graph import AgentGraph, END

def test_agent_graph_basic_routing():
    graph = AgentGraph()
    
    # Simple nodes
    def step_add(state):
        return {"value": state.get("value", 0) + 1}
        
    def step_multiply(state):
        return {"value": state.get("value", 0) * 2}
        
    graph.add_node("add", step_add)
    graph.add_node("multiply", step_multiply)
    
    # Conditional routing logic
    def check_limit(state):
        if state["value"] >= 10:
            return END
        else:
            return "multiply"
            
    # Edges
    graph.add_edge("add", "multiply")
    graph.add_conditional_edges("multiply", check_limit)
    
    # If limit is not reached, back to add! Wait, the logic above:
    # add -> multiply. multiply -> (END if >=10 else multiply).
    # That would loop multiply forever. Let's fix the test logic.
    def loop_logic(state):
        return END if state["value"] >= 10 else "add"
    
    # Redefine conditionals
    graph.edges = {} # reset
    graph.add_edge("add", "multiply")
    graph.add_conditional_edges("multiply", loop_logic)
    
    # Start: value=1
    # add(1) -> 2
    # multiply(2) -> 4
    # loop_logic(4) -> add
    # add(4) -> 5
    # multiply(5) -> 10
    # loop_logic(10) -> END
    
    graph.set_entry_point("add")
    
    final_state = graph.run({"value": 1})
    assert final_state["value"] == 10

def test_missing_entry_point():
    graph = AgentGraph()
    with pytest.raises(ValueError):
        graph.run({"test": 1})

def test_invalid_node_transition():
    graph = AgentGraph()
    graph.add_node("step1", lambda s: {"x": 1})
    graph.add_edge("step1", "missing_node")
    graph.set_entry_point("step1")
    
    with pytest.raises(ValueError, match="not found in graph"):
        graph.run({})
