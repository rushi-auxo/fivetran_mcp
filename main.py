import os
import requests
from requests.auth import _basic_auth_str
from fastapi import FastAPI # type: ignore
from pydantic import BaseModel
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

# Load env vars from .env file
load_dotenv()
# FastAPI app
app = FastAPI()

# Load API credentials from env vars
FIVETRAN_API_KEY = os.getenv("FIVETRAN_API_KEY")
FIVETRAN_API_SECRET = os.getenv("FIVETRAN_API_SECRET")

# if FIVETRAN_API_KEY is None or FIVETRAN_API_SECRET is None:
#     raise ValueError("FIVETRAN_API_KEY and FIVETRAN_API_SECRET environment variables must be set.")

headers = {
    "Authorization": f"Basic {_basic_auth_str(FIVETRAN_API_KEY, FIVETRAN_API_SECRET)}", # type: ignore
    "Content-Type": "application/json"
}

# Request model
class SyncRequest(BaseModel):
    id: str

# @app.post("/sync_connection")
# def sync_connection(req: SyncRequest):
#     """Sync a Fivetran connection by ID"""
#     # Unpause connector
#     connector_url = f"https://api.fivetran.com/v1/connectors/{req.id}"
#     requests.patch(connector_url, json={"paused": False}, headers=headers)

#     # Force sync
#     sync_url = f"https://api.fivetran.com/v1/connectors/{req.id}/force"
#     response = requests.post(sync_url, headers=headers)

#     return response.json()

@app.get("/get_info/{connector_id}")
def get_connector_info(connector_id: str) -> dict:
    """
    Retrieve metadata and status for a given connector.
    """
    print(f"Getting info for connector ID: {connector_id}")
    print(FIVETRAN_API_KEY, FIVETRAN_API_SECRET)
    BASE_URL = "https://api.fivetran.com/v1/connections"
    auth     = HTTPBasicAuth(FIVETRAN_API_KEY, FIVETRAN_API_SECRET) # type: ignore
    headers  = {"Content-Type": "application/json; version=2"}
 
    url = f"{BASE_URL}/{connector_id}"
    resp = requests.get(url, auth=auth, headers=headers)
    print(resp.text)
    resp.raise_for_status()
    return resp.json()["data"]
 

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}