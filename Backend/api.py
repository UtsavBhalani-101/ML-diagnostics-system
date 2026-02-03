"""
Minimal FastAPI Backend with Pydantic Input/Output Schema Validation
"""
import os
import re
import json
import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Any, List

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

# Session state to track valid file upload and target column
# In a production app, this would use proper session management or database
_valid_file_uploaded = {"status": False, "filename": None, "target_column": None}


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


class TargetColumnRequest(BaseModel):
    """Input schema for setting the target column."""
    target_column: str = Field(..., description="Name of the target column", min_length=1)
    
    @field_validator('target_column')
    @classmethod
    def validate_column_name(cls, v):
        """Validate column name using regex - must be a valid identifier."""
        # Allow letters, numbers, underscores, spaces, and common special chars
        # Must start with a letter or underscore
        pattern = r'^[a-zA-Z_][a-zA-Z0-9_\s\-\.]*$'
        if not re.match(pattern, v.strip()):
            raise ValueError(
                f"Invalid column name format: '{v}'. "
                "Column names must start with a letter or underscore and contain only "
                "letters, numbers, underscores, spaces, hyphens, or dots."
            )
        return v.strip()


class TargetColumnResponse(BaseModel):
    """Output schema for target column validation."""
    valid: bool = Field(..., description="Whether the target column is valid and exists")
    target_column: str = Field(..., description="The validated target column name")
    message: str = Field(..., description="Status message")
    available_columns: Optional[List[str]] = Field(None, description="List of available columns if target not found")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "valid": True,
                    "target_column": "income",
                    "message": "Target column 'income' found and set successfully.",
                    "available_columns": None
                }
            ]
        }
    }


