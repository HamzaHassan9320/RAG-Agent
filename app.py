import streamlit as st
from agent_setup import agent_query
from db.database import db
from datetime import datetime
import pytz

st.set_page_config(page_title="RAG-Agent Chat", page_icon="🤖", layout="wide")

# -------------------------
# Optional Custom CSS for Sidebar (without overriding colors)
# -------------------------
st.markdown("""
    <style>
    /* Scrollable container for sessions */
    .session-list {
        height: 400px;
        overflow-y: auto;
        margin-top: 0.5rem;
        margin-bottom: 1rem;
    }
    /* Session item styling */
    .session-item {
        display: block;
        padding: 0.5rem 0.75rem;
        margin: 0.25rem 0;
        cursor: pointer;
        overflow: hidden;
        white-space: nowrap;
        text-overflow: ellipsis;
        text-decoration: none;
        border-radius: 4px;
    }
    .session-item:hover {
        background-color: #E0E0E0;
    }
    .session-item.active {
        background-color: #D0D0D0;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

# -------------------------
# Session State
# -------------------------
if 'current_session_id' not in st.session_state:
    st.session_state.current_session_id = None

# -------------------------
# SIDEBAR
# -------------------------
with st.sidebar:
    st.title("Chat Sessions")

    # "New Chat" button
    if st.button("New Chat"):
        st.session_state.current_session_id = None
        st.set_query_params()   
        st.rerun()

    st.markdown("---")

    # Scrollable container for session list
    sessions = db.get_sessions()
    session_list_html = "<div class='session-list'>"
    for session in sessions:
        active_class = "active" if str(session['id']) == str(st.session_state.current_session_id) else ""
        session_list_html += f"<a class='session-item {active_class}' title='{session['name']}' href='?session_id={session['id']}'>{session['name']}</a>"
    session_list_html += "</div>"
    st.markdown(session_list_html, unsafe_allow_html=True)

# -------------------------
# CHECK URL QUERY PARAMS
# -------------------------
query_params = st.query_params
if "session_id" in query_params:
    st.session_state.current_session_id = int(query_params["session_id"][0])

# -------------------------
# MAIN CHAT AREA
# -------------------------
st.title("🤖 RAG-Agent Chat")

if st.session_state.current_session_id:
    messages = db.get_session_messages(st.session_state.current_session_id)
else:
    messages = []

# Display chat messages using st.chat_message 
for msg in messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# -------------------------
# Chat input using st.chat_input (always pinned at bottom)
# -------------------------
user_input = st.chat_input("Ask me something...")
if user_input:
    # Create a new session if none is active
    if st.session_state.current_session_id is None:
        name = user_input[:40].strip().replace("\n", " ") + ("..." if len(user_input) > 40 else "")
        session_id = db.create_session(name or f"Chat {datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S')}")
        st.session_state.current_session_id = session_id

    # Save and display the user's message
    db.add_message(st.session_state.current_session_id, "user", user_input)
    with st.chat_message("user"):
        st.write(user_input)

    # Query the agent and display the response
    with st.spinner("🤖 Thinking..."):
        result = agent_query(user_input)
    db.add_message(st.session_state.current_session_id, "assistant", result.response)
    with st.chat_message("assistant"):
        st.write(result.response)

    # Rerun to update the conversation
    st.rerun()
