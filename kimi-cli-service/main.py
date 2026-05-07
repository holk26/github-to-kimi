import os
import subprocess
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Kimi CLI Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

WORKSPACE_ROOT = os.environ.get("WORKSPACE_ROOT", "/workspace")

class CommandRequest(BaseModel):
    command: str
    user_id: str = "default"

class WorkspaceRequest(BaseModel):
    user_id: str
    repo_url: str = None

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "kimi-cli"}

@app.post("/execute")
async def execute_command(request: CommandRequest):
    if not request.command or not request.command.strip():
        raise HTTPException(status_code=400, detail="Command is required")
    
    user_dir = os.path.join(WORKSPACE_ROOT, "users", request.user_id)
    os.makedirs(user_dir, exist_ok=True)
    
    try:
        result = subprocess.run(
            request.command,
            shell=True,
            cwd=user_dir,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        return {
            "output": result.stdout,
            "error": result.stderr,
            "returncode": result.returncode,
            "user_id": request.user_id,
            "working_dir": user_dir
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Command timed out after 300 seconds")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/workspace/init")
async def init_workspace(request: WorkspaceRequest):
    user_dir = os.path.join(WORKSPACE_ROOT, "users", request.user_id)
    os.makedirs(user_dir, exist_ok=True)
    
    result_data = {
        "user_id": request.user_id,
        "workspace_dir": user_dir,
        "initialized": True
    }
    
    if request.repo_url:
        try:
            result = subprocess.run(
                f"git clone {request.repo_url} .",
                shell=True,
                cwd=user_dir,
                capture_output=True,
                text=True,
                timeout=120
            )
            result_data["clone_output"] = result.stdout
            result_data["clone_error"] = result.stderr
            result_data["clone_returncode"] = result.returncode
        except Exception as e:
            result_data["clone_error"] = str(e)
    
    return result_data

@app.get("/workspace/{user_id}/files")
async def list_files(user_id: str, path: str = ""):
    user_dir = os.path.join(WORKSPACE_ROOT, "users", user_id)
    target_dir = os.path.join(user_dir, path) if path else user_dir
    
    if not os.path.exists(target_dir):
        raise HTTPException(status_code=404, detail="Path not found")
    
    if not target_dir.startswith(user_dir):
        raise HTTPException(status_code=403, detail="Access denied")
    
    files = []
    try:
        for item in os.listdir(target_dir):
            item_path = os.path.join(target_dir, item)
            files.append({
                "name": item,
                "type": "directory" if os.path.isdir(item_path) else "file",
                "path": os.path.relpath(item_path, user_dir)
            })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    return {"files": files, "user_id": user_id, "current_path": path}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
