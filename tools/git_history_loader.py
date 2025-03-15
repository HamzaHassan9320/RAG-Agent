# tools/git_history_loader.py

import os
from git import Repo
import shutil
import stat
from datetime import datetime

def extract_commit_history(repo_path: str, branch: str = "master", limit: int = 100):
    """
    Extract commit history from a Git repository, including diffs.
    Returns a list of dictionaries with commit hash, author, date, message, and diff.
    """
    if not os.path.exists(repo_path):
        raise FileNotFoundError("Repository not found at: " + repo_path)
    
    repo = Repo(repo_path)
    if branch is None:
        branch = get_default_branch(repo)
    commits = list(repo.iter_commits(branch, max_count=limit))
    commit_docs = []
    for commit in commits:
        commit_date = datetime.fromtimestamp(commit.committed_date).isoformat()
        # Extract diff if possible (compare to first parent)
        if commit.parents:
            diff_items = commit.diff(commit.parents[0], create_patch=True)
            diff_text = "\n".join([item.diff.decode("utf-8", errors="ignore") for item in diff_items])
        else:
            diff_text = "Initial commit - no diff available."
        
        commit_docs.append({
            "commit_hash": commit.hexsha,
            "author": commit.author.name,
            "date": commit_date,
            "message": commit.message.strip(),
            "diff": diff_text
        })
    return commit_docs

def clone_repo(repo_url: str, clone_path: str = "./temp_repo"):
    """
    Clone the repository from the given URL to a local path.
    """
    if os.path.exists(clone_path):
        make_writable(clone_path)
        shutil.rmtree(clone_path)
    Repo.clone_from(repo_url, clone_path)
    return clone_path

def make_writable(path):
    """
    Recursively change file permissions to writable.
    """
    import os, stat
    for root, dirs, files in os.walk(path):
        for name in files:
            full_path = os.path.join(root, name)
            os.chmod(full_path, stat.S_IWRITE)

def get_default_branch(repo):
    try:
        return repo.active_branch.name
    except TypeError:
        # Fallback if in a detached HEAD state:
        return repo.git.symbolic_ref("HEAD").split('/')[-1]