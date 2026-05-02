#!/usr/bin/env bash
# v2 ablation: train on cleaned data (full mix vs omi-health-only), eval each.
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MODEL="${MODEL:-mlx-community/Qwen2.5-1.5B-Instruct-4bit}"
ITERS="${ITERS:-300}"
LIMIT="${LIMIT:-57}"

REPORTS_DIR="${PROJECT_ROOT}/evaluation/reports"
ADAPTERS_DIR="${PROJECT_ROOT}/adapters"
DATA_FULL="${PROJECT_ROOT}/data/mlx_full"
DATA_OMI="${PROJECT_ROOT}/data/mlx_omi_only"
TEST_SET="${PROJECT_ROOT}/data/splits/test.jsonl"
short_name=$(echo "$MODEL" | sed 's/.*\///' | tr '[:upper:]' '[:lower:]')

if [ -f "${PROJECT_ROOT}/.env" ]; then set -a; source "${PROJECT_ROOT}/.env"; set +a; fi

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
  local label="$1"; local out="$2"
  echo "=== eval: $label ==="
  PYTHONUNBUFFERED=1 python -u "${PROJECT_ROOT}/evaluation/scripts/batch_evaluate.py" \
    --dataset "$TEST_SET" --output "$out" --mode mlx --per-source --limit "$LIMIT" --timeout 600
}

run_finetune() {
  local data_dir="$1"; local adapter="$2"
  echo "=== finetune: $data_dir -> $adapter ==="
  pkill -f "uvicorn app.main" 2>/dev/null || true
  sleep 2
  rm -rf "$adapter"; mkdir -p "$adapter"
  python -m mlx_lm lora \
    --model "$MODEL" --train --data "$data_dir" --iters "$ITERS" \
    --batch-size 1 --learning-rate 1e-4 --num-layers 8 \
    --adapter-path "$adapter" --steps-per-report 25 --steps-per-eval 100 --save-every 100
}

# 1) Fine-tune on cleaned full mix
run_finetune "$DATA_FULL" "${ADAPTERS_DIR}/${short_name}_v2_full"
start_backend "${ADAPTERS_DIR}/${short_name}_v2_full"
run_eval "${short_name} v2 ft full" "${REPORTS_DIR}/results_${short_name}_v2_ft_full.json"

# 2) Ablation: fine-tune on omi-only
run_finetune "$DATA_OMI" "${ADAPTERS_DIR}/${short_name}_v2_omi"
start_backend "${ADAPTERS_DIR}/${short_name}_v2_omi"
run_eval "${short_name} v2 ft omi-only" "${REPORTS_DIR}/results_${short_name}_v2_ft_omi.json"

# 3) Compare
python "${PROJECT_ROOT}/evaluation/scripts/compare_runs.py" \
  "${REPORTS_DIR}/results_demo_baseline.json" \
  "${REPORTS_DIR}/results_${short_name}_base.json" \
  "${REPORTS_DIR}/results_${short_name}_v2_ft_full.json" \
  "${REPORTS_DIR}/results_${short_name}_v2_ft_omi.json" \
  --out "${REPORTS_DIR}/comparison.md"

echo "all done. report: ${REPORTS_DIR}/comparison.md"
pkill -f "uvicorn app.main" 2>/dev/null || true
