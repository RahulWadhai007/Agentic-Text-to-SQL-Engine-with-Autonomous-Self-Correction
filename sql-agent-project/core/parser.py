# core/parser.py
"""
Sanitises raw LLM output into executable SQL.
Strips markdown fences, conversational filler, and normalises semicolons.
"""

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
