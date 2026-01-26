import os
import sys

# --- Stability Fixes (Must be first) ---
# Critical for Mac ARM64 to prevent OpenMP crashes
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

# Add conda environment's bin to PATH so it can find ffmpeg
conda_bin = os.path.join(sys.prefix, "bin")
if conda_bin not in os.environ["PATH"]:
    os.environ["PATH"] = conda_bin + os.pathsep + os.environ["PATH"]

import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles

# Import modules
from core.video_processor import process_and_ingest_video
from core.agent import invoke_agent

app = FastAPI(title="VideoBrain API")

# CORS (Allow Frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
)
 
# Serve uploaded videos statically
os.makedirs("temp_uploads", exist_ok=True)
app.mount("/videos", StaticFiles(directory="temp_uploads"), name="videos")
 
# --- Models ---
class ChatRequest(BaseModel):
    message: str
    video_id: str
    thread_id: str

class ChatResponse(BaseModel):
    response: str

# --- Endpoints ---

@app.get("/")
def health_check():
    return {"status": "ok"}

@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    # Basic validation
    allowed_extensions = [".mp4", ".mov", ".avi", ".mkv"]
    if not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
        raise HTTPException(status_code=400, detail="Unsupported video format.")
    
    # Save temp file
    temp_dir = "temp_uploads"
    os.makedirs(temp_dir, exist_ok=True)
    file_path = os.path.join(temp_dir, file.filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Process Video (Multimodal: Visual + Audio)
        video_id = process_and_ingest_video(file_path)
        
        return {"video_id": video_id, "filename": file.filename}
        
    except Exception as e:
        print(f"Error processing video: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # Invoke Multimodal Agent
        response_text = invoke_agent(
            user_message=request.message,
            video_id=request.video_id,
            thread_id=request.thread_id
        )
        return {"response": response_text}
    except Exception as e:
        print(f"Error in chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
