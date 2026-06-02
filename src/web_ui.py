from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import uvicorn
from pydantic import BaseModel
from typing import Optional

from src.ai_agent import AIAgent
from src.log_searcher import LogSearcher

app = FastAPI(title="Log Searcher & AI Analyzer Web UI")

# Setup templates
os.makedirs("src/templates", exist_ok=True)
templates = Jinja2Templates(directory="src/templates")

ai_agent = AIAgent()
log_searcher = LogSearcher()

# Simple memory for the chat (in a real app, this should be keyed by session/user)
chat_history = []

class ChatRequest(BaseModel):
    message: str

class SearchRequest(BaseModel):
    filepath: str
    query: Optional[str] = None
    search_type: str = "smart"

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    global chat_history
    user_msg = request.message
    
    chat_history.append({"role": "user", "content": user_msg})
    
    try:
        response_text, updated_history = await ai_agent.chat(chat_history)
        chat_history = updated_history
        return {"response": response_text}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/api/search")
async def search_endpoint(request: SearchRequest):
    try:
        results = await log_searcher.search_file(
            request.filepath, 
            query=request.query, 
            search_type=request.search_type
        )
        return {"results": results}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

from src.vfs import vfs
from src.os_mount import mount_smb, unmount

@app.get("/api/directory")
async def get_directory(path: str = "./"):
    """Returns a directory listing for the sidebar using VFS."""
    try:
        nodes = await vfs.list_dir(path)
        items = [
            {
                "name": n.name,
                "path": n.path,
                "is_dir": n.is_dir,
                "protocol": n.protocol
            } for n in nodes
        ]
        
        # Sort directories first, then files
        items.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))
        
        # Calculate parent path or canonical path
        current_path = path
        if path == "." or path == "./":
            current_path = os.path.abspath(path)
            
        return {"items": items, "current_path": current_path}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

class VFSConnectionRequest(BaseModel):
    id: str
    protocol: str # sftp, smb
    host: str
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    share_name: Optional[str] = None

@app.post("/api/vfs/add")
async def add_vfs_connection(request: VFSConnectionRequest):
    try:
        vfs.add_connection(request.id, request.dict())
        return {"status": "success", "id": request.id}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/vfs/list")
async def list_vfs_connections():
    return {"connections": list(vfs.connections.keys())}

def run_web_ui(host="127.0.0.1", port=8000):
    print(f"Starting Web UI on http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)
