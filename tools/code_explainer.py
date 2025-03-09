# tools/code_explainer.py

from llama_index.llms.ollama import Ollama

def explain_code(code_snippet: str) -> str:

    """ Uses an LLM to generate an explanation """

    llm = Ollama(model="llama3.2:3b-instruct-q6_K", request_timeout=500)
    prompt = f"Explain the following code snippet in simple terms: \n\n{code_snippet}"
    explanation =llm(prompt)
    return explanation