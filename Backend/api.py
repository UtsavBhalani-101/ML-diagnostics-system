"""
FastAPI backend for ML Diagnostics.
"""
import os
import re
import pandas as pd
import io
from typing import Any, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from Backend.file_support_check import (
    get_supported_extensions,
    validate_and_load,
    _load_dataframe_by_extension
)
from engine.Layer_1.pipeline import run_pipeline_from_df


RESULTS_DIR = "results"
os.makedirs(os.path.join(RESULTS_DIR, "layer_1"), exist_ok=True)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


DOCS_PAYLOAD = {
    "overview": (
        "Signal → Risk → Decision is the core philosophy of this system. "
        "It exists to validate dataset structure before any model training begins, "
        "so teams can catch preventable failures early instead of discovering them "
        "after spending time on experiments. Upload a file, select a target column, "
        "and the engine evaluates structural risk across three dimensions in a single request."
    ),
    "layers": {
        "layer_1": {
            "name": "Structural Risk",
            "purpose": (
                "Layer 1 evaluates whether the dataset is structurally fit for modeling. "
                "It inspects the raw table before feature engineering or model selection. "
                "Signals are extracted, converted into risk scores per dimension, and surfaced "
                "as an overall risk gauge with per-dimension breakdowns."
            ),
            "dimensions": {
                "data_integrity": (
                    "Checks whether the data is internally consistent and usable. "
                    "This includes missingness ratios, duplicate density, constant columns, "
                    "hidden missing values, and mixed-type fields."
                ),
                "target_viability": (
                    "Checks whether the selected target can support supervised learning. "
                    "This includes missing labels, target variability, class imbalance, "
                    "and uncertainty about the task implied by the target."
                ),
                "sample_adequacy": (
                    "Checks whether the dataset has enough sample support relative to its feature space. "
                    "This helps surface small-sample and overfitting risk before training."
                ),
            },
            "outputs": {
                "risk_score": "A 0 to 1 score where higher values indicate higher structural risk.",
                "status": "SAFE, WARNING, or CRITICAL based on the evaluated risk level.",
                "primary_causes": (
                    "The dominant issues driving the risk, ranked by contribution. "
                    "Each includes a risk value and a mapped action for investigation."
                ),
                "contributing_factors": "Secondary additive factors that combine into risk but are not the main failure source.",
                "quick_actions": "Concrete first steps to reduce the highest-risk issues, derived from primary issue actions.",
            },
        },
        "layer_2": {
            "status": "coming_soon",
            "message": "Layer 2 (Feature-Level Diagnostics) is currently being built and is coming soon.",
        },
    },
    "interpretation": (
        "Read overall risk first to decide whether the dataset is broadly safe to continue with. "
        "Then inspect the dimension breakdown to see which area is driving that result. "
        "Primary issues are the main blockers; contributing factors matter, but they should be addressed "
        "after the dominant cause. Proceed when risk is SAFE or understood and acceptable. Act before modeling "
        "when status is WARNING or CRITICAL, especially if the primary issue affects data integrity or the target."
    ),
    "limitations": (
        "This system is heuristic-based. It is not ground truth, it does not replace domain expertise, "
        "and it still requires human judgment when deciding whether a dataset is acceptable for a specific use case. "
        "Maximum upload size is 10 MB."
    ),
}

MODELS_PAYLOAD = {
    "status": "not_available",
    "message": "Model layer not implemented yet",
    "roadmap": [
        "Integration with ML pipelines",
        "Automated model evaluation",
    ],
}


class FileValidationResponse(BaseModel):
    is_valid: bool = Field(..., description="Whether the file is valid and supported")
    filename: str = Field(..., description="Name of the uploaded file")
    extension: str = Field(..., description="File extension detected")
    error: Optional[str] = Field(None, description="Error message if validation failed")


class SupportedExtensionsResponse(BaseModel):
    extensions: list[str] = Field(..., description="List of supported file extensions")
    count: int = Field(..., description="Total number of supported extensions")


