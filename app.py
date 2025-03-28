import streamlit as st
from agent_setup import agent_query
from db.database import db
from datetime import datetime
import pytz

st.set_page_config(page_title="RAG-Agent Chat", page_icon="🤖", layout="wide")

# Inject custom CSS for styling
st.markdown("""
    <style>
    /* Chat message styles */
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        font-size: 1rem;
    }
    .user-message { background-color: #d1ecf1; }
    .assistant-message { background-color: #f8f9fa; }
    .chat-timestamp {
        font-size: 0.75rem;
        color: #888;
        margin-bottom: 0.25rem;
    }

    /* Use a system UI font for a native look */
    html, body, button, .session-item {
      font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif !important;
    }

    /* Sidebar style */
    [data-testid="stSidebar"] {
      background-color: #F7F7F7;  /* light grey background */
    }

    /* Session list items */
    .session-item {
      display: block;
      padding: 0.5rem 0.75rem;
      margin: 0.25rem 0;
      cursor: pointer;
      overflow: hidden;
      white-space: nowrap;
      text-overflow: ellipsis;  /* single-line truncation */
      color: #333;
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

    /* Main chat area improvements */
    section.main div.block-container {
      max-width: 800px;
      padding: 1rem 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# Check URL query parameters for session_id and update session state if present
query_params = st.experimental_get_query_params()
if "session_id" in query_params:
    st.session_state.current_session_id = query_params["session_id"][0]

# Session state initialization
if 'current_session_id' not in st.session_state:
    st.session_state.current_session_id = None

# Sidebar: List sessions
with st.sidebar:
    st.title("Chat Sessions")
    
    # "New Chat" button at the top
    if st.button("New Chat"):
        st.session_state.current_session_id = None
        st.experimental_set_query_params()  # Clear query parameters
        st.experimental_rerun()
    
    st.markdown("---")
    
    # Scrollable container for session list using HTML wrapper
    session_list_html = "<div style='height:400px; overflow:auto;'>"
    sessions = db.get_sessions()
    for session in sessions:
        active_class = "active" if st.session_state.current_session_id == str(session['id']) else ""
        # Each session is a clickable anchor that passes the session id via URL query parameters.
        session_list_html += f"<a class='session-item {active_class}' title='{session['name']}' href='?session_id={session['id']}'>{session['name']}</a>"
    session_list_html += "</div>"
    st.markdown(session_list_html, unsafe_allow_html=True)

# Main app area
st.title("🤖 RAG-Agent Chat")

# Input box
with st.form(key="chat_form", clear_on_submit=True):
    user_input = st.text_area("Your message:", key="user_input", placeholder="Ask me something...")
    submitted = st.form_submit_button("Send")

if submitted and user_input.strip():
    # Create a session on first message if needed
    if st.session_state.current_session_id is None:
        name = user_input[:40].strip().replace("\n", " ") + ("..." if len(user_input) > 40 else "")
        session_id = db.create_session(name or f"Chat {datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S')}")
        st.session_state.current_session_id = session_id

    db.add_message(st.session_state.current_session_id, "user", user_input)

    with st.spinner("🤖 Thinking..."):
        result = agent_query(user_input)
        db.add_message(st.session_state.current_session_id, "assistant", result.response)

    st.experimental_rerun()

# Display chat history
if st.session_state.current_session_id:
    messages = db.get_session_messages(st.session_state.current_session_id)
    for msg in messages:
        st.markdown(
            f"""<div class="chat-message {'user-message' if msg['role'] == 'user' else 'assistant-message'}">
                <div class="chat-timestamp">{msg['created_at'].strftime('%Y-%m-%d %H:%M:%S')}</div>
                {msg['content']}
            </div>""",
            unsafe_allow_html=True
        )
else:
    st.info("👈 Start a new chat by sending your first message.")
