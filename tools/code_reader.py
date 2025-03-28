# tools/code_reader.py

from llama_index.core.tools import FunctionTool
from llama_index.core import Document, VectorStoreIndex
from llama_index.core.embeddings import resolve_embed_model
from llama_index.llms.ollama import Ollama
from tools.code_explainer import explain_code
import os

class CodeVectorStore:
    def __init__(self):
        self.embed_model = resolve_embed_model("local:BAAI/bge-m3")
        self.llm = Ollama(model="llama3.2:3b-instruct-q6_K", request_timeout=500)
        self.vector_stores = {}  # Map of filename -> VectorStoreIndex
        
    def process_file(self, file_path: str):
        """Creates vector embeddings for code file content"""
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Split code into meaningful chunks (functions, classes, etc.)
        chunks = self._split_code_into_chunks(content)
        
        documents = []
        for chunk in chunks:
            doc = Document(
                text=chunk,
                metadata={
                    "file": file_path,
                    "type": "code_chunk"
                }
            )
            documents.append(doc)
            
        self.vector_stores[file_path] = VectorStoreIndex.from_documents(
            documents,
            embed_model=self.embed_model
        )
        
        return content
        
    def _split_code_into_chunks(self, content: str):
        """Split code into logical chunks (functions, classes, blocks)"""
        # Simple splitting by double newlines for now
        # Could be improved with proper code parsing
        chunks = [chunk.strip() for chunk in content.split("\n\n") if chunk.strip()]
        return chunks
        
    def query_code(self, file_path: str, query: str):
        """Query the vector store for relevant code sections"""
        if file_path not in self.vector_stores:
            return None
            
        vector_store = self.vector_stores[file_path]
        query_engine = vector_store.as_query_engine(llm=self.llm)
        response = query_engine.query(query)
        
        return response.response

# Global vector store instance
code_vector_store = CodeVectorStore()

def code_reader_func(file_name: str, query: str = None):
    path = os.path.join("data", file_name)
    try:
        # Process file and get content
        content = code_vector_store.process_file(path)
        
        # If there's a specific query, use vector search
        if query:
            explanation = code_vector_store.query_code(path, query)
        else:
            # Otherwise use general explanation
            explanation = explain_code(content)
            
        return {
            "file_content": content,
            "explanation": explanation
        }
    except Exception as e:
        return {"error": str(e)}
    
code_reader = FunctionTool.from_defaults(
    fn=code_reader_func,
    name="CodeReader",
    description=(
        "Analyzes Python code files using vector embeddings for semantic search. "
        "Can answer specific questions about code or provide general explanations. "
        "Example query: 'How does the error handling work in this code?'"
    )
)
