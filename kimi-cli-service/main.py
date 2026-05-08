import os
import subprocess
import time
import socket
from fastapi import FastAPI, HTTPException, Header, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from typing import Optional
import httpx

app = FastAPI(title="Kimi CLI Service", version="2.2.0")

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

kimi_web_instances = {}

class CommandRequest(BaseModel):
    command: str
    user_id: str = "default"

class WorkspaceRequest(BaseModel):
    user_id: str
    repo_url: Optional[str] = None

async def verify_api_key(x_api_key: Optional[str] = Header(None, alias="X-API-Key")):
    if not x_api_key or x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return x_api_key

def get_next_port():
    used_ports = set()
    for user_instances in kimi_web_instances.values():
        for port in user_instances.values():
            used_ports.add(port)
    port = KIMI_WEB_PORT_START
    while port in used_ports:
        port += 1
    return port

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def wait_for_port(port, timeout=30):
    start_time = time.time()
    while time.time() - start_time < timeout:
        if is_port_in_use(port):
            return True
        time.sleep(0.5)
    return False

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "kimi-cli",
        "version": "2.2.0",
        "active_instances": sum(len(v) for v in kimi_web_instances.values())
    }

@app.post("/workspace/init", dependencies=[Depends(verify_api_key)])
async def init_workspace(request: WorkspaceRequest):
    user_dir = os.path.join(WORKSPACE_ROOT, "users", request.user_id)
    os.makedirs(user_dir, exist_ok=True)
    result_data = {"user_id": request.user_id, "workspace_dir": user_dir, "initialized": True}
    if request.repo_url:
        try:
            result = subprocess.run(
                f"git clone {request.repo_url} .",
                shell=True, cwd=user_dir, capture_output=True, text=True, timeout=120
            )
            result_data["clone_output"] = result.stdout
            result_data["clone_error"] = result.stderr
            result_data["clone_returncode"] = result.returncode
        except Exception as e:
            result_data["clone_error"] = str(e)
    return result_data

@app.post("/kimi-web/open", dependencies=[Depends(verify_api_key)])
async def open_kimi_web(request: Request):
    body = await request.json()
    user_id = body.get("userId") or body.get("user_id", "default")
    repo_url = body.get("repoUrl") or body.get("repo_url", "")
    repo_name = body.get("repoName") or body.get("repo_name", "")
    
    if not repo_url or not repo_name:
        raise HTTPException(status_code=400, detail="repoUrl and repoName are required")
    
    user_dir = os.path.join(WORKSPACE_ROOT, "users", user_id)
    project_dir = os.path.join(user_dir, repo_name)
    os.makedirs(user_dir, exist_ok=True)
    
    if not os.path.exists(project_dir):
        try:
            result = subprocess.run(
                f"git clone {repo_url} {repo_name}",
                shell=True, cwd=user_dir, capture_output=True, text=True, timeout=120
            )
            if result.returncode != 0:
                return {"error": f"Failed to clone: {result.stderr}"}
        except Exception as e:
            return {"error": str(e)}
    
    # Check if already running
    if user_id in kimi_web_instances and repo_name in kimi_web_instances[user_id]:
        port = kimi_web_instances[user_id][repo_name]
        if is_port_in_use(port):
            return {
                "success": True,
                "url": f"{KIMI_WEB_PUBLIC_URL}/web/{user_id}/{repo_name}/",
                "repo_name": repo_name,
                "port": port,
                "already_running": True
            }
        del kimi_web_instances[user_id][repo_name]
    
    port = get_next_port()
    
    try:
        env = os.environ.copy()
        env["PATH"] = "/root/.local/bin:" + env.get("PATH", "")
        log_file = f"/tmp/kimi-web-{user_id}-{repo_name}.log"
        
        # Start kimi web with nohup
        cmd = f"cd {project_dir} && nohup kimi web --network --host 0.0.0.0 --port {port} --no-open > {log_file} 2>&1 &"
        subprocess.run(cmd, shell=True, cwd=project_dir, env=env, capture_output=True, timeout=10)
        
        if user_id not in kimi_web_instances:
            kimi_web_instances[user_id] = {}
        kimi_web_instances[user_id][repo_name] = port
        
        if not wait_for_port(port, timeout=30):
            try:
                with open(log_file, 'r') as f:
                    logs = f.read()
            except:
                logs = "No logs available"
            return {"error": "Kimi Web failed to start", "logs": logs, "port": port}
        
        return {
            "success": True,
            "url": f"{KIMI_WEB_PUBLIC_URL}/web/{user_id}/{repo_name}/",
            "repo_name": repo_name,
            "port": port
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/execute", dependencies=[Depends(verify_api_key)])
async def execute_command(request: CommandRequest):
    if not request.command or not request.command.strip():
        raise HTTPException(status_code=400, detail="Command is required")
    
    user_dir = os.path.join(WORKSPACE_ROOT, "users", request.user_id)
    os.makedirs(user_dir, exist_ok=True)
    
    try:
        env = os.environ.copy()
        env["PATH"] = "/root/.local/bin:" + env.get("PATH", "")
        result = subprocess.run(
            request.command, shell=True, cwd=user_dir,
            capture_output=True, text=True, timeout=300, env=env
        )
        return {
            "output": result.stdout,
            "error": result.stderr,
            "returncode": result.returncode,
            "user_id": request.user_id
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Command timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/web/{user_id}/{repo_name}/{path:path}")
async def proxy_kimi_web(user_id: str, repo_name: str, path: str, request: Request):
    if user_id not in kimi_web_instances or repo_name not in kimi_web_instances[user_id]:
        raise HTTPException(status_code=404, detail="Instance not found")
    
    port = kimi_web_instances[user_id][repo_name]
    if not is_port_in_use(port):
        del kimi_web_instances[user_id][repo_name]
        raise HTTPException(status_code=404, detail="Instance no longer running")
    
    target_path = f"/{path}" if path else "/"
    if request.query_params:
        target_path += f"?{request.query_params}"
    
    target_url = f"http://127.0.0.1:{port}{target_path}"
    
    try:
        async with httpx.AsyncClient() as client:
            method = request.method
            
            if method == "GET":
                response = await client.get(target_url, follow_redirects=True, timeout=30)
            elif method == "POST":
                body = await request.body()
                response = await client.post(target_url, content=body, follow_redirects=True, timeout=30)
            else:
                response = await client.request(method, target_url, follow_redirects=True, timeout=30)
            
            content = response.content
            content_type = response.headers.get("content-type", "")
            
            # Rewrite HTML URLs
            if "text/html" in content_type:
                html = content.decode('utf-8', errors='replace')
                html = html.replace('href="/', f'href="/web/{user_id}/{repo_name}/')
                html = html.replace("href='/", f"href='/web/{user_id}/{repo_name}/")
                html = html.replace('src="/', f'src="/web/{user_id}/{repo_name}/')
                html = html.replace("src='/", f"src='/web/{user_id}/{repo_name}/")
                html = html.replace('href="./', f'href="/web/{user_id}/{repo_name}/')
                html = html.replace("href='./", f"href='/web/{user_id}/{repo_name}/")
                html = html.replace('src="./', f'src="/web/{user_id}/{repo_name}/')
                html = html.replace("src='./", f"src='/web/{user_id}/{repo_name}/")
                content = html.encode('utf-8')
            
            return PlainTextResponse(
                content=content,
                status_code=response.status_code,
                headers={"content-type": content_type}
            )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Proxy error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
