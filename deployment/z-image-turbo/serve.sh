#!/usr/bin/env bash
set -euo pipefail

MODEL="${MODEL:-Tongyi-MAI/Z-Image-Turbo}"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"

exec vllm serve "$MODEL" \
  --omni \
  --quantization bitsandbytes \
  --host "$HOST" \
  --port "$PORT"
