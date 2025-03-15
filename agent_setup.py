# agent_setup.py
from llama_index.llms.ollama import Ollama
from llama_parse import LlamaParse
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, PromptTemplate
from llama_index.core.embeddings import resolve_embed_model
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.core.agent import ReActAgent
from pydantic import BaseModel
from llama_index.core.output_parsers import PydanticOutputParser
from llama_index.core.query_pipeline import QueryPipeline
import ast
from tools.code_reader import code_reader
from tools.code_quality import code_quality_tool
from tools.git_analyser import git_analyser_tool
from tools.extractors import extract_docx, extract_html, extract_markdown
from prompts import context, code_parser_template
from dotenv import load_dotenv

load_dotenv()

llm = Ollama(model="llama3.2:3b-instruct-q6_K", request_timeout=500)
pdf_parser = LlamaParse(result_type= "text")

file_extractor = {
    ".pdf": pdf_parser,
    ".docx": lambda file: LlamaParse(result_type="text").parse(extract_docx(file)),
    ".html": lambda file: LlamaParse(result_type="text").parse(extract_html(file)),
    ".md": lambda file: LlamaParse(result_type="text").parse(extract_markdown(file))
}

documents = SimpleDirectoryReader("./data", file_extractor=file_extractor).load_data()
embed_model = resolve_embed_model("local:BAAI/bge-m3")
vector_index = VectorStoreIndex.from_documents(documents, embed_model=embed_model)
query_engine = vector_index.as_query_engine(llm=llm)

tools = [
    QueryEngineTool(
        query_engine=query_engine,
        metadata=ToolMetadata(
            name="ResumeReviewer",
            description="Provides general professional experience information."
        ),
    ),
    code_reader,
    git_analyser_tool,
    code_quality_tool,
]

from llama_index.core.agent.react.output_parser import ReActOutputParser

class CustomReActOutputParser(ReActOutputParser):
    def parse(self, output: str, is_streaming: bool = False):
        try:
            return super().parse(output, is_streaming)
        except ValueError as e:
            if "Action: None" in output:
                return {
                    "reasoning": "The agent concluded no action was needed.",
                    "response": output.split("Observation:")[1].strip() if "Observation:" in output else "No additional observations provided.",
                }
            raise e

code_llm = Ollama(model="llama3.2:3b-instruct-q6_K", request_timeout=500)
agent = ReActAgent.from_tools(tools, llm=code_llm, verbose=True, output_parser=CustomReActOutputParser(), context=context)

# Optionally, wrap the agent query in a function for easy access:
def agent_query(prompt: str) -> dict:
    result = agent.query(prompt)
    # Optionally run further processing or query pipeline steps...
    return result
