# services/llm.py
"""
Instantiates and exposes the ChatOpenAI LLM client as a singleton.
All LLM configuration is read from centralised settings — nothing is hardcoded.
"""

from langchain_openai import ChatOpenAI
from pydantic import SecretStr
from config import settings

# Single LLM instance shared across the application
llm = ChatOpenAI(
    base_url=settings.openai_api_base,
    api_key=SecretStr(settings.openai_api_key),
    model=settings.model_name,
    temperature=settings.llm_temperature,
)
