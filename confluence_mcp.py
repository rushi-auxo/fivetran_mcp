import os
import requests
from fastmcp import FastMCP
from dotenv import load_dotenv
import datetime
import httpx
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

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}

BASE_URL = "https://api.github.com"

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

# ---------- PR Tools ----------

@mcp.tool()
def list_pull_requests(owner: str, repo: str, state: str = "open") -> list[dict]:
    """List pull requests in a repo (default: open)"""
    url = f"{BASE_URL}/repos/{owner}/{repo}/pulls?state={state}"
    resp = httpx.get(url, headers=HEADERS)
    if resp.status_code != 200:
        return [{"error": resp.text}]
    return [{"number": pr["number"], "title": pr["title"], "state": pr["state"], "user": pr["user"]["login"]}
            for pr in resp.json()]

@mcp.tool()
def create_pull_request(owner: str, repo: str, title: str, head: str, base: str, body: str = "") -> dict:
    """
    Create a pull request.
    - head: the branch where your changes are (feature-branch)
    - base: the branch you want to merge into (e.g., main)
    """
    url = f"{BASE_URL}/repos/{owner}/{repo}/pulls"
    payload = {"title": title, "head": head, "base": base, "body": body}
    resp = httpx.post(url, json=payload, headers=HEADERS)
    if resp.status_code not in (200, 201):
        return {"error": resp.text}
    return resp.json()

# ---------- NEW: PR Review & Comment Tools ----------

@mcp.tool()
def comment_on_pull_request(owner: str, repo: str, pr_number: int, body: str) -> dict:
    """Add a comment to a pull request"""
    url = f"{BASE_URL}/repos/{owner}/{repo}/issues/{pr_number}/comments"
    resp = httpx.post(url, json={"body": body}, headers=HEADERS)
    if resp.status_code not in (200, 201):
        return {"error": resp.text}
    return resp.json()

@mcp.tool()
def review_pull_request(owner: str, repo: str, pr_number: int, body: str, event: str = "COMMENT") -> dict:
    """
    Review a pull request.
    event can be: COMMENT, APPROVE, REQUEST_CHANGES
    """
    url = f"{BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
    payload = {"body": body, "event": event}
    resp = httpx.post(url, json=payload, headers=HEADERS)
    if resp.status_code not in (200, 201):
        return {"error": resp.text}
    return resp.json()

# ---------- Resource ----------

@mcp.resource("github://{username}")
def get_user_profile(username: str) -> dict:
    """Fetch a GitHub user profile"""
    url = f"{BASE_URL}/users/{username}"
    resp = httpx.get(url, headers=HEADERS)
    if resp.status_code != 200:
        return {"error": resp.text}
    return resp.json()


# ==========================
# Run MCP
# ==========================
if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)
