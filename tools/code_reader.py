# tools/code_reader.py

from llama_index.core.tools import FunctionTool
from tools.code_explainer import explain_code
import os

def code_reader_func(file_name: str):
    path = os.path.join("data", file_name)
    try:
        with open(path, "r") as f:
            content = f.read()
            explanation = explain_code(content)
            return{"file_content": content, "explanation": explanation}
    except Exception as e:
        return{"error": str(e)}
    
code_reader = FunctionTool.from_defaults(
    fn= code_reader_func,
    name="CodeReader",
    description="Analyses Python code files, extracts relevant information, and provides an explanation."
)
