import os
import subprocess
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="Kimi CLI Service")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

WORKSPACE_ROOT = os.environ.get("WORKSPACE_ROOT", "/workspace")
API_KEY = os.environ.get("API_KEY", "kimi-service-secret-key-2024")

class CommandRequest(BaseModel):
    command: str
    user_id: str = "default"

class WorkspaceRequest(BaseModel):
    user_id: str
    repo_url: str = None

async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    """Verify API key from header"""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_api_key

@app.get("/health")
async def health_check():
    """Public health check endpoint"""
    return {
        "status": "healthy",
        "service": "kimi-cli",
        "version": "1.0.0"
    }

@app.post("/execute", dependencies=[Depends(verify_api_key)])
async def execute_command(request: CommandRequest):
    """Execute a command in the user's workspace (requires API key)"""
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

@app.post("/workspace/init", dependencies=[Depends(verify_api_key)])
async def init_workspace(request: WorkspaceRequest):
    """Initialize workspace and optionally clone a repo (requires API key)"""
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
    """List files in user's workspace (requires API key)"""
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

@app.post("/kimi/run", dependencies=[Depends(verify_api_key)])
async def run_kimi(request: CommandRequest):
    """Run kimi CLI command - installs it first if not present (requires API key)"""
    if not request.command or not request.command.strip():
        raise HTTPException(status_code=400, detail="Command is required")
    
    user_dir = os.path.join(WORKSPACE_ROOT, "users", request.user_id)
    os.makedirs(user_dir, exist_ok=True)
    
    # Check if kimi is installed, if not install it
    kimi_check = subprocess.run(
        "which kimi",
        shell=True,
        capture_output=True,
        text=True
    )
    
    if kimi_check.returncode != 0:
        # Try to install kimi
        try:
            install_result = subprocess.run(
                "curl -LsSf https://astral.sh/uv/install.sh | sh && export PATH=\"/root/.local/bin:$PATH\" && uv tool install kimi-cli",
                shell=True,
                capture_output=True,
                text=True,
                timeout=120
            )
            if install_result.returncode != 0:
                return {
                    "output": "",
                    "error": f"Failed to install kimi CLI:\n{install_result.stderr}",
                    "returncode": 1,
                    "user_id": request.user_id
                }
        except Exception as e:
            return {
                "output": "",
                "error": f"Error installing kimi: {str(e)}",
                "returncode": 1,
                "user_id": request.user_id
            }
    
    # Run kimi command
    try:
        result = subprocess.run(
            f"kimi {request.command}",
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