class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Error message")


class PrimaryIssueResponse(BaseModel):
    name: str = Field(..., description="Risk name")
    risk: float = Field(..., description="Risk contribution for this issue")
    action: str = Field(..., description="Mapped next action for investigation")


class DimensionBreakdownResponse(BaseModel):
    dominant: dict[str, float] = Field(..., description="Primary causes that should not be diluted")
    additive: dict[str, float] = Field(..., description="Contributing factors that combine into risk")


class DimensionResultResponse(BaseModel):
    status: str = Field(..., description="Dimension status label")
    risk: float = Field(..., description="Dimension total risk score")
    breakdown: DimensionBreakdownResponse = Field(..., description="Risk contribution breakdown")
    signals: dict[str, Any] = Field(..., description="Signals for this dimension")
    primary_issues: list[PrimaryIssueResponse] = Field(..., description="Top dominant issues with mapped actions")
    interpretation: str = Field(..., description="Short explanation of the dimension state")


class OverallRiskResponse(BaseModel):
    status: str = Field(..., description="Worst status across all dimensions")
    risk: float = Field(..., description="Overall risk score")
    primary_failure_source: Optional[str] = Field(None, description="Highest-risk dimension key")
    failing_dimensions: int = Field(..., description="Number of dimensions currently not SAFE")
    total_dimensions: int = Field(..., description="Total number of evaluated dimensions")


class Layer1FinalOutputResponse(BaseModel):
    overall: OverallRiskResponse = Field(..., description="Overall Layer 1 structural risk summary")
    dimensions: dict[str, DimensionResultResponse] = Field(..., description="Dimension-level structural risk outputs")


class Layer1OutputResponse(BaseModel):
    data_loaded: bool = Field(..., description="Whether the data was successfully loaded")
    shape: list[int] = Field(..., description="Shape of the dataset [rows, columns]")
    signals: dict[str, Any] = Field(..., description="Signal metrics from Layer 1 analysis")
    logic: dict[str, Any] = Field(..., description="Logic analysis results")
    final_output: Layer1FinalOutputResponse = Field(..., description="Formatted output for frontend display")
    status: str = Field(..., description="Status of the pipeline execution")


class TargetColumnRequest(BaseModel):
    target_column: str = Field(..., description="Name of the target column", min_length=1)

    @field_validator("target_column")
    @classmethod
    def validate_column_name(cls, value: str) -> str:
        pattern = r"^[a-zA-Z_][a-zA-Z0-9_\s\-\.]*$"
        cleaned = value.strip()
        if not re.match(pattern, cleaned):
            raise ValueError(
                f"Invalid column name format: '{value}'. "
                "Column names must start with a letter or underscore and contain only "
                "letters, numbers, underscores, spaces, hyphens, or dots."
            )
        return cleaned


class TargetColumnResponse(BaseModel):
    valid: bool = Field(..., description="Whether the target column is valid and exists")
    target_column: str = Field(..., description="The validated target column name")
    message: str = Field(..., description="Status message")
    available_columns: Optional[list[str]] = Field(None, description="List of available columns if target not found")


class DatasetColumnsResponse(BaseModel):
    filename: str = Field(..., description="Name of the uploaded file")
    columns: list[str] = Field(..., description="List of column names in the dataset")
    column_count: int = Field(..., description="Total number of columns")
    suggested_target: str = Field(..., description="Suggested target column")


class DocsResponse(BaseModel):
    overview: str
    layers: dict[str, Any]
    interpretation: str
    limitations: str


class ModelsResponse(BaseModel):
    status: str
    message: str
    roadmap: list[str]


app = FastAPI(
    title="ML Diagnostics API",
    description="API for validating and analyzing machine learning datasets",
    version="1.0.0",
)

_DEFAULT_ORIGINS = [
    "http://localhost:3001",
    "http://localhost:3000",
    "http://127.0.0.1:3001",
    "http://127.0.0.1:3000",
]

