# services/database.py
"""
Manages the PostgreSQL connection, schema extraction, and RLS-aware SQL execution.
All database I/O is isolated here — no business logic, no LLM calls.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from config import settings


def get_db_connection():
    """Establishes a connection to the PostgreSQL database using centralised config."""
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


def get_database_schema() -> str:
    """
    Extracts the schema from the database and formats it into a highly
    token-efficient string to be injected into the LLM's system prompt.
    """
    conn = get_db_connection()
    if not conn:
        return "Error: Could not connect to database."

    cursor = None
    try:
        cursor = conn.cursor()

        # Query information_schema to get tables and columns dynamically
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

        # Format into a dense, token-friendly string
        schema_text = "Database Schema:\n"
        for table, columns in schema_dict.items():
            schema_text += f"Table '{table}': {', '.join(columns)}\n"

        return schema_text

    except psycopg2.Error as e:
        return f"Error extracting schema: {e}"
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def execute_sql(query: str, role: str = "admin") -> dict:
    """
    Executes a SQL query against the database, enforcing Row-Level Security (RLS).

    Steps:
      1. Switch to the restricted 'ai_agent' role so RLS policies apply.
      2. Set the session variable `app.current_role` to the user's business role.
      3. Execute the AI-generated query within that security context.
    """
    conn = get_db_connection()
    if not conn:
        return {"status": "error", "message": "Database connection failed."}

    cursor = None
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Switch to restricted role so RLS is enforced
        cursor.execute("SET ROLE ai_agent;")

        # Set the business role for this transaction
        cursor.execute(f"SELECT set_config('app.current_role', '{role.lower()}', true);")

        # Execute the AI-generated query
        cursor.execute(query)

        if cursor.description:
            results = cursor.fetchall()
            return {"status": "success", "data": results}
        else:
            conn.commit()
            return {"status": "success", "data": "Query executed successfully."}

    except psycopg2.Error as e:
        return {"status": "error", "message": str(e)}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
