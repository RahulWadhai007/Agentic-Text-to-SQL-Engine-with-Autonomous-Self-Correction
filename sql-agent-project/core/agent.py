# core/agent.py
"""
Public façade for the AI agent — the ONLY entry point external code should call.
Isolates callers from graph internals, node wiring, and prompt details.
"""

from langchain_core.runnables import RunnableConfig

from services.database import get_database_schema
from core.graph import sql_agent


def run_agent(user_question: str, thread_id: str, role: str) -> dict:
    """
    Runs the self-correcting SQL agent for a given question.

    Args:
        user_question: The natural-language question from the user.
        thread_id:     Unique session/thread ID for conversation memory isolation.
        role:          Business role (e.g. 'admin', 'employee') for RLS enforcement.

    Returns:
        The final AgentState dict after the graph completes.
    """
    schema = get_database_schema()

    initial_state = {
        "question": user_question,
        "schema": schema,
        "retry_count": 0,
        "error_message": "",
        "sql_query": "",
        "final_result": None,
        "role": role,
    }

    config: RunnableConfig = {"configurable": {"thread_id": thread_id}}

    final_state = sql_agent.invoke(initial_state, config=config)
    return final_state