def _get_cors_origins() -> list[str]:
    env_origins = os.environ.get("CORS_ORIGINS", "").strip()
    if env_origins:
        return [origin.strip() for origin in env_origins.split(",") if origin.strip()]
    return _DEFAULT_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _validate_file_or_raise(content: bytes, filename: str):
    validation_result = validate_and_load(content, filename)
    if not validation_result["is_valid"]:
        raise HTTPException(
            status_code=400,
            detail=validation_result["error"] or "Invalid dataset file."
        )


def _safe_filename(filename: str) -> str:
    safe_name = os.path.basename(filename or "").strip()
    if not safe_name:
        raise HTTPException(status_code=400, detail="No filename provided")
    return safe_name


async def _read_upload_bytes(file: UploadFile) -> tuple[str, bytes]:
    filename = _safe_filename(file.filename or "")
    try:
        content = await file.read()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {exc}") from exc

    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum allowed size is {MAX_FILE_SIZE // (1024 * 1024)} MB.",
        )

    return filename, content


def load_dataframe_from_bytes(content: bytes, filename: str) -> pd.DataFrame:
    source = io.BytesIO(content)
    extension = os.path.splitext(filename)[1].lower()
    return _load_dataframe_by_extension(source, extension)


def _resolve_target_column(columns: list[str], requested_target: Optional[str]) -> Optional[str]:
    if not requested_target:
        return None

    cleaned_target = requested_target.strip()
    if not cleaned_target:
        return None

    if cleaned_target in columns:
        return cleaned_target

    case_insensitive = {column.lower(): column for column in columns}
    match = case_insensitive.get(cleaned_target.lower())
    if match:
        return match

    raise HTTPException(
        status_code=400,
        detail=f"Target column '{cleaned_target}' was not found in the uploaded dataset.",
    )



@app.post(
    "/validate-file",
    response_model=FileValidationResponse,
    responses={
        200: {"model": FileValidationResponse, "description": "File validation result"},
        400: {"model": ErrorResponse, "description": "Bad request"},
    },
    summary="Validate uploaded file",
    description="Validates the uploaded file and rejects empty or unreadable datasets.",
)
async def validate_file(file: UploadFile = File(...)) -> FileValidationResponse:
    filename, content = await _read_upload_bytes(file)

    # 1. Validate format
    validation_result = validate_and_load(content, filename)
    if not validation_result["is_valid"]:
        raise HTTPException(
            status_code=400,
            detail=validation_result["error"] or "Invalid dataset file.",
        )

    # 2. Parse to DataFrame to verify it's not empty
    try:
        df = load_dataframe_from_bytes(content, filename)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid dataset file: {exc}") from exc

    if df.empty or df.shape[1] == 0:
        raise HTTPException(
            status_code=400,
            detail="Dataset is empty. Upload a file with at least one row and one column.",
        )

    # 3. Return validation response
    return FileValidationResponse(**validation_result)


@app.get(
    "/supported-extensions",
    response_model=SupportedExtensionsResponse,
    summary="Get supported file extensions",
)
async def supported_extensions() -> SupportedExtensionsResponse:
    extensions = get_supported_extensions()
    return SupportedExtensionsResponse(extensions=extensions, count=len(extensions))


@app.get("/")
async def home() -> dict[str, Any]:
    return {
        "message": "Welcome to ML Diagnostics API",
        "version": "1.0.0",
        "description": "API for validating and analyzing machine learning datasets",
        "max_file_size_mb": MAX_FILE_SIZE // (1024 * 1024),
        "endpoints": {
            "GET /": "Home page",
            "GET /health": "Health check endpoint",
            "GET /docs": "Interactive API documentation (Swagger UI)",
            "GET /redoc": "Alternative API documentation (ReDoc)",
            "POST /validate-file": "Upload and validate a data file (max 10 MB)",
            "GET /supported-extensions": "List supported file formats",
            "POST /dataset-columns": "Upload file and get column names",
            "POST /set-target-column": "Upload file and validate a target column",
            "POST /api/diagnostics/run": "Upload a dataset with target column and run Layer 1 diagnostics",
            "GET /api/docs": "Get product documentation content",
            "GET /api/models": "Get current model-layer status",
        },
        "workflow": [
            "1. Validate a file using POST /validate-file (file upload, multipart/form-data)",
            "2. View available columns using POST /dataset-columns (file upload)",
            "3. Validate target column using POST /set-target-column (file + target_column form field)",
            "4. Run Layer 1 diagnostics using POST /api/diagnostics/run (file + optional target_column form field)",
        ],
    }


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}


