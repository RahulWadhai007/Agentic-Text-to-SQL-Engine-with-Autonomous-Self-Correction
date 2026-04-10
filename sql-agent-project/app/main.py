# app/main.py
import uuid
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Optional, List
from app.agent import run_agent

# Initialize the FastAPI application
app = FastAPI(
    title="Agentic Text-to-SQL Engine",
    description="An autonomous AI agent that translates natural language to SQL with self-correction and threaded state.",
    version="1.1.0"
)

# ==========================================
# DATA MODELS (Pydantic)
# ==========================================
class QueryRequest(BaseModel):
    question: str
    thread_id: Optional[str] = None  # Allows the frontend to send a user or session ID
    role: str = "admin" # <-- ADD THIS

class QueryResponse(BaseModel):
    status: str
    original_question: str
    sql_query: Optional[str] = None
    data: Optional[List[Any]] = None
    attempts: int
    error_message: Optional[str] = None

# ==========================================
# API ENDPOINTS
# ==========================================
@app.get("/")
def read_root():
    return {"message": "Text-to-SQL Agent API is live. Send POST requests to /ask"}

@app.post("/ask", response_model=QueryResponse)
def ask_database(request: QueryRequest):
    """
    Takes a natural language question, passes it through the LangGraph self-correction loop,
    maintains conversational memory via thread_id, and returns the final SQL query and extracted data.
    """
    # If no thread_id is provided by the frontend, generate a temporary one for this session
    session_id = request.thread_id or str(uuid.uuid4())
    print(f"\n[API] Received request for Thread ID: {session_id} | Question: '{request.question}'")
    
    try:
        # Trigger the LangGraph agent with the specific thread_id and role
        final_state = run_agent(request.question, session_id, request.role)
        
        # Check if the agent hit the maximum retry limit and failed
        if final_state.get("error_message"):
            return QueryResponse(
                status="failed",
                original_question=request.question,
                attempts=final_state.get("retry_count", 0) + 1,
                error_message=final_state.get("error_message")
            )
            
        # If successful, return the data
        return QueryResponse(
            status="success",
            original_question=request.question,
            sql_query=final_state.get("sql_query"),
            data=final_state.get("final_result"),
            attempts=final_state.get("retry_count", 0) + 1
        )
        
    except Exception as e:
        # Catch any catastrophic server errors outside the agent loop
        print(f"[API] Critical Server Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))