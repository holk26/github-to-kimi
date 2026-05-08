import os
import subprocess
from fastapi import FastAPI, HTTPException, Header, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="Kimi CLI Service", version="1.1.0")

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
KIMI_WEB_PORT = int(os.environ.get("KIMI_WEB_PORT", "5494"))
KIMI_WEB_PUBLIC_URL = os.environ.get("KIMI_WEB_PUBLIC_URL", "https://kimi-cli.x.moonsbow.com")

class CommandRequest(BaseModel):
    command: str
    user_id: str = "default"

class WorkspaceRequest(BaseModel):
    user_id: str
    repo_url: Optional[str] = None

class KimiWebRequest(BaseModel):
    userId: str
    repoUrl: str
    repoName: str

class KimiWebRequestLegacy(BaseModel):
    user_id: str
    repo_url: str
    repo_name: str

async def verify_api_key(x_api_key: Optional[str] = Header(None, alias="X-API-Key")):
    """Verify API key from header"""
    if not x_api_key or x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return x_api_key

@app.get("/health")
async def health_check():
    """Public health check endpoint"""
    return {
        "status": "healthy",
        "service": "kimi-cli",
        "version": "1.1.0"
    }

@app.post("/workspace/init", dependencies=[Depends(verify_api_key)])
async def init_workspace(request: WorkspaceRequest):
    """Initialize workspace and optionally clone a repo"""
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

@app.post("/kimi-web/open", dependencies=[Depends(verify_api_key)])
async def open_kimi_web(request: Request):
    """Open Kimi Web UI with the specified project - accepts both camelCase and snake_case"""
    body = await request.json()
    
    # Support both camelCase (from frontend) and snake_case (legacy)
    user_id = body.get("userId") or body.get("user_id", "default")
    repo_url = body.get("repoUrl") or body.get("repo_url", "")
    repo_name = body.get("repoName") or body.get("repo_name", "")
    
    if not repo_url or not repo_name:
        raise HTTPException(status_code=400, detail="repoUrl/repo_url and repoName/repo_name are required")
    
    user_dir = os.path.join(WORKSPACE_ROOT, "users", user_id)
    project_dir = os.path.join(user_dir, repo_name)
    
    # Ensure workspace exists
    os.makedirs(user_dir, exist_ok=True)
    
    # Clone repo if not exists
    if not os.path.exists(project_dir):
        try:
            result = subprocess.run(
                f"git clone {repo_url} {repo_name}",
                shell=True,
                cwd=user_dir,
                capture_output=True,
                text=True,
                timeout=120
            )
            if result.returncode != 0:
                return {
                    "error": f"Failed to clone: {result.stderr}",
                    "returncode": result.returncode
                }
        except Exception as e:
            return {"error": str(e)}
    
    # Return the public URL for the terminal with the repo
    kimi_web_url = f"{KIMI_WEB_PUBLIC_URL}/terminal?repo={repo_name}&user={user_id}"
    
    return {
        "success": True,
        "url": kimi_web_url,
        "kimi_web_url": kimi_web_url,
        "project_dir": project_dir,
        "repo_name": repo_name,
        "user_id": user_id,
        "message": "Project ready for Kimi Web"
    }

@app.post("/kimi-web/start", dependencies=[Depends(verify_api_key)])
async def start_kimi_web(request: CommandRequest):
    """Start Kimi Web server for the user"""
    user_dir = os.path.join(WORKSPACE_ROOT, "users", request.user_id)
    os.makedirs(user_dir, exist_ok=True)
    
    # Check if kimi is installed
    kimi_check = subprocess.run(
        "which kimi",
        shell=True,
        capture_output=True,
        text=True
    )
    
    if kimi_check.returncode != 0:
        # Install kimi
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
                    "error": f"Failed to install kimi: {install_result.stderr}",
                    "returncode": 1
                }
        except Exception as e:
            return {"error": str(e)}
    
    # Start kimi web in background
    try:
        subprocess.Popen(
            f"kimi web --host 0.0.0.0 --port {KIMI_WEB_PORT} --work-dir {user_dir} --no-open",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        return {
            "success": True,
            "kimi_web_url": f"http://kimi-cli-a5jcf4:{KIMI_WEB_PORT}",
            "message": "Kimi Web started successfully"
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/execute", dependencies=[Depends(verify_api_key)])
async def execute_command(request: CommandRequest):
    """Execute a command in the user's workspace"""
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