class DatasetColumnsResponse(BaseModel):
    """Output schema for listing dataset columns."""
    filename: str = Field(..., description="Name of the uploaded file")
    columns: List[str] = Field(..., description="List of column names in the dataset")
    column_count: int = Field(..., description="Total number of columns")
    suggested_target: str = Field(..., description="Suggested target column (last column)")


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
    description="Validates if the uploaded file is a supported format and can be read as a DataFrame. After uploading, use /dataset-columns to view columns and /set-target-column to set the target before running analysis."
)
async def validate_file(
    file: UploadFile = File(..., description="The data file to validate")
) -> FileValidationResponse:
    """
    Validates an uploaded file:
    1. Checks file extension against supported formats
    2. Attempts to load file with pandas
    3. Saves the file if valid
    
    Note: Pipeline is NOT run automatically. Use /set-target-column and /run-analysis.
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
            # Update session state to track successful upload
            # Reset target_column when new file is uploaded
            _valid_file_uploaded["status"] = True
            _valid_file_uploaded["filename"] = file.filename
            _valid_file_uploaded["target_column"] = None  # Reset target column for new file
                
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


@app.get(
    "/",
    summary="Home Page",
    description="Welcome page with API overview and available endpoints."
)
async def home():
    """
    Home page endpoint that provides an overview of the ML Diagnostics API.
    """
    return {
        "message": "Welcome to ML Diagnostics API",
        "version": "1.0.0",
        "description": "API for validating and analyzing machine learning datasets",
        "endpoints": {
            "GET /": "Home page (this page)",
            "GET /health": "Health check endpoint",
            "GET /docs": "Interactive API documentation (Swagger UI)",
            "GET /redoc": "Alternative API documentation (ReDoc)",
            "POST /validate-file": "Upload and validate a data file",
            "GET /supported-extensions": "List supported file formats",
            "GET /dataset-columns": "View columns in uploaded dataset",
            "POST /set-target-column": "Set the target column for analysis",
            "POST /run-analysis": "Run Layer 1 analysis on uploaded file",
            "GET /layer-1-output": "Get Layer 1 analysis results"
        },
        "workflow": [
            "1. Upload a file using POST /validate-file",
            "2. View available columns using GET /dataset-columns",
            "3. Set target column using POST /set-target-column",
            "4. Run analysis using POST /run-analysis",
            "5. View results using GET /layer-1-output"
        ]
    }


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


# ============================================================
# Target Column Management Endpoints
# ============================================================

@app.get(
    "/dataset-columns",
    response_model=DatasetColumnsResponse,
    responses={
        200: {"model": DatasetColumnsResponse, "description": "List of dataset columns"},
        400: {"model": ErrorResponse, "description": "No file uploaded"}
    },
    summary="Get dataset columns",
    description="Returns all column names from the uploaded dataset to help user select a target column."
)
async def get_dataset_columns() -> DatasetColumnsResponse:
    """
    Returns all columns from the uploaded dataset.
    Useful for users to see available columns before selecting a target.
    """
    if not _valid_file_uploaded["status"] or not _valid_file_uploaded["filename"]:
        raise HTTPException(
            status_code=400,
            detail="No valid file has been uploaded. Please upload a file first using /validate-file."
        )
    
    file_path = os.path.join(UPLOAD_DIR, _valid_file_uploaded["filename"])
    
    if not os.path.exists(file_path):
        _valid_file_uploaded["status"] = False
        _valid_file_uploaded["filename"] = None
        raise HTTPException(
            status_code=400,
            detail="Previously uploaded file no longer exists. Please upload a new file."
        )
    
    try:
        df = pd.read_csv(file_path)
        columns = df.columns.tolist()
        
        return DatasetColumnsResponse(
            filename=_valid_file_uploaded["filename"],
            columns=columns,
            column_count=len(columns),
            suggested_target=columns[-1] if columns else ""
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read dataset columns: {str(e)}"
        )


@app.post(
    "/set-target-column",
    response_model=TargetColumnResponse,
    responses={
        200: {"model": TargetColumnResponse, "description": "Target column validation result"},
        400: {"model": ErrorResponse, "description": "Invalid request or column not found"},
        422: {"model": ErrorResponse, "description": "Validation error - invalid column name format"}
    },
    summary="Set target column",
    description="Validates and sets the target column for analysis. Column name is validated using regex and checked against the dataset."
)
async def set_target_column(request: TargetColumnRequest) -> TargetColumnResponse:
    """
    Validates and sets the target column:
    1. Validates column name format using regex
    2. Checks if column exists in the uploaded dataset
    3. Stores the target column for subsequent analysis
    """
    if not _valid_file_uploaded["status"] or not _valid_file_uploaded["filename"]:
        raise HTTPException(
            status_code=400,
            detail="No valid file has been uploaded. Please upload a file first using /validate-file."
        )
    
    file_path = os.path.join(UPLOAD_DIR, _valid_file_uploaded["filename"])
    
    if not os.path.exists(file_path):
        _valid_file_uploaded["status"] = False
        _valid_file_uploaded["filename"] = None
        raise HTTPException(
            status_code=400,
            detail="Previously uploaded file no longer exists. Please upload a new file."
        )
    
    try:
        df = pd.read_csv(file_path)
        columns = df.columns.tolist()
        target_col = request.target_column
        
        # Check if column exists (case-sensitive)
        if target_col in columns:
            _valid_file_uploaded["target_column"] = target_col
            return TargetColumnResponse(
                valid=True,
                target_column=target_col,
                message=f"Target column '{target_col}' found and set successfully.",
                available_columns=None
            )
        
        # Check for case-insensitive match
        lower_columns = {col.lower(): col for col in columns}
        if target_col.lower() in lower_columns:
            actual_col = lower_columns[target_col.lower()]
            _valid_file_uploaded["target_column"] = actual_col
            return TargetColumnResponse(
                valid=True,
                target_column=actual_col,
                message=f"Target column found as '{actual_col}' (case-insensitive match).",
                available_columns=None
            )
        
        # Column not found - return error with available columns
        return TargetColumnResponse(
            valid=False,
            target_column=target_col,
            message=f"Target column '{target_col}' not found in the dataset. Please choose from available columns.",
            available_columns=columns
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to validate target column: {str(e)}"
        )


@app.post(
    "/run-analysis",
    response_model=Layer1OutputResponse,
    responses={
        200: {"model": Layer1OutputResponse, "description": "Analysis completed successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request - no file uploaded"}
    },
    summary="Run Layer 1 analysis",
    description="Runs the Layer 1 analysis pipeline on the entire uploaded dataset. No target column needed for Layer 1."
)
async def run_analysis() -> Layer1OutputResponse:
    """
    Runs the Layer 1 analysis pipeline:
    1. Checks if file is uploaded
    2. Runs the pipeline on ENTIRE DataFrame (all columns)
    3. Returns the analysis results
    
    Note: Layer 1 always analyzes all columns. Target column is NOT used in Layer 1.
    """
    if not _valid_file_uploaded["status"] or not _valid_file_uploaded["filename"]:
        raise HTTPException(
            status_code=400,
            detail="No valid file has been uploaded. Please upload a file first using /validate-file."
        )
    
    file_path = os.path.join(UPLOAD_DIR, _valid_file_uploaded["filename"])
    
    if not os.path.exists(file_path):
        _valid_file_uploaded["status"] = False
        _valid_file_uploaded["filename"] = None
        _valid_file_uploaded["target_column"] = None
        raise HTTPException(
            status_code=400,
            detail="Previously uploaded file no longer exists. Please upload a new file."
        )
    
    try:
        # Run pipeline on entire DataFrame (Layer 1 does NOT use target column)
        pipeline_result = run_pipeline(file_path)
        
        # Convert tuple shape to list for JSON serialization
        if 'shape' in pipeline_result and isinstance(pipeline_result['shape'], tuple):
            pipeline_result['shape'] = list(pipeline_result['shape'])
        
        # Save pipeline output to results folder
        with open(LAYER1_OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(pipeline_result, f, indent=4, default=str)
        
        return Layer1OutputResponse(**pipeline_result)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Pipeline execution failed: {str(e)}"
        )
