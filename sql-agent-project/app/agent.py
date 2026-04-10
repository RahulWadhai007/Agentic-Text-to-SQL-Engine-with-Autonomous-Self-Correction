# app/agent.py
import os
import re
from typing import TypedDict, Annotated, List, Any
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END
from pydantic import SecretStr
from app.database import get_database_schema, execute_sql

load_dotenv()

# ==========================================
# 1. DEFINE THE STATE
# ==========================================
class AgentState(TypedDict):
    """The memory of our agent. This passes between nodes."""
    question: str
    schema: str
    sql_query: str
    error_message: str
    retry_count: int
    final_result: Any
    role: str

# ==========================================
# 2. LLM CONFIGURATION (LM STUDIO)
# ==========================================
llm = ChatOpenAI(
    base_url=os.getenv("OPENAI_API_BASE"),
    api_key=SecretStr(os.getenv("OPENAI_API_KEY") or ""),
    model=os.getenv("MODEL_NAME") or "gpt-3.5-turbo",
    temperature=0 # Absolute 0 temperature. We want logic, not creativity.
)

# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================
def clean_sql(raw_text: str) -> str:
    """Strips markdown and conversational filler from local LLM outputs."""
    # Extract everything between ```sql and ``` if it exists
    match = re.search(r"```sql(.*?)```", raw_text, re.DOTALL | re.IGNORECASE)
    if match:
        query = match.group(1)
    else:
        query = raw_text
    
    # Remove any trailing semicolons and whitespace
    query = query.strip().rstrip(';')
    # Add a single semicolon to the end
    return query + ";"

# ==========================================
# 4. NODE FUNCTIONS
# ==========================================
def generate_sql(state: AgentState) -> dict:
    """Drafts or re-drafts the SQL query based on state."""
    question = state["question"]
    schema = state["schema"]
    error = state.get("error_message", "")
    
    # If there is an error, we are in self-correction mode.
    role_context = f"\nYou are generating queries for a user with the security role: {state.get('role', 'Unknown')}."
    if error:
        system_prompt = f"""You are an elite PostgreSQL engineer.{role_context}
Your previous query failed with this exact error: {error}
Fix the SQL query to answer the user's question.
Return ONLY valid SQL code. No markdown, no explanations.
Database Schema:
{schema}"""
    else:
        system_prompt = f"""You are an elite PostgreSQL engineer.{role_context}
Write a SQL query to answer the user's question.
Return ONLY valid SQL code. No markdown, no explanations.
Database Schema:
{schema}"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "{question}")
    ])
    
    chain = prompt | llm
    response = chain.invoke({"question": question})
    
    # Clean the output before passing to the next node
    raw_sql = str(response.content) if response.content else ""
    cleaned_sql = clean_sql(raw_sql)
    
    print(f"\n[Agent] Generated SQL:\n{cleaned_sql}\n")
    return {"sql_query": cleaned_sql}

def execute_and_verify(state: AgentState) -> dict:
    """Runs the SQL. Routes to end if successful, or triggers retry if failed."""
    sql = state["sql_query"]
    retries = state.get("retry_count", 0)
    user_role = state.get("role", "admin") # Get the role
    
    print(f"[Agent] Executing query as {user_role.upper()}...")
    result = execute_sql(sql, role=user_role) # Pass the role to the database
    
    if result["status"] == "success":
        print("[Agent] Success! Data retrieved.")
        return {"final_result": result["data"], "error_message": ""}
    else:
        print(f"[Agent] Execution Failed. Error: {result['message']}")
        return {"error_message": result["message"], "retry_count": retries + 1}

def should_continue(state: AgentState) -> str:
    """Conditional routing logic."""
    # If there is no error, we are done.
    if not state.get("error_message"):
        return "end"
    # If we hit 3 retries, stop to save tokens/prevent infinite loops.
    if state.get("retry_count", 0) >= 3:
        print("[Agent] Max retries reached. Halting.")
        return "end"
    # Otherwise, loop back and try to fix it.
    return "retry"

# ==========================================
# app/agent.py
# Add this import at the top of your file:
from langgraph.checkpoint.memory import MemorySaver

# ... (keep all your existing state, nodes, and LLM config exactly the same) ...

# ==========================================
# 5. BUILD THE GRAPH (UPDATED WITH CHECKPOINTER)
# ==========================================
workflow = StateGraph(AgentState)

workflow.add_node("generate_sql", generate_sql)
workflow.add_node("execute_and_verify", execute_and_verify)

workflow.set_entry_point("generate_sql")
workflow.add_edge("generate_sql", "execute_and_verify")

workflow.add_conditional_edges(
    "execute_and_verify",
    should_continue,
    {
        "end": END,
        "retry": "generate_sql"
    }
)

# THE UPGRADE: Initialize memory and attach it to the compiler
memory = MemorySaver()
sql_agent = workflow.compile(checkpointer=memory)

# ==========================================
# 6. RUNNER FUNCTION (UPDATED FOR MULTI-USER)
# ==========================================
def run_agent(user_question: str, thread_id: str, role: str):
    """
    Now requires a thread_id. This ensures User A's SQL errors 
    do not leak into User B's conversation.
    """
    schema = get_database_schema()
    
    # We only pass the question. LangGraph will automatically fetch 
    # the rest of the state from memory if this thread_id exists.
    initial_state = {
        "question": user_question,
        "schema": schema,
        "retry_count": 0,
        "error_message": "",
        "sql_query": "",
        "final_result": None,
        "role": role # Pass the role into the initial state
    }
    
    # THE UPGRADE: Pass the thread_id into the execution config
    config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
    
    final_state = sql_agent.invoke(initial_state, config=config)
    return final_state