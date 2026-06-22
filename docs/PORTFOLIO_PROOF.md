# Portfolio Proof

## What the project does

SOAPFlow is a healthcare note generation system with transcription, de-identification, multiple backend options, and evaluation artifacts.

## Why it is technically impressive

- It combines privacy-sensitive preprocessing with generation and validation.
- The repo includes local and backend-flexible workflows.
- Evaluation artifacts compare rule-based and model-based approaches.

## Architecture summary

- Transcript or audio input -> de-identification/transcription -> SOAP note generation -> validation/evaluation -> frontend review.

## How to run locally

- `make install`
- `make frontend-install`
- `make api`
- `make frontend`

## How to test

- `pytest`
- `npm run build` in `frontend/`
- Any synthetic PHI or SOAP checklist tests added under `backend/tests/`

## How to benchmark or evaluate

- Review `evaluation/reports/comparison.md`
- Review `evaluation/reports/demo_results.json`

## Verified metrics only

- Rule-based demo ROUGE-L: 0.0947
- Rule-based demo latency: 2 ms
- Qwen 2.5 7B few-shot ROUGE-L: 0.1757
- Qwen 2.5 7B few-shot latency: 57,588 ms

## Current limitations

- No real PHI should ever be used in fixtures or docs.
- Full cloud-backed workflows should remain optional, not required.

## Future improvements

- Add a local privacy mode guide and deterministic de-identification evaluator.
- Add SOAP note validation checks and a small FHIR-inspired export path.
- Add synthetic fixtures with documented failure cases.

## Resume bullets

- Built a healthcare note generation pipeline with transcription, de-identification, and evaluation artifacts.
- Compared rule-based and model-based generations using verified ROUGE-L and latency measurements.
- Designed the system to support local-first clinical demos without requiring paid APIs.

## Verification Log

- `python3 /Users/sushildalavi/Desktop/Github/SOAPFlow/scripts/evaluate_deid.py` - pass - 2026-06-17 - Evaluated synthetic PHI fixtures with fallback de-identification.
- `python3 -m pytest /Users/sushildalavi/Desktop/Github/SOAPFlow/backend/tests/test_deid_eval.py` - pass - 2026-06-17 - Verified the synthetic de-id evaluator.
