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
JIRA_API_TOKEN = os.getenv("CONFLUENCE_TOKEN")

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
    """Create a Jira issue in the given project"""
    url = f"{JIRA_BASE_URL}/rest/api/3/issue"
    payload = {
        "fields": {
            "project": {"key": project_key},
            "summary": summary,
            "issuetype": {"name": issue_type},
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": description}]
                    }
                ]
            }
        }
    }
    resp = httpx.post(url, json=payload, headers=AUTH_HEADER)
    if resp.status_code not in (200, 201):
        return {"error": resp.text}
    return resp.json()

@mcp.tool()
def search_issues_text(keyword: str, max_results: int = 10) -> list[dict]:
    """Search Jira issues by keyword in summary or description"""
    url = f"{JIRA_BASE_URL}/rest/api/3/search"
    jql = f'text ~ "{keyword}" ORDER BY created DESC'
    params = {"jql": jql, "maxResults": max_results}
    resp = httpx.get(url, headers=AUTH_HEADER, params=params)
    if resp.status_code != 200:
        return [{"error": resp.text}]
    
    issues = resp.json().get("issues", [])
    return [
        {
            "key": i["key"],
            "summary": i["fields"]["summary"],
            "status": i["fields"]["status"]["name"]
        }
        for i in issues
    ]

@mcp.tool()
def add_jira_comment(issue_key: str, comment: str) -> dict:
    """Add a comment to a Jira issue"""
    url = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}/comment"
    payload = {
        "body": {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": comment}]
                }
            ]
        }
    }
    resp = httpx.post(url, json=payload, headers=AUTH_HEADER)
    if resp.status_code not in (200, 201):
        return {"error": resp.text}
    return resp.json()

@mcp.tool()
def list_transitions_steps(issue_key: str) -> list[dict]:
    """
    List all possible transitions (statuses) for a Jira issue.
    Returns the transition name and its ID.
    """
    url = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}/transitions"
    resp = httpx.get(url, headers=AUTH_HEADER)
    if resp.status_code != 200:
        return [{"error": f"Failed to fetch transitions: {resp.text}"}]

    transitions = resp.json().get("transitions", [])
    return [{"id": t["id"], "name": t["name"]} for t in transitions]

@mcp.tool()
def transition_issue(issue_key: str, status: str) -> dict:
    """
    Transition a Jira issue to a new status (by name, e.g. 'In Progress', 'Done').
    """
    # 1. Get available transitions
    url = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}/transitions"
    resp = httpx.get(url, headers=AUTH_HEADER)
    if resp.status_code != 200:
        return {"error": f"Failed to fetch transitions: {resp.text}"}

    transitions = resp.json().get("transitions", [])
    if not transitions:
        return {"error": "No transitions available for this issue."}

    # 2. Find transition matching the desired status
    match = next((t for t in transitions if t["name"].lower() == status.lower()), None)
    if not match:
        return {
            "error": f"Status '{status}' not found. Available: {[t['name'] for t in transitions]}"
        }

    transition_id = match["id"]

    # 3. Perform the transition
    do_url = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}/transitions"
    do_resp = httpx.post(do_url, headers=AUTH_HEADER, json={"transition": {"id": transition_id}})
    if do_resp.status_code not in (200, 204):
        return {"error": f"Failed to transition: {do_resp.text}"}

    return {"success": True, "issue": issue_key, "new_status": status}


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
