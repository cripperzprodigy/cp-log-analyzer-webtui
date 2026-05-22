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
    keyword: Optional[str] = None
    regex: Optional[str] = None

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

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
            keyword=request.keyword, 
            regex=request.regex
        )
        return {"results": results}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/directory")
async def get_directory(path: str = "./"):
    """Returns a simple directory listing for the sidebar."""
    try:
        items = []
        for item in os.listdir(path):
            full_path = os.path.join(path, item)
            is_dir = os.path.isdir(full_path)
            items.append({
                "name": item,
                "path": full_path,
                "is_dir": is_dir
            })
        # Sort directories first, then files
        items.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))
        return {"items": items, "current_path": os.path.abspath(path)}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

def run_web_ui(port=8000):
    print(f"Starting Web UI on http://localhost:{port}")
    uvicorn.run(app, host="127.0.0.1", port=port)
