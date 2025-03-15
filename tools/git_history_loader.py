import os
from git import Repo
import shutil
import stat
from datetime import datetime
from llama_index.core.schema import TextNode

def get_commit_history(repo_path: str, branch: str = "master", limit: int = 1000):
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
        node = CommitTextNode(
            text=content,
            metadata={
                "commit_hash": commit['commit_hash'],
                "author": commit['author'],
                "__start_date": commit_datetime.isoformat(),
                "__end_date": commit_datetime.isoformat()
            },
            id_=commit['commit_hash']
        )
        nodes.append(node)
    return nodes

def clone_repo(repo_url: str, clone_path: str = "./temp_repo"):
    if os.path.exists(clone_path):
        make_writable(clone_path)
        shutil.rmtree(clone_path)
    Repo.clone_from(repo_url, clone_path)
    return clone_path

def make_writable(path):
    for root, dirs, files in os.walk(path):
        for name in files:
            full_path = os.path.join(root, name)
            os.chmod(full_path, stat.S_IWRITE)

class CommitTextNode(TextNode):
    def get_doc_id(self):
        return self.id_
