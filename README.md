# SOAPFlow

SOAPFlow turns raw doctor-patient transcripts into structured SOAP notes.

It is a local-first clinical documentation stack with a FastAPI backend, a React frontend, streaming generation, transcription support, note history, search, validation, and evaluation workflows.

## What it includes

- Multiple generation backends
- Whisper-based transcription
- PHI de-identification
- Streaming SOAP generation
- Note history and search
- Validation and evaluation
- Local demo and Docker support

## Quick start

```bash
make install
make frontend-install
make api
make frontend
```

Open the frontend in your browser and paste a transcript.

## Features

- Audio or text input
- Streaming output
- Quality checks and warnings
- History and export
- Responsive frontend

## Notes

- The project supports several hosted and local model backends.
- It is designed for local clinical workflows and demo use.
- The backend and frontend can be run separately or together.

## Portfolio Proof

- Architecture and evaluation: [docs/PORTFOLIO_PROOF.md](/Users/sushildalavi/Desktop/Github/SOAPFlow/docs/PORTFOLIO_PROOF.md)
- Verified metrics: [evaluation/reports/comparison.md](/Users/sushildalavi/Desktop/Github/SOAPFlow/evaluation/reports/comparison.md) and [evaluation/reports/demo_results.json](/Users/sushildalavi/Desktop/Github/SOAPFlow/evaluation/reports/demo_results.json)
- Demo and local mode: use the quick start commands above and keep the default path local-first
- Test commands: backend pytest, frontend `npm run build`
