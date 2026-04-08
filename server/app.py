from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from .models import CRMAction, CRMObservation
from .env_logic import CRMEnvLogic
from dotenv import load_dotenv
import uvicorn
import os

# 1. Load environment variables
load_dotenv()

app = FastAPI(title="DataScan CRM OpenEnv", version="0.2.0")

# 2. Initialize environment logic
env = CRMEnvLogic()

@app.get("/")
@app.get("/health")
async def health():
    """Mandatory health check endpoint."""
    return {"status": "healthy", "service": "DataScan CRM OpenEnv"}

@app.get("/metadata")
async def get_metadata():
    """Mandatory metadata discovery endpoint."""
    return {
        "name": "datascan-crm-cleaner-v1",
        "description": "Professional-grade CRM cleaning environment with Regex-based rewards.",
        "version": "0.2.0",
        "author": "Aditya",
        "supported_tasks": ["task_easy_email", "task_medium_phone", "task_hard_duplicates"]
    }

@app.get("/schema")
async def get_schema():
    """Mandatory schema discovery endpoint."""
    return {
        "action": CRMAction.schema(),
        "observation": CRMObservation.schema(),
        "state": {"type": "object", "description": "Current database records"}
    }

@app.post("/mcp")
async def mcp_endpoint():
    """Placeholder for Model Context Protocol compliance."""
    return {
        "jsonrpc": "2.0",
        "result": {"status": "MCP interface active"}
    }

# --- VALIDATION ENDPOINTS ---
@app.get("/Dockerfile")
async def get_dockerfile():
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Dockerfile"))
    if os.path.exists(path):
        return FileResponse(path)
    raise HTTPException(status_code=404, detail="Dockerfile not found")

@app.get("/openenv.yaml")
async def get_config():
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "openenv.yaml"))
    if os.path.exists(path):
        return FileResponse(path)
    raise HTTPException(status_code=404, detail="openenv.yaml not found")
# ----------------------------

@app.post("/reset")
async def reset(task_id: str = "task_easy_email"):
    try:
        obs = env.reset_db(task_id=task_id)
        return {
            "observation": obs,
            "reward": 0.0,
            "done": False,
            "info": {"task_id": task_id}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reset Error: {str(e)}")

@app.post("/step")
async def step(action: CRMAction):
    try:
        obs, reward, done = env.step(action)
        return {
            "observation": obs,
            "reward": reward,
            "done": done,
            "info": {"step_count": env.current_step}
        }
    except Exception as e:
        return {
            "observation": env.get_observation(f"Error: {str(e)}"),
            "reward": -0.1,
            "done": False,
            "info": {"error": str(e)}
        }

@app.get("/state")
async def state():
    try:
        obs = env.get_observation("Current State Requested")
        return {"observation": obs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def main():
    uvicorn.run("server.app:app", host="0.0.0.0", port=7860, reload=False)

if __name__ == "__main__":
    main()