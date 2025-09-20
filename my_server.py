import os
import requests
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth
from fastmcp import FastMCP

# Load env vars
load_dotenv()

FIVETRAN_API_KEY = os.getenv("FIVETRAN_API_KEY")
FIVETRAN_API_SECRET = os.getenv("FIVETRAN_API_SECRET")

if FIVETRAN_API_KEY is None or FIVETRAN_API_SECRET is None:
    raise ValueError("FIVETRAN_API_KEY and FIVETRAN_API_SECRET must be set in environment variables.")

BASE_URL = "https://api.fivetran.com/v1/connectors"
auth = HTTPBasicAuth(FIVETRAN_API_KEY, FIVETRAN_API_SECRET)
headers = {"Content-Type": "application/json; version=2"}

# Init MCP
mcp = FastMCP("My MCP Server")

# ---------------- TOOLS ----------------
@mcp.tool()
def greet(name: str) -> str:
    """Simple greeting tool"""
    return f"Hello, {name}! Welcome to FastMCP."


@mcp.tool()
def get_connector_info(connector_id: str) -> dict:
    """
    Retrieve metadata and status for a given Fivetran connector.
    """
    url = f"{BASE_URL}/{connector_id}"
    resp = requests.get(url, auth=auth, headers=headers)
    print(resp.text)  # debug log
    resp.raise_for_status()
    return resp.json()["data"]

# ---------------- RUN ----------------
if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)
