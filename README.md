# MCP Math Assistant

An AI-powered math assistant that uses a local Qwen 2.5 3B model through Ollama and the Model Context Protocol (MCP) to perform calculations with dedicated Python tools.

## Features

- Natural-language math questions
- Local language model using Ollama
- MCP-based tool integration
- Seven math tools: addition, subtraction, multiplication, division, powers, square roots, and modulo
- Interactive Streamlit chat interface
- Basic conversation history

## Tech Stack

- Python
- Model Context Protocol (MCP)
- Ollama
- Qwen 2.5 3B
- Streamlit

## Project Structure

```text
mcp-math-assistant/
+-- app.py
+-- client.py
+-- server.py
+-- requirements.txt
+-- .gitignore
+-- README.md
```

## Prerequisites

- Python 3.10 or newer
- Ollama installed
- Git (for version control)

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/mcp-math-assistant.git
cd mcp-math-assistant
```

Replace `YOUR_USERNAME` with your GitHub username.

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Download the model

```powershell
ollama pull qwen2.5:3b
```

Ensure Ollama is running before launching the application.

### 5. Run the Streamlit application

```powershell
streamlit run app.py
```

The application will open in your browser.

## Available MCP Tools

| Tool | Purpose |
|---|---|
| `add` | Adds two numbers |
| `subtract` | Subtracts one number from another |
| `multiply` | Multiplies two numbers |
| `divide` | Divides one number by another |
| `power` | Raises a base to an exponent |
| `square_root` | Calculates a non-negative square root |
| `modulo` | Returns the remainder |

## Example Questions

- What is 25 multiplied by 16?
- Divide 144 by 12.
- What is the square root of 225?
- What is 2 raised to the power of 10?
- What is the remainder when 17 is divided by 5?

## Architecture

1. The user asks a question in the Streamlit interface.
2. Ollama runs Qwen 2.5 3B to interpret the request.
3. The model requests an appropriate MCP math tool.
4. The MCP client calls the Python tool exposed by the server.
5. The tool result is returned to the model.
6. The assistant presents the result in the chat interface.

## Notes

- The language model runs locally through Ollama.
- The project uses MCP to separate tool definitions from the AI client.
- Model performance and tool selection depend on the local model and runtime.

## Author
Raghav Kumar
