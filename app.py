import streamlit as st
from agent_setup import agent_query
from db.database import db
from datetime import datetime
import pytz

st.set_page_config(page_title="RAG-Agent Chat", page_icon="🤖", layout="wide")

# CSS styling
st.markdown("""
    <style>
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
    </style>
""", unsafe_allow_html=True)

# Session state
if 'current_session_id' not in st.session_state:
    st.session_state.current_session_id = None

# Sidebar: List sessions
with st.sidebar:
    st.title("💬 Chat Sessions")
    st.markdown("---")
    
    sessions = db.get_sessions()
    for session in sessions:
        if st.button(f"📝 {session['name']}", key=f"session_{session['id']}", use_container_width=True):
            st.session_state.current_session_id = session['id']
            st.rerun()

        if st.button("🗑️", key=f"delete_{session['id']}", use_container_width=True):
            db.delete_session(session['id'])
            if st.session_state.current_session_id == session['id']:
                st.session_state.current_session_id = None
            st.rerun()

# Main app
st.title("🤖 RAG-Agent Chat")

# Input box
with st.form(key="chat_form", clear_on_submit=True):
    user_input = st.text_area("Your message:", key="user_input", placeholder="Ask me something...")
    submitted = st.form_submit_button("Send")

if submitted and user_input.strip():
    # Create a session on first message
    if st.session_state.current_session_id is None:
        name = user_input[:40].strip().replace("\n", " ") + ("..." if len(user_input) > 40 else "")
        session_id = db.create_session(name or f"Chat {datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S')}")
        st.session_state.current_session_id = session_id

    db.add_message(st.session_state.current_session_id, "user", user_input)

    with st.spinner("🤖 Thinking..."):
        result = agent_query(user_input)
        db.add_message(st.session_state.current_session_id, "assistant", result.response)

    st.rerun()

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
