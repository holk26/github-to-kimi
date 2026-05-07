"""
Kimi CLI Service - API REST para ejecutar comandos de Kimi CLI
"""
import os
import subprocess
import json
from typing import Optional
from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Kimi CLI Service", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

WORKSPACE_ROOT = os.environ.get("WORKSPACE_ROOT", "/workspace")


class CommandRequest(BaseModel):
    user_id: str
    command: str
    cwd: Optional[str] = None
    env: Optional[dict] = None


class CloneRequest(BaseModel):
    user_id: str
    repo_url: str
    repo_name: str


class InitWorkspaceRequest(BaseModel):
    user_id: str


def get_user_workspace(user_id: str) -> str:
    """Obtiene el directorio workspace de un usuario"""
    workspace = os.path.join(WORKSPACE_ROOT, "users", user_id)
    os.makedirs(workspace, exist_ok=True)
    os.makedirs(os.path.join(workspace, "repos"), exist_ok=True)
    os.makedirs(os.path.join(workspace, ".kimi"), exist_ok=True)
    os.makedirs(os.path.join(workspace, ".ssh"), exist_ok=True)
    return workspace


@app.get("/health")
async def health():
    return {"status": "ok", "service": "kimi-cli"}


@app.post("/workspace/init")
async def init_workspace(req: InitWorkspaceRequest):
    """Inicializa el workspace de un usuario"""
    workspace = get_user_workspace(req.user_id)
    
    # Configurar git
    gitconfig_path = os.path.join(workspace, ".gitconfig")
    if not os.path.exists(gitconfig_path):
        with open(gitconfig_path, "w") as f:
            f.write("[user]\n\tname = Kimi User\n\temail = user@kimi.local\n")
    
    return {"status": "ok", "workspace": workspace}


@app.post("/repo/clone")
async def clone_repo(req: CloneRequest):
    """Clona un repositorio en el workspace del usuario"""
    workspace = get_user_workspace(req.user_id)
    repo_path = os.path.join(workspace, "repos", req.repo_name)
    
    # Si ya existe, hacer pull
    if os.path.exists(os.path.join(repo_path, ".git")):
        result = subprocess.run(
            ["git", "pull"],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        return {
            "status": "updated",
            "path": repo_path,
            "output": result.stdout,
            "error": result.stderr if result.returncode != 0 else None
        }
    
    # Clonar nuevo repo
    result = subprocess.run(
        ["git", "clone", req.repo_url, repo_path],
        cwd=workspace,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        raise HTTPException(status_code=400, detail=result.stderr)
    
    return {
        "status": "cloned",
        "path": repo_path,
        "output": result.stdout
    }


@app.post("/exec")
async def execute_command(req: CommandRequest):
    """Ejecuta un comando en el workspace del usuario"""
    workspace = get_user_workspace(req.user_id)
    
    # Determinar directorio de trabajo
    cwd = req.cwd or workspace
    if not cwd.startswith(workspace):
        cwd = workspace
    
    # Preparar environment
    env = os.environ.copy()
    if req.env:
        env.update(req.env)
    env["HOME"] = workspace
    env["KIMI_CONFIG_DIR"] = os.path.join(workspace, ".kimi")
    
    # Ejecutar comando
    result = subprocess.run(
        req.command,
        shell=True,
        cwd=cwd,
        capture_output=True,
        text=True,
        env=env,
        timeout=300  # 5 minutos timeout
    )
    
    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "cwd": cwd
    }


@app.get("/workspace/{user_id}/list")
async def list_workspace(user_id: str):
    """Lista los repositorios en el workspace del usuario"""
    workspace = get_user_workspace(user_id)
    repos_dir = os.path.join(workspace, "repos")
    
    repos = []
    if os.path.exists(repos_dir):
        for name in os.listdir(repos_dir):
            repo_path = os.path.join(repos_dir, name)
            if os.path.isdir(os.path.join(repo_path, ".git")):
                # Obtener info del repo
                try:
                    remote = subprocess.run(
                        ["git", "remote", "get-url", "origin"],
                        cwd=repo_path,
                        capture_output=True,
                        text=True
                    )
                    branch = subprocess.run(
                        ["git", "branch", "--show-current"],
                        cwd=repo_path,
                        capture_output=True,
                        text=True
                    )
                    repos.append({
                        "name": name,
                        "path": repo_path,
                        "remote": remote.stdout.strip() if remote.returncode == 0 else None,
                        "branch": branch.stdout.strip() if branch.returncode == 0 else None
                    })
                except:
                    repos.append({"name": name, "path": repo_path})
    
    return {"workspace": workspace, "repos": repos}


@app.websocket("/ws/terminal/{user_id}")
async def websocket_terminal(websocket: WebSocket, user_id: str):
    """WebSocket para terminal interactiva"""
    await websocket.accept()
    workspace = get_user_workspace(user_id)
    
    await websocket.send_text(json.dumps({
        "type": "info",
        "message": f"Conectado al workspace: {workspace}"
    }))
    
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            
            if msg.get("type") == "command":
                command = msg.get("command", "")
                cwd = msg.get("cwd", workspace)
                
                # Validar cwd
                if not cwd.startswith(workspace):
                    cwd = workspace
                
                # Ejecutar comando
                env = os.environ.copy()
                env["HOME"] = workspace
                env["KIMI_CONFIG_DIR"] = os.path.join(workspace, ".kimi")
                
                process = subprocess.Popen(
                    command,
                    shell=True,
                    cwd=cwd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    env=env
                )
                
                # Enviar output en tiempo real
                for line in process.stdout:
                    await websocket.send_text(json.dumps({
                        "type": "output",
                        "data": line
                    }))
                
                process.wait()
                
                await websocket.send_text(json.dumps({
                    "type": "done",
                    "returncode": process.returncode
                }))
                
    except Exception as e:
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": str(e)
        }))
    finally:
        await websocket.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
