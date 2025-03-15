# tools/code_quality.py

import subprocess
from llama_index.core.tools import FunctionTool
import os 

def run_pylint(file_path: str) -> str:
    try:
        result=subprocess.run(["pylint", file_path], capture_output=True, text=True)
        return result.stdout
    except Exception as e:
        return f"Error running pylint: {str(e)}"
    
def code_quality_tool_func(file_name: str):
    path = os.path.join("data", file_name)
    report = run_pylint(path)
    return {"pylint_report": report}

code_quality_tool = FunctionTool.from_defaults(
    fn=code_quality_tool_func,
    name="CodeQualityTool",
    description="Runs pylint analysis on a given python file and returns the code quality report."
)