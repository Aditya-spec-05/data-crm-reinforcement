from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from models import CRMAction, CRMObservation
from env_logic import CRMEnvLogic
from dotenv import load_dotenv
import uvicorn
import os

# 1. Load environment variables from .env file
load_dotenv()

app = FastAPI(title="DataScan CRM OpenEnv")

# 2. Initialize the environment logic
# env_logic will now check for DATABASE_URL automatically
env = CRMEnvLogic()

@app.get("/")
async def root():
    """Health check endpoint for Hugging Face."""
    return {"status": "healthy", "service": "DataScan CRM OpenEnv"}

# --- VALIDATION ENDPOINTS ---
# These allow the OpenEnv validator to verify your configuration files
@app.get("/Dockerfile")
async def get_dockerfile():
    """Serves the Dockerfile for validation purposes."""
    if os.path.exists("Dockerfile"):
        return FileResponse("Dockerfile")
    raise HTTPException(status_code=404, detail="Dockerfile not found")

@app.get("/openenv.yaml")
async def get_config():
    """Serves the openenv.yaml for validation purposes."""
    if os.path.exists("openenv.yaml"):
        return FileResponse("openenv.yaml")
    raise HTTPException(status_code=404, detail="openenv.yaml not found")
# ----------------------------

@app.post("/reset")
async def reset(task_id: str = "task_easy_email"):
    """Resets the database and prepares a specific task."""
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
    """Processes an AI agent action and updates the DB."""
    try:
        obs, reward, done = env.step(action)
        return {
            "observation": obs,
            "reward": reward,
            "done": done,
            "info": {"step_count": env.current_step}
        }
    except Exception as e:
        # Returning error in 'info' allows the agent to self-correct
        return {
            "observation": env.get_observation(f"Error: {str(e)}"),
            "reward": -0.1,
            "done": False,
            "info": {"error": str(e)}
        }

@app.get("/state")
async def state():
    """Returns the current state of all records in the DB."""
    try:
        obs = env.get_observation("Current State Requested")
        return {"observation": obs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Port 7860 is mandatory for Hugging Face Spaces
    # host 0.0.0.0 is required to be accessible outside the container
    uvicorn.run(app, host="0.0.0.0", port=7860)