# tools/git_analyser.py

from datetime import datetime
from llama_index.llms.ollama import Ollama
from llama_index.core.tools import FunctionTool
from tools.git_history_loader import extract_commit_history, clone_repo

def aggregate_commits(commit_docs):
    """
    Aggregate commit information into a single formatted string.
    """
    aggregated = ""
    for commit in commit_docs:
        aggregated += (
            f"Commit Hash: {commit['commit_hash']}\n"
            f"Author: {commit['author']}\n"
            f"Date: {commit['date']}\n"
            f"Message: {commit['message']}\n"
            f"Diff:\n{commit['diff']}\n"
            f"{'-'*50}\n"
        )
    return aggregated

def git_query(query: str, start_date: str = None, end_date: str = None, branch: str = None,
              limit: int = 100, repo_url: str = None):
    """
    Instead of building a vector index, this function extracts commit history,
    aggregates it, and uses an LLM to provide a summary explanation of the commits.
    """
    # If a repository URL is provided, clone it.
    if repo_url and repo_url.strip():
        print(f"Repository URL provided: {repo_url}")
        repo_path = clone_repo(repo_url, "./temp_repo")
        print(f"Cloned repository to: {repo_path}")
    
    # Extract commit history (including diffs)
    commit_docs = extract_commit_history(repo_path, branch, limit)
    
    # Filter commits by start_date and end_date if provided
    if start_date or end_date:
        filtered_docs = []
        for commit in commit_docs:
            commit_date = datetime.fromisoformat(commit['date'])
            if start_date:
                start = datetime.fromisoformat(start_date)
                if commit_date < start:
                    continue
            if end_date:
                end = datetime.fromisoformat(end_date)
                if commit_date > end:
                    continue
            filtered_docs.append(commit)
        commit_docs = filtered_docs

    # Aggregate the commit details into one text block
    aggregated_text = aggregate_commits(commit_docs)
    
    # Create an LLM prompt that asks for a summary explanation of the commit history
    prompt = (
        f"You are an assistant that summarizes git commit history and explains the code changes.\n"
        f"Query: {query}\n\n"
        f"Commit History:\n{aggregated_text}\n\n"
        "Provide a clear, concise summary and commentary on these commits. **Note:** Commits that are dated earlier will be the first commits so go in a sequential structure from oldest to latest."
    )
    
    # Initialize the LLM (ensure it's configured to your provider)
    llm = Ollama(model="llama3.2:3b-instruct-q6_K", request_timeout=500)
    summary = llm.complete(prompt)
    return {"response": summary.text.strip()}

# Wrap as a FunctionTool for the agent
git_analyser_tool = FunctionTool.from_defaults(
    fn=git_query,
    name="GitAnalyser",
    description=(
        "Analyzes Git commit history and provides a summary explanation of the changes. "
        "Example query: 'Summarize commits in the past 6 months.' "
        "Optional: Provide start and end dates in ISO format, or a repository URL."
    )
)
