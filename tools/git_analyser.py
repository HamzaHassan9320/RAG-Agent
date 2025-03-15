# tools/git_analyzer.py
from llama_index.core.embeddings import resolve_embed_model
from llama_index.core import VectorStoreIndex
from llama_index.core.tools import FunctionTool

from tools.git_history_loader import get_commit_history, create_commit_nodes, clone_repo

def create_git_commit_index(repo_path: str, branch: str = "master", limit: int = 100, embed_model_str="local:BAAI/bge-m3"):
    """
    Loads the Git commit history, converts it to nodes, and builds a vector index.
    """
    commit_docs = get_commit_history(repo_path, branch, limit)
    nodes = create_commit_nodes(commit_docs)
    embed_model = resolve_embed_model(embed_model_str)
    git_index = VectorStoreIndex.from_documents(nodes, embed_model=embed_model)
    return git_index

def git_query(query: str, start_date: str = None, end_date: str = None, repo_path: str = "./my_repo", branch: str = "master", limit: int = 100, repo_url: str=None):
    """
    Query the Git commit index with optional time filters.
    This function builds the index on the fly (or you can persist it) and then runs a query.
    """
    if repo_url:
        repo_path = clone_repo(repo_url, "./temp_repo")
    # Build the Git commit index from your repository
    git_index = create_git_commit_index(repo_path, branch, limit)
    
    # Build a metadata filter dictionary
    metadata_filter = {}
    if start_date:
        metadata_filter["__start_date"] = {"$gte": start_date}
    if end_date:
        metadata_filter["__end_date"] = {"$lte": end_date}
    
    # Create a query engine that can use the metadata filters
    query_engine = git_index.as_query_engine(metadata_filter=metadata_filter)
    result = query_engine.query(query)
    return {"response": str(result)}

# Wrap as a FunctionTool for the agent
git_analyser_tool = FunctionTool.from_defaults(
    fn=git_query,
    name="GitAnalyser",
    description=(
        "Analyzes Git commit history with time filters. "
        "Query examples: 'Summarize commits in the past 6 months.' "
        "Provide start and end dates in ISO format if needed."
    )
)
