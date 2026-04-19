# models/api_models.py
"""
Pydantic schemas for the FastAPI request/response contract.
Extracted from the old app/main.py so they can be reused and tested independently.
"""

from typing import Any, Optional, List
from pydantic import BaseModel


class QueryRequest(BaseModel):
    """Inbound payload for the /ask endpoint."""
    question: str
    thread_id: Optional[str] = None  # Allows the frontend to send a user or session ID
    role: str = "admin"


class QueryResponse(BaseModel):
    """Outbound payload returned by the /ask endpoint."""
    status: str
    original_question: str
    sql_query: Optional[str] = None
    data: Optional[List[Any]] = None
    attempts: int
    error_message: Optional[str] = None
