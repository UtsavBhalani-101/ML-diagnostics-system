from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os

# Internal Imports
from .file_support_check import validate_and_load  # Moved to Backend folder
from engine.main_engine import main_engine

app = FastAPI()

# Configuration
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class DiagnosisRequest(BaseModel):
    filename: str

@app.post("/upload")
async def upload_file(file: UploadFile):
    # 1. Read file into memory buffer
    content = await file.read()
    
    # 2. Gatekeeper: Validate BEFORE saving to disk
    try:
        # This uses the stream-based pandas check we refactored
        validate_and_load(content, file.filename)
    except ValueError as e:
        # Rejects the request; no file is saved to 'uploads'
        raise HTTPException(status_code=400, detail=str(e))
    
    # 3. Save ONLY if validated (Prevents folder pollution)
    file_location = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_location, "wb") as f:
        f.write(content)
        
    return {"info": f"File '{file.filename}' verified and saved successfully."}

@app.post("/diagnose")
async def diagnose_file(request: DiagnosisRequest):
    file_path = os.path.join(UPLOAD_DIR, request.filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
        
    # Passes the clean file path to your processing engine
    engine_response = start_engine(file_path)
    return engine_response

# --- Frontend Serving (Keep at bottom) ---
app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    file_path = os.path.join("frontend/dist", full_path)
    if full_path and os.path.isfile(file_path):
        return FileResponse(file_path)
    return FileResponse("frontend/dist/index.html")