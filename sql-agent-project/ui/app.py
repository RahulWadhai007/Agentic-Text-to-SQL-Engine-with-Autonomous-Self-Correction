# ui/app.py
"""
Streamlit chat dashboard — renders the UI, manages session state,
and calls the FastAPI backend via HTTP. Contains zero AI/business logic.
"""

import streamlit as st
import requests
import pandas as pd
import uuid

# ── Page Config ──
st.set_page_config(page_title="Data Copilot", page_icon="🤖", layout="wide")

# ── Custom CSS ──
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

div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarAssistant"]) {
    background-color: transparent;
}
</style>
""", unsafe_allow_html=True)

st.title("🤖 Enterprise Data Copilot")
st.markdown("Ask natural language questions. The agent will draft, test, and self-correct the SQL.")

API_URL = "http://localhost:8000/ask"

# ══════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════
with st.sidebar:
    # ── Security Context ──
    st.header("🔐 Security Context")
    st.markdown("Simulate logging in as different user roles to test Database Row-Level Security (RLS).")

    selected_role = st.selectbox(
        "Login As:",
        ["admin", "employee"],
        index=0,
    )
    st.session_state.current_role = selected_role

    st.divider()
    st.markdown("**Admin:** Sees all global data.\n\n**Employee:** Can only see customers/orders in North America.")

# ── Session State Initialisation ──
if "chat_history" not in st.session_state:
    st.session_state.chat_history = {}  # thread_id -> list of messages

if "chat_titles" not in st.session_state:
    st.session_state.chat_titles = {}  # thread_id -> title string

if "thread_id" not in st.session_state:
    initial_id = str(uuid.uuid4())
    st.session_state.thread_id = initial_id
    st.session_state.chat_history[initial_id] = []
    st.session_state.chat_titles[initial_id] = "New Chat"

current_thread_id = st.session_state.thread_id

# ── Sidebar: Chat Management & Schema Explorer ──
with st.sidebar:
    st.header("Control Panel")

    if st.button("➕ New Chat", use_container_width=True, type="primary"):
        new_id = str(uuid.uuid4())
        st.session_state.thread_id = new_id
        st.session_state.chat_history[new_id] = []
        st.session_state.chat_titles[new_id] = "New Chat"
        st.rerun()

    st.divider()

    st.subheader("Chat History")
    threads_to_delete = []

    for t_id, t_title in reversed(list(st.session_state.chat_titles.items())):
        col1, col2 = st.columns([0.85, 0.15])
        with col1:
            button_type = "primary" if t_id == st.session_state.thread_id else "secondary"
            if st.button(t_title, key=f"load_{t_id}", use_container_width=True, type=button_type):
                st.session_state.thread_id = t_id
                st.rerun()
        with col2:
            if st.button("🗑️", key=f"del_{t_id}", help="Delete chat"):
                threads_to_delete.append(t_id)

    # Handle deletions
    for d_id in threads_to_delete:
        del st.session_state.chat_titles[d_id]
        del st.session_state.chat_history[d_id]
        if st.session_state.thread_id == d_id:
            if len(st.session_state.chat_titles) > 0:
                st.session_state.thread_id = list(st.session_state.chat_titles.keys())[-1]
            else:
                new_id = str(uuid.uuid4())
                st.session_state.thread_id = new_id
                st.session_state.chat_history[new_id] = []
                st.session_state.chat_titles[new_id] = "New Chat"
        st.rerun()

    st.divider()

    st.subheader("Schema Explorer")
    with st.expander("📁 Customers"):
        st.markdown("- `customer_id` (PK)\n- `name`\n- `email`\n- `region`")
    with st.expander("📁 Products"):
        st.markdown("- `product_id` (PK)\n- `product_name`\n- `category`\n- `price`")
    with st.expander("📁 Orders"):
        st.markdown("- `order_id` (PK)\n- `customer_id` (FK)\n- `product_id` (FK)\n- `order_date`\n- `quantity`\n- `returned`")

# ══════════════════════════════════════════
# CHAT AREA
# ══════════════════════════════════════════

# ── Render existing message history ──
active_messages = st.session_state.chat_history.get(current_thread_id, [])

for msg in active_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

        if msg["role"] == "assistant":
            if msg.get("status_badge"):
                st.markdown(msg["status_badge"])

            if msg.get("sql"):
                with st.expander("🔍 View SQL"):
                    st.code(msg["sql"], language="sql")

            if msg.get("data") is not None:
                if len(msg["data"]) > 0:
                    st.dataframe(pd.DataFrame(msg["data"]), use_container_width=True)
                else:
                    st.info("No results found.")

# ── Chat Input ──
if prompt := st.chat_input("Ask your database a question..."):

    # Auto-generate title on first message
    if st.session_state.chat_titles[current_thread_id] == "New Chat":
        short_title = prompt[:20] + "..." if len(prompt) > 20 else prompt
        st.session_state.chat_titles[current_thread_id] = short_title

    # Add user message
    st.session_state.chat_history[current_thread_id].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Call the FastAPI backend
    with st.chat_message("assistant"):
        with st.spinner("Agent is reasoning and executing..."):
            try:
                payload = {
                    "question": prompt,
                    "thread_id": current_thread_id,
                    "role": st.session_state.current_role,
                }
                response = requests.post(API_URL, json=payload)
                data = response.json()

                if data.get("status") == "success":
                    reply_text = "Here is the data you requested."
                    status_badge = f"🟢 **Success** in {data.get('attempts', 1)} attempts"
                    sql_query = data.get("sql_query", "")
                    table_data = data.get("data", [])

                    st.markdown(reply_text)
                    st.markdown(status_badge)

                    with st.expander("🔍 View SQL"):
                        st.code(sql_query, language="sql")

                    if table_data and len(table_data) > 0:
                        st.dataframe(pd.DataFrame(table_data), use_container_width=True)
                    else:
                        st.info("No results found.")

                    st.session_state.chat_history[current_thread_id].append({
                        "role": "assistant",
                        "content": reply_text,
                        "status_badge": status_badge,
                        "sql": sql_query,
                        "data": table_data,
                    })

                else:
                    error_msg = data.get("error_message", "Unknown Error")
                    attempts = data.get("attempts", 1)

                    reply_text = "The agent failed to generate a valid response."
                    status_badge = f"🔴 **Failed** after {attempts} attempts."

                    st.markdown(reply_text)
                    st.error(f"**Error Details:**\n{error_msg}")
                    st.markdown(status_badge)

                    st.session_state.chat_history[current_thread_id].append({
                        "role": "assistant",
                        "content": f"{reply_text}\n\n**Error Details:**\n{error_msg}",
                        "status_badge": status_badge,
                        "sql": None,
                        "data": None,
                    })

            except Exception as e:
                error_msg = f"Server Connection Error: {e}"
                st.error(error_msg)
                st.session_state.chat_history[current_thread_id].append({
                    "role": "assistant",
                    "content": error_msg,
                    "status_badge": None,
                    "sql": None,
                    "data": None,
                })
