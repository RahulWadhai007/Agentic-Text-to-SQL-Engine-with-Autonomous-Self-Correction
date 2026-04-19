# Agentic Text-to-SQL Engine with Autonomous Self-Correction

## Complete Project Explanation (Presentation Guide)

---

## Table of Contents

1. [What Is This Project?](#1-what-is-this-project)
2. [Key Technologies Used](#2-key-technologies-used)
3. [High-Level Architecture](#3-high-level-architecture)
4. [Complete Folder Structure](#4-complete-folder-structure)
5. [Layer-by-Layer Explanation](#5-layer-by-layer-explanation)
   - [Layer 1 — Configuration](#layer-1--configuration-config)
   - [Layer 2 — Data Models](#layer-2--data-models-models)
   - [Layer 3 — Services (External I/O)](#layer-3--services-external-io-services)
   - [Layer 4 — Core AI Logic](#layer-4--core-ai-logic-core)
   - [Layer 5 — API Layer](#layer-5--api-layer-api)
   - [Layer 6 — Frontend UI](#layer-6--frontend-ui-ui)
   - [Layer 7 — Database Setup](#layer-7--database-setup-db--docker)
   - [Layer 8 — Tests](#layer-8--tests-tests)
6. [Full Data Flow (End to End)](#6-full-data-flow-end-to-end)
7. [The Self-Correction Loop Explained](#7-the-self-correction-loop-explained)
8. [Row-Level Security (RLS) Explained](#8-row-level-security-rls-explained)
9. [How to Run the Project](#9-how-to-run-the-project)


---

## 1. What Is This Project?

This is an **AI-powered database assistant** that lets users ask questions in **plain English** (natural language) and automatically:

1. **Translates** the question into a SQL query using a Large Language Model (LLM).
2. **Executes** that SQL query against a real PostgreSQL database.
3. **Self-corrects** — if the generated SQL has errors, the AI reads the error message, understands what went wrong, rewrites the SQL, and tries again (up to 3 retries).
4. **Enforces enterprise-grade security** — uses PostgreSQL's Row-Level Security (RLS) to restrict what data different user roles (Admin vs Employee) can see.

### Real-World Example

| User Types | User Asks | What Happens |
|---|---|---|
| Admin | "Show me all customers" | Returns all 3 customers (global access) |
| Employee | "Show me all customers" | Returns only 1 customer in North America (restricted) |

### Why It's Called "Agentic"

Traditional LLM apps generate one response and stop. This project is **agentic** because the AI operates in a **loop** — it can observe errors, reason about them, and take corrective actions autonomously, like a human developer debugging their own code.

---

## 2. Key Technologies Used

| Technology | Purpose | Why We Chose It |
|---|---|---|
| **Python 3.12** | Core programming language | Industry standard for AI/ML |
| **LangGraph** | AI agent orchestration framework | Enables stateful, graph-based agent loops with built-in memory |
| **LangChain** | LLM abstraction layer | Standardised interface to talk to any LLM (OpenAI, LM Studio, etc.) |
| **LM Studio** | Local LLM server (runs Gemma model) | Free, private, no API costs — runs models locally on your GPU |
| **FastAPI** | Backend REST API framework | Async, auto-docs, Pydantic validation, production-grade |
| **Streamlit** | Frontend chat dashboard | Rapid UI prototyping for data apps |
| **PostgreSQL 15** | Production-grade relational database | Supports Row-Level Security, robust, enterprise-standard |
| **Docker Compose** | Database containerisation | One command to spin up a fully configured database |
| **psycopg2** | Python ↔ PostgreSQL driver | Low-level, fast, production-proven connector |
| **Pydantic** | Data validation & settings management | Type-safe configs and API schemas |
| **LangSmith** | AI observability platform | Traces every LLM call for debugging and monitoring |

---

## 3. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER (Browser)                               │
│                    Streamlit Chat Dashboard                          │
│                        (ui/app.py)                                   │
└───────────────────────────┬─────────────────────────────────────────┘
                            │ HTTP POST /ask
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                                │
│                       (api/main.py)                                  │
│              Receives request, delegates to agent                    │
└───────────────────────────┬─────────────────────────────────────────┘
                            │ Calls run_agent()
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     Core Agent Façade                                │
│                      (core/agent.py)                                 │
│          Loads schema, initialises state, invokes graph              │
└───────────────────────────┬─────────────────────────────────────────┘
                            │ Invokes LangGraph
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  LangGraph State Machine                             │
│                      (core/graph.py)                                 │
│                                                                      │
│   ┌──────────────┐     ┌────────────────────┐                       │
│   │ generate_sql  │────▶│ execute_and_verify │──┐                   │
│   │  (Node 1)     │     │     (Node 2)       │  │                   │
│   └──────▲────────┘     └────────────────────┘  │                   │
│          │                                       │                   │
│          │         ┌──────────────────┐          │                   │
│          └─────────│ should_continue  │◀─────────┘                   │
│           (retry)  │   (Router)       │  (end)──▶ FINISH            │
│                    └──────────────────┘                              │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                ▼                       ▼
┌──────────────────────┐  ┌──────────────────────┐
│   LLM Service        │  │  Database Service     │
│  (services/llm.py)   │  │ (services/database.py)│
│  Talks to LM Studio  │  │ Talks to PostgreSQL   │
└──────────────────────┘  └──────────────────────┘
                                    │
                                    ▼
                          ┌──────────────────┐
                          │   PostgreSQL 15   │
                          │   (Docker)        │
                          │  + RLS Policies   │
                          └──────────────────┘
```

### The 4-Layer Architecture (Separation of Concerns)

| Layer | Package | Responsibility |
|---|---|---|
| **Presentation** | `ui/`, `api/` | User interface and HTTP routing — zero business logic |
| **Core Logic** | `core/` | AI reasoning, graph construction, prompt engineering |
| **Services** | `services/` | External I/O — database queries, LLM calls |
| **Data/Config** | `models/`, `config/` | Data contracts, settings, type definitions |

---

## 4. Complete Folder Structure

```
sql-agent-project/
│
├── .env                          # 🔒 Environment variables (passwords, API keys)
├── .streamlit/
│   └── config.toml               # 🎨 Streamlit dark theme configuration
├── docker-compose.yml            # 🐳 Spins up PostgreSQL in Docker
├── requirements.txt              # 📦 Python dependencies
│
├── config/                       # ⚙️ LAYER 1: Configuration
│   ├── __init__.py               #    Re-exports the singleton settings object
│   └── settings.py               #    Loads .env → creates immutable Settings dataclass
│
├── models/                       # 📐 LAYER 2: Data Models (contracts)
│   ├── __init__.py               #    Re-exports AgentState, QueryRequest, QueryResponse
│   ├── state.py                  #    AgentState — the "memory" dictionary for graph nodes
│   └── api_models.py            #    Pydantic request/response schemas for the REST API
│
├── services/                     # 🔌 LAYER 3: External I/O
│   ├── __init__.py               #    Package marker
│   ├── database.py               #    PostgreSQL connection, schema extraction, SQL execution
│   └── llm.py                    #    Creates the singleton ChatOpenAI LLM client
│
├── core/                         # 🧠 LAYER 4: AI Brain
│   ├── __init__.py               #    Package marker
│   ├── prompts.py                #    All LLM prompt templates (system prompts)
│   ├── parser.py                 #    Cleans raw LLM output → executable SQL
│   ├── nodes.py                  #    LangGraph node functions (generate, execute, route)
│   ├── graph.py                  #    Assembles the StateGraph, wires nodes, compiles
│   └── agent.py                  #    Public façade — the ONLY entry point for external code
│
├── api/                          # 🌐 LAYER 5: REST API
│   ├── __init__.py               #    Package marker
│   └── main.py                   #    FastAPI app, routes (/ask, /), request handling
│
├── ui/                           # 💻 LAYER 6: Frontend
│   ├── __init__.py               #    Package marker
│   └── app.py                    #    Streamlit chat dashboard with role switching
│
├── db/                           # 🗄️ LAYER 7: Database Bootstrap
│   └── init.sql                  #    Creates tables, seeds data, sets up RLS policies
│
└── tests/                        # ✅ LAYER 8: Testing
    └── test_agent.py             #    Smoke-test that invokes the agent from the command line
```

---

## 5. Layer-by-Layer Explanation

---

### LAYER 1 — Configuration (`config/`)

#### Purpose
Centralises ALL environment configuration into a single, immutable object. No other file in the project calls `os.getenv()` directly — they all import `settings` from here.

---

#### File: `.env`

```env
# ── Database (standardised POSTGRES_* naming) ──
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=business_sandbox
POSTGRES_USER=admin
POSTGRES_PASSWORD=securepassword123

# ── LM Studio / OpenAI-compatible LLM ──
OPENAI_API_BASE=http://localhost:1234/v1
OPENAI_API_KEY=lm-studio
MODEL_NAME=gemma

# ── LangSmith Observability ──
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=your_langchain_api_key_here
LANGCHAIN_PROJECT=sql-agent-local-v1
```

**What each variable does:**

| Variable | Purpose |
|---|---|
| `POSTGRES_HOST` | Where PostgreSQL is running (localhost = same machine) |
| `POSTGRES_PORT` | Default PostgreSQL port (5432) |
| `POSTGRES_DB` | Name of the database to connect to |
| `POSTGRES_USER` / `PASSWORD` | Login credentials for PostgreSQL |
| `OPENAI_API_BASE` | URL of the LLM server (LM Studio runs on port 1234) |
| `OPENAI_API_KEY` | API key (for LM Studio, any string works; `lm-studio` is a convention) |
| `MODEL_NAME` | Which model to use (Gemma is a Google open-source LLM) |
| `LANGCHAIN_TRACING_V2` | Enables sending trace logs to LangSmith |
| `LANGCHAIN_API_KEY` | Authentication key for LangSmith dashboard |
| `LANGCHAIN_PROJECT` | Groups all traces under this project name in LangSmith |

**Why `.env`?** — Secrets like passwords and API keys should NEVER be hardcoded in source code. `.env` files are loaded at runtime and excluded from Git via `.gitignore`.

---

#### File: `config/settings.py`

```python
import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Single, authoritative load of environment variables
load_dotenv()

@dataclass(frozen=True)
class Settings:
    """Immutable application configuration — one source of truth."""

    # ── Database ──
    postgres_host: str = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port: str = os.getenv("POSTGRES_PORT", "5432")
    postgres_db: str = os.getenv("POSTGRES_DB", "business_sandbox")
    postgres_user: str = os.getenv("POSTGRES_USER", "admin")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "securepassword123")

    # ── LLM ──
    openai_api_base: str = os.getenv("OPENAI_API_BASE", "http://localhost:1234/v1")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "lm-studio")
    model_name: str = os.getenv("MODEL_NAME", "gpt-3.5-turbo")
    llm_temperature: float = float(os.getenv("LLM_TEMPERATURE", "0"))

    # ── LangSmith ──
    langchain_tracing_v2: str = os.getenv("LANGCHAIN_TRACING_V2", "true")
    langchain_endpoint: str = os.getenv("LANGCHAIN_ENDPOINT", "...")
    langchain_api_key: str = os.getenv("LANGCHAIN_API_KEY", "")
    langchain_project: str = os.getenv("LANGCHAIN_PROJECT", "sql-agent-local-v1")

    # ── Agent Behaviour ──
    max_retries: int = int(os.getenv("AGENT_MAX_RETRIES", "3"))

# Singleton instance
settings = Settings()
```

**Line-by-line breakdown:**

1. **`load_dotenv()`** — Reads the `.env` file and loads all key=value pairs into the process's environment variables. This happens ONCE when the module is first imported.

2. **`@dataclass(frozen=True)`** — Creates a Python dataclass where:
   - `frozen=True` means the object is **immutable** — once created, you cannot accidentally change any setting at runtime. This prevents bugs where code mutates config mid-execution.
   - Each field has a **type annotation** (e.g., `str`, `float`, `int`) for clarity.

3. **`os.getenv("KEY", "default")`** — Reads the environment variable `KEY`. If it doesn't exist (e.g., `.env` is missing), it falls back to the default value. This makes the app resilient.

4. **`settings = Settings()`** — Creates exactly ONE instance at module load time. Every other module does `from config import settings` to get this same object. This is the **Singleton Pattern**.

5. **`max_retries: int = 3`** — Controls how many times the AI agent will retry a failed SQL query before giving up. This prevents infinite loops.

6. **`llm_temperature: float = 0`** — Controls LLM randomness. `0` = deterministic (always same output for same input). Higher values = more creative/random. For SQL generation, we want `0` for consistency.

---

#### File: `config/__init__.py`

```python
from config.settings import settings
__all__ = ["settings"]
```

**Purpose:** This makes `config` a Python package. The `from config import settings` shorthand works because this file **re-exports** `settings` at the package level. Without this, you'd have to write `from config.settings import settings` everywhere.

---

### LAYER 2 — Data Models (`models/`)

#### Purpose
Defines the strict "contracts" (data shapes) that different parts of the system agree on. This prevents bugs — if the API expects a `question` field, the model enforces that it exists.

---

#### File: `models/state.py`

```python
from typing import TypedDict, Any

class AgentState(TypedDict):
    """The memory of our agent. This dictionary passes between graph nodes."""
    question: str        # The user's original natural language question
    schema: str          # The database schema (tables + columns) as a string
    sql_query: str       # The SQL query the LLM generated
    error_message: str   # Error from the last failed execution (empty = no error)
    retry_count: int     # How many times we've retried so far
    final_result: Any    # The query results (list of dicts) or None
    role: str            # The user's security role ("admin" or "employee")
```

**Why this matters:**

This is the **most important file** conceptually. `AgentState` is the **shared memory** that flows between every node in the LangGraph.

Think of it like a clipboard being passed around an office:
- **Node 1 (generate_sql)** reads `question` + `schema` from the clipboard, writes `sql_query` onto it.
- **Node 2 (execute_and_verify)** reads `sql_query` from the clipboard, writes `final_result` or `error_message` + `retry_count` onto it.
- The **router** reads `error_message` and `retry_count` to decide: go back to Node 1 or stop?

`TypedDict` is a Python typing construct that says "this dictionary MUST have these exact keys with these types." It gives us IDE autocompletion and type checking without the overhead of a class.

---

#### File: `models/api_models.py`

```python
from typing import Any, Optional, List
from pydantic import BaseModel

class QueryRequest(BaseModel):
    """Inbound payload for the /ask endpoint."""
    question: str                          # REQUIRED: the user's question
    thread_id: Optional[str] = None        # Optional session ID for memory
    role: str = "admin"                    # Default role is admin

class QueryResponse(BaseModel):
    """Outbound payload returned by the /ask endpoint."""
    status: str                            # "success" or "failed"
    original_question: str                 # Echo back what was asked
    sql_query: Optional[str] = None        # The final SQL (if successful)
    data: Optional[List[Any]] = None       # Query results as list of dicts
    attempts: int                          # How many attempts the agent took
    error_message: Optional[str] = None    # Error details (if failed)
```

**What is Pydantic `BaseModel`?**

Pydantic models provide **automatic validation**. When FastAPI receives a JSON request body, it:
1. Parses the JSON.
2. Checks every field matches the expected type.
3. Returns a `422 Validation Error` if the client sends bad data (e.g., missing `question`).

This means the backend **never crashes** from malformed input — Pydantic rejects it before your code even runs.

**`Optional[str] = None`** means the field can be either a string or absent. If absent, it defaults to `None`.

---

#### File: `models/__init__.py`

```python
from models.state import AgentState
from models.api_models import QueryRequest, QueryResponse
__all__ = ["AgentState", "QueryRequest", "QueryResponse"]
```

**Purpose:** Convenience re-exports so other files can write `from models import AgentState` instead of `from models.state import AgentState`.

---

### LAYER 3 — Services (External I/O) (`services/`)

#### Purpose
All communication with external systems (database, LLM) is isolated here. The core AI logic never directly touches the database or LLM — it calls these service functions instead. This is called **Separation of Concerns**.

---

#### File: `services/llm.py`

```python
from langchain_openai import ChatOpenAI
from pydantic import SecretStr
from config import settings

# Single LLM instance shared across the application
llm = ChatOpenAI(
    base_url=settings.openai_api_base,      # http://localhost:1234/v1 (LM Studio)
    api_key=SecretStr(settings.openai_api_key),  # Wrapped so it's never accidentally logged
    model=settings.model_name,               # "gemma" (the local model)
    temperature=settings.llm_temperature,    # 0 (deterministic)
)
```

**What is happening here?**

1. **`ChatOpenAI`** — This is LangChain's client for any OpenAI-compatible API. LM Studio exposes the same API format as OpenAI (`/v1/chat/completions`), so we can use this same client.

2. **`base_url`** — Points to where the LLM server is running. LM Studio runs locally on `http://localhost:1234/v1`.

3. **`SecretStr`** — A Pydantic type that prevents the API key from being accidentally printed in logs or error messages. If you do `print(api_key)`, it shows `**********` instead of the actual key.

4. **`temperature=0`** — Makes the LLM output deterministic. For SQL generation, we don't want creativity — we want correctness.

5. **Singleton Pattern** — The `llm` object is created once at module load. Every node in the graph imports and reuses this same instance, avoiding the overhead of creating a new connection each time.

---

#### File: `services/database.py`

This is the **largest service file** and handles all database operations. It has 3 functions:

##### Function 1: `get_db_connection()`

```python
def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            host=settings.postgres_host,
            port=settings.postgres_port,
            database=settings.postgres_db,
            user=settings.postgres_user,
            password=settings.postgres_password,
        )
        return conn
    except psycopg2.Error as e:
        print(f"Database connection failed: {e}")
        return None
```

**What it does:** Opens a TCP connection to PostgreSQL using the credentials from settings. If the database is down or credentials are wrong, it catches the error and returns `None` instead of crashing the entire application.

##### Function 2: `get_database_schema()`

```python
def get_database_schema() -> str:
    conn = get_db_connection()
    if not conn:
        return "Error: Could not connect to database."

    cursor = conn.cursor()

    query = """
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position;
    """
    cursor.execute(query)
    rows = cursor.fetchall()

    # Group columns by table
    schema_dict: dict[str, list[str]] = {}
    for table, column, dtype in rows:
        if table not in schema_dict:
            schema_dict[table] = []
        schema_dict[table].append(f"{column} ({dtype})")

    # Format into a dense string
    schema_text = "Database Schema:\n"
    for table, columns in schema_dict.items():
        schema_text += f"Table '{table}': {', '.join(columns)}\n"

    return schema_text
```

**What it does:**

1. Connects to PostgreSQL.
2. Queries the `information_schema.columns` system table — this is a built-in PostgreSQL catalog that describes every table and column in the database.
3. Groups the results by table name.
4. Formats them into a compact string like:
   ```
   Database Schema:
   Table 'customers': customer_id (integer), name (character varying), email (character varying), region (character varying)
   Table 'orders': order_id (integer), customer_id (integer), product_id (integer), order_date (date), quantity (integer), returned (boolean)
   Table 'products': product_id (integer), product_name (character varying), category (character varying), price (numeric)
   ```

**Why?** This string gets injected into the LLM's system prompt so the AI **knows the database structure**. Without this, the LLM would be guessing table/column names.

**Key design decision:** The schema is extracted **dynamically** at runtime. If you add new tables or columns to the database, the agent automatically picks them up. No code changes needed.

##### Function 3: `execute_sql()`

```python
def execute_sql(query: str, role: str = "admin") -> dict:
    conn = get_db_connection()
    if not conn:
        return {"status": "error", "message": "Database connection failed."}

    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Step 1: Switch to restricted role so RLS is enforced
    cursor.execute("SET ROLE ai_agent;")

    # Step 2: Set the business role for this transaction
    cursor.execute(f"SELECT set_config('app.current_role', '{role.lower()}', true);")

    # Step 3: Execute the AI-generated query
    cursor.execute(query)

    if cursor.description:
        results = cursor.fetchall()
        return {"status": "success", "data": results}
    else:
        conn.commit()
        return {"status": "success", "data": "Query executed successfully."}
```

**Step-by-step:**

1. **`cursor_factory=RealDictCursor`** — Normal cursors return rows as tuples `(1, "Alice", ...)`. `RealDictCursor` returns them as dictionaries `{"customer_id": 1, "name": "Alice", ...}`. This makes the data directly JSON-serializable for the API response.

2. **`SET ROLE ai_agent;`** — This is the **security step**. Instead of running the query as the `admin` superuser (who bypasses all security), we switch to the `ai_agent` role which has Row-Level Security (RLS) policies applied. This means the database itself filters which rows are visible.

3. **`set_config('app.current_role', 'admin', true)`** — Sets a session-level variable that the RLS policies read. The `true` parameter means "only for this transaction." The RLS policies check this variable to determine: is this an admin or employee?

4. **`cursor.description`** — This is `None` for INSERT/UPDATE/DELETE statements (which don't return rows) and not-None for SELECT statements. This lets us handle both types of queries correctly.

5. **Error handling** — The entire function is wrapped in try/except. If the LLM generates invalid SQL (e.g., referencing a non-existent column), PostgreSQL throws an error, which we catch and return as `{"status": "error", "message": "..."}`. This error message is then fed back to the LLM for self-correction.

---

### LAYER 4 — Core AI Logic (`core/`)

#### Purpose
This is the **brain** of the application. It contains the AI reasoning logic, prompt engineering, and the LangGraph state machine that orchestrates the self-correction loop.

---

#### File: `core/prompts.py`

```python
# ── SQL Generation — first attempt ──
SQL_GENERATION_SYSTEM_PROMPT = """You are an elite PostgreSQL engineer.{role_context}
Write a SQL query to answer the user's question.
Return ONLY valid SQL code. No markdown, no explanations.
Database Schema:
{schema}"""

# ── SQL Self-Correction — retry after error ──
SQL_CORRECTION_SYSTEM_PROMPT = """You are an elite PostgreSQL engineer.{role_context}
Your previous query failed with this exact error: {error}
Fix the SQL query to answer the user's question.
Return ONLY valid SQL code. No markdown, no explanations.
Database Schema:
{schema}"""

# ── Role context injection fragment ──
ROLE_CONTEXT_TEMPLATE = "\nYou are generating queries for a user with the security role: {role}."
```

**Why separate prompts?**

We have **two** system prompts because the LLM needs different instructions depending on context:

1. **First attempt (`SQL_GENERATION_SYSTEM_PROMPT`):**
   - "Here's the schema. Write SQL to answer this question."
   - Variables filled in: `{role_context}` (what role the user has), `{schema}` (the database structure).

2. **Retry after failure (`SQL_CORRECTION_SYSTEM_PROMPT`):**
   - "Your previous query failed with THIS error. Fix it."
   - Additional variable: `{error}` (the exact PostgreSQL error message).
   - This is the **self-correction** mechanism. By showing the LLM its own mistake, it learns from the error and generates better SQL.

**`ROLE_CONTEXT_TEMPLATE`** — A sentence fragment that tells the LLM what role context to consider. For example: `"You are generating queries for a user with the security role: employee."` This helps the LLM understand the permission context.

**Design: "Return ONLY valid SQL code"** — Local LLMs often add conversational filler like "Here's your query:" or wrap SQL in markdown code blocks. This instruction minimizes that behaviour.

---

#### File: `core/parser.py`

```python
import re

def clean_sql(raw_text: str) -> str:
    """Strips markdown and conversational filler from local LLM outputs."""
    # Extract everything between ```sql and ``` if it exists
    match = re.search(r"```sql(.*?)```", raw_text, re.DOTALL | re.IGNORECASE)
    if match:
        query = match.group(1)
    else:
        query = raw_text

    # Remove any trailing semicolons and whitespace, then add exactly one
    query = query.strip().rstrip(";")
    return query + ";"
```

**What it does:**

Even with "Return ONLY valid SQL" in the prompt, local LLMs sometimes output:

```
Here's the SQL query you need:
```sql
SELECT * FROM customers;
```
```

This function handles that by:

1. **Regex pattern** `r"```sql(.*?)```"` — Looks for text wrapped in SQL markdown fences. The `(.*?)` is a non-greedy capture group that extracts just the SQL inside. `re.DOTALL` makes `.` match newlines too. `re.IGNORECASE` handles `SQL` vs `sql`.

2. **Fallback** — If no markdown fence is found, it assumes the entire output is SQL.

3. **Semicolon normalisation** — Strips any trailing semicolons (there might be 0, 1, or multiple), then adds exactly one. PostgreSQL requires queries to end with `;`.

**Why this file exists:** Without this parser, the agent would try to execute markdown as SQL, causing instant failure on every query with a local LLM.

---

#### File: `core/nodes.py`

This file contains the **3 functions** that make up the LangGraph nodes:

##### Node 1: `generate_sql(state) → dict`

```python
def generate_sql(state: AgentState) -> dict:
    """Drafts or re-drafts the SQL query based on current state."""
    question = state["question"]
    schema = state["schema"]
    error = state.get("error_message", "")
    role_context = ROLE_CONTEXT_TEMPLATE.format(role=state.get("role", "Unknown"))

    # Choose the appropriate prompt template
    if error:
        # RETRY: use the correction prompt that includes the error message
        system_prompt = SQL_CORRECTION_SYSTEM_PROMPT.format(
            role_context=role_context, error=error, schema=schema
        )
    else:
        # FIRST ATTEMPT: use the standard generation prompt
        system_prompt = SQL_GENERATION_SYSTEM_PROMPT.format(
            role_context=role_context, schema=schema
        )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "{question}"),
    ])

    chain = prompt | llm
    response = chain.invoke({"question": question})

    raw_sql = str(response.content) if response.content else ""
    cleaned_sql = clean_sql(raw_sql)

    print(f"\n[Agent] Generated SQL:\n{cleaned_sql}\n")
    return {"sql_query": cleaned_sql}
```

**Step-by-step:**

1. **Reads state** — Pulls the question, schema, error, and role from the AgentState dictionary.

2. **Selects prompt** — If `error` is non-empty, it means we're on a retry and should use the correction prompt. Otherwise, use the standard generation prompt.

3. **`ChatPromptTemplate.from_messages`** — LangChain's way of creating a structured prompt with:
   - A **system message** (instructions for the AI's behaviour)
   - A **user message** (the actual question)

4. **`chain = prompt | llm`** — This is LangChain's **pipe operator** (LCEL — LangChain Expression Language). It creates a chain: prompt → LLM. Data flows left to right: the prompt template is filled with variables, then sent to the LLM.

5. **`chain.invoke({"question": question})`** — Executes the chain. The LLM receives the formatted prompt and returns a response.

6. **`clean_sql(raw_sql)`** — Strips markdown fences and normalises semicolons.

7. **Returns `{"sql_query": cleaned_sql}`** — This partial dictionary is **merged** into the AgentState. Only the `sql_query` key is updated; all other keys remain unchanged.

##### Node 2: `execute_and_verify(state) → dict`

```python
def execute_and_verify(state: AgentState) -> dict:
    """Runs the SQL and routes to end (success) or triggers retry (failure)."""
    sql = state["sql_query"]
    retries = state.get("retry_count", 0)
    user_role = state.get("role", "admin")

    result = execute_sql(sql, role=user_role)

    if result["status"] == "success":
        return {"final_result": result["data"], "error_message": ""}
    else:
        return {"error_message": result["message"], "retry_count": retries + 1}
```

**Step-by-step:**

1. **Reads state** — Gets the SQL query, current retry count, and user role.
2. **Calls `execute_sql()`** — Runs the query against PostgreSQL with RLS enforcement.
3. **Success path** — Returns the data and clears `error_message` (setting it to `""` so the router knows we succeeded).
4. **Failure path** — Returns the error message and increments `retry_count` by 1. The error message from PostgreSQL (e.g., `column "return_reason" does not exist`) will be fed back to the LLM in the next cycle.

##### Router: `should_continue(state) → str`

```python
def should_continue(state: AgentState) -> str:
    """Conditional routing logic — decides whether to retry or stop."""
    if not state.get("error_message"):
        return "end"           # No error → we're done!
    if state.get("retry_count", 0) >= settings.max_retries:
        print("[Agent] Max retries reached. Halting.")
        return "end"           # Too many retries → give up
    return "retry"             # Still have retries left → try again
```

**This is the decision-maker.** It returns a string that LangGraph uses to determine which edge to follow:
- `"end"` → Go to the `END` node (finish)
- `"retry"` → Loop back to `generate_sql` node

**The 3 scenarios:**

| Condition | Return | Effect |
|---|---|---|
| No error message | `"end"` | Query succeeded → stop and return results |
| Error + retries < 3 | `"retry"` | Query failed but we have retries left → loop back |
| Error + retries ≥ 3 | `"end"` | Query failed too many times → stop to prevent infinite loops |

---

#### File: `core/graph.py`

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from models.state import AgentState
from core.nodes import generate_sql, execute_and_verify, should_continue

def build_agent_graph():
    """Constructs and compiles the SQL agent graph."""
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

# Pre-built singleton
sql_agent = build_agent_graph()
```

**This is where the "magic" happens — the LangGraph state machine assembly.**

**Step-by-step:**

1. **`StateGraph(AgentState)`** — Creates a new graph where the state flowing between nodes is our `AgentState` TypedDict.

2. **`add_node("generate_sql", generate_sql)`** — Registers the function as a named node in the graph. The string name is used for routing; the function reference is what gets called.

3. **`set_entry_point("generate_sql")`** — When the graph starts, execution begins at this node.

4. **`add_edge("generate_sql", "execute_and_verify")`** — A **fixed edge**: after `generate_sql` finishes, ALWAYS go to `execute_and_verify`. No conditions.

5. **`add_conditional_edges(...)`** — A **conditional edge**: after `execute_and_verify` finishes, call `should_continue()` to decide where to go. The mapping `{"end": END, "retry": "generate_sql"}` translates the returned string into a destination node.

6. **`MemorySaver()`** — An in-memory checkpointer that stores the full state after each node execution. This enables:
   - **Multi-user isolation** — Different `thread_id` values get separate state histories.
   - **State recovery** — If the server crashes mid-execution, the state isn't lost.

7. **`workflow.compile(checkpointer=memory)`** — Compiles the graph definition into an executable **runnable** (like compiling source code to a binary). The returned object has an `.invoke()` method.

8. **`sql_agent = build_agent_graph()`** — Pre-builds the graph once at module load. This is the singleton that the rest of the app uses.

**Visual representation of the compiled graph:**

```
START
  │
  ▼
[generate_sql] ◀──────── retry
  │                         │
  ▼                         │
[execute_and_verify] ───────┘
  │
  ▼ (end)
 END
```

---

#### File: `core/agent.py`

```python
from langchain_core.runnables import RunnableConfig
from services.database import get_database_schema
from core.graph import sql_agent

def run_agent(user_question: str, thread_id: str, role: str) -> dict:
    """
    Runs the self-correcting SQL agent for a given question.
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
```

**This is the Façade Pattern** — a simple interface that hides the complexity behind it.

**Step-by-step:**

1. **`get_database_schema()`** — Dynamically reads the current database structure so the LLM knows what tables/columns exist.

2. **`initial_state`** — Constructs the starting `AgentState` dictionary with:
   - The user's question
   - The extracted schema
   - Zero retries, no error, no SQL yet, no results yet
   - The user's security role

3. **`RunnableConfig`** — LangGraph's configuration object. The `thread_id` inside `configurable` tells the `MemorySaver` which conversation thread this belongs to. Different users/sessions get isolated memory.

4. **`sql_agent.invoke(initial_state, config=config)`** — Starts the graph execution. The graph runs Node 1 → Node 2 → Router → (possibly loop) → ... → END, then returns the final state dictionary.

5. **Returns `final_state`** — This dictionary contains the final values of ALL fields: `sql_query`, `final_result`, `error_message`, `retry_count`, etc. The API layer reads these to construct the HTTP response.

**Why this file exists:** External code (FastAPI, tests) should NEVER directly call graph nodes or import the graph. They call `run_agent()` and get a result. If we change the internal graph structure, nothing outside this file breaks.

---

### LAYER 5 — API Layer (`api/`)

#### File: `api/main.py`

```python
import uuid
from fastapi import FastAPI, HTTPException
from models.api_models import QueryRequest, QueryResponse
from core.agent import run_agent

app = FastAPI(
    title="Agentic Text-to-SQL Engine",
    description="An autonomous AI agent that translates natural language to SQL...",
    version="2.0.0",
)

@app.get("/")
def read_root():
    """Health-check / welcome endpoint."""
    return {"message": "Text-to-SQL Agent API is live. Send POST requests to /ask"}

@app.post("/ask", response_model=QueryResponse)
def ask_database(request: QueryRequest):
    session_id = request.thread_id or str(uuid.uuid4())

    try:
        final_state = run_agent(request.question, session_id, request.role)

        if final_state.get("error_message"):
            return QueryResponse(
                status="failed",
                original_question=request.question,
                attempts=final_state.get("retry_count", 0) + 1,
                error_message=final_state.get("error_message"),
            )

        return QueryResponse(
            status="success",
            original_question=request.question,
            sql_query=final_state.get("sql_query"),
            data=final_state.get("final_result"),
            attempts=final_state.get("retry_count", 0) + 1,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**Line-by-line:**

1. **`FastAPI(...)`** — Creates the web application. The `title` and `description` appear in the auto-generated docs at `/docs` (Swagger UI).

2. **`@app.get("/")`** — Registers a GET route at the root URL. Used as a health check: "Is the server alive?"

3. **`@app.post("/ask", response_model=QueryResponse)`** — Registers a POST route. `response_model=QueryResponse` tells FastAPI to:
   - Validate the response matches the `QueryResponse` schema.
   - Auto-generate OpenAPI documentation.
   - Serialise `QueryResponse` to JSON.

4. **`request: QueryRequest`** — FastAPI automatically:
   - Reads the raw JSON from the request body.
   - Validates it against `QueryRequest` (e.g., `question` is required, `role` has a default).
   - Returns `422 Unprocessable Entity` if validation fails.

5. **`request.thread_id or str(uuid.uuid4())`** — If the frontend sends a thread ID, use it. Otherwise, generate a random UUID. This ensures every request has a unique session.

6. **`run_agent(...)`** — Delegates to the core agent. Note: the API contains ZERO AI logic, ZERO database logic. It only shapes HTTP requests/responses.

7. **Two response paths:**
   - `error_message` exists → return `status: "failed"` with the error.
   - No error → return `status: "success"` with the SQL and data.

8. **`attempts = retry_count + 1`** — `retry_count` is 0-indexed (0 = first attempt), but humans understand "1 attempt" better than "0 retries."

9. **`HTTPException(status_code=500)`** — Catches catastrophic errors (e.g., LangGraph itself crashes) and returns a proper HTTP 500.

---

### LAYER 6 — Frontend UI (`ui/`)

#### File: `.streamlit/config.toml`

```toml
[theme]
primaryColor = "#4f46e5"                # Indigo accent colour
backgroundColor = "#0f172a"             # Very dark blue-grey (Slate 900)
secondaryBackgroundColor = "#1e293b"    # Slightly lighter dark (Slate 800)
textColor = "#f8fafc"                   # Near-white text (Slate 50)
font = "sans serif"
base = "dark"
```

**Purpose:** Forces Streamlit to use a premium dark mode theme instead of the default white. The colours are from the Tailwind CSS Slate palette.

---

#### File: `ui/app.py`

This is the largest file (228 lines). Here's the breakdown by section:

##### Section 1: Custom CSS Injection (Lines 16-33)

```python
st.markdown("""
<style>
div[data-testid="stChatMessage"] {
    padding: 1rem;
    border-radius: 0.5rem;
    margin-bottom: 1rem;
}

div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"]) {
    background-color: var(--secondary-background-color);
    border-left: 4px solid var(--primary-color);
}
</style>
""", unsafe_allow_html=True)
```

**What it does:** Injects raw CSS to style chat bubbles. User messages get a left border accent and darker background to visually distinguish them from AI messages.

##### Section 2: Sidebar — Security Context (Lines 43-56)

```python
with st.sidebar:
    st.header("🔐 Security Context")
    selected_role = st.selectbox("Login As:", ["admin", "employee"], index=0)
    st.session_state.current_role = selected_role
```

**What it does:** Provides a dropdown to simulate logging in as different roles. When you switch from "admin" to "employee," the RLS policies in PostgreSQL restrict which rows are returned. This demonstrates enterprise security without building a full authentication system.

##### Section 3: Session State Management (Lines 58-71)

```python
if "chat_history" not in st.session_state:
    st.session_state.chat_history = {}     # thread_id → list of messages
if "chat_titles" not in st.session_state:
    st.session_state.chat_titles = {}      # thread_id → title string
if "thread_id" not in st.session_state:
    initial_id = str(uuid.uuid4())
    st.session_state.thread_id = initial_id
    st.session_state.chat_history[initial_id] = []
    st.session_state.chat_titles[initial_id] = "New Chat"
```

**Why `st.session_state`?** Streamlit reruns the entire script from top to bottom on every interaction. Without `session_state`, all variables would be lost between interactions. `session_state` persists data across reruns.

**Data structures:**
- `chat_history` — A dictionary mapping each thread/chat ID to its list of messages.
- `chat_titles` — A dictionary mapping each thread/chat ID to its display title.

##### Section 4: Chat History Management (Lines 73-112)

The sidebar shows a list of previous chats with:
- A button to load each chat (restores the message history).
- A 🗑️ delete button for each chat.
- A "➕ New Chat" button that creates a fresh thread.

##### Section 5: Schema Explorer (Lines 116-122)

```python
st.subheader("Schema Explorer")
with st.expander("📁 Customers"):
    st.markdown("- `customer_id` (PK)\n- `name`\n- `email`\n- `region`")
```

**Purpose:** A collapsible reference that shows users what tables and columns exist, so they know what questions they can ask.

##### Section 6: Chat Message Rendering (Lines 128-147)

```python
for msg in active_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            if msg.get("sql"):
                with st.expander("🔍 View SQL"):
                    st.code(msg["sql"], language="sql")
            if msg.get("data") is not None:
                st.dataframe(pd.DataFrame(msg["data"]), use_container_width=True)
```

**What it does:** Loops through all messages in the current chat and renders them. Assistant messages get additional widgets:
- An expandable SQL code block.
- An interactive data table (powered by Pandas DataFrame).

##### Section 7: Chat Input & API Call (Lines 150-227)

```python
if prompt := st.chat_input("Ask your database a question..."):
    # Add user message to history
    # Call FastAPI backend via HTTP POST
    payload = {"question": prompt, "thread_id": current_thread_id, "role": st.session_state.current_role}
    response = requests.post(API_URL, json=payload)
    data = response.json()
    # Render success or failure...
```

**Flow:**
1. User types a question in the chat input.
2. The question is added to the chat history.
3. The Streamlit app sends an HTTP POST to `http://localhost:8000/ask` (the FastAPI backend).
4. While waiting, a spinner shows "Agent is reasoning and executing..."
5. The response is parsed and displayed:
   - **Success:** Shows a 🟢 badge, the SQL in an expander, and the data as a table.
   - **Failure:** Shows a 🔴 badge with the error details.

**`if prompt := st.chat_input(...)`** — This is the **walrus operator** (`:=`). It both assigns the return value to `prompt` AND evaluates it as a boolean. If the user hasn't typed anything, `prompt` is `None` → falsy → the block is skipped.

---

### LAYER 7 — Database Setup (`db/` & Docker)

#### File: `docker-compose.yml`

```yaml
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: securepassword123
      POSTGRES_DB: business_sandbox
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./db/init.sql:/docker-entrypoint-initdb.d/init.sql

volumes:
  pgdata:
```

**Line-by-line:**

| Line | Purpose |
|---|---|
| `image: postgres:15` | Uses official PostgreSQL 15 Docker image |
| `POSTGRES_USER/PASSWORD/DB` | Configures credentials and database name |
| `"5432:5432"` | Maps container port 5432 to host port 5432 |
| `pgdata:/var/lib/...` | Persistent storage — data survives container restarts |
| `./db/init.sql:/docker-entrypoint-initdb.d/init.sql` | Automatically runs `init.sql` when the database is first created |

**Key insight:** The `docker-entrypoint-initdb.d/` directory is special in the PostgreSQL Docker image. Any `.sql` scripts placed there are executed **once** when the database is initialized for the first time.

---

#### File: `db/init.sql`

This file does 4 things:

##### Part 1: Create Tables (Lines 1-23)

```sql
CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100),
    region VARCHAR(50)
);

CREATE TABLE products (...);
CREATE TABLE orders (...);
```

- `SERIAL PRIMARY KEY` — Auto-incrementing integer ID.
- `VARCHAR(100)` — Variable-length text, max 100 chars.
- `REFERENCES customers(customer_id)` — Foreign key relationship (orders reference customers).

##### Part 2: Seed Data (Lines 25-40)

```sql
INSERT INTO customers (name, email, region) VALUES
('Alice Smith', 'alice@test.com', 'North America'),
('Ravi Kumar', 'ravi@test.com', 'Asia'),
('Elena Rossi', 'elena@test.com', 'Europe');

INSERT INTO products (...);
INSERT INTO orders (...);
```

**Purpose:** Provides sample data so the agent has something to query. Without this, every query would return empty results.

##### Part 3: Create AI Agent Role (Lines 42-46)

```sql
CREATE ROLE ai_agent WITH LOGIN PASSWORD 'readonly_pass';
GRANT CONNECT ON DATABASE business_sandbox TO ai_agent;
GRANT USAGE ON SCHEMA public TO ai_agent;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO ai_agent;
```

**What it does:**
1. Creates a PostgreSQL role called `ai_agent`.
2. Grants it minimal permissions: can connect, can read (SELECT) from all tables.
3. **Cannot** INSERT, UPDATE, DELETE, or DROP anything. This is the **principle of least privilege**.

##### Part 4: Row-Level Security Policies (Lines 48-83)

```sql
-- Turn on RLS
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE products ENABLE ROW LEVEL SECURITY;

-- Admin: can see everything
CREATE POLICY admin_all_customers ON customers FOR SELECT
USING (current_setting('app.current_role', true) = 'admin');

-- Employee: can only see North America
CREATE POLICY employee_na_customers ON customers FOR SELECT
USING (current_setting('app.current_role', true) = 'employee'
       AND region = 'North America');

-- Employee: can only see orders for NA customers
CREATE POLICY employee_na_orders ON orders FOR SELECT
USING (
    current_setting('app.current_role', true) = 'employee' AND
    customer_id IN (SELECT customer_id FROM customers WHERE region = 'North America')
);
```

**How RLS works:**

1. `ENABLE ROW LEVEL SECURITY` — Tells PostgreSQL: "Don't return all rows. Check policies first."
2. Each `CREATE POLICY` defines a rule: "For SELECT queries, only return rows WHERE this condition is true."
3. `current_setting('app.current_role', true)` — Reads the session variable we set in `execute_sql()`.
4. The `true` parameter means "return NULL instead of error if the variable isn't set."

**Result:**

| Role | Customers Visible | Orders Visible | Products Visible |
|---|---|---|---|
| Admin | All 3 | All 4 | All 3 |
| Employee | Only Alice (NA) | Only Alice's orders | All 3 |

---

### LAYER 8 — Tests (`tests/`)

#### File: `tests/test_agent.py`

```python
from core.agent import run_agent

def main():
    question = (
        "Can you give me the names of customers who returned a product, "
        "and sort them by the 'return_reason' column?"
    )

    final_state = run_agent(question, thread_id="test_thread_001", role="admin")

    if final_state.get("error_message"):
        print("Status: FAILED")
        print(f"Last Error: {final_state.get('error_message')}")
    else:
        print("Status: SUCCESS")
        print(f"Final SQL:\n{final_state.get('sql_query')}")
        for row in final_state.get("final_result", []):
            print(f" - {row}")

if __name__ == "__main__":
    main()
```

**Why this test question is special:**

The question asks to sort by `return_reason` — but **that column doesn't exist** in the database. The `orders` table has `returned` (boolean), not `return_reason`.

This test is designed to **trigger the self-correction loop:**

1. **Attempt 1:** LLM generates `SELECT ... ORDER BY return_reason;` → PostgreSQL error: `column "return_reason" does not exist`.
2. **Attempt 2:** Error is fed back to the LLM, which realises the mistake and generates `SELECT ... WHERE returned = TRUE;` (using the correct column name and removing the invalid sort).
3. **Success:** Returns `Ravi Kumar` (the only customer with a returned order).

---

## 6. Full Data Flow (End to End)

Here is **exactly** what happens when a user types "Show me all customers" as Admin:

```
Step 1: USER types "Show me all customers" in Streamlit chat input
        ↓
Step 2: Streamlit sends HTTP POST to http://localhost:8000/ask
        Payload: { "question": "Show me all customers", "thread_id": "abc-123", "role": "admin" }
        ↓
Step 3: FastAPI receives request, validates against QueryRequest schema
        ↓
Step 4: FastAPI calls run_agent("Show me all customers", "abc-123", "admin")
        ↓
Step 5: run_agent() calls get_database_schema()
        → Connects to PostgreSQL
        → Queries information_schema.columns
        → Returns formatted schema string
        ↓
Step 6: run_agent() constructs initial AgentState:
        {
            "question": "Show me all customers",
            "schema": "Database Schema:\nTable 'customers': customer_id (integer)...",
            "retry_count": 0,
            "error_message": "",
            "sql_query": "",
            "final_result": None,
            "role": "admin"
        }
        ↓
Step 7: sql_agent.invoke(initial_state, config) → starts LangGraph
        ↓
Step 8: NODE 1 — generate_sql()
        → No error → uses SQL_GENERATION_SYSTEM_PROMPT
        → Formats prompt with schema + role context
        → Sends to LLM (LM Studio / Gemma)
        → LLM returns: "SELECT * FROM customers;"
        → clean_sql() strips any markdown
        → Returns {"sql_query": "SELECT * FROM customers;"}
        → AgentState updated: sql_query = "SELECT * FROM customers;"
        ↓
Step 9: NODE 2 — execute_and_verify()
        → Calls execute_sql("SELECT * FROM customers;", role="admin")
        → get_db_connection() opens PostgreSQL connection
        → SET ROLE ai_agent; (switch to restricted role)
        → set_config('app.current_role', 'admin', true) (RLS context)
        → Executes SELECT * FROM customers;
        → RLS policy: current_role = 'admin' → returns ALL rows
        → Result: [{"customer_id": 1, "name": "Alice Smith", ...}, ...]
        → Returns {"final_result": [...], "error_message": ""}
        ↓
Step 10: ROUTER — should_continue()
         → error_message is "" (empty) → return "end"
         ↓
Step 11: Graph reaches END → returns final state to run_agent()
         ↓
Step 12: run_agent() returns final_state to FastAPI
         ↓
Step 13: FastAPI constructs QueryResponse:
         {
             "status": "success",
             "original_question": "Show me all customers",
             "sql_query": "SELECT * FROM customers;",
             "data": [{"customer_id": 1, "name": "Alice Smith", ...}, ...],
             "attempts": 1,
             "error_message": null
         }
         ↓
Step 14: HTTP 200 JSON response sent back to Streamlit
         ↓
Step 15: Streamlit renders:
         🟢 Success in 1 attempts
         [🔍 View SQL] expandable section
         Interactive data table with 3 rows
```

---

## 7. The Self-Correction Loop Explained

Here's what happens when the LLM generates **incorrect SQL**:

```
Attempt 1:
    User: "Sort customers by return_reason"
    LLM generates: SELECT * FROM customers ORDER BY return_reason;
    PostgreSQL: ERROR — column "return_reason" does not exist
    retry_count: 0 → 1
    should_continue: error exists, 1 < 3 → "retry"

Attempt 2:
    LLM receives CORRECTION prompt:
    "Your previous query failed with this exact error:
     column 'return_reason' does not exist"
    LLM generates: SELECT c.name FROM customers c
                   JOIN orders o ON c.customer_id = o.customer_id
                   WHERE o.returned = TRUE;
    PostgreSQL: SUCCESS → returns [{"name": "Ravi Kumar"}]
    error_message: "" (cleared)
    should_continue: no error → "end"
    ✅ DONE in 2 attempts
```

**If ALL 3 retries fail:**

```
Attempt 3 fails → retry_count = 3
should_continue: 3 >= 3 (max_retries) → "end"
Returns with error_message populated → API returns status: "failed"
```

---

## 8. Row-Level Security (RLS) Explained

**Same question, different results based on role:**

### Admin asks: "Show me all customers"

```sql
-- RLS Policy applied:
-- current_setting('app.current_role') = 'admin' → TRUE for ALL rows
-- Result: 3 customers returned

| customer_id | name        | region        |
|-------------|-------------|---------------|
| 1           | Alice Smith | North America |
| 2           | Ravi Kumar  | Asia          |
| 3           | Elena Rossi | Europe        |
```

### Employee asks: "Show me all customers"

```sql
-- RLS Policy applied:
-- current_setting('app.current_role') = 'employee' AND region = 'North America'
-- Only rows where BOTH conditions are TRUE
-- Result: 1 customer returned

| customer_id | name        | region        |
|-------------|-------------|---------------|
| 1           | Alice Smith | North America |
```

**The SQL query is identical** (`SELECT * FROM customers;`). The security filtering happens **at the database level**, not in the application code. This is why RLS is considered enterprise-grade — even if the application has a bug, the database won't leak data.

---

## 9. How to Run the Project

### Prerequisites
- Docker Desktop installed and running
- Python 3.12+
- LM Studio running with a model loaded (e.g., Gemma)

### Step 1: Start the Database
```bash
cd sql-agent-project
docker compose up -d
```

### Step 2: Create Virtual Environment & Install Dependencies
```bash
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

### Step 3: Start the FastAPI Backend
```bash
# From the sql-agent-project directory
set PYTHONPATH=.
.venv\Scripts\python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### Step 4: Start the Streamlit Frontend (in a new terminal)
```bash
set PYTHONPATH=.
.venv\Scripts\streamlit run ui/app.py
```

### Step 5: Open the Dashboard
Navigate to `http://localhost:8501` in your browser.

---


*This document covers every file, every function, every line of code, and the full end-to-end data flow of the Agentic Text-to-SQL Engine with Autonomous Self-Correction.*
