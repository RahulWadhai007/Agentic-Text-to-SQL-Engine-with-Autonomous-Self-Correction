# config/settings.py
"""
Loads .env ONCE and exposes a validated Settings dataclass.
Every other module imports `settings` from here instead of calling os.getenv directly.
"""

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

    # ── LLM (LM Studio / OpenAI-compatible) ──
    openai_api_base: str = os.getenv("OPENAI_API_BASE", "http://localhost:1234/v1")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "lm-studio")
    model_name: str = os.getenv("MODEL_NAME", "gpt-3.5-turbo")
    llm_temperature: float = float(os.getenv("LLM_TEMPERATURE", "0"))

    # ── LangSmith Observability ──
    langchain_tracing_v2: str = os.getenv("LANGCHAIN_TRACING_V2", "true")
    langchain_endpoint: str = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
    langchain_api_key: str = os.getenv("LANGCHAIN_API_KEY", "")
    langchain_project: str = os.getenv("LANGCHAIN_PROJECT", "sql-agent-local-v1")

    # ── Agent Behaviour ──
    max_retries: int = int(os.getenv("AGENT_MAX_RETRIES", "3"))


# Singleton instance — import this everywhere
settings = Settings()
