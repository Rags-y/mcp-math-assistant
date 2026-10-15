
import asyncio
import json
import sys

import ollama
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

MODEL = "qwen2.5:3b"


async def main():
    # Start our existing MCP server as a subprocess.
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["server.py"],
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # Discover the tools provided by our MCP server.
            response = await session.list_tools()
            mcp_tools = response.tools

            print("Connected to MCP Math Assistant!")
            print("Available tools:", ", ".join(t.name for t in mcp_tools))
            print("Type 'exit' to quit.\n")

            # Convert MCP tool definitions into Ollama's tool format.
            ollama_tools = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description or tool.name,
                        "parameters": tool.inputSchema,
                    },
                }
                for tool in mcp_tools
            ]

            tool_names = {tool.name for tool in mcp_tools}

            while True:
                question = input("You: ").strip()

                if question.lower() in {"exit", "quit"}:
                    break

                if not question:
                    continue

                messages = [
                    {
                        "role": "system",
                        "content": (
                            "You are a helpful math assistant. "
                            "Use the available math tools to perform "
                            "calculations instead of calculating them yourself. "
                            "Explain the result clearly."
                        ),
                    },
                    {"role": "user", "content": question},
                ]

                try:
                    # Let Qwen decide whether to call a math tool.
                    for _ in range(5):
                        answer = ollama.chat(
                            model=MODEL,
                            messages=messages,
                            tools=ollama_tools,
                        )

                        messages.append(answer.message)
                        tool_calls = answer.message.tool_calls or []

                        if not tool_calls:
                            print(f"\nAssistant: {answer.message.content}\n")
                            break

                        # Execute each requested tool through MCP.
                        for call in tool_calls:
                            name = call.function.name
                            arguments = call.function.arguments

                            if name not in tool_names:
                                result_text = f"Unknown tool: {name}"
                            else:
                                result = await session.call_tool(
                                    name,
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

                            print(f"[MCP tool called: {name}]")
                            print(f"[Tool result: {result_text}]")

                            messages.append(
                                {
                                    "role": "tool",
                                    "tool_name": name,
                                    "content": result_text,
                                }
                            )
                    else:
                        print("Stopped after too many tool-calling rounds.")

                except Exception as error:
                    print(f"Error: {error}")
                    print(
                        "Check that Ollama is running and the model "
                        "qwen2.5:3b is installed."
                    )


if __name__ == "__main__":
    asyncio.run(main())
