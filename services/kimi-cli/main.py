import os
import subprocess
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="Kimi CLI Service", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

WORKSPACE_ROOT = os.environ.get("WORKSPACE_ROOT", "/workspace")
API_KEY = os.environ.get("KIMI_SERVICE_API_KEY", "kimi-service-secret-key-2024")
KIMI_WEB_URL = os.environ.get("KIMI_WEB_URL", "https://kimi-cli.x.moonsbow.com")

class CommandRequest(BaseModel):
    command: str
    user_id: str = "default"
    cwd: Optional[str] = None

class WorkspaceRequest(BaseModel):
    user_id: str
    repo_url: Optional[str] = None
    repo_name: Optional[str] = None

class KimiWebRequest(BaseModel):
    repoUrl: str
    repoName: str
    userId: str = "default"

async def verify_api_key(x_api_key: str = Header(None, alias="X-API-Key")):
    if not x_api_key or x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return x_api_key

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "kimi-cli", "version": "1.1.0"}

@app.post("/execute", dependencies=[Depends(verify_api_key)])
async def execute_command(request: CommandRequest):
    if not request.command or not request.command.strip():
        raise HTTPException(status_code=400, detail="Command is required")
    
    user_dir = os.path.join(WORKSPACE_ROOT, "users", request.user_id)
    os.makedirs(user_dir, exist_ok=True)
    
    cwd = request.cwd if request.cwd else user_dir
    # Security: prevent escaping workspace
    if not cwd.startswith(WORKSPACE_ROOT):
        cwd = user_dir
    
    try:
        result = subprocess.run(
            request.command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        return {
            "output": result.stdout,
            "error": result.stderr,
            "returncode": result.returncode,
            "user_id": request.user_id,
            "working_dir": cwd
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Command timed out after 300 seconds")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/workspace/init", dependencies=[Depends(verify_api_key)])
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

@app.get("/workspace/{user_id}/files", dependencies=[Depends(verify_api_key)])
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

@app.post("/kimi-web/open", dependencies=[Depends(verify_api_key)])
async def kimi_web_open(request: KimiWebRequest):
    """Open a repository in Kimi web workspace and return the public URL."""
    user_dir = os.path.join(WORKSPACE_ROOT, "users", request.userId)
    os.makedirs(user_dir, exist_ok=True)
    
    # Clone the repo if not already cloned
    if request.repoUrl:
        try:
            result = subprocess.run(
                f"git clone {request.repoUrl} .",
                shell=True,
                cwd=user_dir,
                capture_output=True,
                text=True,
                timeout=120
            )
            clone_output = result.stdout
            clone_error = result.stderr
            clone_returncode = result.returncode
        except Exception as e:
            clone_error = str(e)
            clone_returncode = -1
    
    # Return the public URL for accessing this workspace
    public_url = f"{KIMI_WEB_URL}/terminal?repo={request.repoName}&user={request.userId}"
    
    return {
        "success": True,
        "url": public_url,
        "user_id": request.userId,
        "repo_name": request.repoName,
        "workspace_dir": user_dir,
        "clone_output": clone_output if 'clone_output' in dir() else None,
        "clone_error": clone_error if 'clone_error' in dir() else None,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
