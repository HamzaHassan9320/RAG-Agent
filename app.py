# app.py
import streamlit as st
from tools.code_reader import code_reader_func
from tools.git_analyser import git_query
from agent_setup import agent_query 
from dotenv import load_dotenv

load_dotenv()

st.title("RAG-Agent Interactive Dashboard")

st.sidebar.header("Options")
mode = st.sidebar.selectbox("Select mode", ["Code Analysis", "Git Analysis", "Agent Query"])

if mode == "Code Analysis":
    st.header("Upload a Code File")
    uploaded_file = st.file_uploader("Choose a Python file", type=['py'])
    if uploaded_file:
        with open("data/temp_code.py", "wb") as f:
            f.write(uploaded_file.getbuffer())
        result = code_reader_func("temp_code.py")
        st.subheader("File Content")
        st.code(result.get("file_content", ""))
        st.subheader("Explanation")
        explanation = result.get("explanation", "No explanation provided.")
        st.write(explanation)

elif mode == "Git Analysis":
    st.header("Git Commit Analysis")
    repo_path = st.text_input("Enter repository path", "./my_repo") 
    query = st.text_input("Enter your query", "Summarise latest commits")
    start_date = st.text_input("Start date (ISO format)", "")
    end_date = st.text_input("End date (ISO format)", "")
    repo_url = st.text_input("Or enter repository URL", "")
    branch = st.text_input("Enter branch (optional)", "")
    if st.button("Run Analysis"):
        result = git_query(query, start_date, end_date, branch=branch, repo_url=repo_url)
        st.write(result.get("response", "No response."))

elif mode == "Agent Query":
    st.header("Agent Query")
    user_prompt = st.text_area("Enter your query for the agent", "What are the key improvements in the latest commits?")
    if st.button("Submit Query"):
        result = agent_query(user_prompt)
        agent_answer = result.response  
        st.write("Agent Response:")
        st.write(agent_answer)
