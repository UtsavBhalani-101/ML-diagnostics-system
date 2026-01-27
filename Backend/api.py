"""
Minimal FastAPI Backend with Pydantic Input/Output Schema Validation
"""
import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from Backend.file_support_check import validate_and_load, get_supported_extensions


# ============================================================
# Configuration
# ============================================================

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


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
    if result["is_valid"]:
        try:
            file_path = os.path.join(UPLOAD_DIR, file.filename)
            with open(file_path, "wb") as f:
                f.write(content)
            saved = True
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
