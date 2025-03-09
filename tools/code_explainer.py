# tools/code_explainer.py

from llama_index.llms.ollama import Ollama

def explain_code(code_snippet: str) -> str:
    print("[DEBUG] Running explain_code with code snippet")
    
    llm = Ollama(model="llama3.2:3b-instruct-q6_K", request_timeout=500)
    prompt = f"Explain the following code snippet in simple terms: \n\n{code_snippet}"
    
    print("[DEBUG] Prompt sent to LLM")
    
    explanation = llm.complete(prompt)
    
    print("[DEBUG] Explanation returned from LLM")
    
    return explanation
