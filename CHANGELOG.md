# Changelog

All notable changes to SOAPFlow are tracked here. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) without the
strict semver discipline — this is a portfolio project, not a library.

## [Unreleased]

- Section-level streaming so each SOAP card fills independently.
- Per-section confidence scores surfaced in the UI.

### Added

- Few-shot worked example baked into the SOAP system prompt
  (`backend/app/services/prompts.py`).
- New eval run `evaluation/reports/results_ollama_qwen25_7b_fewshot.json`:
  Qwen 2.5 7B + few-shot scores **0.176 ROUGE-L / 0.322 ROUGE-1** on the
  PriMock57 split — 1.85× the rule-based baseline and 1.24× the same
  model with no few-shot. See `evaluation/reports/comparison.md`.

### Changed

- `evaluation/scripts/compare_runs.py` now labels report rows by model
  name (parsed from per-example metadata) instead of dataset filename,
  so the comparison table actually tells you what was run.

### Docs

- README rewritten so the supported-backend table actually matches the
  code (6 backends — openai, anthropic, groq, ollama, mlx, demo —
  instead of the old 3).
- Architecture tree corrected: `datasets/` → `scribe_datasets/`, plus
  `data/`, `adapters/`, `monitoring/`, `docs/` are now listed.
- Six Mermaid diagrams added to README: backend selection, system
  overview, request lifecycle, SSE streaming flow, training/eval
  pipeline, Docker topology, plus two ROUGE/latency bar charts.
- Env example block expanded to cover all six backends (Groq, Ollama,
  MLX) with their actual env-var names and defaults.
- Fine-tuning section now documents both the OpenAI and MLX paths and
  the three trained adapters under `adapters/`.

## [0.1.0] — 2026-05-02

First public-ish version. Everything end-to-end works on a laptop.

### Added

- FastAPI backend with transcribe, generate, stream, history, search,
  and evaluate routes.
- React 19 + Vite frontend with the four SOAP section cards, voice
  recorder, history panel, and settings.
- Server-Sent-Events streaming from `/api/stream`.
- De-identification pipeline (regex + spaCy, optional Presidio).
- Redis-backed cache with in-process fallback.
- Qdrant vector search over past notes.
- Two generation paths: OpenAI hosted, local Qwen 2.5 1.5B + MLX LoRA.
- Dataset adapters for MTS-Dialog, ACI-Bench, OMI-Health, Primock57,
  MIMIC notes, MTSamples, MedDialog, NoteChat, and an in-house
  augmented-notes set.
- Fine-tuning recipes for OpenAI and MLX.
- Evaluation harness (ROUGE, section coverage, PHI leak count, latency).
- DVC pipeline for data + adapter artefacts.
- `docker-compose.yml` for the full stack (API, frontend, Redis,
  Qdrant, MLflow, Prometheus, Grafana).
- HIPAA awareness doc.
