
import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["server.py"],
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.list_tools()

            names = [tool.name for tool in result.tools]
            print(f"Tool count from live MCP server: {len(names)}")
            for name in names:
                print("-", name)


if __name__ == "__main__":
    asyncio.run(main())
