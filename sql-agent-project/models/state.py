# models/state.py
"""
Defines AgentState — the single contract that every LangGraph node reads from and writes to.
"""

from typing import TypedDict, Any


class AgentState(TypedDict):
    """The memory of our agent. This dictionary passes between graph nodes."""
    question: str
    schema: str
    sql_query: str
    error_message: str
    retry_count: int
    final_result: Any
    role: str
