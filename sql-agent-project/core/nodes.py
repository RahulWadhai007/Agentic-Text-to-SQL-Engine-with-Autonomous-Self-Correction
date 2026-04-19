# core/nodes.py
"""
LangGraph node functions and routing predicates.
Each function reads from AgentState and returns a partial state update dict.
"""

from langchain_core.prompts import ChatPromptTemplate

from models.state import AgentState
from services.llm import llm
from services.database import execute_sql
from config import settings
from core.prompts import (
    SQL_GENERATION_SYSTEM_PROMPT,
    SQL_CORRECTION_SYSTEM_PROMPT,
    ROLE_CONTEXT_TEMPLATE,
)
from core.parser import clean_sql


def generate_sql(state: AgentState) -> dict:
    """Drafts or re-drafts the SQL query based on current state."""
    question = state["question"]
    schema = state["schema"]
    error = state.get("error_message", "")
    role_context = ROLE_CONTEXT_TEMPLATE.format(role=state.get("role", "Unknown"))

    # Choose the appropriate prompt template
    if error:
        system_prompt = SQL_CORRECTION_SYSTEM_PROMPT.format(
            role_context=role_context, error=error, schema=schema
        )
    else:
        system_prompt = SQL_GENERATION_SYSTEM_PROMPT.format(
            role_context=role_context, schema=schema
        )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "{question}"),
    ])

    chain = prompt | llm
    response = chain.invoke({"question": question})

    # Clean the output before passing to the next node
    raw_sql = str(response.content) if response.content else ""
    cleaned_sql = clean_sql(raw_sql)

    print(f"\n[Agent] Generated SQL:\n{cleaned_sql}\n")
    return {"sql_query": cleaned_sql}


def execute_and_verify(state: AgentState) -> dict:
    """Runs the SQL and routes to end (success) or triggers retry (failure)."""
    sql = state["sql_query"]
    retries = state.get("retry_count", 0)
    user_role = state.get("role", "admin")

    print(f"[Agent] Executing query as {user_role.upper()}...")
    result = execute_sql(sql, role=user_role)

    if result["status"] == "success":
        print("[Agent] Success! Data retrieved.")
        return {"final_result": result["data"], "error_message": ""}
    else:
        print(f"[Agent] Execution Failed. Error: {result['message']}")
        return {"error_message": result["message"], "retry_count": retries + 1}


def should_continue(state: AgentState) -> str:
    """Conditional routing logic — decides whether to retry or stop."""
    # If there is no error, we are done
    if not state.get("error_message"):
        return "end"
    # If we hit max retries, stop to save tokens / prevent infinite loops
    if state.get("retry_count", 0) >= settings.max_retries:
        print("[Agent] Max retries reached. Halting.")
        return "end"
    # Otherwise, loop back and try to fix it
    return "retry"
