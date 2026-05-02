#!/usr/bin/env bash
# End-to-end ablation: base → LoRA(full mix) → LoRA(MTS-Dialog only) → eval each.
#
# Assumes:
#   - Ollama already stopped (no concurrent VRAM users)
#   - data/mlx_full and data/mlx_mts_only already prepared via prepare_mlx_data.py
#   - HF_TOKEN exported in env (sourced from .env)
#   - mlx-lm and the chosen base model already downloaded
#
# Usage:
#   bash scripts/run_finetune_ablation.sh
#   MODEL=mlx-community/Qwen2.5-1.5B-Instruct-4bit ITERS=300 \
#     bash scripts/run_finetune_ablation.sh

set -euo pipefail

MODEL="${MODEL:-mlx-community/Qwen2.5-1.5B-Instruct-4bit}"
ITERS="${ITERS:-300}"
LIMIT="${LIMIT:-57}"

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPORTS_DIR="${PROJECT_ROOT}/evaluation/reports"
ADAPTERS_DIR="${PROJECT_ROOT}/adapters"
DATA_FULL="${PROJECT_ROOT}/data/mlx_full"
DATA_MTS="${PROJECT_ROOT}/data/mlx_mts_only"
TEST_SET="${PROJECT_ROOT}/data/splits/test.jsonl"
mkdir -p "$REPORTS_DIR" "$ADAPTERS_DIR"

short_name=$(echo "$MODEL" | sed 's/.*\///' | tr '[:upper:]' '[:lower:]')

# Source HF_TOKEN if present
if [ -f .env ]; then set -a; source .env; set +a; fi

start_backend() {
  local adapter="$1"
  pkill -f "uvicorn app.main" 2>/dev/null || true
  sleep 2
  ( cd "${PROJECT_ROOT}/backend" && \
      GENERATION_MODE=mlx \
      MLX_MODEL="$MODEL" \
      MLX_ADAPTER_PATH="$adapter" \
      MLX_MAX_TOKENS=2048 \
      MLX_MAX_TRANSCRIPT_CHARS=6000 \
      nohup uvicorn app.main:app --host 127.0.0.1 --port 8000 > /tmp/scribe_backend.log 2>&1 & )
  sleep 5
  curl -s http://localhost:8000/api/v1/health
  echo
}

run_eval() {
  local label="$1"
  local out="$2"
  echo "=== eval: $label ==="
  PYTHONUNBUFFERED=1 python -u "${PROJECT_ROOT}/evaluation/scripts/batch_evaluate.py" \
    --dataset "$TEST_SET" \
    --output "$out" \
    --mode mlx \
    --per-source \
    --limit "$LIMIT" \
    --timeout 600
}

run_finetune() {
  local data_dir="$1"
  local adapter="$2"
  echo "=== finetune: $data_dir -> $adapter ==="
  rm -rf "$adapter"
  mkdir -p "$adapter"
  python -m mlx_lm lora \
    --model "$MODEL" \
    --train \
    --data "$data_dir" \
    --iters "$ITERS" \
    --batch-size 1 \
    --learning-rate 1e-4 \
    --num-layers 8 \
    --adapter-path "$adapter" \
    --steps-per-report 25 \
    --steps-per-eval 100 \
    --save-every 100
}

# 1) Baseline: base model, no adapter
start_backend ""
run_eval "${short_name} base" "${REPORTS_DIR}/results_${short_name}_base.json"

# 2) Fine-tune on full mix
run_finetune "$DATA_FULL" "${ADAPTERS_DIR}/${short_name}_full"
start_backend "${ADAPTERS_DIR}/${short_name}_full"
run_eval "${short_name} ft full" "${REPORTS_DIR}/results_${short_name}_ft_full.json"

# 3) Ablation: fine-tune on MTS-Dialog only
run_finetune "$DATA_MTS" "${ADAPTERS_DIR}/${short_name}_mts"
start_backend "${ADAPTERS_DIR}/${short_name}_mts"
run_eval "${short_name} ft mts-only" "${REPORTS_DIR}/results_${short_name}_ft_mts.json"

# 4) Final comparison report
python evaluation/scripts/compare_runs.py \
  "${REPORTS_DIR}/results_demo_baseline.json" \
  "${REPORTS_DIR}/results_${short_name}_base.json" \
  "${REPORTS_DIR}/results_${short_name}_ft_full.json" \
  "${REPORTS_DIR}/results_${short_name}_ft_mts.json" \
  --out "${REPORTS_DIR}/comparison.md"

echo "all done. report: ${REPORTS_DIR}/comparison.md"
pkill -f "uvicorn app.main" 2>/dev/null || true
