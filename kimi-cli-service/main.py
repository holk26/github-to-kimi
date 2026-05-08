import os
import subprocess
import re
import time
import socket
from fastapi import FastAPI, HTTPException, Header, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, PlainTextResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional
import httpx

app = FastAPI(title="Kimi CLI Service", version="2.1.0")

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
KIMI_WEB_PORT_START = int(os.environ.get("KIMI_WEB_PORT_START", "5494"))
KIMI_WEB_PUBLIC_URL = os.environ.get("KIMI_WEB_PUBLIC_URL", "https://kimi-cli.x.moonsbow.com")

# Track running kimi web instances: {user_id: {repo_name: port}}
kimi_web_instances = {}

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

async def verify_api_key(x_api_key: Optional[str] = Header(None, alias="X-API-Key")):
    """Verify API key from header"""
    if not x_api_key or x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return x_api_key

def get_next_port():
    """Get next available port for kimi web"""
    used_ports = set()
    for user_instances in kimi_web_instances.values():
        for port in user_instances.values():
            used_ports.add(port)
    
    port = KIMI_WEB_PORT_START
    while port in used_ports:
        port += 1
    return port

def is_port_in_use(port):
    """Check if a port is already in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def wait_for_port(port, timeout=30):
    """Wait for a port to become available"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if is_port_in_use(port):
            return True
        time.sleep(0.5)
    return False

