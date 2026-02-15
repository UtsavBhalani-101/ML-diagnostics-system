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
| `POST` | `/validate-file` | Upload and validate dataset |
| `GET` | `/dataset-columns` | Retrieve dataset schema |
| `POST` | `/set-target-column` | Validate target column |
| `POST` | `/run-analysis` | Execute diagnostic pipeline |
| `GET` | `/layer-1-output` | Retrieve diagnostic results |

### 2. Session Engine (State Controller)

The enforcement layer of the system.

**Responsibilities:**

- Forward-only state transitions
- Dataset lifecycle management
- Diagnostic report storage
- Verdict synthesis
- Session reset and memory wipe

The session engine guarantees:

- No step skipping
- No duplicate uploads without reset
- No modeling before diagnostics

### 3. Diagnostic Engine

Diagnostics are organized into layers with defined scopes.

#### Layer 1 — Structural Triage

Performs dataset-level integrity analysis independent of target selection.

**Evaluates:**

- Dataset dimensionality and scale
- Missingness patterns
- Degenerate or near-constant features
- Duplicate density
- Structural anomalies
- Risk classification across standardized categories

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
  session_engine.py
  states.py
  file_support_check.py

engine/
  Layer_1/
  Layer_2/

frontend/
  Next.js application

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
# Upload file
curl -X POST http://127.0.0.1:8000/validate-file -F "file=@data.csv"

# Inspect columns
curl http://127.0.0.1:8000/dataset-columns

# Set target
curl -X POST http://127.0.0.1:8000/set-target-column \
  -H "Content-Type: application/json" \
  -d '{"target_column": "income"}'

# Run diagnostics
curl -X POST http://127.0.0.1:8000/run-analysis

# Retrieve results
curl http://127.0.0.1:8000/layer-1-output
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