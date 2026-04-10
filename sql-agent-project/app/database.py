# app/database.py
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=os.getenv("POSTGRES_PORT", "5432"),
            database=os.getenv("POSTGRES_DB", "business_sandbox"),
            user=os.getenv("POSTGRES_USER", "admin"),
            password=os.getenv("POSTGRES_PASSWORD", "securepassword123")
        )
        return conn
    except psycopg2.Error as e:
        print(f"Database connection failed: {e}")
        return None

def get_database_schema() -> str:
    """
    Extracts the schema from the database and formats it into a highly 
    token-efficient string to be injected into the local LLM's system prompt.
    """
    conn = get_db_connection()
    if not conn:
        return "Error: Could not connect to database."

    try:
        cursor = conn.cursor()
        
        # Query the information_schema to get tables and columns dynamically
        query = """
            SELECT table_name, column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position;
        """
        cursor.execute(query)
        rows = cursor.fetchall()

        # Group columns by table
        schema_dict = {}
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
    """
    conn = get_db_connection()
    if not conn:
        return {"status": "error", "message": "Database connection failed."}

    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # THE SECURITY MAGIC: Set the PostgreSQL session variable for this specific transaction
        # To set custom session variables, use set_config() so it doesn't try to parse it as a keyword
        
        # NOTE: Because we are connected as 'admin' (superuser), we must switch to our read-only 'ai_agent' 
        # role for this transaction so that Row-Level Security (RLS) is actually enforced!
        cursor.execute("SET ROLE ai_agent;")
        
        cursor.execute(f"SELECT set_config('app.current_role', '{role.lower()}', true);")
        
        # Now run the AI's generated query
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