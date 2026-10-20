# MCP Math Assistant

An AI-powered assistant that uses a local Qwen 2.5 3B model through Ollama and the Model Context Protocol (MCP) to perform calculations and interact with Google Sheets using natural-language instructions.

## Features

- Natural-language math questions
- Local LLM inference through Ollama
- MCP-based tool discovery and execution
- Seven math tools for common calculations
- Google Sheets integration for reading and updating quantities
- Streamlit chat interface with conversation history
- MCP tool-call logs displayed alongside assistant responses
- Division-by-zero error handling
- Missing-item protection for quantity updates
- Verification of successful Google Sheets writes

## Tech Stack

- Python
- Streamlit
- Ollama
- Qwen 2.5 3B
- Model Context Protocol (MCP)
- Google Sheets API
- Google OAuth 2.0

## Project Structure

```text
mcp-math-assistant/
├── app.py
├── client.py
├── server.py
├── check_mcp_tools.py
├── requirements.txt
├── .gitignore
├── README.md
├── credentials.json       # Local OAuth credentials; do not commit
├── token.json             # Local OAuth token; do not commit
└── .venv/                 # Virtual environment; do not commit
```

The OAuth files and virtual environment are shown for explanation only. They should remain excluded from version control.

## Prerequisites

- Python 3.10 or newer, compatible with the project's dependencies
- Ollama installed and running
- Git
- A Google account with access to the target spreadsheet
- A Google Cloud project with the Google Sheets API enabled
- OAuth client credentials for the Google Sheets integration

## Setup

### 1. Clone the repository

```powershell
git clone https://github.com/YOUR_USERNAME/mcp-math-assistant.git
cd mcp-math-assistant
```

Replace `YOUR_USERNAME` with the GitHub account that hosts the repository.

### 2. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Install and start Ollama

Download Ollama from [ollama.com](https://ollama.com/), then pull the configured model:

```powershell
ollama pull qwen2.5:3b
```

Make sure Ollama is running before launching the assistant.

### 5. Configure Google Sheets access

1. Open the [Google Cloud Console](https://console.cloud.google.com/).
2. Select or create a Google Cloud project.
3. Enable the Google Sheets API.
4. Configure the OAuth consent screen as required for your account and testing setup.
5. Create an OAuth client ID and download its client credentials.
6. Place the credentials file in the project root as `credentials.json`, following the naming expected by the implementation.
7. Complete the OAuth authorization flow required by the project to generate `token.json`.
8. Ensure the authorized Google account has access to the target spreadsheet.

The application is configured to use the spreadsheet ID supplied in its source code. If you use a different spreadsheet, update the configured ID deliberately and ensure the account is authorized to access it.

**Security:** Never commit `credentials.json` or `token.json`, share their contents publicly, or paste their secrets into issue trackers. Keep both files in `.gitignore`.

### 6. Run the application

```powershell
streamlit run app.py
```

Streamlit will provide a local URL, usually `http://localhost:8501`.

## Available MCP Tools

### Math tools

| Tool | Purpose |
|---|---|
| `add` | Adds two numbers |
| `subtract` | Subtracts one number from another |
| `multiply` | Multiplies two numbers |
| `divide` | Divides one number by another |
| `power` | Raises a base to an exponent |
| `square_root` | Calculates a non-negative square root |
| `modulo` | Returns the remainder |

### Google Sheets tools

| Tool | Purpose |
|---|---|
| `read_google_sheet` | Reads a specified spreadsheet range |
| `write_google_sheet_range` | Writes values to a specified range |
| `append_google_sheet_row` | Appends a row to a sheet |
| `increment_google_sheet_quantity` | Finds an existing item and adjusts its quantity |

The quantity increment tool checks for the requested item before writing. When the item is absent, it reports that the item was not found rather than creating a new item. Successful quantity updates are verified by reading the resulting value.

## Example Questions

### Math

- What is 25 multiplied by 16?
- Divide 144 by 12.
- What is the square root of 225?
- What is 2 raised to the power of 10?
- What is the remainder when 17 is divided by 5?

### Google Sheets

- What are the current quantities of all items in my Google Sheet?
- Increase the quantity of Apples by 2.
- Increase the quantity of Pineapples by 1, but do not add it if it doesn't exist.

**Note:** Spreadsheet update requests can change real data. Confirm the requested item and quantity before executing writes.

## Architecture

1. The user submits a natural-language question through Streamlit.
2. Ollama runs Qwen 2.5 3B to interpret the request.
3. The application discovers available MCP tools and provides the relevant tool definitions to the model.
4. The model selects a tool and supplies its arguments.
5. The MCP client communicates with the Python MCP server over standard input/output.
6. The server executes the selected math or Google Sheets operation.
7. The result is returned to the model, which generates a response for the chat interface.
8. The UI displays recorded MCP tool calls for responses that have logs.

## Validation and Testing

The following behaviors have been tested during development:

- Python syntax compilation for `app.py` and `server.py`
- Basic multiplication
- Division-by-zero error handling
- Reading Google Sheets data through MCP
- Incrementing an existing item and verifying the update
- Restoring a test quantity to its original value
- Rejecting a request to increment an item that does not exist
- Displaying populated MCP tool-call logs in the Streamlit UI

These checks demonstrate the tested behaviors; they do not constitute exhaustive testing of every tool or every failure condition.

## Troubleshooting

**Ollama connection or model errors**
- Confirm Ollama is installed and running.
- Verify the model is available with `ollama list`.
- Confirm the model name matches the one configured in `app.py`.

**Google Sheets authorization errors**
- Confirm the Google Sheets API is enabled.
- Verify the OAuth account has access to the spreadsheet.
- Reauthorize if the saved token is expired or has incompatible scopes.
- Keep OAuth credentials private.

**MCP tool errors**
- Confirm the server starts successfully.
- Run the project's MCP tool-check script if its dependencies and configuration are available.
- Inspect the tool-call logs and the server error message before retrying an operation.

## Future Improvements

Potential future work includes broader automated tests, clearer error reporting, and improved handling of ambiguous spreadsheet requests.

## Author
Raghav Kumar
