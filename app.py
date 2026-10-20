SPREADSHEET_ID = "1YVjl26DOXL7CM6Oe3PGxzlmjF79kGASUQVqfv3UfTSs"
import asyncio
import json
import sys
from pathlib import Path

import ollama
import streamlit as st
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


MODEL = "qwen2.5:3b"
PROJECT_DIR = Path(__file__).resolve().parent
MAX_TOOL_ROUNDS = 8

SYSTEM_PROMPT = """
You are MCP Math Assistant, an assistant that can use math tools
and Google Sheets tools.

GENERAL RULES
- Use MCP tools for calculations and spreadsheet operations.
- Never claim that an operation succeeded unless the tool confirms it.
- If a tool returns an error, explain the error or retry with corrected
  arguments. Never pretend a failed operation succeeded.
- Use the exact tool names and argument schemas provided.
- Do not invent spreadsheet contents or tool results.

GOOGLE SHEETS RULES
- read_google_sheet reads data. Inspect its returned values before editing.
- write_google_sheet_range updates an existing range and can overwrite
  the cells in that range.
- append_google_sheet_row appends a new row.
- For values_json, supply a JSON string containing an array of row arrays.
  Examples:
  A single cell containing 15: [[15]]
  A row containing an item and quantity: [["Mangoes", 20]]
- Never send an empty array such as [] when writing a value.
- When changing a quantity, first read the sheet, find the exact item,
  calculate the new quantity using the math tools, and identify the
  correct cell address.
- Update only the required quantity cell. Do not overwrite the full table.
- After writing, read the updated cell to verify the stored value.
- Report success only when the write succeeds and the follow-up read
  confirms the expected value.
- If the write fails, do not claim the spreadsheet was changed.
- The configured spreadsheet uses the tab named Sheet1.
- For reading all item names and quantities, use range_name="A:B".
- Never invent a range or tab name such as ItemQuantities.
- Use the exact configured spreadsheet ID supplied by the application.
- If a tool call fails, report the error and do not invent spreadsheet contents.

When the user requests an operation on a spreadsheet, complete the
operation using the tools instead of merely describing what you would do.
"""


st.set_page_config(
    page_title="MCP Math Assistant",
    page_icon="🧮",
    layout="centered",
)

st.title("🧮 MCP Math Assistant")
st.caption(
    "Ask a question. Qwen can use MCP math tools and Google Sheets."
)

if "messages" not in st.session_state:
    st.session_state.messages = []

if "tool_logs" not in st.session_state:
    st.session_state.tool_logs = {}