@app.get("/api/docs", response_model=DocsResponse)
async def get_docs_content() -> DocsResponse:
    return DocsResponse(**DOCS_PAYLOAD)


@app.get("/api/models", response_model=ModelsResponse)
async def get_models_content() -> ModelsResponse:
    return ModelsResponse(**MODELS_PAYLOAD)


@app.post(
    "/api/diagnostics/run",
    response_model=Layer1OutputResponse,
    responses={
        200: {"model": Layer1OutputResponse, "description": "Diagnostics completed successfully"},
        400: {"model": ErrorResponse, "description": "Invalid file, dataset, or target column"},
        500: {"model": ErrorResponse, "description": "Diagnostics pipeline failed"},
    },
    summary="Upload a dataset and run diagnostics",
    description="Accepts a file upload, validates it, optionally validates a target column, and runs the Layer 1 pipeline.",
)
async def run_diagnostics(
    file: UploadFile = File(...),
    target_column: Optional[str] = Form(default=None),
) -> Layer1OutputResponse:
    filename, content = await _read_upload_bytes(file)
    _validate_file_or_raise(content, filename)
    df = load_dataframe_from_bytes(content, filename)
    resolved_target = _resolve_target_column(df.columns.tolist(), target_column)
    result = run_pipeline_from_df(df, resolved_target)
    return Layer1OutputResponse(**result)



@app.post(
    "/dataset-columns",
    response_model=DatasetColumnsResponse,
    responses={
        200: {"model": DatasetColumnsResponse, "description": "List of dataset columns"},
        400: {"model": ErrorResponse, "description": "Invalid file"},
    },
    summary="Get dataset columns from uploaded file",
    description="Accepts a file upload and returns the column names found in the dataset.",
)
async def get_dataset_columns(file: UploadFile = File(...)) -> DatasetColumnsResponse:
    filename, content = await _read_upload_bytes(file)

    try:
        _validate_file_or_raise(content, filename)
        df = load_dataframe_from_bytes(content, filename)
        columns = df.columns.tolist()
        return DatasetColumnsResponse(
            filename=filename,
            columns=columns,
            column_count=len(columns),
            suggested_target=columns[-1] if columns else "",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post(
    "/set-target-column",
    response_model=TargetColumnResponse,
    responses={
        200: {"model": TargetColumnResponse, "description": "Target column validation result"},
        400: {"model": ErrorResponse, "description": "Invalid request or column not found"},
        422: {"model": ErrorResponse, "description": "Validation error - invalid column name format"},
    },
    summary="Validate target column against uploaded file",
    description="Accepts a file upload and a target column name, validates the column exists in the dataset.",
)
async def set_target_column(
    file: UploadFile = File(...),
    target_column: str = Form(...),
) -> TargetColumnResponse:
    filename, content = await _read_upload_bytes(file)

    try:
        _validate_file_or_raise(content, filename)
        df = load_dataframe_from_bytes(content, filename)
        columns = df.columns.tolist()
        actual_target = _resolve_target_column(columns, target_column)
        if actual_target is None:
            raise HTTPException(status_code=400, detail="Target column is required.")

        message = (
            f"Target column '{actual_target}' found and set successfully."
            if actual_target == target_column
            else f"Target column found as '{actual_target}' (case-insensitive match)."
        )
        return TargetColumnResponse(
            valid=True,
            target_column=actual_target,
            message=message,
            available_columns=None,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to validate target column: {exc}") from exc

