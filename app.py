
import asyncio
import sys
from pathlib import Path

import ollama
import streamlit as st
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


MODEL = "qwen2.5:3b"
PROJECT_DIR = Path(__file__).resolve().parent

st.set_page_config(
    page_title="MCP Math Assistant",
    page_icon="🧮",
    layout="centered",
)

st.title("🧮 MCP Math Assistant")
st.caption("Ask a question. Qwen can use your MCP math tools to calculate the answer.")

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
                    "content": (
                        "You are a helpful math assistant. "
                        "Use the available MCP math tools for calculations. "
                        "Do not calculate arithmetic yourself when a tool "
                        "is available. Explain results clearly."
                    ),
                },
                *chat_history,
            ]

            for _ in range(5):
                response = ollama.chat(
                    model=MODEL,
                    messages=model_messages,
                    tools=ollama_tools,
                )

                assistant_message = response.message
                tool_calls = assistant_message.tool_calls or []

                if not tool_calls:
                    return assistant_message.content, logs

                model_messages.append(assistant_message)

                for call in tool_calls:
                    tool_name = call.function.name
                    arguments = call.function.arguments

                    if tool_name not in allowed_tools:
                        result_text = f"Unknown tool: {tool_name}"
                        logs.append(f"{tool_name}: {result_text}")
                    else:
                        result = await session.call_tool(
                            tool_name,
                            arguments=arguments,
                        )

                        result_text = "\n".join(
                            block.text
                            if hasattr(block, "text")
                            else str(block)
                            for block in result.content
                        )

                        if result.isError:
                            result_text = f"Tool error: {result_text}"

                        logs.append(
                            f"{tool_name}({arguments}) → {result_text}"
                        )

                    model_messages.append(
                        {
                            "role": "tool",
                            "tool_name": tool_name,
                            "content": result_text,
                        }
                    )

            return "I couldn't finish the calculation in time. Please try again.", logs


# Display previous messages.
for index, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        logs = st.session_state.tool_logs.get(index, [])
        if logs:
            with st.expander("View MCP tool calls"):
                for log in logs:
                    st.code(log, language="text")


# Accept a new question.
question = st.chat_input("Try: What is 25 multiplied by 16?")

if question:
    st.session_state.messages.append(
        {"role": "user", "content": question}
    )

    with st.chat_message("user"):
        st.markdown(question)

    history = [
        {"role": message["role"], "content": message["content"]}
        for message in st.session_state.messages
        if message["role"] in ("user", "assistant")
    ]

    

if prompt := st.chat_input("Ask a question"):
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    # Build conversation history for the model
    history = [
        {"role": message["role"], "content": message["content"]}
        for message in st.session_state.messages
        if message["role"] in ("user", "assistant")
    ]

    try:
        with st.spinner("Thinking..."):
            answer, logs = asyncio.run(ask_assistant(history))

        assistant_index = len(st.session_state.messages)
        st.session_state.messages.append({
            "role": "assistant",
            "content": answer
        })
        st.session_state.tool_logs[assistant_index] = logs

    except Exception as e:
        st.error(
            "Something went wrong while processing your question. "
            "Check that Ollama is running and the model is available."
        )
        st.caption(f"Error details: {e}")

    st.rerun()