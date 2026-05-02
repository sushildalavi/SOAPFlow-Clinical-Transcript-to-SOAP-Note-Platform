#!/usr/bin/env bash
# LoRA fine-tune Qwen 2.5 with mlx-lm on Apple Silicon.
#
# Defaults are tuned for 16GB M-series Macs. Edit MODEL/ITERS/BATCH_SIZE
# to scale up if you have more headroom.
#
# Usage:
#   bash training/scripts/finetune_mlx.sh data/mlx adapters/qwen25_3b_full
#   MODEL=mlx-community/Qwen2.5-7B-Instruct-4bit \
#     bash training/scripts/finetune_mlx.sh data/mlx adapters/qwen25_7b_full

set -euo pipefail

DATA_DIR="${1:-data/mlx}"
ADAPTER_DIR="${2:-adapters/qwen25_3b_full}"
MODEL="${MODEL:-mlx-community/Qwen2.5-3B-Instruct-4bit}"
ITERS="${ITERS:-200}"
BATCH_SIZE="${BATCH_SIZE:-1}"
LR="${LR:-1e-4}"
NUM_LAYERS="${NUM_LAYERS:-8}"

mkdir -p "$ADAPTER_DIR"

echo "model=$MODEL data=$DATA_DIR adapter=$ADAPTER_DIR iters=$ITERS"
python -m mlx_lm lora \
  --model "$MODEL" \
  --train \
  --data "$DATA_DIR" \
  --iters "$ITERS" \
  --batch-size "$BATCH_SIZE" \
  --learning-rate "$LR" \
  --num-layers "$NUM_LAYERS" \
  --adapter-path "$ADAPTER_DIR" \
  --steps-per-report 10 \
  --steps-per-eval 50 \
  --save-every 100
