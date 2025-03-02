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
from tools.git_analyser import git_analyser_tool
from prompts import context, code_parser_template
from dotenv import load_dotenv

load_dotenv()

llm = Ollama(model="llama3.2:3b-instruct-q6_K", request_timeout=500)

parser = LlamaParse(result_type= "text")

file_extractor = {".pdf": parser}

documents = SimpleDirectoryReader("./data", file_extractor = file_extractor).load_data()

embed_model = resolve_embed_model("local:BAAI/bge-m3")

vector_index = VectorStoreIndex.from_documents(documents, embed_model=embed_model)

query_engine = vector_index.as_query_engine(llm=llm)

tools = [
    QueryEngineTool(
        query_engine=query_engine,
        metadata = ToolMetadata(
            name="ResumeReviewer",
            description="Provides general professional experience information."
        ),
    ),
    code_reader,
    git_analyser_tool,
]

from llama_index.core.agent.react.output_parser import ReActOutputParser

class CustomReActOutputParser(ReActOutputParser):
    def parse(self, output: str, is_streaming: bool = False):
        try:
            return super().parse(output, is_streaming)
        except ValueError as e:
            if "Action: None" in output:
                # Handle the case gracefully
                return {
                    "reasoning": "The agent concluded no action was needed.",
                    "response": output.split("Observation:")[1].strip() if "Observation:" in output else "No additional observations provided.",
                }
            raise e

code_llm = Ollama(model="llama3.2:3b-instruct-q6_K", request_timeout=500)
agent = ReActAgent.from_tools(tools, llm=code_llm, verbose=True,output_parser=CustomReActOutputParser(), context=context)

class CodeOutput(BaseModel):
    information: str
    description: str
    filename: str

parser = PydanticOutputParser(CodeOutput)
json_prompt_str = parser.format(code_parser_template)
json_prompt_tmpl = PromptTemplate(json_prompt_str)
output_pipeline = QueryPipeline(chain=[json_prompt_tmpl, llm])

while (prompt := input("Enter a prompt (q to quit): ")) != "q":
    result = agent.query(prompt)
    next_result = output_pipeline.run(response=result)
    cleaned_json = ast.literal_eval(str(next_result).replace("assistant:", ""))

    print("Output Generated")
    print(cleaned_json["information"])

    print("\n\nDescription:", cleaned_json["description"])

    filename =cleaned_json["filename"]

