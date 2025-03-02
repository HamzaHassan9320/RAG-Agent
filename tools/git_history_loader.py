import os
from git import Repo
from datetime import datetime
from llama_index.core.schema import TextNode

def get_commit_history(repo_path: str, branch: str = "master", limit: int = 100):
    """
    Fetch commit history from a Git repository.
    Returns a list of commit dictionaries with commit hash, author, date, and message.
    """
    if not os.path.exists(repo_path):
        raise FileNotFoundError("Repository not found at: " + repo_path)
    
    repo = Repo(repo_path)
    commits = list(repo.iter_commits(branch, max_count=limit))
    commit_docs = []
    for commit in commits:
        commit_date = datetime.fromtimestamp(commit.committed_date).isoformat()
        commit_doc = {
            "commit_hash": commit.hexsha,
            "author": commit.author.name,
            "date": commit_date,
            "message": commit.message.strip()
        }
        commit_docs.append(commit_doc)
    return commit_docs

def create_commit_nodes(commit_docs):
    """
    Convert commit dictionaries into LlamaIndex TextNodes.
    Each node includes time-based metadata for filtering.
    """
    nodes = []
    for commit in commit_docs:
        content = (f"Commit {commit['commit_hash']} by {commit['author']} on {commit['date']}:\n"
                   f"{commit['message']}")
        commit_datetime = datetime.fromisoformat(commit['date'])
        node = TextNode(
            text=content,
            metadata={
                "commit_hash": commit['commit_hash'],
                "author": commit['author'],
                "__start_date": commit_datetime.isoformat(),
                "__end_date": commit_datetime.isoformat()
            }
        )
        nodes.append(node)
    return nodes
