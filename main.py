import os
import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

# Load env vars from .env
load_dotenv()

FIVETRAN_API_KEY = os.getenv("FIVETRAN_API_KEY")
FIVETRAN_API_SECRET = os.getenv("FIVETRAN_API_SECRET")

if not FIVETRAN_API_KEY or not FIVETRAN_API_SECRET:
    raise RuntimeError("FIVETRAN_API_KEY and FIVETRAN_API_SECRET must be set in the environment variables.")

BASE_URL = "https://api.fivetran.com/v1"
auth = HTTPBasicAuth(FIVETRAN_API_KEY, FIVETRAN_API_SECRET)
BASE_HEADERS = {"Content-Type": "application/json"}

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Server running!"}


# ---------------- MCP ENDPOINT ----------------
@app.get("/mcp")
def mcp_handler(id: str, action: str):
    """
    Usage:
    /mcp?id=<connector_id>&action=get_info
    /mcp?id=<connector_id>&action=sync_connection
    """
    try:
        if action == "get_info":
            url = f"{BASE_URL}/connectors/{id}"
            resp = requests.get(url, auth=auth, headers=BASE_HEADERS)
            return resp.json()

        elif action == "sync_connection":
            url = f"{BASE_URL}/connectors/{id}/force"
            resp = requests.post(url, auth=auth, headers=BASE_HEADERS)
            return resp.json()

        else:
            return {"error": "Invalid action. Use get_info or sync_connection."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------- SSE ENDPOINT ----------------
@app.get("/sse")
def sse_endpoint():
    """
    Very simple Server-Sent Events endpoint
    Streams 'Hello World' every second.
    """

    def event_stream():
        yield "data: Hello World\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
