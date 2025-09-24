import os
import requests
from dotenv import load_dotenv
from fastmcp import FastMCP

# ---------------- ENV ----------------
load_dotenv()
AIRBYTE_CLIENT_ID = os.getenv("AIRBYTE_CLIENT_ID")
AIRBYTE_CLIENT_SECRET = os.getenv("AIRBYTE_CLIENT_SECRET")

if AIRBYTE_CLIENT_ID is None or AIRBYTE_CLIENT_SECRET is None:
    raise ValueError("AIRBYTE_CLIENT_ID and AIRBYTE_CLIENT_SECRET must be set in environment variables.")

BASE_URL = "https://api.airbyte.com/v1"
HEADERS = {"accept": "application/json", "content-type": "application/json"}

PAYLOAD_TOKEN = {
    "client_id": AIRBYTE_CLIENT_ID,
    "client_secret": AIRBYTE_CLIENT_SECRET
}

# ---------------- INIT MCP ----------------
mcp = FastMCP("Airbyte MCP Server")

# ---------------- HELPERS ----------------
def get_access_token():
    url = f"{BASE_URL}/applications/token"
    resp = requests.post(url, json=PAYLOAD_TOKEN, headers=HEADERS)
    resp.raise_for_status()
    return resp.json().get("access_token")

def airbyte_get(endpoint: str):
    token = get_access_token()
    HEADERS["Authorization"] = f"Bearer {token}"
    resp = requests.get(f"{BASE_URL}{endpoint}", headers=HEADERS)
    resp.raise_for_status()
    return resp.json()

def airbyte_post(endpoint: str, payload: dict):
    token = get_access_token()
    HEADERS["Authorization"] = f"Bearer {token}"
    resp = requests.post(f"{BASE_URL}{endpoint}", json=payload, headers=HEADERS)
    resp.raise_for_status()
    return resp.json()

# ---------------- TOOLS ----------------
@mcp.tool()
def get_all_sources() -> dict:
    """List all Airbyte sources"""
    return airbyte_get("/sources")

@mcp.tool()
def get_info_source(source_id: str) -> dict:
    """Get info about a specific source"""
    return airbyte_get(f"/sources/{source_id}")

@mcp.tool()
def list_all_connections() -> dict:
    """List all Airbyte connections"""
    return airbyte_get("/connections")

@mcp.tool()
def get_connection_info(connection_id: str) -> dict:
    """Get info about a specific connection"""
    return airbyte_get(f"/connections/{connection_id}")

@mcp.tool()
def create_connection_blob(source_id: str, destination_id: str = "735f737a-118e-464b-b1bd-96dfafb5460b") -> dict:
    """Create connection from Blob storage to destination"""
    payload = {
        "sourceId": source_id,
        "destinationId": destination_id,
        "status": "active",
        "name": "azure_blob_to_snowflake_conn",
        "namespaceDefinition": "destination"
    }
    return airbyte_post("/connections", payload)

@mcp.tool()
def sync_job(connection_id: str) -> dict:
    """Trigger sync for a connection"""
    payload = {"jobType": "sync", "connectionId": connection_id}
    return airbyte_post("/jobs", payload)

# ---------------- RUN ----------------
if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)
