🤖 Agentic Text-to-SQL Engine: Self-Correcting Data Copilot
This project is a high-performance, enterprise-ready AI agent that translates natural language into complex PostgreSQL queries. Unlike traditional "one-shot" AI models, this engine uses a stateful graph architecture to execute queries, catch syntax errors, and autonomously self-correct until the correct data is retrieved.

🌟 Key Technical Features
Self-Healing SQL Logic: Built with LangGraph, the agent doesn't stop if it makes a mistake. If the database returns a psycopg2 error, the agent captures the trace, analyzes it, and rewrites the SQL—often fixing JOIN or SCHEMA errors in a single loop.

Enterprise-Grade Security (RLS): Implements Row-Level Security directly within PostgreSQL. Even if the AI drafts a valid query, the database itself blocks unauthorized access.

Contextual Multi-Turn Memory: Uses thread_id session management to allow follow-up questions (e.g., asking "And what about Ravi?" after a general customer query) without losing context.

Local LLM Optimization: Specifically configured to run efficiently on local hardware (tested on RTX 3050) using quantized models like Gemma-4B via LM Studio.

Full Observability: Integrated with LangSmith for deep-dive tracing of every node execution, prompt version, and token count.

🏗️ The Architecture
The system is designed to be production-ready and decoupled:

Frontend: A polished Streamlit dashboard with a ChatGPT-style interface and integrated database schema explorer.

API Layer: FastAPI backend handling session threads and security headers.

The Brain: A LangGraph state machine orchestrating the reasoning and retry logic.

The Shield: PostgreSQL 15 running in Docker, enforcing session-based security policies.

🛠️ Tech Stack
Frameworks: LangGraph, LangChain, FastAPI

Database: PostgreSQL (Dockerized)

Interface: Streamlit

Observability: LangSmith

Language: Python 3.10+

🚀 The "Final Boss" Demo: Security Enforcement
This project solves the "AI Privacy" problem. We implemented a Zero-Trust model where the database engine, not the AI, makes the final call on data visibility:

Admin Mode: Full access to global regions and sales.

Employee Mode: Even if the AI writes a SELECT *, the database physically hides rows outside of the "North America" region based on the session's virtual role.

🎓 Author
[Rahul Wadhai] 8th Semester University Student | Aspiring AI & MLOps Engineer
