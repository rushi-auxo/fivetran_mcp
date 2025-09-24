import os
import httpx
from fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()

# Create MCP Server
mcp = FastMCP("Jira MCP Server")

# Jira credentials
JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")

if not all([JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN]):
    raise RuntimeError("Set JIRA_BASE_URL, JIRA_EMAIL, and JIRA_API_TOKEN environment variables.")

if not all([JIRA_EMAIL, JIRA_API_TOKEN]):
    raise RuntimeError("JIRA_EMAIL and JIRA_API_TOKEN must be set and not None.")

import base64

basic_auth = httpx.BasicAuth(str(JIRA_EMAIL), str(JIRA_API_TOKEN))
auth_value = base64.b64encode(f"{JIRA_EMAIL}:{JIRA_API_TOKEN}".encode()).decode()

AUTH_HEADER = {
    "Authorization": f"Basic {auth_value}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# ---------- Issue Tools ----------

@mcp.tool()
def create_jira_issue(project_key: str, summary: str, description: str, issue_type: str = "Task") -> dict:
    """Create a Jira issue"""
    url = f"{JIRA_BASE_URL}/rest/api/3/issue"
    payload = {
        "fields": {
            "project": {"key": project_key},
            "summary": summary,
            "description": description,
            "issuetype": {"name": issue_type}
        }
    }
    resp = httpx.post(url, headers=AUTH_HEADER, json=payload)
    if resp.status_code not in (200, 201):
        return {"error": resp.text}
    return resp.json()

@mcp.tool()
def search_issues(jql: str) -> list[dict]:
    """Search Jira issues using JQL"""
    url = f"{JIRA_BASE_URL}/rest/api/3/search"
    params = {"jql": jql}
    resp = httpx.get(url, headers=AUTH_HEADER, params=params)
    if resp.status_code != 200:
        return [{"error": resp.text}]
    return resp.json().get("issues", [])

@mcp.tool()
def add_comment(issue_key: str, comment: str) -> dict:
    """Add a comment to a Jira issue"""
    url = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}/comment"
    resp = httpx.post(url, headers=AUTH_HEADER, json={"body": comment})
    if resp.status_code not in (200, 201):
        return {"error": resp.text}
    return resp.json()

@mcp.tool()
def transition_issue(issue_key: str, transition_id: str) -> dict:
    """Transition a Jira issue to a new status"""
    url = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}/transitions"
    resp = httpx.post(url, headers=AUTH_HEADER, json={"transition": {"id": transition_id}})
    if resp.status_code not in (200, 204):
        return {"error": resp.text}
    return {"success": True}

@mcp.tool()
def assign_issue(issue_key: str, assignee: str) -> dict:
    """Assign a Jira issue to a user"""
    url = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}/assignee"
    resp = httpx.put(url, headers=AUTH_HEADER, json={"accountId": assignee})
    if resp.status_code not in (200, 204):
        return {"error": resp.text}
    return {"success": True}

# ---------- Resource ----------

@mcp.resource("jira://{issue_key}")
def get_jira_issue(issue_key: str) -> dict:
    """Fetch a Jira issue"""
    url = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}"
    resp = httpx.get(url, headers=AUTH_HEADER)
    if resp.status_code != 200:
        return {"error": resp.text}
    return resp.json()

# ---------- Run Server ----------

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)