async def ask_assistant(chat_history):
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["server.py"],
        cwd=str(PROJECT_DIR),
    )

    logs = []

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            tool_response = await session.list_tools()
            available_tools = tool_response.tools

            ollama_tools = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description or tool.name,
                        "parameters": tool.inputSchema,
                    },
                }
                for tool in available_tools
            ]

            allowed_tools = {tool.name for tool in available_tools}

            model_messages = [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                *chat_history,
            ]

            for round_number in range(MAX_TOOL_ROUNDS):
                response = ollama.chat(
                    model=MODEL,
                    messages=model_messages,
                    tools=ollama_tools,
                )

                assistant_message = response.message
                tool_calls = assistant_message.tool_calls or []

                if not tool_calls:
                    return assistant_message.content or "", logs

                # Keep the assistant's tool-call message in the history.
                model_messages.append(assistant_message)

                for call in tool_calls:
                    tool_name = call.function.name
                    arguments = call.function.arguments or {}

                    if not isinstance(arguments, dict):
                        result_text = (
                            "Tool error: arguments must be a JSON object. "
                            "Retry with the correct argument structure."
                        )
                        logs.append(f"{tool_name}: {result_text}")

                    elif tool_name not in allowed_tools:
                        result_text = (
                            f"Tool error: unknown tool '{tool_name}'. "
                            "Use only the available MCP tools."
                        )
                        logs.append(f"{tool_name}: {result_text}")

                   
                    else:
                        # Always use the configured spreadsheet ID for
                        # Google Sheets tools.
                        google_sheets_tools = {
                            "read_google_sheet",
                            "write_google_sheet_range",
                            "append_google_sheet_row",
                            "increment_google_sheet_quantity",
                        }
                        if tool_name == "read_google_sheet":
                            range_name = arguments.get("range_name", "A:B")
                            if range_name == "ItemQuantities":
                                arguments["range_name"] = "A:B"

                        if tool_name in google_sheets_tools:
                            arguments["spreadsheet_id"] = SPREADSHEET_ID

                        # Validate write arguments before calling the server.
                        validation_error = None

                        if tool_name == "write_google_sheet_range":
                            raw_values = arguments.get("values_json")

                            try:
                                parsed_values = json.loads(raw_values)
                                if (
                                    not isinstance(parsed_values, list)
                                    or not parsed_values
                                    or any(
                                        not isinstance(row, list)
                                        for row in parsed_values
                                    )
                                ):
                                    raise ValueError(
                                        "values_json must be a non-empty "
                                        "JSON array of row arrays, e.g. [[15]]."
                                    )
                            except (
                                TypeError,
                                json.JSONDecodeError,
                                ValueError,
                            ):
                                validation_error = (
                                    "Invalid values_json. Provide a non-empty "
                                    "JSON array of row arrays. For a single "
                                    "cell containing 15, use the string "
                                    '\'[[15]]\'. Do not use []. Retry with '
                                    "the intended value."
                                )

                        if validation_error:
                            result_text = f"Tool error: {validation_error}"
                            logs.append(
                                f"{tool_name}({arguments}) -> {result_text}"
                            )
                        else:
                            try:
                                result = await session.call_tool(
                                    tool_name,
                                    arguments=arguments,
                                )

                                result_parts = []
                                for block in result.content or []:
                                    if hasattr(block, "text"):
                                        result_parts.append(block.text)
                                    else:
                                        result_parts.append(str(block))

                                result_text = "\n".join(result_parts)

                                if result.isError:
                                    result_text = (
                                        f"Tool error: {result_text}. "
                                        "Correct the arguments or report "
                                        "the failure; do not claim success."
                                    )

                                logs.append(
                                    f"{tool_name}({arguments}) -> {result_text}"
                                )

                            except Exception as exc:
                                result_text = (
                                    f"Tool error: {type(exc).__name__}: {exc}. "
                                    "Check the arguments and retry if possible."
                                )
                                logs.append(
                                    f"{tool_name}({arguments}) -> {result_text}"
                                )

                    # Return tool results to the model so it can decide
                    # whether to retry, continue, or report the error.
                    model_messages.append(
                        {
                            "role": "tool",
                            "tool_name": tool_name,
                            "content": result_text,
                        }
                    )

            return (
                "I couldn't complete the request within the tool-call limit. "
                "Check the MCP tool calls before assuming any spreadsheet "
                "changes were saved.",
                logs,
            )


# Display conversation history.
for index, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        if message["role"] == "assistant":
            logs = st.session_state.tool_logs.get(index, [])

            if logs:
                with st.expander("View MCP tool calls"):
                    for log in logs:
                        st.code(log, language="text")



# Use one chat input only.
if prompt := st.chat_input("Ask a math or Google Sheets question"):
    st.session_state.messages.append(
        {"role": "user", "content": prompt}
    )

    history = [
        {
            "role": message["role"],
            "content": message["content"],
        }
        for message in st.session_state.messages
        if message["role"] in ("user", "assistant")
    ]

    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        with st.spinner("Thinking and using MCP tools..."):
            answer, logs = asyncio.run(ask_assistant(history))

        assistant_index = len(st.session_state.messages)
        st.session_state.messages.append(
            {"role": "assistant", "content": answer}
        )
        st.session_state.tool_logs[assistant_index] = logs

    except Exception as exc:
        error_message = (
            "Something went wrong while processing your question. "
            "Check that Ollama is running and the MCP server starts correctly."
        )
        st.session_state.messages.append(
            {"role": "assistant", "content": error_message}
        )
        st.session_state.tool_logs[
            len(st.session_state.messages) - 1
        ] = [f"{type(exc).__name__}: {exc}"]

    st.rerun()
