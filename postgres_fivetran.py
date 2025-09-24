import os
import psycopg2
import requests
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth
from fastmcp import FastMCP

# ─── Load environment variables ───────────────────────────────
load_dotenv()
FIVETRAN_API_KEY = os.getenv("FIVETRAN_API_KEY")
FIVETRAN_API_SECRET = os.getenv("FIVETRAN_API_SECRET")

if FIVETRAN_API_KEY is None or FIVETRAN_API_SECRET is None:
    raise ValueError("FIVETRAN_API_KEY and FIVETRAN_API_SECRET must be set in environment variables.")

# ─── Fivetran API setup ───────────────────────────────────────
BASE_URL = "https://api.fivetran.com/v1/connectors"
auth = HTTPBasicAuth(FIVETRAN_API_KEY, FIVETRAN_API_SECRET)
headers = {"Content-Type": "application/json; version=2"}

# ─── Init MCP server ─────────────────────────────────────────
mcp = FastMCP("My MCP Server")

# ---------------- TOOLS ----------------
# ─── Fivetran Tools ──────────────────────────────────────────
@mcp.tool()
def create_connection_for_postgress(connection_name, host, database):
    """
    Create a Fivetran PostgreSQL connector.

    This tool builds and sends a POST request to the Fivetran `/v1/connectors`
    endpoint using the provided PostgreSQL connection details.

    Args:
        connection_name (str): Friendly name for the connector, often used as `config.schema_prefix`.
        host (str): PostgreSQL host address (e.g., "db.company.com").
        port (int): Port number for the PostgreSQL instance (default: 5432).
        database (str): Name of the source database.


    Returns:
        str: Confirmation message including the created connector ID.
    """
    port = 5432 
    user = "Administratorpostgrssql" 
    password = "Welcome@123"
    payload = {
        "service": "azure_postgres",
        "group_id": "arched_seeming",
        "schema": "azure_postgres_test",
        "paused": False,
        "sync_frequency": 1440,
        "config": {
            "schema_prefix": connection_name,
            "destination_schema_naming": "FIVETRAN_NAMING",
            "host": host,
            "port": port,
            "database": database,
            "user": user,
            "password": password,
            "always_encrypted": True,
            "connection_type": "Directly",
            "auth_method": "PASSWORD",
            "update_method": "TELEPORT"
        }
    }
    response = requests.post(BASE_URL, json=payload, headers=headers, auth=auth)
    data = response.json()
    conn_id = data["data"]["id"]
    return f"Connector created successfully! ID: {conn_id}"


@mcp.tool()
def get_all_connections():
    """
    List all Fivetran connections in the account.

    Returns:
        list of tuples: Each tuple contains:
            - conn_name (dict): Connector schema name.
            - id (dict): Connector ID.
    """
    resp = requests.get(BASE_URL, auth=auth, headers=headers)
    pairs = [({"conn_name": item["schema"]}, {"id": item["id"]}) for item in resp.json()["data"]["items"]]
    return pairs


@mcp.tool()
def get_connector_info(connector_id: str) -> dict:
    """
    Retrieve metadata for a specific Fivetran connector.

    Args:
        connector_id (str): Unique ID of the connector (e.g., "postgres_abc123").

    Returns:
        dict: Full connector object as returned by Fivetran API (resp.json()["data"]).
    """
    url = f"{BASE_URL}/{connector_id}"
    resp = requests.get(url, auth=auth, headers=headers)
    resp.raise_for_status()
    return resp.json()["data"]


@mcp.tool()
def sync_connection(connector_id):
    """
    Trigger an immediate data sync for a Fivetran connector.

    This forces a sync for the specified connector without waiting for
    the next scheduled interval.

    Args:
        connector_id (str): Unique ID of the connector to sync.

    Returns:
        int: Status code from the Fivetran API indicating success or failure.
    """
    url = f"{BASE_URL}/{connector_id}/sync"
    payload = {"force": True}
    resp = requests.post(url, json=payload, headers=headers, auth=auth)
    return resp.json()["code"]

# ---------------- RUN ----------------
if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)
