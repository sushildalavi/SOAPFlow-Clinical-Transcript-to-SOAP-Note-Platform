# Contributing to SOAPFlow

This is a portfolio project, but PRs and issues are welcome — bug reports,
docs fixes, evaluation runs against new datasets, all useful.

## Getting set up

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

If you only want to poke at the API, the backend works without the
frontend running and vice versa (the frontend hits `http://localhost:8000`
by default — change `VITE_API_URL` to point elsewhere).

## Branching

`main` is the trunk. For non-trivial changes, branch off, push, open a PR.
For one-line typo fixes feel free to push straight to `main`.

## Commit style

Short, lowercase, imperative — `fix history pagination`, `bump fastapi`,
`tighten phi regex`. Don't worry about Conventional Commits, but try to
keep one logical change per commit.

## Tests

```bash
cd backend && pytest
cd frontend && npm test
```

Backend uses `pytest` + `httpx`'s `AsyncClient`. Frontend uses Vitest +
Testing Library. CI is not wired up yet — please run them locally before
opening a PR.

## Style

- **Python**: ruff for lint, black for formatting (line length 100).
- **TypeScript**: eslint + the project's existing config. No prettier
  config; let eslint handle it.
- Prefer adding to existing files over creating new ones.
- Keep functions small. If a service module is creeping past ~300 lines
  it is probably hiding two services in a trench coat.

## Adding a new dataset adapter

1. Drop a new file in `scribe_datasets/adapters/<name>_adapter.py`.
2. Subclass `BaseAdapter` and implement `iter_examples()` yielding
   `{"transcript": str, "soap": dict}` records.
3. Register it in `scribe_datasets/adapters/__init__.py`.
4. Add the dataset to `scripts/build_dataset_stack.py`.
5. Run `python scripts/build_dataset_stack.py --only <name>` to smoke
   test, then a full build to produce a fresh mixed split.

## Adding a new evaluation metric

Metrics live in `backend/app/services/evaluator.py`. The evaluator
returns a flat dict keyed by metric name; `evaluation/scripts/` reads
those dicts to build comparison reports. Add the metric, regenerate
`evaluation/reports/comparison.md`, and include the diff in your PR.

## Things to avoid

- Bringing in a heavy UI library when a shadcn primitive will do.
- Adding migrations frameworks "in case we need them later". When the
  schema actually starts to churn, then we add Alembic.
- Logging PHI. Anything user-supplied gets de-identified before it goes
  near a structured log line.
