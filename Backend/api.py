"""
Minimal FastAPI Backend with Pydantic Input/Output Schema Validation
"""
import os
import json
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Any

from Backend.file_support_check import validate_and_load, get_supported_extensions
from engine.Layer_1.pipeline import run_pipeline


# ============================================================
# Configuration
# ============================================================

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Results folder for pipeline outputs
RESULTS_DIR = "results"
os.makedirs(os.path.join(RESULTS_DIR, "layer_1"), exist_ok=True)

# Path to Layer 1 pipeline output
LAYER1_OUTPUT_PATH = os.path.join(RESULTS_DIR, "layer_1", "output.json")

# Session state to track valid file upload
# In a production app, this would use proper session management or database
_valid_file_uploaded = {"status": False, "filename": None}


# ============================================================
# Pydantic Schemas (Input/Output Validation)
# ============================================================

class FileValidationResponse(BaseModel):
    """Output schema for file validation endpoint."""
    is_valid: bool = Field(..., description="Whether the file is valid and supported")
    filename: str = Field(..., description="Name of the uploaded file")
    extension: str = Field(..., description="File extension detected")
    saved: bool = Field(False, description="Whether the file was saved to uploads folder")
    error: Optional[str] = Field(None, description="Error message if validation failed")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "is_valid": True,
                    "filename": "data.csv",
                    "extension": ".csv",
                    "saved": True,
                    "error": None
                }
            ]
        }
    }


class SupportedExtensionsResponse(BaseModel):
    """Output schema for supported extensions endpoint."""
    extensions: list[str] = Field(..., description="List of supported file extensions")
    count: int = Field(..., description="Total number of supported extensions")


class ErrorResponse(BaseModel):
    """Standard error response schema."""
    detail: str = Field(..., description="Error message")


class Layer1OutputResponse(BaseModel):
    """Output schema for Layer 1 pipeline results."""
    data_loaded: bool = Field(..., description="Whether the data was successfully loaded")
    shape: list[int] = Field(..., description="Shape of the dataset [rows, columns]")
    signals: dict[str, Any] = Field(..., description="Signal metrics from Layer 1 analysis")
    logic: dict[str, Any] = Field(..., description="Logic analysis results")
    report: str = Field(..., description="Human-readable report text")
    status: str = Field(..., description="Status of the pipeline execution")


# ============================================================
# FastAPI App
# ============================================================

app = FastAPI(
    title="File Validation API",
    description="API for validating uploaded data files",
    version="1.0.0"
)


# ============================================================
# Routes
# ============================================================

@app.post(
    "/validate-file",
    response_model=FileValidationResponse,
    responses={
        200: {"model": FileValidationResponse, "description": "File validation result"},
        400: {"model": ErrorResponse, "description": "Bad request"}
    },
    summary="Validate uploaded file",
    description="Validates if the uploaded file is a supported format and can be read as a DataFrame."
)
async def validate_file(
    file: UploadFile = File(..., description="The data file to validate")
) -> FileValidationResponse:
    """
    Validates an uploaded file:
    1. Checks file extension against supported formats
    2. Attempts to load file with pandas
    3. Returns structured validation result
    """
    # Input validation: Check if file was provided
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    # Read file content
    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")
    
    # Validate and load the file
    result = validate_and_load(content, file.filename)
    
    # Save file ONLY if valid
    saved = False
    pipeline_executed = False
    if result["is_valid"]:
        try:
            file_path = os.path.join(UPLOAD_DIR, file.filename)
            with open(file_path, "wb") as f:
                f.write(content)
            saved = True
            # Update session state to track successful upload
            _valid_file_uploaded["status"] = True
            _valid_file_uploaded["filename"] = file.filename
            
            # Run Layer 1 pipeline on the uploaded file
            try:
                pipeline_result = run_pipeline(file_path)
                
                # Convert tuple shape to list for JSON serialization
                if 'shape' in pipeline_result and isinstance(pipeline_result['shape'], tuple):
                    pipeline_result['shape'] = list(pipeline_result['shape'])
                
                # Save pipeline output to results folder
                with open(LAYER1_OUTPUT_PATH, "w", encoding="utf-8") as f:
                    json.dump(pipeline_result, f, indent=4)
                pipeline_executed = True
            except Exception as pipeline_error:
                result["error"] = f"File saved but pipeline failed: {str(pipeline_error)}"
                
        except Exception as e:
            result["error"] = f"File valid but failed to save: {str(e)}"
    
    # Return validated response (Pydantic enforces schema)
    return FileValidationResponse(**result, saved=saved)


@app.get(
    "/supported-extensions",
    response_model=SupportedExtensionsResponse,
    summary="Get supported file extensions",
    description="Returns a list of all file extensions that can be validated."
)
async def supported_extensions() -> SupportedExtensionsResponse:
    """Returns all supported file extensions."""
    extensions = get_supported_extensions()
    return SupportedExtensionsResponse(
        extensions=extensions,
        count=len(extensions)
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get(
    "/layer-1-output",
    response_model=Layer1OutputResponse,
    responses={
        200: {"model": Layer1OutputResponse, "description": "Layer 1 pipeline results"},
        400: {"model": ErrorResponse, "description": "Bad request - no valid file uploaded"},
        404: {"model": ErrorResponse, "description": "Output file not found"}
    },
    summary="Get Layer 1 analysis output",
    description="Returns the Layer 1 pipeline analysis results. Requires a valid file to be uploaded first via /validate-file endpoint."
)
async def get_layer1_output() -> Layer1OutputResponse:
    """
    Returns Layer 1 pipeline output:
    1. Checks if a valid file has been uploaded
    2. Reads and returns the pipeline output JSON
    """
    # Check if a valid file has been uploaded
    if not _valid_file_uploaded["status"]:
        raise HTTPException(
            status_code=400,
            detail="No valid file has been uploaded. Please upload a valid file using the /validate-file endpoint first."
        )
    
    # Check if the uploaded file still exists in uploads folder
    if _valid_file_uploaded["filename"]:
        file_path = os.path.join(UPLOAD_DIR, _valid_file_uploaded["filename"])
        if not os.path.exists(file_path):
            _valid_file_uploaded["status"] = False
            _valid_file_uploaded["filename"] = None
            raise HTTPException(
                status_code=400,
                detail="Previously uploaded file no longer exists. Please upload a new file."
            )
    
    # Read and return the Layer 1 output
    try:
        if not os.path.exists(LAYER1_OUTPUT_PATH):
            raise HTTPException(
                status_code=404,
                detail=f"Layer 1 output file not found at: {LAYER1_OUTPUT_PATH}"
            )
        
        with open(LAYER1_OUTPUT_PATH, "r", encoding="utf-8") as f:
            output_data = json.load(f)
        
        return Layer1OutputResponse(**output_data)
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse Layer 1 output JSON: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read Layer 1 output: {str(e)}"
        )
