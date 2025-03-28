# tools/git_analyser.py

from datetime import datetime
from llama_index.llms.ollama import Ollama
from llama_index.core.tools import FunctionTool
from llama_index.core import Document, VectorStoreIndex
from llama_index.core.embeddings import resolve_embed_model
from tools.git_history_loader import extract_commit_history, clone_repo
import os

class GitCommitVectorStore:
    def __init__(self):
        self.embed_model = resolve_embed_model("local:BAAI/bge-m3")
        self.llm = Ollama(model="llama3.2:3b-instruct-q6_K", request_timeout=500)
        self.vector_stores = {}  # Map of repo_url -> VectorStoreIndex
        
    def process_repo(self, repo_url: str, branch: str = None, limit: int = 100):
        """
        Creates or updates vector embeddings for a repository's commits
        """
        # Clone repo if needed
        repo_path = clone_repo(repo_url, "./temp_repo")
        
        # Extract commit history
        commit_docs = extract_commit_history(repo_path, branch, limit)
        
        # Convert commits to Documents for vector store
        documents = []
        for commit in commit_docs:
            # Create rich metadata for better retrieval
            metadata = {
                "commit_hash": commit["commit_hash"],
                "author": commit["author"],
                "date": commit["date"],
                "type": "git_commit"
            }
            
            # Combine commit info into a searchable text
            text = f"""
            Commit: {commit['commit_hash']}
            Author: {commit['author']}
            Date: {commit['date']}
            Message: {commit['message']}
            
            Changes:
            {commit['diff']}
            """
            
            doc = Document(text=text, metadata=metadata)
            documents.append(doc)
        
        # Create or update vector store for this repo
        self.vector_stores[repo_url] = VectorStoreIndex.from_documents(
            documents,
            embed_model=self.embed_model
        )
        
    def query_commits(self, repo_url: str, query: str, start_date: str = None, end_date: str = None):
        """
        Query the vector store for relevant commits
        """
        if repo_url not in self.vector_stores:
            self.process_repo(repo_url)
            
        vector_store = self.vector_stores[repo_url]
        
        # Create metadata filters for date range if specified
        metadata_filters = {}
        if start_date or end_date:
            date_filter = {}
            if start_date:
                date_filter["$gte"] = start_date
            if end_date:
                date_filter["$lte"] = end_date
            metadata_filters["date"] = date_filter
            
        # Query the vector store with local LLM
        query_engine = vector_store.as_query_engine(
            metadata_filters=metadata_filters if metadata_filters else None,
            llm=self.llm
        )
        response = query_engine.query(query)
        
        return response.response

# Global vector store instance
git_vector_store = GitCommitVectorStore()

def git_query(query: str, start_date: str = None, end_date: str = None, branch: str = None,
              limit: int = 100, repo_url: str = None):
    """
    Query git commit history using vector embeddings for more accurate retrieval
    """
    if not repo_url:
        return {"response": "Please provide a repository URL"}
        
    try:
        response = git_vector_store.query_commits(
            repo_url=repo_url,
            query=query,
            start_date=start_date,
            end_date=end_date
        )
        return {"response": response}
    except Exception as e:
        return {"response": f"Error analyzing repository: {str(e)}"}

# Wrap as a FunctionTool for the agent
git_analyser_tool = FunctionTool.from_defaults(
    fn=git_query,
    name="GitAnalyser",
    description=(
        "Analyzes Git commit history using vector embeddings for semantic search. "
        "Example query: 'Find commits related to performance improvements' "
        "Required: Provide repository URL. Optional: Provide start and end dates in ISO format."
    )
)
