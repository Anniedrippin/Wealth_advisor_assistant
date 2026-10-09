import json
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

app = FastAPI(title="Mock CRM Service", version="1.0.0")

DATA_FILE = Path(__file__).parent / "data" / "clients.json"


def load_clients():
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "mock_crm"}


@app.get("/mock-crm/clients/{client_id}")
def get_client_profile(client_id: str):
    clients = load_clients()
    if client_id in clients:
        return clients[client_id]
    raise HTTPException(status_code=404, detail=f"Client '{client_id}' not found in CRM database.")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
