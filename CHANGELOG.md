# Changelog

All notable changes to SOAPFlow are tracked here. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) without the
strict semver discipline — this is a portfolio project, not a library.

## [Unreleased]

- Section-level streaming so each SOAP card fills independently.
- Per-section confidence scores surfaced in the UI.

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
