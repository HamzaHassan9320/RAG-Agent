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
import re
import json

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

class SimpleAgentResponse:
    def __init__(self, text: str, is_done: bool = True):
        self.text = text
        self.is_done = is_done

    def get_content(self):
        return self.text

class CustomReActOutputParser(ReActOutputParser):
    def parse(self, output: str, is_streaming: bool = False):
        try:
            # First, try to extract the tool output if present.
            # Look for a pattern like "Observation: {json}" or "Observation:\n{...}"
            obs_match = re.search(r"Observation:\s*(\{.*\})", output, re.DOTALL)
            if obs_match:
                # If we get JSON, try to load it
                try:
                    parsed_obs = json.loads(obs_match.group(1))
                    # If the parsed output has a 'response', return that.
                    if isinstance(parsed_obs, dict) and "response" in parsed_obs:
                        response_text = parsed_obs["response"]
                        return SimpleAgentResponse(response_text.strip())
                except json.JSONDecodeError:
                    # If it's not JSON, fallback to plain text extraction
                    obs_text = obs_match.group(1)
                    return SimpleAgentResponse(obs_text.strip())

            # If no "Observation:" is found, check for a final answer by splitting by "Final Answer:"
            final_match = re.search(r"Final Answer:\s*(.*)", output, re.DOTALL)
            if final_match:
                return SimpleAgentResponse(final_match.group(1).strip())

            # If nothing special is found, fallback to the default parser
            parsed = super().parse(output, is_streaming)
            if isinstance(parsed, dict) and "response" in parsed:
                resp = parsed["response"]
                if hasattr(resp, "text"):
                    final_text = resp.text.strip()
                    return SimpleAgentResponse(final_text)
                elif isinstance(resp, str):
                    return SimpleAgentResponse(resp.strip())
            if isinstance(parsed, str):
                return SimpleAgentResponse(parsed.strip())
            if hasattr(parsed, "get_content") and hasattr(parsed, "is_done"):
                return parsed
            return parsed

        except ValueError as e:
            if "Action: None" in output:
                final_text = output.split("Observation:")[1].strip() if "Observation:" in output else "No additional observations provided."
                return SimpleAgentResponse(final_text)
            raise e

code_llm = Ollama(model="llama3.2:3b-instruct-q6_K", request_timeout=1000, temperature=0)
agent = ReActAgent.from_tools(tools, llm=code_llm, verbose=True, output_parser=CustomReActOutputParser(), context=context, temperature=0)

# Optionally, wrap the agent query in a function for easy access:
def agent_query(prompt: str) -> dict:
    result = agent.query(prompt)
    return result


