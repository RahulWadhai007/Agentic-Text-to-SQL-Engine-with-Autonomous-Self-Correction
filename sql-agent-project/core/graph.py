# core/graph.py
"""
Assembles the LangGraph StateGraph, wires nodes and conditional edges,
and compiles it with a MemorySaver checkpointer for multi-user state isolation.
"""

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from models.state import AgentState
from core.nodes import generate_sql, execute_and_verify, should_continue


def build_agent_graph():
    """Constructs and compiles the SQL agent graph. Returns the compiled runnable."""
    workflow = StateGraph(AgentState)

    # Register nodes
    workflow.add_node("generate_sql", generate_sql)
    workflow.add_node("execute_and_verify", execute_and_verify)

    # Wire the flow
    workflow.set_entry_point("generate_sql")
    workflow.add_edge("generate_sql", "execute_and_verify")
    workflow.add_conditional_edges(
        "execute_and_verify",
        should_continue,
        {
            "end": END,
            "retry": "generate_sql",
        },
    )

    # Compile with memory for multi-user thread isolation
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)


# Pre-built singleton — ready to invoke
sql_agent = build_agent_graph()
