# Working notes

Loose collection of design decisions, gotchas, and "I'll forget this
in a week" reminders. Not polished — feel free to add to it.

---

## SOAP schema

We follow the classic four-section structure:

- **Subjective** — patient's own words, HPI, ROS.
- **Objective** — vitals, exam findings, results.
- **Assessment** — clinical impression, differential.
- **Plan** — meds, follow-up, patient education.

The model's output is forced to JSON via the prompt + a Pydantic
validator. If parsing fails we retry once with a "respond with valid
JSON only" nudge before giving up and surfacing the raw text.

## Why two model paths

There are two generation paths and they exist for different reasons:

1. **OpenAI** (`gpt-4o-mini` by default) — for the hosted demo and as a
   strong baseline in evals.
2. **Local Qwen 2.5 1.5B + LoRA adapter** via MLX — for showing the
   project runs end-to-end on a laptop with no API keys, and for the
   "small fine-tuned model can match a big base model" story in evals.

Don't add a third unless there's a clear reason.

## De-identification

The de-id pipeline is deliberately conservative — false positives are
fine, false negatives are not. Order matters:

1. Regex sweep (SSN, MRN, phone, email, dates).
2. spaCy NER for PERSON, GPE, ORG.
3. Optional Presidio pass when configured.

Replacement is `[NAME]`, `[DATE]`, `[ADDRESS]`, etc. — keeping the
shape of the sentence so the LLM still has context.

## Caching

`services/cache.py` uses Redis when `REDIS_URL` is set, otherwise an
in-process LRU. Cache key is `soapflow:{prefix}:{sha256(payload)}`.
We cache by the *de-identified* transcript so the same conversation
typed slightly differently doesn't double-charge an OpenAI call.

## Streaming

Server-Sent Events, not WebSockets. SSE is one-way which is exactly
what we need (server pushes tokens, client never sends mid-stream),
auto-reconnects in browsers for free, and works through almost any
proxy without configuration.

## Evaluation

`evaluation/scripts/batch_evaluate.py` runs a model against a held-out
split and writes a JSON report into `evaluation/reports/`. The current
metric set:

- ROUGE-1 / ROUGE-L vs reference SOAP.
- Section coverage (did the model produce all four sections?).
- PHI leak count (any de-id miss in the output?).
- Latency p50 / p95.

Comparison is done by `evaluation/scripts/compare_runs.py` which spits
out `evaluation/reports/comparison.md`.

## Things I broke and fixed (so future-me doesn't)

- **CORS**: forgot to allow `Authorization` in `expose_headers`.
  Symptom: token shows up on the Network tab but `useStream` can't
  read it. Fix in `core/middleware.py`.
- **SSE through nginx**: needs `proxy_buffering off` and
  `proxy_read_timeout` bumped, otherwise the first token shows up
  after the *whole* generation finishes. Fix in `frontend/nginx.conf`.
- **MLX adapters loading slowly**: don't reload per request. The
  generator service caches the loaded model in module scope and
  reuses it.

## Open ideas (not commitments)

- Section-level streaming (each card streams independently).
- Confidence scores per SOAP section so the UI can flag low-conf
  bits for review.
- A proper migrations setup — Alembic, probably.
- Evaluator using GPT-4 as a judge for clinical faithfulness, not
  just lexical overlap.
