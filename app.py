# app.py
import streamlit as st
from agent_setup import agent_query
from db.database import db
from datetime import datetime
import pytz

# Configure page
st.set_page_config(
    page_title="RAG-Agent Chat",
    page_icon="🤖",
    layout="wide"
)

# Add CSS for better styling
st.markdown("""
    <style>
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        line-height: 1.5;
    }
    .user-message {
        background-color: #e3f2fd;
    }
    .assistant-message {
        background-color: #f5f5f5;
    }
    .chat-timestamp {
        font-size: 0.8rem;
        color: #666;
        margin-bottom: 0.5rem;
    }
    .session-button {
        width: 100%;
        text-align: left;
        padding: 0.5rem;
        margin: 0.2rem 0;
        border: none;
        background: none;
        cursor: pointer;
    }
    .session-button:hover {
        background-color: #f0f2f6;
    }
    .session-button.active {
        background-color: #e3f2fd;
    }
    .delete-button {
        color: #dc3545;
        float: right;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'current_session_id' not in st.session_state:
    st.session_state.current_session_id = None

# Sidebar with chat sessions
with st.sidebar:
    st.title("💬 Chat Sessions")
    
    # New chat button
    if st.button("🆕 New Chat"):
        # Create a new session with timestamp as name
        timestamp = datetime.now(pytz.UTC).strftime("%Y-%m-%d %H:%M:%S")
        session_id = db.create_session(f"Chat {timestamp}")
        st.session_state.current_session_id = session_id
        st.experimental_rerun()
    
    st.markdown("---")
    
    # List existing sessions
    sessions = db.get_sessions()
    for session in sessions:
        col1, col2 = st.columns([4, 1])
        with col1:
            if st.button(
                f"📝 {session['name']}",
                key=f"session_{session['id']}",
                help=f"Created: {session['created_at'].strftime('%Y-%m-%d %H:%M:%S')}",
                use_container_width=True
            ):
                st.session_state.current_session_id = session['id']
                st.experimental_rerun()
        with col2:
            if st.button(
                "🗑️",
                key=f"delete_{session['id']}",
                help="Delete this chat session",
                use_container_width=True
            ):
                db.delete_session(session['id'])
                if st.session_state.current_session_id == session['id']:
                    st.session_state.current_session_id = None
                st.experimental_rerun()

# Main chat interface
st.title("🤖 RAG-Agent Chat")

if st.session_state.current_session_id is None:
    st.info("👈 Create a new chat session or select an existing one from the sidebar")
else:
    # Display chat messages
    messages = db.get_session_messages(st.session_state.current_session_id)
    
    for message in messages:
        with st.container():
            st.markdown(
                f"""<div class="chat-message {'user-message' if message['role'] == 'user' else 'assistant-message'}">
                    <div class="chat-timestamp">{message['created_at'].strftime('%Y-%m-%d %H:%M:%S')}</div>
                    {message['content']}
                </div>""",
                unsafe_allow_html=True
            )
    
    # Chat input
    with st.container():
        user_input = st.text_area(
            "Your message",
            key="user_input",
            help="Type your message here and press Ctrl+Enter to send",
            placeholder="Ask me anything about the code or repository..."
        )
        
        if user_input:
            # Add user message to database
            db.add_message(
                st.session_state.current_session_id,
                "user",
                user_input
            )
            
            # Get agent response
            with st.spinner("🤔 Thinking..."):
                result = agent_query(user_input)
                
                # Add assistant message to database
                db.add_message(
                    st.session_state.current_session_id,
                    "assistant",
                    result.response
                )
            
            # Clear input and refresh
            st.session_state.user_input = ""
            st.experimental_rerun()
