import asyncio
from fastmcp import Client

client = Client("https://7d006c6da2ce.ngrok-free.app/mcp")

async def call_tool(name: str):
    async with client:
        result = await client.call_tool("greet", {"name": name})
        print(result)

asyncio.run(call_tool("Ford"))