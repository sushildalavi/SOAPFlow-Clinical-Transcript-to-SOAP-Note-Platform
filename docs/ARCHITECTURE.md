# SOAPFlow — Architecture

This document is a quick map of how SOAPFlow is wired together. It is meant
for someone who has just cloned the repo and wants to know where to look
before changing things.

---

## High level

```
              ┌──────────────────────────┐
              │        Frontend          │
              │   React 19 + Vite + TS   │
              │  Tailwind + shadcn/ui    │
              └────────────┬─────────────┘
                           │ REST + SSE
                           ▼
              ┌──────────────────────────┐
              │        Backend           │
              │    FastAPI (Python 3.11) │
              │  Pydantic v2 / SQLAlch.  │
              └────────────┬─────────────┘
       ┌────────────┬──────┴──────┬─────────────┐
       ▼            ▼             ▼             ▼
   SQLite/PG     Redis        Qdrant        Whisper / LLM
   (history)   (cache)       (search)       (inference)
```

The boring stack on purpose — nothing fancy, easy to deploy, easy to swap
out a piece at a time.

---

## Backend layout (`backend/app/`)

| Path             | What lives here                                                 |
| ---------------- | --------------------------------------------------------------- |
| `main.py`        | FastAPI app factory, lifespan hooks, router wiring.             |
| `core/`          | Cross-cutting: config, logging, auth, middleware, metrics.      |
| `api/routes/`    | One module per route group (transcribe, generate, history, …). |
| `services/`      | Business logic: SOAP generation, ASR, de-id, cache, search.    |
| `db/`            | SQLAlchemy engine/session and ORM models.                       |
| `schemas/`       | Pydantic request/response models — the wire contract.           |
| `models/`        | Domain dataclasses (the SOAP note structure).                   |
| `utils/`         | Small helpers.                                                  |

### Request flow for `/api/generate`

```
Client ─► auth middleware ─► rate-limit ─► route handler
                                                │
                                                ▼
                                        services.generator
                                          │   │   │
                                          │   │   └─ services.cache  (lookup)
                                          │   └────── services.deidentify
                                          └────────── services.prompts
                                                │
                                                ▼
                                          LLM (OpenAI / local Qwen via MLX)
                                                │
                                                ▼
                                          services.validator
                                                │
                                                ▼
                                         persist (db.models.Note)
```

`/api/stream` follows the same path but yields tokens via SSE.

### Database

Default is SQLite for local dev (`backend/soapflow.db`). For anything
beyond a laptop, point `DATABASE_URL` at Postgres — SQLAlchemy handles
the rest. Migrations are not in yet; we recreate tables on first boot.

---

## Frontend layout (`frontend/src/`)

| Path                  | What lives here                                  |
| --------------------- | ------------------------------------------------ |
| `App.tsx`             | Top-level routing/layout.                        |
| `lib/api.ts`          | Thin fetch wrapper around the backend.           |
| `lib/utils.ts`        | UI helpers (clsx, formatters).                   |
| `hooks/`              | `useStream`, `useGenerate`, `useHistory`, etc.   |
| `components/ui/`      | shadcn-style primitives (button, card, …).       |
| `components/soap/`    | SOAP-specific UI (input, output, section cards). |
| `components/voice/`   | Mic capture + waveform.                          |
| `components/history/` | Past notes browser.                              |

`useStream` opens an `EventSource` to `/api/stream` and progressively
fills the SOAP section cards as tokens arrive. That's the whole magic
trick — the rest is plumbing.

---

## Datasets and training

Anything under `scribe_datasets/` is glue code that turns a public dataset
(MTS-Dialog, ACI-Bench, OMI-Health, Primock57, MIMIC notes, etc.) into a
common JSONL schema with `transcript` and `soap` fields.

`scripts/build_dataset_stack.py` runs all the adapters and produces the
mixed dataset that `training/scripts/finetune_*.py` consumes.

We track raw artifacts and trained adapter weights with **DVC**
(`dvc.yaml`), not git. Adapter metadata (the small `adapter_config.json`
plus a README) is committed so reviewers can see what was trained.

---

## Why these choices

- **FastAPI** — async, easy to add streaming endpoints, Pydantic schemas
  give us OpenAPI for free.
- **SQLite by default** — keeps the "clone and run" story honest. Swap
  to Postgres for shared environments.
- **Qdrant** for vector search — runs locally in Docker, no extra ops.
- **MLX adapters** for the local model path — Apple Silicon only, but
  the inference is fast enough for a real demo on a laptop.
- **shadcn/ui** — copy-paste components instead of a heavyweight UI
  library; we own the code and can tweak it.

---

## What's intentionally out of scope

- Multi-tenant auth / RBAC. There's a single-user JWT flow, that's it.
- Real BAA-grade HIPAA controls (see `HIPAA.md` for the disclaimer).
- A migrations system. Add Alembic when the schema starts to churn.
- Any kind of usage billing / metering.
