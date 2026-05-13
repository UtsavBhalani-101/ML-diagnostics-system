# ML Diagnostic Engine

A diagnostic-first machine learning system that evaluates dataset integrity and structural validity before permitting model execution.

Modeling is not the default action.
It is a consequence of validated data.

---

## Why This Exists

Most ML workflows prioritize speed of model training over data validity.

This system reverses that order.

Instead of:

```
Upload → Train → Inspect Accuracy
```

It enforces:

```
Upload → Diagnose → Synthesize Verdict → (Maybe) Model
```

Model execution is granted only after centralized diagnostic evaluation.

---

## Core Principles

- Diagnostics before modeling
- Centralized decision authority
- Explicit forward-only state transitions
- Single dataset per session
- No silent overrides
- Permission derived from severity hierarchy

---

## High-Level Workflow

1. Upload and validate dataset
2. Inspect dataset schema
3. Set target column
4. Run structural diagnostics (Layer 1)
5. Synthesize verdict
6. If permitted → model execution phase

All modeling permissions are determined by diagnostic severity.

---

## Architecture Overview

The system is composed of four primary layers:

### 1. Backend API (FastAPI)

The REST interface orchestrating the workflow.

**Responsibilities:**

- File upload and validation
- Dataset inspection
- Target column validation
- Diagnostic execution
- Result retrieval
- Strict schema enforcement

**Key endpoints include:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/validate-file` | Upload and validate dataset (max 10 MB) |
| `POST` | `/dataset-columns` | Upload file and get column names |
| `POST` | `/set-target-column` | Upload file and validate a target column |
| `POST` | `/api/diagnostics/run` | Upload dataset with target and run Layer 1 diagnostics |
| `GET` | `/supported-extensions` | List supported file formats |
| `GET` | `/api/docs` | Get product documentation content |
| `GET` | `/api/models` | Get model-layer status |

### 2. Diagnostic Engine

Diagnostics are organized into layers with defined scopes.

#### Layer 1 — Structural Triage

Performs dataset-level integrity analysis independent of target selection.

**Evaluates:**

- Data Integrity: missingness, duplicates, constant columns, hidden missing values, mixed types
- Target Validity: missing labels, target variability, class imbalance, task inference
- Sample Adequacy: sample-to-feature ratio, small-sample and overfitting risk

Produces structured findings with severity:

```
SAFE
WARNING
CRITICAL
```

Layer 2 (Feature-Level Diagnostics) is under development and extends analysis per feature type.

### 4. Verdict Synthesis

Permission logic is centralized within the Session Engine.

**Severity hierarchy:**

| Condition | Verdict | Effect |
|-----------|---------|--------|
| Any `CRITICAL` | `BLOCKED` | Modeling disabled |
| Any `WARNING` | `CONSTRAINED` | Modeling allowed with restrictions |
| All `SAFE` | `ALLOWED` | Full modeling access |

Diagnostics do not enforce constraints directly.
They only produce findings.

The Verdict determines permissions.

---

## System State Machine

The engine follows a strict forward-only progression:

```
NO_SESSION
  → DATA_LOADED
    → DIAGNOSTICS_RUNNING
      → MODEL_DECIDED
        → MODEL_EXECUTION
```

The only backward transition:

```python
reset_session()
```

State enforces order.
Verdict enforces permissions.

---

## What Makes This Different

| Traditional ML Tools | ML Diagnostic Engine |
|----------------------|----------------------|
| Modeling is default | Modeling is earned |
| Warnings are advisory | Warnings affect permissions |
| Failures may be silent | Critical findings block execution |
| Constraints are scattered | Constraints derived centrally |
| Multiple datasets active | One dataset per session |
| Loose workflow order | Strict state enforcement |

This system prioritizes epistemic integrity over convenience.

---

## Project Structure

```
Backend/
  api.py
  file_support_check.py

engine/
  Layer_1/
    Signals/
    Logic/
    pipeline.py
    formatter.py
    risk_template.py
  Layer_2/

frontend/
  Next.js application (apps/web/)

uploads/
results/
tests/
```

Internal diagnostic heuristics are implemented within the engine modules.

---

## How to run

### Backend

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn Backend.api:app --reload
```

API available at: `http://127.0.0.1:8000`

Docs available at: `http://127.0.0.1:8000/docs`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend available at: `http://localhost:3001`

---

## Example Usage (API)

```bash
# Validate a file
curl -X POST http://127.0.0.1:8000/validate-file -F "file=@data.csv"

# Get columns from uploaded file
curl -X POST http://127.0.0.1:8000/dataset-columns -F "file=@data.csv"

# Validate target column
curl -X POST http://127.0.0.1:8000/set-target-column \
  -F "file=@data.csv" \
  -F "target_column=income"

# Run Layer 1 diagnostics
curl -X POST http://127.0.0.1:8000/api/diagnostics/run \
  -F "file=@data.csv" \
  -F "target_column=income"
```

---

## Design Philosophy

| Component | Role |
|-----------|------|
| Signals | Extract quantitative facts |
| Logic | Interpret facts |
| Diagnostics | Produce standardized findings |
| Verdict | Synthesize severity into permission |
| Session Engine | Enforce policy |
| State Machine | Prevent workflow violations |

---

## Future Direction

- Persistent session storage
- User authentication
- Full Layer 2 feature-level diagnostics
- Constraint-aware model execution
- Report export (JSON / PDF)
- Programmatic API extensions