import os
import requests
from fastmcp import FastMCP
from dotenv import load_dotenv
import datetime
# Load env vars
load_dotenv()
# ==========================
# Confluence Setup
# ==========================
CONFLUENCE_BASE_URL = os.getenv("CONFLUENCE_BASE_URL")  # e.g. https://your-domain.atlassian.net/wiki
CONFLUENCE_USER = os.getenv("CONFLUENCE_USER")          # your Atlassian email
CONFLUENCE_TOKEN = os.getenv("CONFLUENCE_TOKEN")        # API token
SPACE_KEY = os.getenv("CONFLUENCE_SPACE_KEY") 

if not (CONFLUENCE_BASE_URL and CONFLUENCE_USER and CONFLUENCE_TOKEN):
    raise ValueError("Missing Confluence environment variables. "
                     "Please set CONFLUENCE_BASE_URL, CONFLUENCE_USER, and CONFLUENCE_TOKEN.")

auth: tuple[str, str] = (CONFLUENCE_USER, CONFLUENCE_TOKEN)
headers = {"Content-Type": "application/json"}

mcp = FastMCP("Confluence MCP")

# ==========================
# Tools
# ==========================

@mcp.tool()
def summarize_page(page_id: str) -> str:
    """Fetch and summarize a Confluence page by ID."""
    url = f"{CONFLUENCE_BASE_URL}/rest/api/content/{page_id}?expand=body.storage"
    resp = requests.get(url, auth=auth, headers=headers)
    resp.raise_for_status()
    content = resp.json()["body"]["storage"]["value"]

    # Simple summarization (truncate). Swap with LLM if desired.
    summary = content[:500] + "..." if len(content) > 500 else content
    return f"Summary of page {page_id}: {summary}"


@mcp.tool()
def create_page(body: str) -> dict:
    """
    Create a new Confluence page in the given space.
    - title auto-generated as current date + time
    - body can be any string (conversation, JSON, etc.)
    """
    if not SPACE_KEY:
        raise ValueError("Missing CONFLUENCE_SPACE_KEY in environment variables")

    # auto-generate title with timestamp
    title = f"Conversation - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    url = f"{CONFLUENCE_BASE_URL}/rest/api/content"
    payload = {
        "type": "page",
        "title": title,
        "space": {"key": SPACE_KEY},
        "body": {
            "storage": {
                "value": str(body),   # ensure any type gets stored as text
                "representation": "storage"
            }
        }
    }

    resp = requests.post(url, auth=auth, headers=headers, json=payload)
    resp.raise_for_status()
    return resp.json()

@mcp.tool()
def navigate_spaces(limit: int = 10) -> list:
    """List spaces available in Confluence."""
    url = f"{CONFLUENCE_BASE_URL}/rest/api/space?limit={limit}"
    resp = requests.get(url, auth=auth, headers=headers)
    resp.raise_for_status()
    spaces = resp.json().get("results", [])
    return [{"key": s["key"], "name": s["name"]} for s in spaces]


# ==========================
# Run MCP
# ==========================
if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)
