# SOAPFlow — Turn Doctor-Patient Conversations into SOAP Notes, Instantly

![SOAPFlow Banner](https://img.shields.io/badge/SOAPFlow-AI%20Clinical%20Scribe-0ea5e9?style=for-the-badge&logo=stethoscope)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.9-3178C6?style=flat-square&logo=typescript)](https://www.typescriptlang.org/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

> **SOAPFlow** converts raw doctor-patient conversation transcripts into structured, clinically formatted **SOAP notes** in seconds using state-of-the-art AI. Built for doctors, nurses, and clinical staff who need fast, accurate medical documentation.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Frontend Guide](#frontend-guide)
- [Docker Deployment](#docker-deployment)
- [Development](#development)
- [Testing](#testing)
- [Fine-tuning](#fine-tuning)
- [Evaluation](#evaluation)
- [Contributing](#contributing)

---

## Overview

SOAP (Subjective, Objective, Assessment, Plan) notes are the universal standard for clinical documentation. Writing them manually after every patient visit is time-consuming. SOAPFlow automates this process by:

1. Accepting raw, unformatted conversation transcripts
2. Running them through GPT-4o, Claude, a local Ollama model, or a built-in demo engine
3. Returning a complete, structured SOAP note with quality validation warnings
4. Persisting notes in a local history for future reference

**Supported AI Backends:**
| Mode | Model | Notes |
|------|-------|-------|
| `openai` | GPT-4o | Best quality, requires OpenAI API key |
| `anthropic` | Claude claude-opus-4-6 | High quality, requires Anthropic API key |
| `demo` | Rule-based | Always available, no API key needed |

---

## Features

### Core
- **One-click SOAP generation** from any conversation transcript
- **3 AI backends** — OpenAI, Anthropic, or demo mode
- **Smart validation** — 10+ automated quality checks with severity levels (info / warning / error)
- **Note history** — SQLite persistence to save, retrieve, and delete past notes
- **Batch generation** — Process up to 10 transcripts in one API call
- **ROUGE + BLEU evaluation** — Score your notes against a reference standard
- **8 demo transcripts** across diverse clinical scenarios

### Frontend
- Split-panel layout (transcript input | SOAP output)
- Live word/character counter
- Formatted SOAP view + Raw JSON viewer
- History panel to browse and reload past notes
- Model selector (OpenAI / Anthropic / Demo)
- Export as plain text or JSON
- Print to PDF
- Toast notifications
- Fully responsive (mobile + desktop)

### API
- Auto-generated OpenAPI docs at `/docs`
- Request ID tracking
- CORS configuration
- Structured error responses

---

## Architecture

```
SOAPFlow/
├── backend/                    # FastAPI Python backend
│   ├── app/
│   │   ├── main.py             # Application entry point
│   │   ├── core/
│   │   │   ├── config.py       # Pydantic settings (env vars)
│   │   │   └── exceptions.py   # Custom HTTP exceptions
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── generate.py  # POST /generate, /batch-generate
│   │   │       ├── history.py   # GET/POST/DELETE /history
│   │   │       ├── evaluate.py  # POST /evaluate
│   │   │       ├── health.py    # GET /health
│   │   │       └── demo.py      # GET /demo-transcript
│   │   ├── db/
│   │   │   ├── database.py     # SQLAlchemy engine + session
│   │   │   └── models.py       # ORM models (SOAPNoteRecord)
│   │   ├── services/
│   │   │   ├── generator.py    # SOAP generation logic
│   │   │   ├── validator.py    # Quality checks & warnings
│   │   │   ├── evaluator.py    # ROUGE/BLEU scoring
│   │   │   └── prompts.py      # System & user prompts
│   │   └── schemas/
│   │       ├── request.py      # Request DTOs
│   │       └── response.py     # Response models
│   ├── tests/                  # pytest test suite
│   └── requirements.txt
│
├── frontend/                   # React + Vite + TypeScript
│   ├── src/
│   │   ├── App.tsx             # Root component + layout
│   │   ├── components/
│   │   │   ├── soap/           # Transcript input, SOAP output
│   │   │   ├── history/        # Note history panel
│   │   │   ├── layout/         # Navbar
│   │   │   └── ui/             # Reusable Radix UI components
│   │   ├── hooks/              # useGenerate, useHistory, useSettings
│   │   ├── lib/                # API client, utilities
│   │   └── types/              # TypeScript interfaces
│   └── package.json
│
├── datasets/                   # Dataset adapters for training data
├── training/                   # Fine-tuning pipeline scripts
├── evaluation/                 # Evaluation notebooks + scripts
├── scripts/                    # Setup and start scripts
├── docker-compose.yml          # Full stack Docker deployment
└── .github/workflows/          # CI/CD pipelines
```

**Data Flow:**
```
Transcript → Validation → AI Model → Structured JSON → Quality Checks → SOAP Note + Warnings
                                                                            ↓
                                                                     SQLite History DB
```

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- (Optional) OpenAI or Anthropic API key

### 1. Clone & Configure

```bash
git clone https://github.com/sushildalavi/SOAPFlow.git
cd SOAPFlow
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your API keys (optional — demo mode works without them)

# Start the API server
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`
- Swagger docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The app will be available at `http://localhost:5173`

### One-command setup (macOS/Linux)

```bash
bash scripts/setup.sh
```

---

## Configuration

All configuration is via environment variables in `backend/.env`:

```env
# AI Provider API Keys (at least one recommended for production)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Generation Mode: "openai" | "anthropic" | "demo"
# Auto-detected from available keys if not set
GENERATION_MODE=demo

# Model selection (optional — defaults shown)
OPENAI_MODEL=gpt-4o
ANTHROPIC_MODEL=claude-opus-4-6

# App settings
APP_VERSION=1.0.0
DEBUG=false

# CORS — add your production frontend URL
ALLOWED_ORIGINS=["http://localhost:5173","http://localhost:3000"]

# Input limits
MAX_TRANSCRIPT_LENGTH=20000
MIN_TRANSCRIPT_LENGTH=50
```

**Priority Logic:** If `GENERATION_MODE=demo` but API keys are present, the server auto-promotes to `openai` (or `anthropic` if no OpenAI key).

---

## API Reference

### Health

```
GET /api/v1/health
```
Returns server status, API configuration, and active generation mode.

**Response:**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "generation_mode": "openai",
  "openai_configured": true,
  "anthropic_configured": false
}
```

---

### Generate SOAP Note

```
POST /api/v1/generate
```

**Request Body:**
```json
{
  "transcript": "Doctor: What brings you in today?\nPatient: I've had a headache...",
  "include_raw_json": true,
  "mode": null
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `transcript` | string | Yes | Raw conversation text (50–20,000 chars) |
| `include_raw_json` | boolean | No | Return raw JSON in response (default: true) |
| `mode` | string \| null | No | Override: `"openai"`, `"anthropic"`, `"demo"` |

**Response:**
```json
{
  "success": true,
  "soap_note": {
    "subjective": "Patient reports 3-day headache...",
    "objective": "BP 120/80, HR 72, temp 98.6°F...",
    "assessment": "Tension-type headache, likely stress-related...",
    "plan": "1. Ibuprofen 400mg TID PRN pain..."
  },
  "warnings": [
    {
      "code": "MISSING_OBJECTIVE_DATA",
      "message": "Objective section may be missing measurable clinical data.",
      "severity": "info",
      "field": "objective"
    }
  ],
  "metadata": {
    "model": "gpt-4o",
    "mode": "openai",
    "transcript_word_count": 342,
    "transcript_char_count": 2180,
    "note_word_count": 98,
    "processing_time_ms": 2341.5,
    "sections_populated": 4
  }
}
```

---

### Batch Generate

```
POST /api/v1/batch-generate
```

Process up to 10 transcripts in a single request.

```json
{
  "transcripts": ["Doctor: ...", "Doctor: ..."]
}
```

---

### History

```
GET    /api/v1/history              # List all saved notes
POST   /api/v1/history              # Save a note
GET    /api/v1/history/{id}         # Get a specific note
DELETE /api/v1/history/{id}         # Delete a note
DELETE /api/v1/history              # Clear all history
```

**Save Note Request:**
```json
{
  "transcript": "...",
  "soap_note": { "subjective": "...", ... },
  "metadata": { "model": "gpt-4o", ... },
  "title": "Optional custom title"
}
```

---

### Evaluate

```
POST /api/v1/evaluate
```

Score a generated note against a reference using ROUGE/BLEU metrics.

```json
{
  "transcript": "...",
  "generated_note": { "subjective": "...", ... },
  "reference_note": { "subjective": "...", ... }
}
```

---

### Demo Transcripts

```
GET /api/v1/demo-transcripts/list   # List available demo cases
GET /api/v1/demo-transcript?index=0 # Get specific demo transcript
```

Available demos:
| Index | Title | Scenario |
|-------|-------|----------|
| 0 | Hypertension Follow-Up | Type 2 DM + HTN management |
| 1 | Acute Respiratory | Community-acquired pneumonia |
| 2 | Pediatric Well Visit | 6-year well-child check |
| 3 | Mental Health Consult | Depression screening |
| 4 | Emergency Chest Pain | Acute MI workup |
| 5 | Chronic Pain | Fibromyalgia management |
| 6 | Orthopedic Consult | Knee injury evaluation |
| 7 | Diabetes New Onset | Type 2 DM initial presentation |

---

## Frontend Guide

### Generate a SOAP Note
1. Paste your transcript in the left panel
2. (Optional) Select AI model from the dropdown
3. Click **Generate SOAP Note**
4. Review the formatted note, warnings, and metadata in the right panel

### History Panel
- Click the **History** icon in the navbar to open the history sidebar
- Previous notes are grouped by date
- Click any note to reload it in the output panel
- Delete individual notes or clear all history

### Export Options
- **Text** — Downloads a formatted `.txt` file
- **JSON** — Downloads structured SOAP data as `.json`
- **Print** — Opens browser print dialog (optimized for PDF export)

### Model Selector
Use the model dropdown in the transcript input panel to override the server's default generation mode on a per-request basis.

---

## Docker Deployment

### Full Stack (Recommended)

```bash
# Copy and configure environment
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys

# Start everything
docker-compose up --build
```

Services:
- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`

### Backend Only

```bash
cd backend
docker build -t soapflow-api .
docker run -p 8000:8000 --env-file .env soapflow-api
```

---

## Development

### Backend Development

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

The server auto-reloads on file changes. The SQLite database (`soapflow.db`) is created automatically in the `backend/` directory on first run.

### Frontend Development

```bash
cd frontend
npm run dev
```

The Vite dev server proxies all `/api` requests to `http://localhost:8000`.

### Adding a New AI Backend

1. Add generation function in `backend/app/services/generator.py`
2. Add the mode to `Literal["openai", "anthropic", "demo", "new_mode"]` in `config.py`
3. Update the `generate_soap()` dispatcher function
4. Add API key to `.env.example`

---

## Testing

### Backend Tests

```bash
cd backend
source venv/bin/activate
pytest tests/ -v
```

Test coverage:
- `test_health.py` — Health endpoint
- `test_generate.py` — SOAP generation (demo mode)
- `test_validation.py` — Transcript and note validation
- `test_history.py` — History CRUD operations
- `test_evaluate.py` — Evaluation scoring
- `test_demo.py` — Demo transcript endpoints

### Frontend Tests

```bash
cd frontend
npm run test
```

---

## Fine-tuning

To fine-tune your own model on clinical transcripts:

```bash
# Generate synthetic training data
python training/scripts/prepare_dataset.py --output data/training.jsonl --count 500

# Submit fine-tuning job (OpenAI)
python training/scripts/finetune_openai.py --data data/training.jsonl

# Monitor the job
python training/scripts/finetune_openai.py --check --job-id ftjob-xxx
```

See `training/configs/openai_finetune.json` for hyperparameter configuration.

---

## Evaluation

### Dataset stack

SOAPFlow is trained and evaluated against a tiered dataset stack defined in
[`scribe_datasets/adapters/__init__.py`](scribe_datasets/adapters/__init__.py).
Each adapter normalizes its source into `(transcript, soap_note)` pairs.

| Tier | Datasets | Role |
| --- | --- | --- |
| **Gold (real dialogue ↔ note)** | ACI-Bench, MTS-Dialog, PriMock57 | benchmark + train |
| **Synthetic augmentation** | NoteChat, Augmented Clinical Notes, omi-health | scale |
| **Style/format only** | MIMIC-IV-Note, MTSamples | note adaptation |

See [`data/README.md`](data/README.md) for per-dataset paths and licensing.

### Build splits

```bash
python scripts/build_dataset_stack.py --output-dir data/splits
```

The script is best-effort — missing datasets are reported and skipped, and
`data/splits/manifest.json` records what was built and what was missing.

### Evaluate

Free local path with [Ollama](https://ollama.com/):

```bash
ollama pull qwen2.5:7b
GENERATION_MODE=ollama OLLAMA_MODEL=qwen2.5:7b \
  uvicorn app.main:app --app-dir backend
python evaluation/scripts/batch_evaluate.py \
  --dataset data/splits/test.jsonl \
  --output evaluation/reports/results.json \
  --mode ollama \
  --per-source
```

`--per-source` breaks ROUGE-L / sections-populated out by dataset (PriMock57,
ACI-Bench, etc.) so ablations stay honest.

Jupyter notebook for interactive analysis:

```bash
cd evaluation/notebooks
jupyter notebook soap_evaluation.ipynb
```

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes with tests
4. Run the test suite: `cd backend && pytest tests/ -v`
5. Submit a pull request

### Code Style
- **Python:** Black formatter, isort imports, type hints throughout
- **TypeScript:** ESLint + Prettier, strict mode enabled
- **Commits:** Conventional commits (`feat:`, `fix:`, `test:`, `docs:`)

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Acknowledgements

Built with [FastAPI](https://fastapi.tiangolo.com/), [React](https://react.dev/), [Tailwind CSS](https://tailwindcss.com/), [OpenAI](https://openai.com/), [Anthropic Claude](https://anthropic.com/), [Ollama](https://ollama.com/), and [Radix UI](https://radix-ui.com/).

Datasets: [ACI-Bench](https://physionet.org/content/aci-bench/), [MTS-Dialog](https://github.com/abachaa/MTS-Dialog), [PriMock57](https://github.com/babylonhealth/primock57), [NoteChat](https://huggingface.co/datasets/akemiH/NoteChat), [Augmented Clinical Notes](https://huggingface.co/datasets/AGBonnet/augmented-clinical-notes), [omi-health](https://huggingface.co/datasets/omi-health/medical-dialogue-to-soap-summary), [MIMIC-IV-Note](https://physionet.org/content/mimic-iv-note/), [MTSamples](https://www.kaggle.com/datasets/tboyle10/medicaltranscriptions).
