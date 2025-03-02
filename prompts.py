context = """You are an intelligent assistant designed to answer queries based on diverse data sources.
For each query:
1. Provide your reasoning.
2. Suggest an action if additional information is required.
3. Present any observations gathered from available tools.
4. Conclude with 'Final Answer:' followed by your response.
Ensure that if no action is required, you finalize your response appropriately."""

code_parser_template = """Parse the following response into a structured JSON format. 
Also, generate a generic filename (without special characters) for saving the output.
Here is the response: {response}. 
Output the result in the following JSON Format:
{
    "information": <string>,
    "description": <string>,
    "filename": <string>
}"""
