# app.py

import streamlit as st
from tools.code_reader import code_reader_func
from tools.git_analyser import git_query

st.title("RAG-Agent Interactive Dashboard")

st.sidebar.header("Options")
mode = st.sidebar.selectbox("Select mode", ["Code Analysis", "Git Analysis"])


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
        st.write(result.get("explanation", "No explanation available"))

elif mode == "Git Analysis":
    st.header("Git Commit Analysis")
    repo_path = st.text_input("Enter repository path", "./my_repo") 
    query = st.text_input("Enter your query", "Summarise latest commits")
    start_date= st.text_input("Start date (ISO format)", "")
    end_date = st.text_input("End date (ISO format)", "")
    if st.button("Run Analysis"):
        result = git_query(query, start_date, end_date, repo_path = repo_path)
        st.write(result.get("response", "No response."))