@app.get("/health")
async def health_check():
    """Public health check endpoint"""
    return {
        "status": "healthy",
        "service": "kimi-cli",
        "version": "2.1.0",
        "active_instances": sum(len(v) for v in kimi_web_instances.values())
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
    """Open Kimi Web UI with the specified project - starts kimi web server"""
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
    
    # Check if kimi web is already running for this user/repo
    if user_id in kimi_web_instances and repo_name in kimi_web_instances[user_id]:
        port = kimi_web_instances[user_id][repo_name]
        # Verify it's still running
        if is_port_in_use(port):
            public_url = f"{KIMI_WEB_PUBLIC_URL}/web/{user_id}/{repo_name}"
            return {
                "success": True,
                "url": public_url,
                "kimi_web_url": public_url,
                "project_dir": project_dir,
                "repo_name": repo_name,
                "user_id": user_id,
                "port": port,
                "message": "Kimi Web already running",
                "already_running": True
            }
        else:
            # Clean up stale entry
            del kimi_web_instances[user_id][repo_name]
    
    # Find available port
    port = get_next_port()
    
    # Start kimi web in background using nohup
    try:
        env = os.environ.copy()
        env["PATH"] = "/root/.local/bin:" + env.get("PATH", "")
        
        log_file = f"/tmp/kimi-web-{user_id}-{repo_name}.log"
        
        # Use nohup to keep process running after parent exits
        # kimi web takes the directory as a positional argument
        cmd = f"cd {project_dir} && nohup kimi web --network --host 0.0.0.0 --port {port} --no-open > {log_file} 2>&1 &"
        
        subprocess.run(
            cmd,
            shell=True,
            cwd=project_dir,
            env=env,
            capture_output=True,
            timeout=10
        )
        
        # Store instance info
        if user_id not in kimi_web_instances:
            kimi_web_instances[user_id] = {}
        kimi_web_instances[user_id][repo_name] = port
        
        # Wait for server to start
        if not wait_for_port(port, timeout=30):
            # Check logs for errors
            try:
                with open(log_file, 'r') as f:
                    logs = f.read()
            except:
                logs = "Could not read logs"
            
            return {
                "error": "Kimi Web failed to start within 30 seconds",
                "logs": logs,
                "port": port
            }
        
        public_url = f"{KIMI_WEB_PUBLIC_URL}/web/{user_id}/{repo_name}"
        
        return {
            "success": True,
            "url": public_url,
            "kimi_web_url": public_url,
            "project_dir": project_dir,
            "repo_name": repo_name,
            "user_id": user_id,
            "port": port,
            "message": "Kimi Web started successfully"
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/kimi-web/stop", dependencies=[Depends(verify_api_key)])
async def stop_kimi_web(request: Request):
    """Stop a running Kimi Web instance"""
    body = await request.json()
    user_id = body.get("userId") or body.get("user_id", "default")
    repo_name = body.get("repoName") or body.get("repo_name", "")
    
    if user_id in kimi_web_instances and repo_name in kimi_web_instances[user_id]:
        port = kimi_web_instances[user_id][repo_name]
        # Kill process on port
        subprocess.run(f"pkill -f 'kimi web --port {port}'", shell=True)
        del kimi_web_instances[user_id][repo_name]
        return {"success": True, "message": f"Kimi Web stopped on port {port}"}
    
    return {"success": False, "message": "No running instance found"}

@app.post("/execute", dependencies=[Depends(verify_api_key)])
async def execute_command(request: CommandRequest):
    """Execute a command in the user's workspace"""
    if not request.command or not request.command.strip():
        raise HTTPException(status_code=400, detail="Command is required")
    
    user_dir = os.path.join(WORKSPACE_ROOT, "users", request.user_id)
    os.makedirs(user_dir, exist_ok=True)
    
    try:
        env = os.environ.copy()
        env["PATH"] = "/root/.local/bin:" + env.get("PATH", "")
        
        result = subprocess.run(
            request.command,
            shell=True,
            cwd=user_dir,
            capture_output=True,
            text=True,
            timeout=300,
            env=env
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

@app.get("/web/{user_id}/{repo_name}/{path:path}")
async def proxy_kimi_web(user_id: str, repo_name: str, path: str, request: Request):
    """Proxy requests to the appropriate kimi web instance"""
    if user_id not in kimi_web_instances or repo_name not in kimi_web_instances[user_id]:
        raise HTTPException(status_code=404, detail="Kimi Web instance not found")
    
    port = kimi_web_instances[user_id][repo_name]
    
    # Verify port is still active
    if not is_port_in_use(port):
        del kimi_web_instances[user_id][repo_name]
        raise HTTPException(status_code=404, detail="Kimi Web instance is no longer running")
    
    # Build target URL
    target_path = f"/{path}" if path else "/"
    query_string = str(request.query_params) if request.query_params else ""
    if query_string:
        target_path += f"?{query_string}"
    
    target_url = f"http://localhost:{port}{target_path}"
    
    try:
        async with httpx.AsyncClient() as client:
            # Forward the request
            method = request.method
            headers = dict(request.headers)
            headers.pop("host", None)
            
            # Add X-Forwarded headers for proper proxy behavior
            headers["X-Forwarded-For"] = request.client.host if request.client else "127.0.0.1"
            headers["X-Forwarded-Proto"] = "https"
            headers["X-Forwarded-Host"] = request.headers.get("host", "kimi-cli.x.moonsbow.com")
            
            if method == "GET":
                response = await client.get(target_url, headers=headers, follow_redirects=True, timeout=30)
            elif method == "POST":
                body = await request.body()
                response = await client.post(target_url, headers=headers, content=body, follow_redirects=True, timeout=30)
            else:
                response = await client.request(method, target_url, headers=headers, follow_redirects=True, timeout=30)
            
            # Rewrite URLs in HTML content
            content = response.content
            content_type = response.headers.get("content-type", "")
            
            if "text/html" in content_type:
                html = content.decode('utf-8', errors='replace')
                # Rewrite absolute URLs to go through our proxy
                html = re.sub(
                    r'(href|src|action)="/([^"]*)"',
                    rf'\1="/web/{user_id}/{repo_name}/\2"',
                    html
                )
                html = re.sub(
                    r"(href|src|action)='/([^']*)'",
                    rf"\1='/web/{user_id}/{repo_name}/\2'",
                    html
                )
                # Also handle websocket URLs
                html = re.sub(
                    r'ws://[^"\']*',
                    f'wss://{request.headers.get("host", "kimi-cli.x.moonsbow.com")}/web/{user_id}/{repo_name}/ws',
                    html
                )
                content = html.encode('utf-8')
            
            return PlainTextResponse(
                content=content,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error proxying to Kimi Web: {str(e)}")

@app.get("/web/{user_id}/{repo_name}")
async def proxy_kimi_web_root(user_id: str, repo_name: str, request: Request):
    """Proxy root requests to kimi web instance"""
    return await proxy_kimi_web(user_id, repo_name, "", request)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
