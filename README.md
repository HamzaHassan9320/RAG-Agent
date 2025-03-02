# RAG-Agent: A Retrieval-Augmented Generation Agent Using LlamaIndex

**RAG-Agent** is a modular, extensible retrieval-augmented generation (RAG) system built with [LlamaIndex](https://github.com/jerryjliu/llama_index). It integrates multiple tools—including a code reader and a Git commit analyzer with time-aware retrieval—to help answer queries by supplementing LLM responses with domain-specific and time-based context.

## Features

- **Multi-Source Data Ingestion:**  
  Ingests documents (PDFs, code files) from a local directory using custom file extractors.

- **Git Commit Analysis:**  
  Uses GitPython to load commit history from a specified Git repository, converts commits into indexed nodes with metadata, and supports time-aware retrieval.

- **ReAct Agent Integration:**  
  Combines LlamaIndex with a ReAct agent to process queries, perform reasoning, and invoke the appropriate tools automatically.

- **Flexible Tooling:**  
  Easily add or modify tools. The current implementation includes:
  - **Code Reader:** Analyzes Python source files.
  - **Git Analyzer:** Queries Git commit history based on time filters.

## Installation

This project uses [Poetry](https://python-poetry.org/) for dependency management.

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/your-username/rag-agent.git
   cd rag-agent
