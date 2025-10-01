import os
import httpx
from fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()

# Create MCP Server
mcp = FastMCP("GitHub MCP Server")

# GitHub token
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}

BASE_URL = "https://api.github.com"

# ---------- Existing Tools (Repos, Issues, PRs) ----------

# @mcp.tool()
# def list_repos(username: str) -> list[str]:
#     """List public repositories for a GitHub user"""
#     url = f"{BASE_URL}/users/{username}/repos"
#     resp = httpx.get(url, headers=HEADERS)
#     if resp.status_code != 200:
#         return [f"❌ Error {resp.status_code}: {resp.text}"]

#     data = resp.json()
#     if not isinstance(data, list):
#         return [f"Unexpected response: {data}"]

#     return [repo.get("full_name", "unknown") for repo in data]

# @mcp.tool()
# def create_issue(owner: str, repo: str, title: str, body: str) -> dict:
#     """Create an issue in a GitHub repo"""
#     url = f"{BASE_URL}/repos/{owner}/{repo}/issues"
#     payload = {"title": title, "body": body}
#     resp = httpx.post(url, json=payload, headers=HEADERS)
#     if resp.status_code not in (200, 201):
#         return {"error": resp.text}
#     return resp.json()

# @mcp.tool()
# def list_issues(owner: str, repo: str, state: str = "open") -> list[dict]:
#     """List issues in a GitHub repo (default: open)"""
#     url = f"{BASE_URL}/repos/{owner}/{repo}/issues?state={state}"
#     resp = httpx.get(url, headers=HEADERS)
#     if resp.status_code != 200:
#         return [{"error": resp.text}]
#     return [{"number": i["number"], "title": i["title"], "state": i["state"]} for i in resp.json()]

# @mcp.tool()
# def close_issue(owner: str, repo: str, issue_number: int) -> dict:
#     """Close an issue by number"""
#     url = f"{BASE_URL}/repos/{owner}/{repo}/issues/{issue_number}"
#     resp = httpx.patch(url, json={"state": "closed"}, headers=HEADERS)
#     if resp.status_code != 200:
#         return {"error": resp.text}
#     return resp.json()

# @mcp.tool()
# def repo_details(owner: str, repo: str) -> dict:
#     """Get details about a GitHub repo"""
#     url = f"{BASE_URL}/repos/{owner}/{repo}"
#     resp = httpx.get(url, headers=HEADERS)
#     if resp.status_code != 200:
#         return {"error": resp.text}
#     data = resp.json()
#     return {
#         "full_name": data.get("full_name"),
#         "description": data.get("description"),
#         "stars": data.get("stargazers_count"),
#         "forks": data.get("forks_count"),
#         "watchers": data.get("watchers_count"),
#         "language": data.get("language"),
#         "url": data.get("html_url"),
#     }

# @mcp.tool()
# def search_repos(query: str, sort: str = "stars", order: str = "desc") -> list[dict]:
#     """Search repositories by keyword"""
#     url = f"{BASE_URL}/search/repositories?q={query}&sort={sort}&order={order}"
#     resp = httpx.get(url, headers=HEADERS)
#     if resp.status_code != 200:
#         return [{"error": resp.text}]
#     items = resp.json().get("items", [])
#     return [{"full_name": r["full_name"], "stars": r["stargazers_count"], "url": r["html_url"]} for r in items]

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

# ---------- Run Server ----------

if __name__ == "__main__":
    if not GITHUB_TOKEN:
        raise RuntimeError("Set GITHUB_TOKEN environment variable.")
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)
